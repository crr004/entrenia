import uuid
from datetime import datetime, timezone
import logging
import os
from typing import Tuple, List, Optional, Dict

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

logger = logging.getLogger(__name__)
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
MODELS_DIR = os.path.join(MEDIA_ROOT, "models")


async def get_classifier_by_id(
    *, session: AsyncSession, id: uuid.UUID
) -> Optional[Classifier]:
    """Obtiene un clasificador por su ID."""

    stmt = select(Classifier).where(Classifier.id == id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_classifier_by_userid_and_name(
    *, session: AsyncSession, user_id: uuid.UUID, name: str
) -> Optional[Classifier]:
    """Obtiene un clasificador por el ID del usuario y su nombre."""

    stmt = select(Classifier).where(
        Classifier.user_id == user_id, Classifier.name == name
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_classifier(
    *, session: AsyncSession, user_id: uuid.UUID, classifier_in: ClassifierCreate
) -> Classifier:
    """Crea un nuevo clasificador en la base de datos."""

    classifier_data = classifier_in.model_dump()
    classifier = Classifier(user_id=user_id, **classifier_data)

    session.add(classifier)
    await session.commit()
    await session.refresh(classifier)

    return classifier


async def update_classifier(
    *, session: AsyncSession, classifier: Classifier, classifier_data: ClassifierUpdate
) -> Classifier:
    """Actualiza los datos de un clasificador."""

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
    """Actualiza el estado de entrenamiento y las métricas de un clasificador."""

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
    """Elimina un clasificador de la base de datos y sus archivos asociados."""

    # Eliminar archivo del modelo si existe.
    if classifier.file_path and os.path.exists(classifier.file_path):
        try:
            os.remove(classifier.file_path)
        except Exception as e:
            logger.error(
                f"Error deleting model file: {classifier.file_path} - {str(e)}"
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
