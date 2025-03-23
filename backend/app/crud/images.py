import uuid

from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.images import Image, ImageUpdate


async def get_image_by_id(*, session: AsyncSession, id: uuid.UUID) -> Image | None:
    """Obtiene una imagen dado su ID.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        id (uuid.UUID): ID de la imagen.

    Returns:
        Image | None: Imagen encontrada o None si no existe.
    """

    image = await session.get(Image, id)
    if not image:
        return None
    return image


async def get_image_by_datasetid_and_name(
    *, session: AsyncSession, dataset_id: uuid.UUID, name: str
) -> Image | None:
    """Obtiene una imagen dado el ID del dataset y el nombre de la imagen.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset al que pertenece la imagen.
        name (str): Nombre de la imagen.

    Returns:
        Image | None: Imagen encontrada o None si no existe.
    """

    statement = select(Image).where(Image.dataset_id == dataset_id, Image.name == name)
    res = await session.execute(statement)
    image = res.scalars().first()
    if not image:
        return None
    return image


async def get_images_sorted(
    *,
    session: AsyncSession,
    dataset_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Image], int]:
    """Obtiene imágenes con ordenación y búsqueda.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset al que pertenecen las imágenes.
        skip (int): Cantidad de imágenes a omitir (paginación).
        limit (int): Cantidad de imágenes a devolver (paginación).
        search (str | None): Término de búsqueda para nombre o etiqueta.
        sort_by (str): Campo por el que ordenar. Puede ser 'name', 'label' o 'created_at'.
        sort_order (str): Orden de la ordenación. Puede ser 'asc' o 'desc'.

    Returns:
        tuple[list[Image], int]: Imágenes encontradas y conteo total.
    """

    # Crear la consulta base.
    query = select(Image).where(Image.dataset_id == dataset_id)
    count_query = select(func.count()).select_from(
        select(Image.id).where(Image.dataset_id == dataset_id)
    )

    # Aplicar búsqueda si se proporciona un término de búsqueda.
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.where(
            Image.name.ilike(search_term)
            | (Image.label.ilike(search_term) & Image.label.is_not(None))
        )
        count_query = select(func.count()).select_from(
            select(Image.id)
            .where(
                Image.dataset_id == dataset_id,
                Image.name.ilike(search_term)
                | (Image.label.ilike(search_term) & Image.label.is_not(None)),
            )
            .subquery()
        )

    # Aplicar ordenación según el campo y dirección especificados.
    if sort_by == "name":
        query = query.order_by(
            Image.name.asc() if sort_order == "asc" else Image.name.desc(),
            Image.id.asc(),  # Ordenación secundaria estable por ID.
        )
    elif sort_by == "label":
        # Para label: NULL al final en ambos órdenes
        if sort_order == "asc":
            query = query.order_by(
                Image.label.is_(None).asc(),
                Image.label.asc(),
                Image.created_at.asc(),
                Image.id.asc(),  # Ordenación terciaria estable.
            )
        else:
            query = query.order_by(
                Image.label.is_(None).asc(),
                Image.label.desc(),
                Image.created_at.desc(),
                Image.id.asc(),  # Ordenación terciaria estable. por ID.
            )
    else:  # created_at (por defecto).
        query = query.order_by(
            Image.created_at.asc() if sort_order == "asc" else Image.created_at.desc(),
            Image.id.asc(),  # Ordenación secundaria estable por ID.
        )

    # Obtener conteo total.
    count_result = await session.execute(count_query)
    total_count = count_result.scalar_one() or 0

    # Aplicar paginación.
    query = query.offset(skip).limit(limit)

    # Ejecutar consulta.
    result = await session.execute(query)
    images = result.scalars().all()

    return images, total_count


async def update_image(
    *, session: AsyncSession, image: Image, image_data: ImageUpdate
) -> Image:
    """Actualiza los datos de una imagen.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        image (Image): Imagen a actualizar.
        image_data (ImageUpdate): Datos de la imagen a actualizar.

    Returns:
        Image: Imagen actualizada.
    """

    image.sqlmodel_update(image_data)
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def delete_image(*, session: AsyncSession, image: Image) -> None:
    """Elimina una imagen de la base de datos.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        image (Image): Imagen a eliminar.
    """

    await session.delete(image)
    await session.commit()
