import os
import uuid
import logging

from sqlmodel import select, func
from sqlalchemy import distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.datasets import Dataset, DatasetCreate, DatasetUpdate
from app.models.images import Image
from app.models.users import User

logger = logging.getLogger(__name__)
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")


async def get_dataset_by_id(*, session: AsyncSession, id: uuid.UUID) -> Dataset | None:
    """Obtiene un dataset dado su ID.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        id (uuid.UUID): ID del dataset.

    Returns:
        Dataset | None: Dataset encontrado.
    """

    dataset = await session.get(Dataset, id)
    if not dataset:
        return None
    return dataset


async def get_dataset_by_userid_and_name(
    *, session: AsyncSession, user_id: uuid.UUID, name: str
) -> Dataset | None:
    """Obtiene un dataset dado su ID de usuario y nombre.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        user_id (uuid.UUID): ID del usuario.
        name (str): Nombre del dataset.

    Returns:
        Dataset | None: Dataset encontrado.
    """

    statement = select(Dataset).where(Dataset.user_id == user_id, Dataset.name == name)
    res = await session.execute(statement)
    dataset = res.scalars().first()
    if not dataset:
        return None
    return dataset


async def create_dataset(
    *, session: AsyncSession, user_id: uuid.UUID, dataset_in: DatasetCreate
) -> Dataset:
    """Crea un nuevo dataset en la base de datos.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        user_id (uuid.UUID): ID del usuario propietario.
        dataset_in (Dataset): Datos del dataset a crear.

    Returns:
        Dataset: Dataset creado.
    """

    dataset = Dataset.model_validate(dataset_in, update={"user_id": user_id})
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


async def update_dataset(
    *, session: AsyncSession, dataset: Dataset, dataset_data: DatasetUpdate
) -> Dataset:
    """Actualiza los datos de un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset (Dataset): Dataset a actualizar.
        dataset_in (DatasetUpdate): Datos del dataset a actualizar.

    Returns:
        Dataset: Dataset actualizado.
    """

    dataset.sqlmodel_update(dataset_data)
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


