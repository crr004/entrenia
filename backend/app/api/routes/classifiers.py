import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.models.classifiers import (
    ClassifierCreate,
    ClassifierReturn,
    ClassifierDetailReturn,
    ClassifiersReturn,
    ClassifierUpdate,
)
from app.models.messages import Message
from app.crud.users import (
    SessionDep,
    CurrentUser,
    get_user_by_id,
)
import app.crud.classifiers as crud_classifiers
import app.crud.datasets as crud_datasets

router = APIRouter(prefix="/classifiers", tags=["classifiers"])

VALID_ARCHITECTURES = ["resnet18", "resnet34", "resnet50", "mobilenet", "efficientnet"]


@router.get("/architectures", response_model=list[str])
async def get_available_architectures(current_user: CurrentUser) -> list[str]:
    """Devuelve la lista de arquitecturas de modelos disponibles.

    Args:
        current_user (CurrentUser): Usuario actual.

    Returns:
        List[str]: Lista de nombres de arquitecturas disponibles.
    """

    return VALID_ARCHITECTURES


@router.post("/", response_model=ClassifierReturn)
async def create_classifier(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    classifier_in: ClassifierCreate,
) -> ClassifierReturn:
    """Crea un nuevo clasificador.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        classifier_in (ClassifierCreate): Datos del clasificador a crear.

    Raises:
        HTTPException[403]: Si el usuario no tiene privilegios suficientes.
        HTTPException[409]: Si ya existe un clasificador con el mismo nombre para este usuario.
        HTTPException[404]: Si el dataset no existe.
        HTTPException[400]: Si la arquitectura seleccionada no es válida.

    Returns:
        ClassifierReturn: Datos del clasificador creado.
    """

    if classifier_in.architecture not in VALID_ARCHITECTURES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid architecture. Must be one of: {', '.join(VALID_ARCHITECTURES)}",
        )

    dataset = await crud_datasets.get_dataset_by_userid_and_name(
        session=session,
        user_id=current_user.id,
        name=classifier_in.dataset_name,
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with name '{classifier_in.dataset_name}' not found in your datasets",
        )

    # Verificar si ya existe un clasificador con el mismo nombre para este usuario.
    existing_classifier = await crud_classifiers.get_classifier_by_userid_and_name(
        session=session, user_id=current_user.id, name=classifier_in.name
    )
    if existing_classifier:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user already has a classifier with that name",
        )

    modified_classifier_data = classifier_in.model_dump()
    modified_classifier_data["dataset_id"] = dataset.id

    classifier = await crud_classifiers.create_classifier(
        session=session,
        user_id=current_user.id,
        classifier_in=ClassifierCreate(**modified_classifier_data),
    )

    classifier_dict = classifier.model_dump()

    return ClassifierReturn(**classifier_dict)


@router.get("/", response_model=ClassifiersReturn)
async def read_classifiers(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> ClassifiersReturn:
    """Obtiene clasificadores con soporte para ordenación y búsqueda avanzados:

        - Ordenación por: name, created_at, status, username (solo admin).
        - Dirección de ordenación: asc o desc.
        - Paginación: usando parámetros skip y limit.
        - Búsqueda: filtra clasificadores por nombre o descripción (también por username si es admin).

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        skip (int): Cantidad de clasificadores a omitir (paginación).
        limit (int): Cantidad de clasificadores a devolver (paginación).
        search (str | None): Texto a buscar en el nombre o descripción del clasificador (o username).
        sort_by (str): Campo por el cual ordenar los clasificadores.
        sort_order (str): Dirección de ordenación.

    Raises:
        HTTPException[400]: Si los parámetros sort_order o sort_by no son válidos.

    Returns:
        ClassifiersReturn: Lista de clasificadores encontrados y su conteo total.
    """

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_order. Must be 'asc' or 'desc'",
        )

    valid_sort_fields = ["name", "created_at", "status"]
    if current_user.is_admin:
        valid_sort_fields.append("username")

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}",
        )

    admin_view = current_user.is_admin
    user_id = None if admin_view else current_user.id

    classifiers_with_usernames, count = await crud_classifiers.get_classifiers_sorted(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=user_id,
        admin_view=admin_view,
    )

    classifier_returns = []
    for classifier, username in classifiers_with_usernames:
        classifier_dict = classifier.model_dump()
        classifier_dict["username"] = username
        classifier_returns.append(ClassifierReturn(**classifier_dict))

    return ClassifiersReturn(classifiers=classifier_returns, count=count)


