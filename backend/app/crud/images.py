import os
import uuid
import zipfile
import tempfile
import csv
import io
import base64
import logging
from typing import Dict

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from app.models.images import Image, ImageCreate, ImageUpdate
from app.crud.cache import invalidate_dataset_cache

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
IMAGES_DIR = os.path.join(MEDIA_ROOT, "images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
THUMBNAIL_SIZE = (100, 100)
OUTPUT_FORMAT = "JPEG"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_image_extension(filename: str) -> bool:
    """Verifica si la extensión del archivo es válida.

    Args:
        filename (str): Nombre del archivo.

    Returns:
        bool: True si la extensión es válida, False de lo contrario.
    """

    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


async def create_image(
    *,
    session: AsyncSession,
    image_in: ImageCreate,
    dataset_id: uuid.UUID,
    update_cache: bool = True,
) -> Image:
    """Crea una nueva imagen en la base de datos.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        image_in (ImageCreate): Datos de la imagen a crear.
        dataset_id (uuid.UUID): ID del dataset al que pertenece la imagen.

    Returns:
        Image: Imagen creada.
    """

    image = Image.model_validate(image_in)
    session.add(image)
    await session.commit()
    await session.refresh(image)

    # Invalidar la caché del dataset después de añadir una imagen.
    if update_cache:
        await invalidate_dataset_cache(session=session, dataset_id=dataset_id)

    return image


async def delete_image(*, session: AsyncSession, image: Image) -> None:
    """Elimina una imagen de la base de datos y su archivo asociado.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        image (Image): Imagen a eliminar.

    Returns:
        None
    """

    try:
        file_path = os.path.join(MEDIA_ROOT, image.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Loguear el error pero continuar con la eliminación del registro.
        logger.error(f"Error deleting file {file_path}: {str(e)}", exc_info=True)

    # Guardar el dataset_id antes de eliminar.
    dataset_id = image.dataset_id

    # Eliminar la imagen.
    await session.delete(image)
    await session.commit()

    # Invalidar la caché del dataset después de eliminar una imagen.
    await invalidate_dataset_cache(session=session, dataset_id=dataset_id)


def create_thumbnail(image: PILImage.Image) -> str:
    """Crea una miniatura de la imagen y la convierte a base64.

    Args:
        image (PILImage.Image): Imagen original.

    Returns:
        str: Miniatura en formato base64.
    """

    try:
        thumb = image.copy()

        # Convertir a RGB si está en modo P o tiene canal alpha.
        if thumb.mode == "P":
            thumb = thumb.convert("RGB")
        elif thumb.mode in ["RGBA", "LA"]:
            bg = PILImage.new("RGB", thumb.size, (255, 255, 255))
            bg.paste(
                thumb,
                mask=thumb.split()[3] if thumb.mode == "RGBA" else thumb.split()[1],
            )
            thumb = bg
        elif thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        thumb.thumbnail(THUMBNAIL_SIZE)
        buffer = io.BytesIO()
        thumb.save(buffer, format=OUTPUT_FORMAT)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        # Loguear el error pero continuar con la creación de la miniatura.
        logger.error(f"Error creating thumbnail: {str(e)}", exc_info=True)
        # En caso de error, crear una miniatura en blanco.
        blank = PILImage.new("RGB", THUMBNAIL_SIZE, (240, 240, 240))
        buffer = io.BytesIO()
        blank.save(buffer, format=OUTPUT_FORMAT)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def convert_and_save_image(source_path: str, image_id: uuid.UUID) -> str:
    """Convierte y guarda una imagen en un formato estandarizado.

    Args:
        source_path (str): Ruta de la imagen original.
        image_id (uuid.UUID): ID de la imagen.

    Returns:
        str: Ruta de la imagen convertida.
    """

    # Asegurar que el directorio de imágenes existe.
    os.makedirs(IMAGES_DIR, exist_ok=True)

    with PILImage.open(source_path) as img:
        # Convertir a RGB si no es ya RGB.
        if img.mode == "P":
            # Convertir imagen en modo paleta a RGB.
            img = img.convert("RGB")
        elif img.mode in ["RGBA", "LA"]:
            # Manejar imágenes con canal alpha.
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else img.split()[1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Nombre y ruta del archivo.
        file_name = f"{image_id}.jpg"
        target_path = os.path.join(IMAGES_DIR, file_name)

        # Guardar en formato estandarizado (JPEG).
        img.save(target_path, format=OUTPUT_FORMAT, quality=90, optimize=True)

        return os.path.join("images", file_name)


async def process_csv_file(csv_file: UploadFile) -> Dict[str, str]:
    """Procesa un archivo CSV y devuelve un diccionario con los nombres de las imágenes y sus etiquetas.

    Args:
        csv_file (UploadFile): Archivo CSV subido.

    Raises:
        HTTPException[400]: Si hay un error al procesar el archivo CSV.

    Returns:
        Dict[str, str]: Diccionario con nombres de imágenes como claves y etiquetas como valores.
    """

    csv_data = {}
    try:
        csv_content = await csv_file.read()
        # Decodificar el contenido del CSV.
        csv_text = csv_content.decode("utf-8-sig").splitlines()
        csv_reader = csv.reader(csv_text)
        for row in csv_reader:
            if len(row) < 2:
                continue  # Ignorar filas sin suficientes columnas.
            image_name = row[0].strip()
            label = row[1].strip()
            csv_data[image_name] = label
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV file: {str(e)}",
        )
    finally:
        await csv_file.seek(0)

    return csv_data


async def process_zip_with_images(
    *,
    session: AsyncSession,
    dataset_id: uuid.UUID,
    zip_content: bytes,
    csv_data: Dict[str, str] = None,
) -> Dict[str, int]:
    """Procesa un archivo ZIP con imágenes y opcionalmente un archivo CSV con etiquetas.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        dataset_id (uuid.UUID): ID del dataset al que pertenecen las imágenes.
        zip_content (bytes): Contenido del archivo ZIP subido.
        csv_data (Dict[str, str], optional): Diccionario con nombres de imágenes y etiquetas.

    Raises:
        HTTPException[400]: Si hay un error al procesar el archivo ZIP o las imágenes.

    Returns:
        Dict[str, int]: Estadísticas del procesamiento, incluyendo imágenes procesadas, omitidas e inválidas.
    """

    stats = {
        "processed_images": 0,
        "skipped_images": 0,
        "invalid_images": 0,
        "labels_applied": 0,
        "invalid_image_details": [],
        "duplicated_image_details": [],
        "skipped_label_details": [],
    }

    # Conjunto para controlar qué etiquetas específicas se han aplicado.
    applied_labels = set()

    # Usar directorio temporal para procesar los archivos.
    with tempfile.TemporaryDirectory() as temp_dir:
        # Guardar el ZIP en el directorio temporal.
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_content)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Verificar que contiene imágenes válidas.
                image_files = []
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        continue
                    if is_valid_image_extension(file_info.filename):
                        image_files.append(file_info)
                if not image_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The ZIP file doesn't contain any valid image files",
                    )
                # Limitar cantidad de imágenes.
                max_images = 10000
                if len(image_files) > max_images:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Too many images in ZIP file. Maximum allowed: {max_images}",
                    )
                # Procesar imágenes una por una.
                for file_info in image_files:
                    try:
                        # Extraer el nombre de archivo.
                        filename = os.path.basename(file_info.filename)
                        # Verificar si la imagen ya existe en la base de datos.
                        existing_image = await get_image_by_datasetid_and_name(
                            session=session, dataset_id=dataset_id, name=filename
                        )
                        if existing_image:
                            # Si la imagen ya existe, omitirla y registrar el detalle.
                            stats["skipped_images"] += 1
                            stats["duplicated_image_details"].append(file_info.filename)
                            continue
                        # Extraer imagen.
                        extracted_path = zip_ref.extract(file_info, temp_dir)
                        # Procesar imagen.
                        try:
                            with PILImage.open(extracted_path) as img:
                                # Generar UUID para la imagen.
                                # Servirá como ID en la base de datos y como nombre de archivo.
                                image_id = uuid.uuid4()
                                # Crear miniatura en base64.
                                thumbnail_data = create_thumbnail(img)
                                # Convertir y guardar imagen estandarizada (JPEG).
                                file_path = convert_and_save_image(
                                    extracted_path, image_id
                                )
                                # Obtener etiqueta del CSV si existe.
                                # Se permiten pares imagen.{ext},etiqueta o imagen,etiqueta.
                                label = None
                                filename_without_ext = os.path.splitext(filename)[0]
                                if csv_data and (
                                    filename in csv_data
                                    or filename_without_ext in csv_data
                                ):
                                    stats["labels_applied"] += 1
                                    # Registrar en el conjunto qué etiqueta se ha aplicado.
                                    if filename in csv_data:
                                        applied_labels.add(filename)
                                    else:
                                        applied_labels.add(filename_without_ext)
                                    label = csv_data.get(
                                        filename, csv_data.get(filename_without_ext)
                                    )
                                # Crear entrada en la base de datos.
                                image_create = ImageCreate(
                                    id=image_id,
                                    name=filename,
                                    file_path=file_path,
                                    dataset_id=dataset_id,
                                    label=label,
                                    thumbnail=thumbnail_data,
                                )
                                await create_image(
                                    session=session,
                                    image_in=image_create,
                                    dataset_id=dataset_id,
                                    update_cache=False,
                                )
                                stats["processed_images"] += 1
                        except UnidentifiedImageError:
                            stats["invalid_images"] += 1
                            stats["invalid_image_details"].append(file_info.filename)
                            continue
                    except Exception as e:
                        stats["invalid_images"] += 1
                        stats["invalid_image_details"].append(file_info.filename)
                        continue
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The file is not a valid ZIP file",
            )

    if csv_data:
        for csv_key, csv_value in csv_data.items():
            # Si la etiqueta no se aplicó a ninguna imagen, añadirla a los detalles.
            if csv_key not in applied_labels:
                stats["skipped_label_details"].append(f"{csv_key}={csv_value}")

    # Invalidar la caché una sola vez al final si se procesó al menos una imagen.
    if stats["processed_images"] > 0:
        await invalidate_dataset_cache(session=session, dataset_id=dataset_id)

    return stats


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
        # Para label: NULL al final en ambos órdenes.
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
) -> dict:
    """Actualiza los datos de una imagen.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        image (Image): Imagen a actualizar.
        image_data (ImageUpdate): Datos de la imagen a actualizar.

    Returns:
        Image: Imagen actualizada.
    """

    # Verificar si ha cambiado la etiqueta según el tipo de datos.
    if isinstance(image_data, dict):
        label_changed = "label" in image_data
    else:
        # Si es un objeto Pydantic.
        label_changed = "label" in image_data.model_dump(exclude_unset=True)

    # Actualizar la imagen.
    image.sqlmodel_update(image_data)
    session.add(image)
    await session.commit()
    await session.refresh(image)

    image_dict = {
        "id": image.id,
        "name": image.name,
        "file_path": image.file_path,
        "label": image.label,
        "dataset_id": image.dataset_id,
        "thumbnail": image.thumbnail,
        "created_at": image.created_at,
    }

    # Solo invalidar la caché si cambió la etiqueta.
    if label_changed:
        await invalidate_dataset_cache(session=session, dataset_id=image.dataset_id)

    return image_dict
