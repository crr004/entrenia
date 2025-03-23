import uuid

from fastapi import APIRouter, HTTPException, status

from app.models.datasets import (
    DatasetCreate,
    DatasetReturn,
    DatasetUpdate,
    DatasetsReturn,
    DatasetLabelDetailsReturn,
)
from app.models.messages import Message
from app.crud.users import SessionDep, CurrentUser, get_user_by_id
from app.crud.datasets import (
    get_dataset_by_id,
    get_dataset_by_userid_and_name,
    get_dataset_counts,
    get_dataset_label_details,
)
import app.crud.datasets as crud_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=DatasetsReturn)
async def read_datasets(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> DatasetsReturn:
    """Obtiene datasets con soporte para ordenación y búsqueda avanzados:

        - Ordenación por: name, created_at, image_count, category_count, is_public, username (solo admin).
        - Dirección de ordenación: asc o desc.
        - Paginación: usando parámetros skip y limit.
        - Búsqueda: filtra datasets por nombre o descripción (también por username si es admin).

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        skip (int): Cantidad de datasets a omitir (paginación).
        limit (int): Cantidad de datasets a devolver (paginación).
        search (str | None): Texto a buscar en el nombre o descripción del dataset (o username).
        sort_by (str): Campo por el cual ordenar los datasets.
        sort_order (str): Dirección de ordenación.


    Raises:
        HTTPException[400]: Si los parámetros sort_order o sort_by no son válidos.

    Returns:
        DatasetsReturn: Lista de datasets encontrados y su conteo total.
    """

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_order. Must be 'asc' or 'desc'",
        )

    valid_sort_fields = [
        "name",
        "created_at",
        "image_count",
        "category_count",
        "is_public",
    ]
    if current_user.is_admin:
        valid_sort_fields.append("username")

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}",
        )

    admin_view = current_user.is_admin
    user_id = None if admin_view else current_user.id

    result, count, includes_username = await crud_datasets.get_user_datasets_sorted(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=user_id,
        admin_view=admin_view,
    )

    dataset_returns = []

    # Manejar diferentes formatos de resultado según si incluyen usernames.
    # Por optimización de consultas, no se hace un join a la tabla de usuarios si no es necesario.
    # Por eso se diferencian estos dos casos.
    if includes_username:
        # La variable result contiene tuplas (dataset, username).
        for dataset, username in result:

            dataset_dict = dataset.model_dump()

            counts = await get_dataset_counts(session=session, dataset_id=dataset.id)

            dataset_dict["image_count"] = counts.get("image_count", 0)
            dataset_dict["category_count"] = counts.get("category_count", 0)
            dataset_dict["username"] = username

            dataset_returns.append(DatasetReturn(**dataset_dict))
    else:
        # La variable result contiene solo datasets.
        for dataset in result:

            dataset_dict = dataset.model_dump()

            counts = await get_dataset_counts(session=session, dataset_id=dataset.id)

            dataset_dict["image_count"] = counts.get("image_count", 0)
            dataset_dict["category_count"] = counts.get("category_count", 0)

            if admin_view:
                user = await get_user_by_id(session=session, id=dataset.user_id)
                if user:
                    dataset_dict["username"] = user.username

            dataset_returns.append(DatasetReturn(**dataset_dict))

    return DatasetsReturn(datasets=dataset_returns, count=count)


@router.get("/{dataset_id}", response_model=DatasetReturn)
async def read_dataset(
    session: SessionDep, current_user: CurrentUser, dataset_id: uuid.UUID
) -> DatasetReturn:
    """Devuelve los datos de un dataset específico dado su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        dataset_id (uuid.UUID): Id del dataset a buscar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        DatasetReturn: Datos del dataset.
    """

    # Se guarda is_admin al principio para evitar lazy loading.
    is_admin = bool(current_user.is_admin)

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    dataset_dict = dataset.model_dump()

    counts = await get_dataset_counts(session=session, dataset_id=dataset.id)

    dataset_dict["image_count"] = counts.get("image_count", 0)
    dataset_dict["category_count"] = counts.get("category_count", 0)

    if is_admin:
        user = await get_user_by_id(session=session, id=dataset.user_id)
        if user:
            dataset_dict["username"] = user.username

    return DatasetReturn(**dataset_dict)


@router.get("/{dataset_id}/label-details", response_model=DatasetLabelDetailsReturn)
async def read_dataset_label_details(
    session: SessionDep, current_user: CurrentUser, dataset_id: uuid.UUID
) -> DatasetLabelDetailsReturn:
    """Devuelve detalles de las etiquetas y categorías de un dataset específico.

    Args:
        session (SessionDep): Sesión de la base de datos.
        dataset_id (uuid.UUID): Id del dataset a buscar.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        DatasetLabelDetailsReturn: Detalles de etiquetas y categorías del dataset.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    details = await get_dataset_label_details(session=session, dataset_id=dataset_id)

    return DatasetLabelDetailsReturn(**details)


@router.post("/", response_model=DatasetReturn)
async def create_dataset(
    *, session: SessionDep, current_user: CurrentUser, dataset_in: DatasetCreate
) -> DatasetReturn:
    """Crea un nuevo dataset.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        dataset_in (DatasetCreate): Datos del dataset a crear.

    Raises:
        HTTPException[409]: Si el usuario ya tiene un dataset con ese nombre.

    Returns:
        DatasetReturn: Datos del dataset creado.
    """

    dataset = await get_dataset_by_userid_and_name(
        session=session, user_id=current_user.id, name=dataset_in.name
    )
    if dataset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user already has a dataset with that name",
        )

    dataset = await crud_datasets.create_dataset(
        session=session, user_id=current_user.id, dataset_in=dataset_in
    )

    return dataset


@router.patch("/{dataset_id}", response_model=DatasetReturn)
async def update_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_id: uuid.UUID,
    dataset_in: DatasetUpdate,
) -> DatasetReturn:
    """Actualiza un dataset existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        dataset_id (uuid.UUID): ID del dataset a actualizar.
        dataset_in (DatasetUpdate): Datos del dataset a actualizar.

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.
        HTTPException[409]: Si el usuario ya tiene un dataset con ese nombre.

    Returns:
        DatasetReturn: Datos del dataset actualizado.
    """

    # Se guarda is_admin al principio para evitar lazy loading.
    is_admin = bool(current_user.is_admin)

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    if dataset_in.name:
        existing_dataset = await get_dataset_by_userid_and_name(
            session=session, user_id=dataset.user_id, name=dataset_in.name
        )
        if existing_dataset and (existing_dataset.id != dataset_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user already has a dataset with that name",
            )

    update_dict = dataset_in.model_dump(exclude_unset=True)

    dataset = await crud_datasets.update_dataset(
        session=session, dataset=dataset, dataset_data=update_dict
    )

    dataset_dict = dataset.model_dump()

    counts = await get_dataset_counts(session=session, dataset_id=dataset.id)

    dataset_dict["image_count"] = counts.get("image_count", 0)
    dataset_dict["category_count"] = counts.get("category_count", 0)

    if is_admin:
        user = await get_user_by_id(session=session, id=dataset.user_id)
        if user:
            dataset_dict["username"] = user.username

    return DatasetReturn(**dataset_dict)


@router.delete("/{dataset_id}")
async def delete_dataset(
    session: SessionDep, current_user: CurrentUser, dataset_id: uuid.UUID
) -> Message:
    """Elimina un dataset existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        dataset_id (uuid.UUID): ID del dataset a eliminar.

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        Message: Mensaje de confirmación.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    await crud_datasets.delete_dataset(session=session, dataset=dataset)

    return Message(message="Dataset deleted successfully")
