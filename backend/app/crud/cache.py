import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.datasets import Dataset


async def invalidate_dataset_cache(
    *, session: AsyncSession, dataset_id: uuid.UUID
) -> None:
    """Invalida la caché de conteos de un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.
    """

    dataset = await session.get(Dataset, dataset_id)
    if not dataset:
        return

    # Invalidar la caché estableciendo los conteos a None.
    dataset.cached_image_count = None
    dataset.cached_category_count = None
    dataset.cache_updated_at = None

    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)


async def update_dataset_cache(
    *,
    session: AsyncSession,
    dataset_id: uuid.UUID,
    image_count: int | None = None,
    category_count: int | None = None
) -> None:
    """Actualiza la caché de conteos de un dataset con valores conocidos.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.
        image_count (int, optional): Número de imágenes (si ya se conoce).
        category_count (int, optional): Número de categorías (si ya se conoce).
    """

    dataset = await session.get(Dataset, dataset_id)
    if not dataset:
        return

    # Actualizar la caché con los valores proporcionados.
    if image_count is not None:
        dataset.cached_image_count = image_count

    if category_count is not None:
        dataset.cached_category_count = category_count

    dataset.cache_updated_at = datetime.now(timezone.utc)

    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
