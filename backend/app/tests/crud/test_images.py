import uuid
import pytest
import io
import base64
from unittest.mock import MagicMock, AsyncMock, patch, mock_open

from PIL import Image as PILImage

from app.crud.images import (
    get_image_by_id,
    get_image_by_datasetid_and_name,
    get_images_sorted,
    create_image,
    update_image,
    delete_image,
    create_thumbnail,
    convert_and_save_image,
    is_valid_image_extension,
)
from app.models.images import Image, ImageCreate, ImageUpdate

pytestmark = pytest.mark.asyncio


class TestImagesCRUD:

    async def test_get_image_by_id_success(self, mock_session):
        """Prueba de obtención exitosa de una imagen por ID."""

        # Configuración.
        image_id = uuid.uuid4()

        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.name = "test_image.jpg"
        mock_image.file_path = "images/test_image.jpg"
        mock_image.dataset_id = uuid.uuid4()
        mock_image.label = "test_label"
        mock_image.thumbnail = "base64_data"
        mock_image.__class__ = Image

        mock_session.get = AsyncMock(return_value=mock_image)

        # Ejecución.
        result = await get_image_by_id(session=mock_session, id=image_id)

        # Verificación.
        assert result is mock_image
        mock_session.get.assert_called_once_with(Image, image_id)

    async def test_get_image_by_id_not_found(self, mock_session):
        """Prueba cuando la imagen no existe."""

        # Configuración.
        image_id = uuid.uuid4()
        mock_session.get = AsyncMock(return_value=None)

        # Ejecución.
        result = await get_image_by_id(session=mock_session, id=image_id)

        # Verificación.
        assert result is None
        mock_session.get.assert_called_once_with(Image, image_id)

    async def test_get_image_by_datasetid_and_name_success(self, mock_session):
        """Prueba de obtención exitosa de una imagen por dataset_id y nombre."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image_name = "test_image.jpg"

        mock_image = MagicMock()
        mock_image.id = uuid.uuid4()
        mock_image.name = image_name
        mock_image.dataset_id = dataset_id
        mock_image.__class__ = Image

        # Configurar el resultado de la consulta.
        execute_result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.first.return_value = mock_image
        execute_result.scalars.return_value = scalars_result

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución.
        with patch("app.crud.images.select") as mock_select:
            mock_select.return_value = MagicMock()

            result = await get_image_by_datasetid_and_name(
                session=mock_session, dataset_id=dataset_id, name=image_name
            )

            # Verificación.
            assert result is mock_image
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()

    async def test_get_image_by_datasetid_and_name_not_found(self, mock_session):
        """Prueba cuando la imagen no existe por dataset_id y nombre."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image_name = "nonexistent_image.jpg"

        # Configurar el resultado de la consulta para que no encuentre nada.
        execute_result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.first.return_value = None
        execute_result.scalars.return_value = scalars_result

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución.
        with patch("app.crud.images.select") as mock_select:
            mock_select.return_value = MagicMock()

            result = await get_image_by_datasetid_and_name(
                session=mock_session, dataset_id=dataset_id, name=image_name
            )

            # Verificación.
            assert result is None
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()

    async def test_create_image_success(self, mock_session):
        """Prueba de creación exitosa de una imagen."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image_id = uuid.uuid4()

        image_in = ImageCreate(
            id=image_id,
            name="new_image.jpg",
            file_path="images/new_image.jpg",
            dataset_id=dataset_id,
            thumbnail="base64_thumbnail_data",
        )

        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.name = image_in.name
        mock_image.file_path = image_in.file_path
        mock_image.dataset_id = dataset_id
        mock_image.thumbnail = image_in.thumbnail

        with patch("app.crud.images.Image.model_validate") as mock_validate:
            mock_validate.return_value = mock_image

            with patch(
                "app.crud.images.invalidate_dataset_cache"
            ) as mock_invalidate_cache:
                # Ejecución.
                result = await create_image(
                    session=mock_session, image_in=image_in, dataset_id=dataset_id
                )

                # Verificación.
                assert result is mock_image
                mock_validate.assert_called_once_with(image_in)
                mock_session.add.assert_called_once_with(mock_image)
                assert mock_session.commit.call_count == 1
                assert mock_session.refresh.call_count == 1
                mock_invalidate_cache.assert_called_once_with(
                    session=mock_session, dataset_id=dataset_id
                )

    async def test_update_image_success(self, mock_session):
        """Prueba de actualización exitosa de una imagen."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image = MagicMock()
        image.id = uuid.uuid4()
        image.name = "original_name.jpg"
        image.dataset_id = dataset_id
        image.label = None
        image.__class__ = Image

        image_update = ImageUpdate(label="new_label")

        # Ejecución.
        with patch("app.crud.images.invalidate_dataset_cache") as mock_invalidate_cache:
            result = await update_image(
                session=mock_session, image=image, image_data=image_update
            )

            # Verificación.
            assert "id" in result
            assert result["name"] == image.name
            assert result["label"] == image.label
            assert result["dataset_id"] == image.dataset_id

            image.sqlmodel_update.assert_called_once_with(image_update)
            mock_session.add.assert_called_once_with(image)
            assert mock_session.commit.call_count == 1
            assert mock_session.refresh.call_count == 1
            mock_invalidate_cache.assert_called_once_with(
                session=mock_session, dataset_id=dataset_id
            )

    async def test_update_image_no_label_change(self, mock_session):
        """Prueba de actualización de una imagen sin cambiar la etiqueta."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image = MagicMock()
        image.id = uuid.uuid4()
        image.name = "original_name.jpg"
        image.dataset_id = dataset_id
        image.label = "existing_label"
        image.__class__ = Image

        # Actualizar solo el nombre, no la etiqueta.
        image_update = ImageUpdate(name="new_name.jpg")

        # Ejecución.
        with patch("app.crud.images.invalidate_dataset_cache") as mock_invalidate_cache:
            result = await update_image(
                session=mock_session, image=image, image_data=image_update
            )

            # Verificación.
            assert "id" in result
            assert result["name"] == image.name
            assert result["label"] == image.label
            assert result["dataset_id"] == image.dataset_id

            image.sqlmodel_update.assert_called_once_with(image_update)
            mock_session.add.assert_called_once_with(image)
            assert mock_session.commit.call_count == 1
            assert mock_session.refresh.call_count == 1

            # No se debe invalidar la caché porque no cambió la etiqueta.
            mock_invalidate_cache.assert_not_called()

    async def test_delete_image_success(self, mock_session):
        """Prueba de eliminación exitosa de una imagen."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image = MagicMock()
        image.id = uuid.uuid4()
        image.name = "image_to_delete.jpg"
        image.file_path = "images/image_to_delete.jpg"
        image.dataset_id = dataset_id

        with patch("app.crud.images.os.path.exists") as mock_exists, patch(
            "app.crud.images.os.remove"
        ) as mock_remove, patch(
            "app.crud.images.invalidate_dataset_cache"
        ) as mock_invalidate_cache:

            # Simular que el archivo existe.
            mock_exists.return_value = True

            # Ejecución.
            await delete_image(session=mock_session, image=image)

            # Verificación.
            mock_exists.assert_called_once()
            mock_remove.assert_called_once()
            mock_session.delete.assert_called_once_with(image)
            assert mock_session.commit.call_count == 1
            mock_invalidate_cache.assert_called_once_with(
                session=mock_session, dataset_id=dataset_id
            )

    async def test_delete_image_file_not_found(self, mock_session):
        """Prueba de eliminación de una imagen cuyo archivo no existe."""

        # Configuración.
        dataset_id = uuid.uuid4()
        image = MagicMock()
        image.id = uuid.uuid4()
        image.name = "missing_file.jpg"
        image.file_path = "images/missing_file.jpg"
        image.dataset_id = dataset_id

        with patch("app.crud.images.os.path.exists") as mock_exists, patch(
            "app.crud.images.os.remove"
        ) as mock_remove, patch(
            "app.crud.images.invalidate_dataset_cache"
        ) as mock_invalidate_cache:

            # Simular que el archivo no existe.
            mock_exists.return_value = False

            # Ejecución.
            await delete_image(session=mock_session, image=image)

            # Verificación.
            mock_exists.assert_called_once()
            mock_remove.assert_not_called()  # No debería intentar eliminar el archivo.
            mock_session.delete.assert_called_once_with(image)
            assert mock_session.commit.call_count == 1
            mock_invalidate_cache.assert_called_once_with(
                session=mock_session, dataset_id=dataset_id
            )

    async def test_get_images_sorted_success(self, mock_session):
        """Prueba de obtención exitosa de imágenes con ordenación."""

        # Configuración.
        dataset_id = uuid.uuid4()

        # Crear algunas imágenes de prueba.
        mock_images = []
        for i in range(3):
            img = MagicMock()
            img.id = uuid.uuid4()
            img.name = f"test_image_{i}.jpg"
            img.dataset_id = dataset_id
            img.label = f"label_{i}" if i % 2 == 0 else None
            mock_images.append(img)

        # Configurar los resultados de las consultas.
        images_result = MagicMock()
        scalar_images = MagicMock()
        scalar_images.all.return_value = mock_images
        images_result.scalars.return_value = scalar_images

        count_result = MagicMock()
        count_result.scalar_one.return_value = len(mock_images)

        # Configurar mock_session.execute para devolver estos resultados en orden.
        mock_session.execute = AsyncMock(side_effect=[count_result, images_result])

        # Ejecución.
        with patch("app.crud.images.select") as mock_select:
            mock_select.return_value = MagicMock()

            result, count = await get_images_sorted(
                session=mock_session,
                dataset_id=dataset_id,
                skip=0,
                limit=10,
                sort_by="name",
                sort_order="asc",
            )

            # Verificación.
            assert result == mock_images
            assert count == len(mock_images)
            assert mock_session.execute.call_count == 2
            assert mock_select.call_count >= 1

    async def test_is_valid_image_extension(self):
        """Prueba de validación de extensiones de imágenes."""

        # Configuración - Extensiones válidas e inválidas.
        valid_extensions = [
            "image.jpg",
            "image.jpeg",
            "image.png",
            "image.gif",
            "image.webp",
        ]
        invalid_extensions = [
            "document.pdf",
            "script.js",
            "style.css",
            "image.bmp",
            "image.tiff",
        ]

        # Verificación.
        for filename in valid_extensions:
            assert is_valid_image_extension(filename) is True

        for filename in invalid_extensions:
            assert is_valid_image_extension(filename) is False

    async def test_create_thumbnail_success(self):
        """Prueba de creación exitosa de una miniatura."""

        # Crear una imagen PIL para probar.
        img = PILImage.new("RGB", (200, 200), color="red")

        # Ejecución.
        thumbnail_data = create_thumbnail(img)

        # Verificación.
        assert isinstance(thumbnail_data, str)
        assert len(thumbnail_data) > 0
        # Verificar que es un string base64 válido.
        try:
            base64.b64decode(thumbnail_data)
            is_valid_base64 = True
        except Exception:
            is_valid_base64 = False
        assert is_valid_base64 is True

    async def test_create_thumbnail_with_error_handling(self):
        """Prueba de creación de miniatura con manejo de errores."""

        # Crear un mock de imagen que cause error al copiarse.
        mock_img = MagicMock()
        mock_img.copy.side_effect = Exception("Simulated error")
        mock_img.mode = "RGB"

        # Ejecución.
        with patch("app.crud.images.PILImage.new") as mock_new:
            # Simular la creación de una imagen en blanco como fallback.
            blank_img = MagicMock()
            buffer = io.BytesIO()
            buffer.write(b"test_data")
            blank_img.save.side_effect = lambda buf, format: buf.seek(0)
            mock_new.return_value = blank_img

            thumbnail_data = create_thumbnail(mock_img)

            # Verificación.
            assert isinstance(thumbnail_data, str)
            mock_new.assert_called_once()  # Se debería crear una imagen en blanco.

    async def test_convert_and_save_image(self):
        """Prueba de conversión y guardado de una imagen."""

        # Configuración.
        source_path = "/tmp/test_image.png"
        image_id = uuid.uuid4()

        # Crear mocks para PIL y os.
        with patch("app.crud.images.PILImage.open") as mock_open_image, patch(
            "app.crud.images.os.makedirs"
        ) as mock_makedirs, patch("builtins.open", mock_open()), patch(
            "app.crud.images.IMAGES_DIR", "/app/media/images"
        ):

            # Configurar el mock de la imagen.
            mock_img = MagicMock()
            mock_img.mode = "RGB"  # Modo que no requiere conversión.
            mock_open_image.return_value.__enter__.return_value = mock_img

            # Ejecución.
            result = convert_and_save_image(source_path, image_id)

            # Verificación.
            mock_makedirs.assert_called_once_with("/app/media/images", exist_ok=True)
            mock_img.save.assert_called_once()  # Debería guardar la imagen.
            assert result == f"images/{image_id}.jpg"
