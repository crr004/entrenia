import os
import uuid
import logging
import contextlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Generator
import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_recall_fscore_support,
)
import tensorflow as tf

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
                architecture=classifier_architecture,
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

            # 5. Evaluar explícitamente el modelo en el conjunto de validación.
            eval_metrics = model.evaluate(val_ds, verbose=0)
            eval_results = dict(zip(model.metrics_names, eval_metrics))

            # 5.1 Inicializar diccionario de métricas con las métricas del historial.
            train_metrics = {}
            for k, v in history.history.items():
                train_metrics[k] = float(v[-1])  # Convertir valores a float para JSON.

            # 5.2 Añadir métricas de evaluación explícita pero mantener las originales.
            eval_metrics = model.evaluate(val_ds, verbose=0)
            eval_results = dict(zip(model.metrics_names, eval_metrics))

            # Solo actualizar métricas que no existan o que sean específicas de validación.
            for k, v in eval_results.items():
                if k not in train_metrics or k.startswith("val_"):
                    train_metrics[k] = float(v)

            # 5.3 Calcular matriz de confusión y métricas adicionales.
            y_true = []
            y_pred = []
            y_prob = []  # Para métricas adicionales como AUC, si se necesitan.

            # Recopilar predicciones y etiquetas reales del conjunto de validación.
            for images, labels in val_ds:
                predictions = model.predict(images, verbose=0)

                # Guardar las probabilidades/logits originales para posibles métricas adicionales.
                y_prob.extend(predictions)

                # Convertir predicciones a clases dependiendo de la arquitectura y tipo de salida.
                if classifier_architecture == "efficientnetb3" and num_classes == 2:
                    # EfficientNetB3 con 1 neurona de salida y sigmoid.
                    predicted_classes = (predictions > 0.5).astype(int).flatten()
                elif classifier_architecture == "xception_mini" and num_classes == 2:
                    # Xception Mini con 1 neurona de salida y sigmoid.
                    predicted_classes = (predictions > 0.5).astype(int).flatten()
                elif classifier_architecture == "resnet50" and num_classes == 2:
                    # ResNet50 con 1 neurona de salida y sigmoid.
                    predicted_classes = (predictions > 0.5).astype(int).flatten()
                else:
                    # Modelo multiclase.
                    predicted_classes = np.argmax(predictions, axis=1)

                # Extender listas con las nuevas predicciones y etiquetas.
                y_true.extend(labels.numpy())
                y_pred.extend(predicted_classes)

            # Calcular matriz de confusión.
            cm = confusion_matrix(y_true, y_pred)
            confusion_matrix_json = cm.tolist()

            # 5.4 Calcular accuracy a partir de la matriz de confusión para validar consistencia.
            accuracy_from_cm = (
                np.sum(np.diag(cm)) / np.sum(cm) if np.sum(cm) > 0 else 0.0
            )
            train_metrics["accuracy_from_confusion_matrix"] = float(accuracy_from_cm)

            # 5.5 Añadir matriz de confusión a las métricas.
            train_metrics["confusion_matrix"] = confusion_matrix_json

            # 5.6 Añadir métricas adicionales: precision, recall, f1.
            class_report = classification_report(
                y_true,
                y_pred,
                target_names=[index_to_label[i] for i in range(num_classes)],
                output_dict=True,
            )
            train_metrics["classification_report"] = class_report

            # Calcular precisión, recall y f1 por clase.
            precision, recall, f1, support = precision_recall_fscore_support(
                y_true, y_pred, average=None
            )

            # Añadir métricas por clase.
            for i in range(num_classes):
                class_name = index_to_label[i]
                train_metrics[f"precision_{class_name}"] = float(precision[i])
                train_metrics[f"recall_{class_name}"] = float(recall[i])
                train_metrics[f"f1_{class_name}"] = float(f1[i])

            # Añadir métricas promedio.
            train_metrics["precision_macro"] = float(np.mean(precision))
            train_metrics["recall_macro"] = float(np.mean(recall))
            train_metrics["f1_macro"] = float(np.mean(f1))

            # Calcular promedio ponderado.
            precision_weighted, recall_weighted, f1_weighted, _ = (
                precision_recall_fscore_support(y_true, y_pred, average="weighted")
            )
            train_metrics["precision_weighted"] = float(precision_weighted)
            train_metrics["recall_weighted"] = float(recall_weighted)
            train_metrics["f1_weighted"] = float(f1_weighted)

            # 5.7 Añadir información sobre las clases y la distribución.
            train_metrics["num_samples_per_class"] = {
                label: int(np.sum(np.array(y_true) == idx))
                for idx, label in index_to_label.items()
            }

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

            logger.info(f"Clasificador {classifier_uuid} entrenado exitosamente")
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
    metrics: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    model_path: Optional[str] = None,
) -> None:
    """Actualiza el estado de un clasificador en la base de datos.

    Args:
        classifier_uuid (uuid.UUID): UUID del clasificador.
        status (ClassifierTrainingStatus): Nuevo estado del clasificador.
        metrics (Optional[Dict[str, Any]]): Métricas del entrenamiento, incluye matriz de confusión.
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

        # Inicializar diccionario de métricas.
        current_metrics = dict(classifier.metrics or {})

        # Añadir o actualizar métricas si están presentes.
        if metrics:
            current_metrics.update(metrics)

        # Añadir mensaje de error a las métricas si está presente.
        if error_message:
            current_metrics["error_message"] = error_message

        # Actualizar las métricas solo si hay algo que actualizar.
        if current_metrics:
            classifier.metrics = current_metrics

        if model_path:
            classifier.file_path = model_path

        if status == ClassifierTrainingStatus.TRAINED:
            classifier.trained_at = datetime.now(timezone.utc)

        session.add(classifier)
