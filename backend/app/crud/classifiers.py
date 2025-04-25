import uuid
from datetime import datetime, timezone
import logging
import os
from typing import Tuple, List, Optional, Dict, Any
import base64
import io
import numpy as np
from PIL import Image as PILImage
import tensorflow as tf

from sqlalchemy import or_, desc, asc, func
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classifiers import (
    Classifier,
    ClassifierCreate,
    ClassifierUpdate,
    ClassifierTrainingStatus,
)
from app.models.users import User
from app.tasks.celery_app import train_model
from app.ml.model_utils import load_model, load_model_metadata

logger = logging.getLogger(__name__)
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
MODELS_DIR = os.path.join(MEDIA_ROOT, "models")


async def get_classifier_by_id(
    *, session: AsyncSession, id: uuid.UUID
) -> Optional[Classifier]:
    """Obtiene un clasificador por su ID.

    Args:
        session: Sesión de base de datos.
        id: ID del clasificador.

    Returns:
        Classifier: Clasificador encontrado o None si no existe.
    """

    stmt = select(Classifier).where(Classifier.id == id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_classifier_by_userid_and_name(
    *, session: AsyncSession, user_id: uuid.UUID, name: str
) -> Optional[Classifier]:
    """Obtiene un clasificador por el ID del usuario y su nombre.

    Args:
        session: Sesión de base de datos.
        user_id: ID del usuario propietario.
        name: Nombre del clasificador.

    Returns:
        Classifier: Clasificador encontrado o None si no existe.
    """

    stmt = select(Classifier).where(
        Classifier.user_id == user_id, Classifier.name == name
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_classifier(
    *, session: AsyncSession, user_id: uuid.UUID, classifier_in: ClassifierCreate
) -> Classifier:
    """Crea un nuevo clasificador en la base de datos.

    Args:
        session: Sesión de base de datos.
        user_id: ID del usuario propietario.
        classifier_in: Datos del clasificador a crear.

    Returns:
        Classifier: Clasificador creado.
    """

    classifier_data = classifier_in.model_dump()

    if (
        "model_parameters" not in classifier_data
        or classifier_data["model_parameters"] is None
    ):
        classifier_data["model_parameters"] = {}

    default_params = {
        "learning_rate": 0.001,
        "epochs": 20,
        "batch_size": 32,
        "validation_split": 0.2,
    }

    for param, default_value in default_params.items():
        if param not in classifier_data["model_parameters"]:
            classifier_data["model_parameters"][param] = default_value

    classifier = Classifier(
        user_id=user_id,
        status=ClassifierTrainingStatus.TRAINING,
        metrics=None,
        **classifier_data,
    )

    classifier_id = classifier.id
    dataset_id = classifier.dataset_id
    classifier_architecture = classifier.architecture
    model_parameters = classifier.model_parameters

    architecture = classifier_data["architecture"]
    if architecture == "xception_mini":
        image_size = [180, 180]
    elif architecture == "efficientnetb3":
        image_size = [300, 300]
    elif architecture == "resnet50":
        image_size = [224, 224]
    else:
        image_size = [180, 180]

    model_parameters["image_size"] = image_size

    session.add(classifier)
    await session.commit()
    await session.refresh(classifier)

    await start_training_task(
        classifier_id=classifier_id,
        dataset_id=dataset_id,
        classifier_architecture=classifier_architecture,
        model_parameters=model_parameters,
    )

    return classifier


async def update_classifier(
    *, session: AsyncSession, classifier: Classifier, classifier_data: ClassifierUpdate
) -> Classifier:
    """Actualiza los datos de un clasificador.

    Args:
        session: Sesión de base de datos.
        classifier: Clasificador a actualizar.
        classifier_data: Datos actualizados del clasificador.

    Returns:
        Classifier: Clasificador actualizado.
    """

    classifier_update = classifier_data.model_dump(exclude_unset=True)
    classifier.sqlmodel_update(classifier_update)

    session.add(classifier)
    await session.commit()
    await session.refresh(classifier)

    return classifier


async def update_classifier_training_status(
    *,
    session: AsyncSession,
    classifier_id: uuid.UUID,
    status: ClassifierTrainingStatus,
    metrics: Optional[Dict[str, float]] = None,
    error_message: Optional[str] = None,
) -> Optional[Classifier]:
    """Actualiza el estado de entrenamiento y las métricas de un clasificador.

    Args:
        session: Sesión de base de datos.
        classifier_id: ID del clasificador.
        status: Nuevo estado de entrenamiento.
        metrics: Métricas opcionales.
        error_message: Mensaje de error opcional.

    Returns:
        Classifier: Clasificador actualizado o None si no se encontró.
    """

    classifier = await get_classifier_by_id(session=session, id=classifier_id)
    if not classifier:
        return None

    classifier.status = status

    if metrics:
        classifier.metrics = metrics

    if status == ClassifierTrainingStatus.TRAINED:
        classifier.trained_at = datetime.now(timezone.utc)

    session.add(classifier)
    await session.commit()
    await session.refresh(classifier)

    return classifier


async def delete_classifier(*, session: AsyncSession, classifier: Classifier) -> None:
    """Elimina un clasificador de la base de datos y sus archivos asociados.

    Args:
        session: Sesión de base de datos.
        classifier: Clasificador a eliminar.

    Returns:
        None
    """

    # Eliminar archivos del modelo si existen.
    if classifier.file_path:
        try:
            # Directorio que contiene el modelo y sus metadatos.
            model_dir = os.path.join(MEDIA_ROOT, classifier.file_path)
            if os.path.exists(model_dir):
                # Eliminar el archivo del modelo.
                model_file = os.path.join(model_dir, "model.keras")
                if os.path.exists(model_file):
                    os.remove(model_file)

                # Eliminar el archivo de metadatos.
                metadata_file = os.path.join(model_dir, "metadata.json")
                if os.path.exists(metadata_file):
                    os.remove(metadata_file)

                # Eliminar el directorio.
                try:
                    os.rmdir(model_dir)
                except OSError as e:
                    logger.warning(f"Error deleting directory at {model_dir}: {str(e)}")
        except Exception as e:
            logger.error(
                f"Error deleting model files at {model_dir}: {str(e)}", exc_info=True
            )

    # Eliminar el clasificador de la base de datos.
    await session.delete(classifier)
    await session.commit()


async def get_classifiers_sorted(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user_id: Optional[uuid.UUID] = None,
    admin_view: bool = False,
) -> Tuple[List[Tuple[Classifier, str]], int]:
    """Obtiene una lista paginada de clasificadores con ordenación y filtrado.

    Args:
        session: Sesión de base de datos.
        skip: Número de registros a omitir.
        limit: Número máximo de registros a devolver.
        search: Término de búsqueda para nombre y descripción.
        sort_by: Campo por el que ordenar.
        sort_order: Orden ascendente o descendente.
        user_id: ID del usuario propietario (None si es administrador).
        admin_view: Indica si la vista es para administradores.

    Returns:
        Clasificadores encontrados con nombres de usuario y conteo total.
    """

    # Crear término de búsqueda si existe.
    search_term = f"%{search.strip()}%" if search and search.strip() else None

    # Consulta base con join a la tabla de usuarios para obtener el username.
    query = select(Classifier, User.username).join(User, Classifier.user_id == User.id)

    # Aplicar filtro de usuario si no es administrador o si se especifica un usuario.
    if not admin_view and user_id is not None:
        query = query.where(Classifier.user_id == user_id)

    # Aplicar búsqueda si se proporciona.
    if search_term:
        if admin_view:
            # Para administradores, buscar también por nombre de usuario.
            query = query.where(
                or_(
                    Classifier.name.ilike(search_term),
                    Classifier.description.ilike(search_term),
                    User.username.ilike(search_term),
                )
            )
        else:
            # Para usuarios normales, buscar solo en sus clasificadores.
            query = query.where(
                or_(
                    Classifier.name.ilike(search_term),
                    Classifier.description.ilike(search_term),
                )
            )

    # Aplicar ordenación.
    if sort_by == "name":
        query = query.order_by(
            asc(Classifier.name) if sort_order == "asc" else desc(Classifier.name)
        )
    elif sort_by == "status":
        query = query.order_by(
            asc(Classifier.status) if sort_order == "asc" else desc(Classifier.status)
        )
    elif sort_by == "username" and admin_view:
        query = query.order_by(
            asc(User.username) if sort_order == "asc" else desc(User.username)
        )
    else:  # created_at por defecto.
        query = query.order_by(
            asc(Classifier.created_at)
            if sort_order == "asc"
            else desc(Classifier.created_at)
        )

    # Consulta para contar el total de resultados.
    count_query = select(func.count()).select_from(
        select(Classifier.id)
        .join(User, Classifier.user_id == User.id)
        .where(
            *(
                [Classifier.user_id == user_id]
                if not admin_view and user_id is not None
                else []
            )
        )
        .where(
            *(
                [
                    or_(
                        Classifier.name.ilike(search_term),
                        Classifier.description.ilike(search_term),
                        User.username.ilike(search_term) if admin_view else False,
                    )
                ]
                if search_term
                else []
            )
        )
        .subquery()
    )

    # Obtener conteo total.
    count_result = await session.execute(count_query)
    total_count = count_result.scalar_one() or 0

    # Aplicar paginación.
    query = query.offset(skip).limit(limit)

    # Ejecutar consulta.
    result = await session.execute(query)
    classifiers_with_usernames = [
        (classifier, username) for classifier, username in result
    ]

    return classifiers_with_usernames, total_count


async def start_training_task(
    classifier_id: uuid.UUID,
    dataset_id: uuid.UUID,
    classifier_architecture: str,
    model_parameters: Dict[str, Any],
) -> bool:
    """Inicia una tarea para entrenar un clasificador.

    Args:
        classifier_id: ID del clasificador.
        dataset_id: ID del dataset.
        classifier_architecture: Arquitectura del modelo.
        model_parameters: Parámetros de entrenamiento.

    Returns:
        bool: True si la tarea se inició correctamente, False en caso contrario.
    """

    try:
        train_model.delay(
            classifier_id=str(classifier_id),
            dataset_id=str(dataset_id),
            classifier_architecture=classifier_architecture,
            model_parameters=model_parameters,
        )
        return True
    except Exception as e:
        logger.error(f"Error while initializing training for {classifier_id}: {str(e)}")
        return False


async def perform_inference(
    *, classifier: Classifier, image_files: List[bytes], filenames: List[str]
) -> Dict[str, Any]:
    """Realiza inferencia usando un modelo entrenado en un lote de imágenes.

    Args:
        classifier: Clasificador con modelo entrenado.
        image_files: Lista con los datos binarios de las imágenes.
        filenames: Lista con los nombres de los archivos de imagen.

    Returns:
        Dict: Resultados de la inferencia para cada imagen.
    """

    if (
        not classifier.file_path
        or classifier.status != ClassifierTrainingStatus.TRAINED
    ):
        raise ValueError("Model is not trained or file path is missing")

    # Preparar rutas de archivos.
    model_dir = os.path.join(MEDIA_ROOT, classifier.file_path)
    model_path = os.path.join(model_dir, "model.keras")

    # Cargar metadatos del modelo.
    try:
        metadata = load_model_metadata(model_dir)
    except Exception as e:
        logger.error(f"Error loading model metadata: {str(e)}", exc_info=True)
        raise ValueError(f"Error loading model metadata: {str(e)}")

    # Obtener mapping de clases y parámetros de entrenamiento.
    class_mapping = metadata.get("class_mapping", {})
    image_size = metadata.get("train_params", {}).get("image_size", [180, 180])
    num_classes = len(class_mapping)

    # Cargar el modelo.
    try:
        tf.keras.backend.clear_session()  # Limpiar sesión para evitar problemas.
        model = load_model(model_path)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        raise ValueError(f"Error loading model: {str(e)}")

    # Definir preprocesamiento específico según arquitectura.
    def get_preprocessor(architecture):
        # Función identidad para modelos que ya incluyen normalización.
        def preprocess_identity(img_array):
            return img_array

        # Para modelos sin normalización interna.
        def preprocess_default(img_array):
            return img_array / 255.0

        # Seleccionar el preprocesador adecuado según el modelo.
        if architecture in ["xception_mini", "efficientnetb3", "resnet50"]:
            return preprocess_identity
        else:
            return preprocess_default

    # Seleccionar el preprocesador adecuado.
    preprocessor = get_preprocessor(classifier.architecture)

    # Función para preprocesar imágenes.
    def preprocess_image(img_data: bytes) -> np.ndarray:
        try:
            img = PILImage.open(io.BytesIO(img_data))
            img = img.convert("RGB")  # Asegurar que sea RGB.
            img = img.resize(tuple(image_size))
            img_array = np.array(img)
            img_array = preprocessor(
                img_array
            )  # Aplicar el preprocesamiento específico del modelo.
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}", exc_info=True)
            raise ValueError(f"Error preprocessing image: {str(e)}")

    # Procesar cada imagen.
    results = []
    for i, img_data in enumerate(image_files):
        filename = filenames[i] if i < len(filenames) else f"image_{i}.jpg"

        try:
            # Preprocesar imagen.
            img_array = preprocess_image(img_data)

            # Añadir batch dimension.
            img_batch = np.expand_dims(img_array, 0)

            # Realizar predicción.
            predictions = model.predict(img_batch, verbose=0)

            # Formatear resultados según tipo de modelo (binario o multiclase).
            if num_classes == 2:
                score = float(predictions[0][0])
                class_predictions = {
                    class_mapping["0"]: float(1 - score),
                    class_mapping["1"]: float(score),
                }
                predicted_class = (
                    class_mapping["1"] if score > 0.5 else class_mapping["0"]
                )
                confidence = max(score, 1 - score)
            else:
                # Modelo multiclase.
                probabilities = predictions[0]
                class_predictions = {
                    class_mapping[str(i)]: float(prob)
                    for i, prob in enumerate(probabilities)
                }
                predicted_idx = np.argmax(probabilities)
                predicted_class = class_mapping[str(predicted_idx)]
                confidence = float(probabilities[predicted_idx])

            # Generar miniatura para incluir en resultados.
            img = PILImage.open(io.BytesIO(img_data))
            img.thumbnail((100, 100))
            img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            thumbnail = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Añadir resultado.
            results.append(
                {
                    "filename": filename,
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "all_predictions": class_predictions,
                    "thumbnail": thumbnail,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.error(f"Error processing image {filename}: {str(e)}", exc_info=True)
            results.append({"filename": filename, "error": str(e), "status": "failed"})

    return {
        "results": results,
        "model_name": classifier.name,
        "processed_images": len(results),
        "classifier_id": str(classifier.id),
    }
