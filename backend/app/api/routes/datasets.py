import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from app.models.datasets import (
    DatasetCreate,
    DatasetReturn,
    DatasetUpdate,
    DatasetsReturn,
    DatasetLabelDetailsReturn,
    DatasetUploadResult,
    UnlabeledImagesResponse,
    CsvLabelData,
    CsvLabelingResponse,
)
from app.models.messages import Message
from app.crud.users import (
    SessionDep,
    CurrentUser,
    get_user_by_id,
)
from app.crud.datasets import (
    get_dataset_by_id,
    get_dataset_by_userid_and_name,
    get_dataset_counts,
    get_dataset_label_details,
    get_unlabeled_images,
    label_images_with_csv,
)
import app.crud.datasets as crud_datasets
import app.crud.images as crud_images

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/public", response_model=DatasetsReturn)
async def get_public_datasets(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
) -> DatasetsReturn:
    """Obtiene datasets públicos (campo is_public a true) con soporte para paginación y búsqueda.

    Args:
        session (SessionDep): Sesión de la base de datos.
        skip (int): Cantidad de datasets a omitir (paginación).
        limit (int): Cantidad de datasets a devolver (paginación).
        search (str | None): Texto a buscar en el usuario, nombre o descripción del dataset.

    Returns:
        DatasetsReturn: Lista de datasets públicos encontrados y su conteo total.
    """

    datasets, count = await crud_datasets.get_public_datasets(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
    )

    # Extraer datos tempranamente.
    # Esto soluciona el problema del contexto greenlet en caso de tener que actualizar el dataset en la misma consulta.
    dataset_info = []
    for dataset in datasets:
        dataset_info.append(
            {
                "dataset_id": dataset.id,
                "dataset_dict": dataset.model_dump(),
                "user_id": dataset.user_id,
            }
        )

    dataset_returns = []
    for data in dataset_info:
        counts = await get_dataset_counts(
            session=session, dataset_id=data["dataset_id"]
        )

        dataset_dict = data["dataset_dict"]
        dataset_dict["image_count"] = counts.get("image_count", 0)
        dataset_dict["category_count"] = counts.get("category_count", 0)

        # Obtener el nombre de usuario del propietario del dataset.
        user = await get_user_by_id(session=session, id=data["user_id"])
        if user:
            dataset_dict["username"] = user.username

        dataset_returns.append(DatasetReturn(**dataset_dict))

    return DatasetsReturn(datasets=dataset_returns, count=count)


