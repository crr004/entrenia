import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from fastapi import HTTPException, status

from app.api.routes.images import (
    read_images,
    read_image,
    update_image,
    delete_image,
)
from app.models.images import ImageUpdate

pytestmark = pytest.mark.asyncio


class TestImageRoutes:

    async def test_read_images_success(
        self,
        mock_session,
        mock_user,
        mock_dataset,
    ):
        """Prueba de lectura exitosa de imágenes de un dataset."""

        # Configuración.
        mock_user.is_admin = False
        mock_user.id = uuid.uuid4()
        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.
        dataset_id = mock_dataset.id

        with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset_by_id:
            mock_get_dataset_by_id.return_value = mock_dataset

            images = []
            for i in range(3):
                img = MagicMock()
                img.id = uuid.uuid4()
                img.name = f"test_image_{i}.jpg"
                img.file_path = f"images/test_image_{i}.jpg"
                img.dataset_id = dataset_id
                img.label = f"label_{i}" if i % 2 == 0 else None
                img.thumbnail = f"base64data_{i}"
                img.created_at = datetime.now(timezone.utc)
                images.append(img)

            total_count = len(images)

            with patch(
                "app.api.routes.images.crud_images.get_images_sorted"
            ) as mock_get_images:

                async def mock_get_images_sorted(*args, **kwargs):
                    return images, total_count

                mock_get_images.side_effect = mock_get_images_sorted

                with patch(
                    "app.models.images.ImageReturn.model_validate"
                ) as mock_validate:

                    def side_effect(img):
                        mock_return = MagicMock()
                        mock_return.id = img.id
                        mock_return.name = img.name
                        mock_return.file_path = img.file_path
                        mock_return.dataset_id = img.dataset_id
                        mock_return.label = img.label
                        mock_return.thumbnail = img.thumbnail
                        mock_return.created_at = img.created_at
                        return mock_return

                    mock_validate.side_effect = side_effect

                    # Ejecución.
                    response = await read_images(
                        session=mock_session,
                        current_user=mock_user,
                        dataset_id=dataset_id,
                        skip=0,
                        limit=100,
                    )

                    # Verificación.
                    assert response.count == total_count
                    assert len(response.images) == total_count
                    mock_get_dataset_by_id.assert_called_once_with(
                        session=mock_session, id=dataset_id
                    )
                    mock_get_images.assert_called_once()

    async def test_read_images_not_found(
        self,
        mock_session,
        mock_user,
    ):
        """Prueba de error al leer imágenes de un dataset que no existe."""

        # Configuración.
        mock_user.is_admin = False
        dataset_id = uuid.uuid4()

        with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset_by_id:
            mock_get_dataset_by_id.return_value = None

            # Ejecución y verificación.
            with pytest.raises(HTTPException) as exc_info:
                await read_images(
                    session=mock_session,
                    current_user=mock_user,
                    dataset_id=dataset_id,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in exc_info.value.detail.lower()

    async def test_read_images_unauthorized(
        self, mock_session, mock_user, mock_get_dataset_by_id, mock_dataset
    ):
        """Prueba de error al leer imágenes de un dataset al que el usuario no tiene acceso."""

        # Configuración.
        other_user_id = uuid.uuid4()
        mock_dataset.user_id = other_user_id  # Dataset pertenece a otro usuario.
        mock_get_dataset_by_id.return_value = mock_dataset
        dataset_id = mock_dataset.id

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_images(
                session=mock_session,
                current_user=mock_user,
                dataset_id=dataset_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "privileges" in exc_info.value.detail

    async def test_read_images_invalid_sort_params(self, mock_session, mock_user):
        """Prueba de error al usar parámetros de ordenación inválidos."""

        # Configuración.
        dataset_id = uuid.uuid4()

        # Ejecución y verificación - Sort order inválido.
        with pytest.raises(HTTPException) as exc_info:
            await read_images(
                session=mock_session,
                current_user=mock_user,
                dataset_id=dataset_id,
                sort_order="invalid",
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid sort_order" in exc_info.value.detail

        # Ejecución y verificación - Sort by inválido.
        with pytest.raises(HTTPException) as exc_info:
            await read_images(
                session=mock_session,
                current_user=mock_user,
                dataset_id=dataset_id,
                sort_by="invalid",
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid sort_by" in exc_info.value.detail

    async def test_read_image_success(self, mock_session, mock_user, mock_dataset):
        """Prueba de lectura exitosa de una imagen específica."""

        # Configuración.
        mock_user.is_admin = False
        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.

        image_id = uuid.uuid4()

        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.name = "test_image.jpg"
        mock_image.file_path = "images/test.jpg"
        mock_image.label = "test_label"
        mock_image.dataset_id = mock_dataset.id
        mock_image.thumbnail = "base64data"
        mock_image.created_at = datetime.now(timezone.utc)

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                with patch(
                    "app.models.images.ImageReturn.model_validate"
                ) as mock_validate:
                    mock_return = MagicMock()
                    mock_return.id = mock_image.id
                    mock_return.name = mock_image.name
                    mock_return.file_path = mock_image.file_path
                    mock_return.dataset_id = mock_image.dataset_id
                    mock_return.label = mock_image.label
                    mock_return.thumbnail = mock_image.thumbnail
                    mock_return.created_at = mock_image.created_at
                    mock_validate.return_value = mock_return

                    # Ejecución.
                    response = await read_image(
                        session=mock_session,
                        current_user=mock_user,
                        image_id=image_id,
                    )

                    # Verificación.
                    mock_get_image.assert_called_once_with(
                        session=mock_session, id=image_id
                    )
                    mock_get_dataset.assert_called_once_with(
                        session=mock_session, id=mock_image.dataset_id
                    )
                    assert response.id == mock_image.id
                    assert response.name == mock_image.name

    async def test_read_image_not_found(self, mock_session, mock_user):
        """Prueba de error al leer una imagen que no existe."""

        # Configuración.
        image_id = uuid.uuid4()

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = None

            # Ejecución y verificación.
            with pytest.raises(HTTPException) as exc_info:
                await read_image(
                    session=mock_session,
                    current_user=mock_user,
                    image_id=image_id,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in exc_info.value.detail

    async def test_read_image_dataset_not_found(self, mock_session, mock_user):
        """Prueba de error cuando el dataset de la imagen no existe."""

        # Configuración.
        image_id = uuid.uuid4()
        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.dataset_id = uuid.uuid4()

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = None

                # Ejecución y verificación.
                with pytest.raises(HTTPException) as exc_info:
                    await read_image(
                        session=mock_session,
                        current_user=mock_user,
                        image_id=image_id,
                    )

                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
                assert "Dataset not found" in exc_info.value.detail

    async def test_read_image_unauthorized(self, mock_session, mock_user, mock_dataset):
        """Prueba de error al leer una imagen a la que el usuario no tiene acceso."""

        # Configuración.
        image_id = uuid.uuid4()
        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.dataset_id = mock_dataset.id

        other_user_id = uuid.uuid4()
        mock_dataset.user_id = other_user_id  # Dataset pertenece a otro usuario.

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                # Ejecución y verificación.
                with pytest.raises(HTTPException) as exc_info:
                    await read_image(
                        session=mock_session,
                        current_user=mock_user,
                        image_id=image_id,
                    )

                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "privileges" in exc_info.value.detail

    async def test_update_image_success(self, mock_session, mock_user, mock_dataset):
        """Prueba de actualización exitosa de una imagen."""

        # Configuración.
        mock_user.is_admin = False

        image_id = uuid.uuid4()
        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.name = "original_name.jpg"
        mock_image.file_path = "images/test.jpg"
        mock_image.label = "original_label"
        mock_image.dataset_id = mock_dataset.id
        mock_image.thumbnail = "base64data"
        mock_image.created_at = datetime.now(timezone.utc)

        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.

        image_update = ImageUpdate(
            name="new_name.jpg",
            label="new_label",
        )

        updated_image = MagicMock()
        updated_image.id = image_id
        updated_image.name = "new_name.jpg"
        updated_image.label = "new_label"
        updated_image.file_path = "images/test.jpg"
        updated_image.dataset_id = mock_dataset.id
        updated_image.thumbnail = "base64data"
        updated_image.created_at = datetime.now(timezone.utc)

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                with patch(
                    "app.api.routes.images.crud_images.get_image_by_datasetid_and_name"
                ) as mock_get_by_name:
                    mock_get_by_name.return_value = None

                    with patch(
                        "app.api.routes.images.crud_images.update_image"
                    ) as mock_update:
                        mock_update.return_value = updated_image

                        with patch(
                            "app.models.images.ImageReturn.model_validate"
                        ) as mock_validate:
                            mock_return = MagicMock()
                            mock_return.id = updated_image.id
                            mock_return.name = updated_image.name
                            mock_return.file_path = updated_image.file_path
                            mock_return.dataset_id = updated_image.dataset_id
                            mock_return.label = updated_image.label
                            mock_return.thumbnail = updated_image.thumbnail
                            mock_return.created_at = updated_image.created_at
                            mock_validate.return_value = mock_return

                            # Ejecución.
                            response = await update_image(
                                session=mock_session,
                                current_user=mock_user,
                                image_id=image_id,
                                image_in=image_update,
                            )

                            # Verificación.
                            mock_get_image.assert_called_once_with(
                                session=mock_session, id=image_id
                            )
                            mock_get_dataset.assert_called_once_with(
                                session=mock_session, id=mock_image.dataset_id
                            )
                            mock_update.assert_called_once()
                            assert response.id == updated_image.id
                            assert response.name == updated_image.name
                            assert response.label == updated_image.label

    async def test_update_image_duplicate_name(
        self, mock_session, mock_user, mock_dataset
    ):
        """Prueba de error al actualizar una imagen con un nombre que ya existe."""

        # Configuración.
        image_id = uuid.uuid4()
        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.dataset_id = mock_dataset.id
        mock_image.name = "original_name.jpg"

        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.

        existing_image = MagicMock()
        existing_image.id = uuid.uuid4()

        image_update = ImageUpdate(
            name="existing_name.jpg",  # Nombre ya existente.
        )

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                with patch(
                    "app.api.routes.images.crud_images.get_image_by_datasetid_and_name"
                ) as mock_get_by_name:
                    mock_get_by_name.return_value = (
                        existing_image  # Ya existe otra imagen con ese nombre.
                    )

                    # Ejecución y verificación.
                    with pytest.raises(HTTPException) as exc_info:
                        await update_image(
                            session=mock_session,
                            current_user=mock_user,
                            image_id=image_id,
                            image_in=image_update,
                        )

                    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
                    assert (
                        "already has an image with that name" in exc_info.value.detail
                    )

    async def test_delete_image_success(self, mock_session, mock_user, mock_dataset):
        """Prueba de eliminación exitosa de una imagen."""

        # Configuración.
        image_id = uuid.uuid4()
        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.dataset_id = mock_dataset.id

        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                with patch(
                    "app.api.routes.images.crud_images.delete_image"
                ) as mock_delete:
                    # Ejecución.
                    response = await delete_image(
                        session=mock_session,
                        current_user=mock_user,
                        image_id=image_id,
                    )

                    # Verificación.
                    mock_get_image.assert_called_once_with(
                        session=mock_session, id=image_id
                    )
                    mock_get_dataset.assert_called_once_with(
                        session=mock_session, id=mock_image.dataset_id
                    )
                    mock_delete.assert_called_once_with(
                        session=mock_session, image=mock_image
                    )
                    assert response.message == "Image deleted successfully"

    async def test_admin_access_other_user_images(
        self, mock_session, mock_admin_user, mock_dataset
    ):
        """Prueba que un admin puede acceder a imágenes de otro usuario."""

        # Configuración.
        mock_admin_user.is_admin = True

        image_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        mock_image = MagicMock()
        mock_image.id = image_id
        mock_image.name = "admin_test.jpg"
        mock_image.file_path = "images/admin_test.jpg"
        mock_image.label = "admin_label"
        mock_image.dataset_id = mock_dataset.id
        mock_image.thumbnail = "base64data"
        mock_image.created_at = datetime.now(timezone.utc)

        mock_dataset.user_id = other_user_id  # Dataset pertenece a otro usuario.

        with patch(
            "app.api.routes.images.crud_images.get_image_by_id"
        ) as mock_get_image:
            mock_get_image.return_value = mock_image

            with patch("app.api.routes.images.get_dataset_by_id") as mock_get_dataset:
                mock_get_dataset.return_value = mock_dataset

                with patch(
                    "app.models.images.ImageReturn.model_validate"
                ) as mock_validate:
                    mock_return = MagicMock()
                    mock_return.id = mock_image.id
                    mock_return.name = mock_image.name
                    mock_return.file_path = mock_image.file_path
                    mock_return.dataset_id = mock_image.dataset_id
                    mock_return.label = mock_image.label
                    mock_return.thumbnail = mock_image.thumbnail
                    mock_return.created_at = mock_image.created_at
                    mock_validate.return_value = mock_return

                    # Ejecución.
                    # No debería lanzar excepción porque es admin.
                    response = await read_image(
                        session=mock_session,
                        current_user=mock_admin_user,
                        image_id=image_id,
                    )

                    # Verificación.
                    assert response is not None
                    mock_get_image.assert_called_once()
                    mock_get_dataset.assert_called_once()