@router.get("/{classifier_id}", response_model=ClassifierReturn)
async def read_classifier(
    session: SessionDep, current_user: CurrentUser, classifier_id: uuid.UUID
) -> ClassifierReturn:
    """Obtiene un clasificador por su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        classifier_id (uuid.UUID): ID del clasificador a obtener.

    Raises:
        HTTPException[404]: Si el clasificador no existe.
        HTTPException[403]: Si el usuario no tiene privilegios suficientes.

    Returns:
        ClassifierReturn: Datos básicos del clasificador.
    """

    classifier = await crud_classifiers.get_classifier_by_id(
        session=session, id=classifier_id
    )

    if not classifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classifier not found"
        )

    is_admin = current_user.is_admin
    if not is_admin and (classifier.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    classifier_dict = classifier.model_dump()

    # Añadir nombre de usuario si es administrador.
    if is_admin:
        user = await get_user_by_id(session=session, id=classifier.user_id)
        if user:
            classifier_dict["username"] = user.username
    else:
        classifier_dict["username"] = current_user.username

    return ClassifierReturn(**classifier_dict)


@router.get("/{classifier_id}/detail", response_model=ClassifierDetailReturn)
async def read_classifier_detail(
    session: SessionDep, current_user: CurrentUser, classifier_id: uuid.UUID
) -> ClassifierDetailReturn:
    """Obtiene información detallada de un clasificador por su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        classifier_id (uuid.UUID): ID del clasificador a obtener.

    Raises:
        HTTPException[404]: Si el clasificador no existe.
        HTTPException[403]: Si el usuario no tiene privilegios suficientes.

    Returns:
        ClassifierDetailReturn: Datos detallados del clasificador, incluyendo métricas,
        parámetros y nombre del dataset.
    """

    classifier = await crud_classifiers.get_classifier_by_id(
        session=session, id=classifier_id
    )

    if not classifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classifier not found"
        )

    is_admin = current_user.is_admin
    if not is_admin and (classifier.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    classifier_dict = classifier.model_dump()

    # Añadir nombre de usuario si es administrador.
    if is_admin:
        user = await get_user_by_id(session=session, id=classifier.user_id)
        if user:
            classifier_dict["username"] = user.username
    else:
        classifier_dict["username"] = current_user.username

    # Obtener y añadir el nombre del dataset si existe.
    if classifier.dataset_id:
        dataset = await crud_datasets.get_dataset_by_id(
            session=session, id=classifier.dataset_id
        )
        if dataset:
            classifier_dict["dataset_name"] = dataset.name
    else:
        classifier_dict["dataset_name"] = None

    return ClassifierDetailReturn(**classifier_dict)


@router.patch("/{classifier_id}", response_model=ClassifierReturn)
async def update_classifier(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    classifier_id: uuid.UUID,
    classifier_in: ClassifierUpdate,
) -> ClassifierReturn:
    """Actualiza un clasificador existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        classifier_id (uuid.UUID): ID del clasificador a actualizar.
        classifier_in (ClassifierUpdate): Datos del clasificador a actualizar.

    Raises:
        HTTPException[404]: Si el clasificador no existe.
        HTTPException[403]: Si el usuario no tiene privilegios suficientes.
        HTTPException[409]: Si ya existe un clasificador con el mismo nombre para este usuario.

    Returns:
        ClassifierReturn: Datos del clasificador actualizado.
    """

    classifier = await crud_classifiers.get_classifier_by_id(
        session=session, id=classifier_id
    )

    if not classifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classifier not found"
        )

    if not current_user.is_admin and (classifier.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    # Verificar si el nuevo nombre ya existe para otro clasificador del mismo usuario.
    if classifier_in.name and classifier_in.name != classifier.name:
        existing_classifier = await crud_classifiers.get_classifier_by_userid_and_name(
            session=session, user_id=classifier.user_id, name=classifier_in.name
        )
        if existing_classifier and (existing_classifier.id != classifier_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user already has a classifier with that name",
            )

    updated_classifier = await crud_classifiers.update_classifier(
        session=session, classifier=classifier, classifier_data=classifier_in
    )

    classifier_dict = updated_classifier.model_dump()

    return ClassifierReturn(**classifier_dict)


@router.delete("/{classifier_id}")
async def delete_classifier(
    session: SessionDep, current_user: CurrentUser, classifier_id: uuid.UUID
) -> Message:
    """Elimina un clasificador existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        classifier_id (uuid.UUID): ID del clasificador a eliminar.

    Raises:
        HTTPException[404]: Si el clasificador no existe.
        HTTPException[403]: Si el usuario no tiene privilegios suficientes.

    Returns:
        Message: Mensaje de éxito.
    """

    classifier = await crud_classifiers.get_classifier_by_id(
        session=session, id=classifier_id
    )

    if not classifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classifier not found"
        )

    if not current_user.is_admin and (classifier.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    await crud_classifiers.delete_classifier(session=session, classifier=classifier)

    return Message(message="Classifier deleted successfully")