async def delete_dataset(*, session: AsyncSession, dataset: Dataset) -> None:
    """Elimina un dataset de la base de datos y todas las imágenes asociadas.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset (Dataset): Dataset a eliminar.
    """

    # Obtener todas las imágenes del dataset.
    images_query = select(Image).where(Image.dataset_id == dataset.id)
    images_result = await session.execute(images_query)
    images = images_result.scalars().all()

    # Eliminar los archivos físicos de cada imagen.
    for image in images:
        try:
            file_path = os.path.join(MEDIA_ROOT, image.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(
                f"Error deleting image file {file_path}: {str(e)}", exc_info=True
            )

    # Eliminar el dataset.
    await session.delete(dataset)
    await session.commit()


async def get_image_count(*, session: AsyncSession, dataset_id: uuid.UUID) -> int:
    """Obtiene el número de imágenes en un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.

    Returns:
        int: Número de imágenes en el dataset.
    """

    statement = select(func.count()).where(Image.dataset_id == dataset_id)
    result = await session.execute(statement)
    count = result.scalar_one_or_none()
    return count or 0


async def get_category_count(*, session: AsyncSession, dataset_id: uuid.UUID) -> int:
    """Obtiene el número de categorías distintas en las imágenes de un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.

    Returns:
        int: Número de categorías distintas en las imágenes del dataset.
    """

    statement = select(func.count(distinct(Image.label))).where(
        Image.dataset_id == dataset_id,
        Image.label.is_not(None),
    )
    result = await session.execute(statement)
    count = result.scalar_one_or_none()
    return count or 0


async def get_dataset_counts(
    *, session: AsyncSession, dataset_id: uuid.UUID
) -> dict[str, int]:
    """Obtiene el número de imágenes y categorías en un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.

    Returns:
        dict[str, int]: Diccionario con el número de imágenes y categorías en el dataset.
    """

    image_count = await get_image_count(session=session, dataset_id=dataset_id)
    category_count = await get_category_count(session=session, dataset_id=dataset_id)

    return {
        "image_count": image_count,
        "category_count": category_count,
    }


async def get_user_datasets_sorted(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user_id: uuid.UUID | None = None,
    admin_view: bool = False,
) -> tuple[list[Dataset] | list[tuple[Dataset, str]], int, bool]:
    """Obtiene datasets con ordenación avanzada, paginación y búsqueda.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        skip (int): Cantidad de datasets a omitir.
        limit (int): Cantidad de datasets a devolver.
        search (str | None): Término de búsqueda.
        sort_by (str): Campo por el que ordenar. Puede ser 'name', 'created_at', 'is_public', 'image_count' o 'category_count'.
        sort_order (str): Orden de la ordenación. Puede ser 'asc' o 'desc'.
        user_id (uuid.UUID | None): ID del usuario propietario del dataset (None si es administrador).
        admin_view (bool): Indica si la vista es para administradores.

    Returns:
        tuple[list[Dataset] | list[tuple[Dataset, str]], int, bool]: Datasets encontrados, conteo total y si incluye usernames.

    """

    # Crear término de búsqueda si existe.
    search_term = f"%{search.strip()}%" if search and search.strip() else None

    includes_username = False

    # CASO 1: Para ordenación por username o cuando el usuario es administrador y hay búsqueda.
    # (pero NO se está ordenando por conteos).
    # Este caso es solo para admnistradores.
    if (
        (admin_view and sort_by == "username") or (admin_view and search_term)
    ) and sort_by not in ["image_count", "category_count"]:
        includes_username = True
        # Realizar un join con la tabla de usuarios para ordenar/buscar por username.
        query = select(Dataset, User.username).join(User, Dataset.user_id == User.id)

        # Aplicar filtro de usuario si es necesario.
        if user_id is not None:
            query = query.where(Dataset.user_id == user_id)

        # Aplicar búsqueda si se proporciona.
        if search_term:
            # Incluir username en la búsqueda.
            query = query.where(
                Dataset.name.ilike(search_term)
                | Dataset.description.ilike(search_term)
                | User.username.ilike(search_term)
            )

        # Aplicar ordenación.
        if sort_by == "username":
            query = query.order_by(
                User.username.asc() if sort_order == "asc" else User.username.desc()
            )
        elif sort_by == "name":
            query = query.order_by(
                Dataset.name.asc() if sort_order == "asc" else Dataset.name.desc()
            )
        elif sort_by == "is_public":
            # Para is_public: True primero en DESC, False primero en ASC.
            if sort_order == "desc":
                query = query.order_by(
                    Dataset.is_public.desc(), Dataset.created_at.desc()
                )
            else:
                query = query.order_by(
                    Dataset.is_public.asc(), Dataset.created_at.asc()
                )
        else:  # created_at (por defecto).
            query = query.order_by(
                Dataset.created_at.asc()
                if sort_order == "asc"
                else Dataset.created_at.desc()
            )

        # Consulta para contar resultados.
        count_query = select(func.count()).select_from(
            select(Dataset.id)
            .join(User, Dataset.user_id == User.id)
            .where(
                (Dataset.name.ilike(search_term) if search_term else True)
                | (Dataset.description.ilike(search_term) if search_term else True)
                | (User.username.ilike(search_term) if search_term else True)
            )
            .subquery()
        )

        # Obtener conteo.
        count_result = await session.execute(count_query)
        total_count = count_result.scalar_one() or 0

        # Aplicar paginación.
        query = query.offset(skip).limit(limit)

        # Ejecutar consulta.
        result = await session.execute(query)

        # Extraer datasets y usernames.
        datasets_with_usernames = []
        for dataset, username in result:
            datasets_with_usernames.append((dataset, username))

        return datasets_with_usernames, total_count, includes_username

    # CASO 2: Ordenación por conteos (image_count, category_count) + búsqueda username.
    # Este caso es solo para administradores.
    elif sort_by in ["image_count", "category_count"] and admin_view and search_term:
        includes_username = True

        # Primero realizar la búsqueda por username (join con users).
        search_query = (
            select(Dataset, User.username)
            .join(User, Dataset.user_id == User.id)
            .where(
                Dataset.name.ilike(search_term)
                | Dataset.description.ilike(search_term)
                | User.username.ilike(search_term)
            )
        )

        if user_id is not None:
            search_query = search_query.where(Dataset.user_id == user_id)

        # Ejecutar la consulta para obtener datasets + usernames.
        search_result = await session.execute(search_query)
        datasets_with_username = [
            (dataset, username) for dataset, username in search_result
        ]

        # Calcular los conteos para ordenar.
        datasets_with_counts = []
        for dataset, username in datasets_with_username:
            if sort_by == "image_count":
                count = await get_image_count(session=session, dataset_id=dataset.id)
            else:  # category_count
                count = await get_category_count(session=session, dataset_id=dataset.id)
            datasets_with_counts.append((dataset, username, count))

        # Ordenar por el conteo (tercer elemento de cada tupla).
        if sort_order == "asc":
            # Orden ascendente.
            datasets_with_counts.sort(key=lambda x: (x[2], x[0].created_at))
        else:
            # Orden descendente.
            datasets_with_counts.sort(
                key=lambda x: (x[2], x[0].created_at), reverse=True
            )

        # Aplicar paginación.
        paginated_results = datasets_with_counts[skip : skip + limit]

        # Eliminar el conteo de las tuplas para mantener el formato esperado (dataset, username).
        final_results = [
            (dataset, username) for dataset, username, _ in paginated_results
        ]

        return final_results, len(datasets_with_username), includes_username

    # CASO 3: Para ordenación por conteos (image_count o category_count) sin username.
    # Este caso es para administradores y usuarios normales.
    elif sort_by in ["image_count", "category_count"]:

        query = select(Dataset)

        # Aplicar filtro de usuario (para que un usuario normal vea solo sus datasets).
        if not admin_view and user_id is not None:
            query = query.where(Dataset.user_id == user_id)

        # Aplicar búsqueda si se proporciona.
        if search_term:
            # Para búsqueda de admin por username, se necesita JOIN con la tabla de usuarios.
            if admin_view:
                query = query.join(User, Dataset.user_id == User.id).where(
                    Dataset.name.ilike(search_term)
                    | Dataset.description.ilike(search_term)
                    | User.username.ilike(search_term)
                )
            else:
                # Búsqueda normal para usuarios no admin.
                query = query.where(
                    Dataset.name.ilike(search_term)
                    | Dataset.description.ilike(search_term)
                )

        # Ejecutar consulta.
        result = await session.execute(query)
        all_datasets = result.scalars().all()

        # Obtener conteo total.
        count_query = select(func.count()).select_from(Dataset)
        if not admin_view and user_id is not None:
            count_query = count_query.where(Dataset.user_id == user_id)
        if search_term:
            # Para búsqueda de admin por username, se necesita JOIN con la tabla de usuarios.
            if admin_view:
                count_query = count_query.join(User, Dataset.user_id == User.id).where(
                    Dataset.name.ilike(search_term)
                    | Dataset.description.ilike(search_term)
                    | User.username.ilike(search_term)
                )
            else:
                # Búsqueda normal para usuarios no admin.
                count_query = count_query.where(
                    Dataset.name.ilike(search_term)
                    | Dataset.description.ilike(search_term)
                )
        count_result = await session.execute(count_query)
        total_count = count_result.scalar_one() or 0

        # Obtener conteos para cada dataset.
        dataset_with_counts = []
        for dataset in all_datasets:
            if sort_by == "image_count":
                count = await get_image_count(session=session, dataset_id=dataset.id)
                dataset_with_counts.append((dataset, count))
            else:  # Si se quiere ordenar por category_count
                count = await get_category_count(session=session, dataset_id=dataset.id)
                dataset_with_counts.append((dataset, count))

        # Ordenar la lista por el conteo.
        if sort_order == "asc":
            dataset_with_counts.sort(key=lambda x: (x[1], x[0].created_at))
        else:
            dataset_with_counts.sort(
                key=lambda x: (x[1], x[0].created_at), reverse=True
            )

        # Aplicar paginación.
        # Hay que hacerla manualmente porque el image_count/category_count no es un campo de la tabla Dataset.
        paginated_datasets = [d[0] for d in dataset_with_counts[skip : skip + limit]]

        return paginated_datasets, total_count, includes_username

    # CASO 4: Para ordenación normal (name, created_at o is_public).
    # Este caso es para administradores y usuarios normales.
    else:

        query = select(Dataset)

        # Aplicar filtro de usuario.
        if not admin_view and user_id is not None:
            query = query.where(Dataset.user_id == user_id)

        # Aplicar búsqueda si se proporciona.
        if search_term:
            query = query.where(
                Dataset.name.ilike(search_term) | Dataset.description.ilike(search_term)
            )

        # Aplicar ordenación estándar.
        if sort_by == "name":
            if sort_order == "asc":
                query = query.order_by(Dataset.name.asc())
            else:
                query = query.order_by(Dataset.name.desc())
        elif sort_by == "is_public":
            # Para is_public: True primero en DESC, False primero en ASC.
            if sort_order == "desc":
                query = query.order_by(
                    Dataset.is_public.desc(), Dataset.created_at.desc()
                )
            else:
                query = query.order_by(
                    Dataset.is_public.asc(), Dataset.created_at.asc()
                )
        else:  # created_at (por defecto).
            if sort_order == "asc":
                query = query.order_by(Dataset.created_at.asc())
            else:
                query = query.order_by(Dataset.created_at.desc())

        # Consulta para contar total.
        count_query = select(func.count()).select_from(Dataset)
        if not admin_view and user_id is not None:
            count_query = count_query.where(Dataset.user_id == user_id)
        if search_term:
            count_query = count_query.where(
                Dataset.name.ilike(search_term) | Dataset.description.ilike(search_term)
            )

        # Obtener conteo.
        count_result = await session.execute(count_query)
        total_count = count_result.scalar_one() or 0

        # Aplicar paginación.
        query = query.offset(skip).limit(limit)

        # Ejecutar consulta.
        result = await session.execute(query)
        datasets = result.scalars().all()

        return datasets, total_count, includes_username


async def get_dataset_label_details(
    *, session: AsyncSession, dataset_id: uuid.UUID
) -> dict:
    """Obtiene detalles de las etiquetas y categorías de un dataset.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset.

    Returns:
        dict: Diccionario con detalles de las etiquetas y categorías.
    """

    # Obtener el conteo de imágenes por categoría.
    statement = (
        select(Image.label, func.count(Image.id).label("count"))
        .where(Image.dataset_id == dataset_id, Image.label.is_not(None))
        .group_by(Image.label)
    )
    result = await session.execute(statement)
    categories = [{"name": name, "image_count": count} for name, count in result]

    # Obtener el número de imágenes etiquetadas.
    labeled_images_stmt = select(func.count(Image.id)).where(
        Image.dataset_id == dataset_id, Image.label.is_not(None)
    )
    labeled_images_result = await session.execute(labeled_images_stmt)
    labeled_images = labeled_images_result.scalar_one() or 0

    # Obtener el número de imágenes no etiquetadas.
    unlabeled_images_stmt = select(func.count(Image.id)).where(
        Image.dataset_id == dataset_id, Image.label.is_(None)
    )
    unlabeled_images_result = await session.execute(unlabeled_images_stmt)
    unlabeled_images = unlabeled_images_result.scalar_one() or 0

    return {
        "dataset_id": dataset_id,
        "categories": categories,
        "count": len(categories),
        "labeled_images": labeled_images,
        "unlabeled_images": unlabeled_images,
    }