@router.get("/public/{dataset_id}", response_model=DatasetReturn)
async def read_public_dataset(
    session: SessionDep,
    dataset_id: uuid.UUID,
    current_user: Optional[CurrentUser] = None,
) -> DatasetReturn:
    """Devuelve los datos de un dataset público específico sin requerir autenticación.

    Args:
        session (SessionDep): Sesión de la base de datos.
        dataset_id (uuid.UUID): Id del dataset a buscar.
        current_user (Optional[CurrentUser]): Usuario actual (opcional).

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el dataset no es público.

    Returns:
        DatasetReturn: Datos del dataset público.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    is_owner = current_user and (dataset.user_id == current_user.id)
    is_admin = current_user and current_user.is_admin

    if not dataset.is_public and not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This dataset is not public",
        )

    dataset_dict = dataset.model_dump()
    dataset_id_counts = dataset.id
    user_id = dataset.user_id

    counts = await get_dataset_counts(session=session, dataset_id=dataset_id_counts)
    dataset_dict["image_count"] = counts.get("image_count", 0)
    dataset_dict["category_count"] = counts.get("category_count", 0)

    user = await get_user_by_id(session=session, id=user_id)
    if user:
        dataset_dict["username"] = user.username

    return DatasetReturn(**dataset_dict)


@router.get(
    "/public/{dataset_id}/label-details", response_model=DatasetLabelDetailsReturn
)
async def read_public_dataset_label_details(
    session: SessionDep,
    dataset_id: uuid.UUID,
    current_user: Optional[CurrentUser] = None,
) -> DatasetLabelDetailsReturn:
    """Devuelve detalles de las etiquetas y categorías de un dataset público sin requerir autenticación.

    Args:
        session (SessionDep): Sesión de la base de datos.
        dataset_id (uuid.UUID): Id del dataset a buscar.
        current_user (Optional[CurrentUser]): Usuario actual (opcional).

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el dataset no es público.

    Returns:
        DatasetLabelDetailsReturn: Detalles de etiquetas y categorías del dataset público.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    is_owner = current_user and (dataset.user_id == current_user.id)
    is_admin = current_user and current_user.is_admin

    if not dataset.is_public and not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This dataset is not public",
        )

    details = await get_dataset_label_details(session=session, dataset_id=dataset_id)

    return DatasetLabelDetailsReturn(**details)


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
        # Extraer todos los datos necesarios de los resultados primero.
        # Esto soluciona el problema del contexto greenlet en caso de tener que actualizar el dataset en la misma consulta.
        dataset_info = []
        for dataset, username in result:
            dataset_info.append(
                {
                    "dataset_id": dataset.id,
                    "dataset_dict": dataset.model_dump(),
                    "username": username,
                    "user_id": dataset.user_id,
                }
            )

        # Usar los datos extraídos.
        for data in dataset_info:
            counts = await get_dataset_counts(
                session=session, dataset_id=data["dataset_id"]
            )

            dataset_dict = data["dataset_dict"]
            dataset_dict["image_count"] = counts.get("image_count", 0)
            dataset_dict["category_count"] = counts.get("category_count", 0)
            dataset_dict["username"] = data["username"]

            dataset_returns.append(DatasetReturn(**dataset_dict))
    else:
        # Extraer todos los datos necesarios de los resultados primero.
        dataset_info = []
        for dataset in result:
            dataset_info.append(
                {
                    "dataset_id": dataset.id,
                    "dataset_dict": dataset.model_dump(),
                    "user_id": dataset.user_id,
                }
            )

        # Usar los datos extraídos.
        for data in dataset_info:
            counts = await get_dataset_counts(
                session=session, dataset_id=data["dataset_id"]
            )

            dataset_dict = data["dataset_dict"]
            dataset_dict["image_count"] = counts.get("image_count", 0)
            dataset_dict["category_count"] = counts.get("category_count", 0)

            if admin_view:
                user = await get_user_by_id(session=session, id=data["user_id"])
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
    dataset_id_counts = dataset.id
    user_id = dataset.user_id

    counts = await get_dataset_counts(session=session, dataset_id=dataset_id_counts)
    dataset_dict["image_count"] = counts.get("image_count", 0)
    dataset_dict["category_count"] = counts.get("category_count", 0)

    if is_admin:
        user = await get_user_by_id(session=session, id=user_id)
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


@router.post(
    "/",
    response_model=DatasetReturn,
    status_code=status.HTTP_201_CREATED,
)
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
    dataset_id_counts = dataset.id
    user_id = dataset.user_id

    counts = await get_dataset_counts(session=session, dataset_id=dataset_id_counts)
    dataset_dict["image_count"] = counts.get("image_count", 0)
    dataset_dict["category_count"] = counts.get("category_count", 0)

    if is_admin:
        user = await get_user_by_id(session=session, id=user_id)
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


