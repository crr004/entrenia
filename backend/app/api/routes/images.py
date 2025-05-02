import uuid

from fastapi import APIRouter, HTTPException, status

from app.models.images import ImageReturn, ImagesReturn, ImageUpdate
from app.models.messages import Message
from app.crud.users import SessionDep, CurrentUser
from app.crud.datasets import get_dataset_by_id
import app.crud.images as crud_images

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/dataset/{dataset_id}", response_model=ImagesReturn)
async def read_images(
    session: SessionDep,
    current_user: CurrentUser,
    dataset_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> ImagesReturn:
    """Obtiene imágenes de un dataset con soporte para ordenación y búsqueda:

        - Ordenación por: name, label, created_at.
        - Dirección de ordenación: asc o desc.
        - Paginación: usando parámetros skip y limit.
        - Búsqueda: filtra imágenes por nombre o etiqueta.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        dataset_id (uuid.UUID): ID del dataset del que obtener las imágenes.
        skip (int): Cantidad de imágenes a omitir (paginación).
        limit (int): Cantidad de imágenes a devolver (paginación).
        search (str | None): Texto a buscar en el nombre o etiqueta de la imagen.
        sort_by (str): Campo por el cual ordenar las imágenes.
        sort_order (str): Dirección de ordenación.

    Raises:
        HTTPException[400]: Si los parámetros sort_order o sort_by no son válidos.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.
        HTTPException[404]: Si no existe un dataset con ese ID.

    Returns:
        ImagesReturn: Lista de imágenes encontradas y su conteo total.
    """

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_order. Must be 'asc' or 'desc'",
        )

    valid_sort_fields = ["name", "label", "created_at"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}",
        )

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

    images, count = await crud_images.get_images_sorted(
        session=session,
        dataset_id=dataset_id,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    image_returns = [ImageReturn.model_validate(image) for image in images]

    return ImagesReturn(images=image_returns, count=count)


@router.get("/{image_id}", response_model=ImageReturn)
async def read_image(
    session: SessionDep, current_user: CurrentUser, image_id: uuid.UUID
) -> ImageReturn:
    """Devuelve los datos de una imagen específica dado su ID.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        image_id (uuid.UUID): ID de la imagen a buscar.

    Raises:
        HTTPException[404]: Si no existe una imagen con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        ImageReturn: Datos de la imagen.
    """

    image = await crud_images.get_image_by_id(session=session, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    dataset = await get_dataset_by_id(session=session, id=image.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    return ImageReturn.model_validate(image)


@router.patch("/{image_id}", response_model=ImageReturn)
async def update_image(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    image_id: uuid.UUID,
    image_in: ImageUpdate,
) -> ImageReturn:
    """Actualiza una imagen existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        image_id (uuid.UUID): ID de la imagen a actualizar.
        image_in (ImageUpdate): Datos de la imagen a actualizar.

    Raises:
        HTTPException[404]: Si no existe una imagen con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.
        HTTPException[409]: Si el nombre de la imagen ya existe en el dataset.

    Returns:
        ImageReturn: Datos de la imagen actualizada.
    """

    image = await crud_images.get_image_by_id(session=session, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    dataset = await get_dataset_by_id(session=session, id=image.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    if image_in.name and image_in.name != image.name:
        existing_image = await crud_images.get_image_by_datasetid_and_name(
            session=session, dataset_id=image.dataset_id, name=image_in.name
        )
        if existing_image and (existing_image.id != image_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The dataset already has an image with that name",
            )

    update_dict = image_in.model_dump(exclude_unset=True)
    updated_image = await crud_images.update_image(
        session=session, image=image, image_data=update_dict
    )

    return ImageReturn.model_validate(updated_image)


@router.delete("/{image_id}")
async def delete_image(
    session: SessionDep, current_user: CurrentUser, image_id: uuid.UUID
) -> Message:
    """Elimina una imagen existente.

    Args:
        session (SessionDep): Sesión de la base de datos.
        current_user (CurrentUser): Usuario actual.
        image_id (uuid.UUID): ID de la imagen a eliminar.

    Raises:
        HTTPException[404]: Si no existe una imagen con ese ID.
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        Message: Mensaje de confirmación.
    """

    image = await crud_images.get_image_by_id(session=session, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    dataset = await get_dataset_by_id(session=session, id=image.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if not current_user.is_admin and (dataset.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    await crud_images.delete_image(session=session, image=image)

    return Message(message="Image deleted successfully")


@router.get("/public-dataset/{dataset_id}", response_model=ImagesReturn)
async def read_public_dataset_images(
    session: SessionDep,
    dataset_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> ImagesReturn:
    """Obtiene imágenes de un dataset público sin requerir autenticación.

        - Ordenación por: name, label, created_at.
        - Dirección de ordenación: asc o desc.
        - Paginación: usando parámetros skip y limit.
        - Búsqueda: filtra imágenes por nombre o etiqueta.

    Args:
        session (SessionDep): Sesión de la base de datos.
        dataset_id (uuid.UUID): ID del dataset público del que obtener las imágenes.
        skip (int): Cantidad de imágenes a omitir (paginación).
        limit (int): Cantidad de imágenes a devolver (paginación).
        search (str | None): Texto a buscar en el nombre o etiqueta de la imagen.
        sort_by (str): Campo por el cual ordenar las imágenes.
        sort_order (str): Dirección de ordenación.

    Raises:
        HTTPException[400]: Si los parámetros sort_order o sort_by no son válidos.
        HTTPException[404]: Si no existe un dataset con ese ID o no es público.

    Returns:
        ImagesReturn: Lista de imágenes encontradas y su conteo total.
    """

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_order. Must be 'asc' or 'desc'",
        )

    valid_sort_fields = ["name", "label", "created_at"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}",
        )

    dataset = await get_dataset_by_id(session=session, id=dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    # Verificar que el dataset es público.
    if not dataset.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or not accessible",
        )

    images, count = await crud_images.get_images_sorted(
        session=session,
        dataset_id=dataset_id,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    image_returns = [ImageReturn.model_validate(image) for image in images]

    return ImagesReturn(images=image_returns, count=count)
