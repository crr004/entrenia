import os
import uuid
import logging
import contextlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Generator

from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.classifiers import Classifier, ClassifierTrainingStatus

from app.ml.models import AVAILABLE_MODELS
from app.ml.data_utils import extract_dataset_from_db, prepare_dataset
from app.ml.model_utils import save_trained_model

# Configuración del broker y backend de resultados.
broker_url = os.environ["BROKER_URL"]
result_backend = os.environ["RESULT_BACKEND"]
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Directorios de modelos.
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
MODELS_DIR = os.path.join(MEDIA_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

app = Celery("entrenia", broker=broker_url, backend=result_backend)

app.conf.update(
    task_serializer=task_serializer,
    result_serializer=result_serializer,
    accept_content=accept_content,
    broker_connection_retry_on_startup=True,
    # Configuraciones adicionales para producción:
    worker_max_tasks_per_child=200,  # Reiniciar trabajadores para prevenir fugas de memoria.
    broker_transport_options={"visibility_timeout": 21600},  # 6 horas.
    task_acks_late=True,  # Confirmar tarea después de finalizar.
    task_reject_on_worker_lost=True,  # Rechazar tareas si el worker muere.
)

# Configuración de base de datos específica para Celery (contexto síncrono).
SYNC_DB_URL = os.environ["POSTGRES_URL"]
sync_engine = create_engine(SYNC_DB_URL)
sync_session_factory = sessionmaker(sync_engine, expire_on_commit=False)


@contextlib.contextmanager
def get_celery_session() -> Generator[Session, None, None]:
    """Genera una nueva sesión síncrona de la base de datos para uso de Celery."""

    session = sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.task(name="train_model", bind=True, max_retries=3)
def train_model(
    self,
    classifier_id: str,
    dataset_id: str,
    classifier_architecture: str,
    model_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """Entrena un modelo de clasificación de imágenes.

    Args:
        self: Instancia de la tarea (requerido para bind=True).
        classifier_id: ID del clasificador en formato string.
        dataset_id: ID del dataset para entrenar.
        classifier_architecture: Arquitectura del modelo a entrenar.
        model_parameters: Parámetros de entrenamiento del modelo.

    Returns:
        dict: Resultado de la operación con el estado del clasificador.
    """

    classifier_uuid = uuid.UUID(classifier_id)
    dataset_uuid = uuid.UUID(dataset_id)

    learning_rate = model_parameters.get("learning_rate", 0.001)
    batch_size = model_parameters.get("batch_size", 32)
    epochs = model_parameters.get("epochs", 20)
    validation_split = model_parameters.get("validation_split", 0.2)
    image_size_raw = model_parameters.get("image_size", [180, 180])

    # Convertir image_size a tupla si es lista (para compatibilidad con JSON).
    image_size = (
        tuple(image_size_raw) if isinstance(image_size_raw, list) else image_size_raw
    )

    # Verificar que la arquitectura está disponible.
    if classifier_architecture not in AVAILABLE_MODELS:
        error_msg = f"Arquitectura no disponible: {classifier_architecture}"
        logger.error(error_msg)
        update_classifier_status(
            classifier_uuid=classifier_uuid,
            status=ClassifierTrainingStatus.FAILED,
            error_message=error_msg,
        )
        return {"status": "error", "classifier_id": classifier_id, "error": error_msg}

    try:
        # 1. Obtener imágenes del dataset.
        with get_celery_session() as session:
            from app.models.images import Image

            stmt = select(Image).where(Image.dataset_id == dataset_uuid)
            images = session.execute(stmt).scalars().all()
            # logger.info(f"Dataset {dataset_uuid} contiene {len(images)} imágenes")

            # 2. Extraer datos de imágenes etiquetadas.
            image_paths, labels, label_to_index, index_to_label = (
                extract_dataset_from_db(images, MEDIA_ROOT)
            )

            num_classes = len(label_to_index)
            if num_classes < 2:
                error_msg = f"Se necesitan al menos 2 clases distintas para entrenar (encontradas: {num_classes})"
                logger.error(error_msg)
                update_classifier_status(
                    classifier_uuid=classifier_uuid,
                    status=ClassifierTrainingStatus.FAILED,
                    error_message=error_msg,
                )
                return {
                    "status": "error",
                    "classifier_id": classifier_id,
                    "error": error_msg,
                }

            # logger.info(f"Preparando entrenamiento con {len(image_paths)} imágenes y {num_classes} clases")

            # 3. Preparar datasets de entrenamiento y validación.
            train_ds, val_ds, dataset_info = prepare_dataset(
                image_paths,
                labels,
                label_to_index,
                validation_split=validation_split,
                batch_size=batch_size,
                image_size=image_size,
            )

            # 4. Obtener el módulo del modelo seleccionado y entrenar.
            model_module = AVAILABLE_MODELS[classifier_architecture]
            model, history = model_module.train(
                train_ds,
                val_ds,
                num_classes,
                epochs=epochs,
                learning_rate=learning_rate,
            )

            # 5. Guardar métricas del entrenamiento.
            train_metrics = {}
            for k, v in history.history.items():
                train_metrics[k] = float(v[-1])  # Convertir valores a float para JSON.

            # 6. Preparar metadatos del modelo.
            metadata = {
                "architecture": classifier_architecture,
                "training_date": datetime.now(timezone.utc).isoformat(),
                "num_classes": num_classes,
                "class_mapping": {
                    str(idx): label for idx, label in index_to_label.items()
                },
                "metrics": train_metrics,
                "train_params": {
                    "epochs": len(history.history["loss"]),
                    "batch_size": batch_size,
                    "validation_split": validation_split,
                    "learning_rate": learning_rate,
                    "image_size": image_size_raw,  # Guardar como lista para compatibilidad con JSON.
                },
            }

            # 7. Guardar modelo entrenado.
            model_rel_path = save_trained_model(
                model, MODELS_DIR, metadata, classifier_id
            )

            # 8. Actualizar estado del clasificador en la BD.
            update_classifier_status(
                classifier_uuid=classifier_uuid,
                status=ClassifierTrainingStatus.TRAINED,
                metrics=train_metrics,
                model_path=model_rel_path,
            )

            # logger.info(f"Clasificador {classifier_uuid} entrenado exitosamente")
            return {
                "status": "success",
                "classifier_id": classifier_id,
                "metrics": train_metrics,
                "file_path": model_rel_path,
            }

    except Exception as e:
        logger.error(f"Error while training the classifier {classifier_uuid}: {str(e)}")

        try:
            update_classifier_status(
                classifier_uuid=classifier_uuid,
                status=ClassifierTrainingStatus.FAILED,
                error_message=str(e),
            )
        except Exception as inner_e:
            logger.error(f"Error while updating failed state: {str(inner_e)}")

        if isinstance(e, (ConnectionError, TimeoutError)):
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {"status": "error", "classifier_id": classifier_id, "error": str(e)}


def update_classifier_status(
    classifier_uuid: uuid.UUID,
    status: ClassifierTrainingStatus,
    metrics: Optional[Dict[str, float]] = None,
    error_message: Optional[str] = None,
    model_path: Optional[str] = None,
) -> None:
    """Actualiza el estado de un clasificador en la base de datos.

    Args:
        classifier_uuid (uuid.UUID): UUID del clasificador.
        status (ClassifierTrainingStatus): Nuevo estado del clasificador.
        metrics (Optional[Dict[str, float]]): Métricas del entrenamiento.
        error_message (Optional[str]): Mensaje de error si aplica.
        model_path (Optional[str]): Ruta al modelo guardado.

    Returns:
        None
    """

    with get_celery_session() as session:
        stmt = select(Classifier).where(Classifier.id == classifier_uuid)
        classifier = session.execute(stmt).scalar_one_or_none()

        if not classifier:
            logger.error(f"Classifier not found: {classifier_uuid}")
            return

        classifier.status = status

        if metrics:
            classifier.metrics = metrics

        if error_message:
            current_params = dict(classifier.model_parameters or {})
            current_params["error"] = error_message
            classifier.model_parameters = current_params

        if model_path:
            classifier.file_path = model_path

        if status == ClassifierTrainingStatus.TRAINED:
            classifier.trained_at = datetime.now(timezone.utc)

        session.add(classifier)