@router.post(
    "/{dataset_id}/upload-zip",
    response_model=DatasetUploadResult,
)
async def upload_zip_with_images(
    dataset_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    csv_file: Optional[UploadFile] = None,
    labeling_option: str = Form(default="none"),
) -> DatasetUploadResult:
    """Procesa un archivo ZIP con imágenes y opcionalmente etiquetas desde un CSV, para añadirlas a un dataset.

    Args:
        dataset_id (uuid.UUID): ID del dataset donde se subirán las imágenes.
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        file (UploadFile): Archivo ZIP con las imágenes.
        csv_file (Optional[UploadFile], optional): Archivo CSV con etiquetas. Default: None.
        labeling_option (str, optional): Opción de etiquetado ('none' o 'csv'). Default: "none".

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.
        HTTPException[400]: Si el archivo no es un ZIP válido.
        HTTPException[413]: Si el archivo excede el tamaño máximo permitido.

    Returns:
        DatasetUploadResult: Resultado del procesamiento con estadísticas detalladas.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    if not current_user.is_admin and dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    # Verificar extensión del archivo.
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must be a ZIP file",
        )

    # Verificar tamaño máximo (150MB).
    file_content = await file.read()
    max_size = 150 * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum allowed (150MB)",
        )

    # Procesar el CSV si se proporciona.
    csv_data = {}
    if labeling_option == "csv" and csv_file:
        csv_data = await crud_images.process_csv_file(csv_file)

    # Procesar las imágenes del ZIP.
    stats = await crud_images.process_zip_with_images(
        session=session,
        dataset_id=dataset_id,
        zip_content=file_content,
        csv_data=csv_data,
    )

    # Calcular etiquetas no aplicadas.
    labels_skipped = len(csv_data) - stats["labels_applied"] if csv_data else 0

    return DatasetUploadResult(
        message="ZIP file processed successfully",
        processed_images=stats["processed_images"],
        skipped_images=stats["skipped_images"],
        invalid_images=stats["invalid_images"],
        labels_applied=stats["labels_applied"],
        labels_skipped=labels_skipped,
        invalid_image_details=stats.get("invalid_image_details", []),
        duplicated_image_details=stats.get("duplicated_image_details", []),
        skipped_label_details=stats.get("skipped_label_details", []),
    )


@router.get("/{dataset_id}/unlabeled-images", response_model=UnlabeledImagesResponse)
async def read_unlabeled_images(
    dataset_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> UnlabeledImagesResponse:
    """Obtiene todas las imágenes sin etiquetar de un dataset dado su ID.

    Args:
        dataset_id (uuid.UUID): ID del dataset
        session (SessionDep): Sesión de base de datos
        current_user (CurrentUser): Usuario actual

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        UnlabeledImagesResponse: Lista de imágenes sin etiquetar.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    if dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    images = await get_unlabeled_images(session=session, dataset_id=dataset_id)

    return UnlabeledImagesResponse(images=images)


@router.post("/{dataset_id}/csv-label", response_model=CsvLabelingResponse)
async def process_csv_labeling(
    dataset_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    csv_data: CsvLabelData,
) -> CsvLabelingResponse:
    """Etiqueta múltiples imágenes basadas en datos CSV.

    Args:
        dataset_id (uuid.UUID): ID del dataset
        session (SessionDep): Sesión de base de datos
        current_user (CurrentUser): Usuario actual
        csv_data (CsvLabelData): Datos con mapeo de nombres de imagen a etiquetas

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        CsvLabelingResponse: Estadísticas del proceso de etiquetado.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    if dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    result = await label_images_with_csv(
        session=session, dataset_id=dataset_id, labels_data=csv_data.labels
    )

    return CsvLabelingResponse(
        labeled_count=result["labeled_count"],
        not_found_count=result["not_found_count"],
        not_found_details=result["not_found_details"],
    )


@router.post("/{dataset_id}/clone", response_model=DatasetReturn)
async def clone_public_dataset(
    dataset_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> DatasetReturn:
    """Clona (añade una copia) un dataset público a la biblioteca personal del usuario.

    Args:
        dataset_id (uuid.UUID): ID del dataset a clonar.
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.

    Raises:
        HTTPException[404]: Si no existe un dataset con ese ID.
        HTTPException[403]: Si el dataset no es público.
        HTTPException[409]: Si el usuario es el propietario del dataset original.

    Returns:
        DatasetReturn: Datos del dataset clonado.
    """

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    if not dataset.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The dataset is not public and cannot be cloned",
        )

    if dataset.user_id == current_user.id:
        # Si el usuario ya es propietario, redireccionar a la vista de detalle.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already own this dataset",
            headers={"x-dataset-id": str(dataset_id)},
        )

    # Obtener el nombre de usuario del propietario original.
    source_user = await get_user_by_id(session=session, id=dataset.user_id)
    if not source_user:
        source_username = "Unknown"
    else:
        source_username = source_user.username

    try:
        cloned_dataset = await crud_datasets.clone_dataset(
            session=session,
            source_dataset_id=dataset_id,
            target_user_id=current_user.id,
            source_username=source_username,
        )

        dataset_dict = cloned_dataset.model_dump()
        cloned_dataset_id = cloned_dataset.id

        # Obtener conteos.
        counts = await get_dataset_counts(session=session, dataset_id=cloned_dataset_id)
        dataset_dict["image_count"] = counts.get("image_count", 0)
        dataset_dict["category_count"] = counts.get("category_count", 0)

        # Añadir el nombre del usuario origen.
        dataset_dict["username"] = source_username

        return DatasetReturn(**dataset_dict)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cloning dataset: {str(e)}",
        )
