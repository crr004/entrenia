import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import uuid

from fastapi import HTTPException, status

from app.api.routes.datasets import (
    get_public_datasets,
    read_public_dataset,
    read_public_dataset_label_details,
    read_datasets,
    read_dataset,
    read_dataset_label_details,
    create_dataset,
    clone_public_dataset,
)
from app.models.datasets import DatasetCreate

pytestmark = pytest.mark.asyncio


class TestDatasetRoutes:

    async def test_get_public_datasets_success(
        self,
        mock_session,
        mock_get_public_datasets,
        mock_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de obtención exitosa de datasets públicos."""

        # Configuración.
        mock_get_public_datasets.return_value = ([mock_dataset], 1)
        mock_user = MagicMock()
        mock_user.username = "testuser"

        with patch("app.api.routes.datasets.get_user_by_id") as local_mock:

            async def mock_get_user(*args, **kwargs):
                return mock_user

            local_mock.side_effect = mock_get_user

            # Ejecución.
            response = await get_public_datasets(
                session=mock_session,
                skip=0,
                limit=10,
                search=None,
            )

            # Verificación.
            assert response.count == 1
            assert len(response.datasets) == 1
            mock_get_public_datasets.assert_called_once_with(
                session=mock_session,
                skip=0,
                limit=10,
                search=None,
            )
            mock_get_dataset_counts.assert_called_once()
            local_mock.assert_called_once()

    async def test_read_public_dataset_success(
        self,
        mock_session,
        mock_get_dataset_by_id,
        mock_public_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de lectura exitosa de un dataset público."""

        # Configuración.
        mock_get_dataset_by_id.return_value = mock_public_dataset
        mock_user = MagicMock()
        mock_user.username = "testuser"

        with patch("app.api.routes.datasets.get_user_by_id") as local_mock:

            async def mock_get_user(*args, **kwargs):
                return mock_user

            local_mock.side_effect = mock_get_user

            dataset_id = mock_public_dataset.id

            # Ejecución.
            response = await read_public_dataset(
                session=mock_session,
                dataset_id=dataset_id,
                current_user=None,
            )

            # Verificación.
            assert response.id == mock_public_dataset.id
            assert response.name == mock_public_dataset.name
            mock_get_dataset_by_id.assert_called_once_with(
                session=mock_session, id=dataset_id
            )
            mock_get_dataset_counts.assert_called_once()
            local_mock.assert_called_once()

    async def test_read_public_dataset_not_found(
        self, mock_session, mock_get_dataset_by_id
    ):
        """Prueba de error al leer un dataset público que no existe."""

        # Configuración.
        mock_get_dataset_by_id.return_value = None
        dataset_id = uuid.uuid4()

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_public_dataset(
                session=mock_session,
                dataset_id=dataset_id,
                current_user=None,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail

    async def test_read_public_dataset_not_public(
        self, mock_session, mock_get_dataset_by_id, mock_dataset
    ):
        """Prueba de error al leer un dataset que no es público."""

        # Configuración.
        mock_get_dataset_by_id.return_value = mock_dataset
        dataset_id = mock_dataset.id

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_public_dataset(
                session=mock_session,
                dataset_id=dataset_id,
                current_user=None,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not public" in exc_info.value.detail

    async def test_read_public_dataset_label_details_success(
        self,
        mock_session,
        mock_get_dataset_by_id,
        mock_public_dataset,
        mock_get_dataset_label_details,
        mock_dataset_label_details,
    ):
        """Prueba de lectura exitosa de detalles de etiquetas de un dataset público."""

        # Configuración.
        mock_get_dataset_by_id.return_value = mock_public_dataset
        mock_get_dataset_label_details.return_value = mock_dataset_label_details
        dataset_id = mock_public_dataset.id

        # Ejecución.
        response = await read_public_dataset_label_details(
            session=mock_session,
            dataset_id=dataset_id,
            current_user=None,
        )

        # Verificación.
        assert response.dataset_id == mock_dataset_label_details["dataset_id"]
        assert len(response.categories) == len(mock_dataset_label_details["categories"])
        assert hasattr(response.categories[0], "name")
        assert hasattr(response.categories[0], "image_count")
        mock_get_dataset_by_id.assert_called_once_with(
            session=mock_session, id=dataset_id
        )
        mock_get_dataset_label_details.assert_called_once_with(
            session=mock_session, dataset_id=dataset_id
        )

    async def test_read_datasets_success(
        self,
        mock_session,
        mock_user,
        mock_get_user_datasets_sorted,
        mock_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de lectura exitosa de datasets del usuario."""

        # Configuración.
        mock_get_user_datasets_sorted.return_value = ([mock_dataset], 1, False)

        # Ejecución.
        response = await read_datasets(
            session=mock_session,
            current_user=mock_user,
            skip=0,
            limit=100,
            search=None,
            sort_by="created_at",
            sort_order="desc",
        )

        # Verificación.
        assert response.count == 1
        assert len(response.datasets) == 1
        mock_get_user_datasets_sorted.assert_called_once_with(
            session=mock_session,
            skip=0,
            limit=100,
            search=None,
            sort_by="created_at",
            sort_order="desc",
            user_id=mock_user.id,
            admin_view=False,
        )
        mock_get_dataset_counts.assert_called_once()

    async def test_read_datasets_admin_success(
        self,
        mock_session,
        mock_admin_user,
        mock_get_user_datasets_sorted,
        mock_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de lectura exitosa de todos los datasets por un administrador."""

        # Configuración.
        mock_get_user_datasets_sorted.return_value = ([mock_dataset], 1, False)
        mock_user = MagicMock()
        mock_user.username = "testuser"

        with patch("app.api.routes.datasets.get_user_by_id") as local_mock:

            async def mock_get_user(*args, **kwargs):
                return mock_user

            local_mock.side_effect = mock_get_user

            # Ejecución.
            response = await read_datasets(
                session=mock_session,
                current_user=mock_admin_user,
                skip=0,
                limit=100,
                search=None,
                sort_by="created_at",
                sort_order="desc",
            )

            # Verificación.
            assert response.count == 1
            assert len(response.datasets) == 1
            mock_get_user_datasets_sorted.assert_called_once_with(
                session=mock_session,
                skip=0,
                limit=100,
                search=None,
                sort_by="created_at",
                sort_order="desc",
                user_id=None,
                admin_view=True,
            )
            mock_get_dataset_counts.assert_called_once()
            local_mock.assert_called_once()

    async def test_read_datasets_invalid_sort_order(self, mock_session, mock_user):
        """Prueba de error al usar un orden de ordenación inválido."""

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_datasets(
                session=mock_session,
                current_user=mock_user,
                skip=0,
                limit=100,
                search=None,
                sort_by="created_at",
                sort_order="invalid",
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid sort_order" in exc_info.value.detail

    async def test_read_dataset_success(
        self,
        mock_session,
        mock_user,
        mock_get_dataset_by_id,
        mock_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de lectura exitosa de un dataset específico."""

        # Configuración.
        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.
        mock_get_dataset_by_id.return_value = mock_dataset
        dataset_id = mock_dataset.id

        # Ejecución.
        response = await read_dataset(
            session=mock_session,
            current_user=mock_user,
            dataset_id=dataset_id,
        )

        # Verificación.
        assert response.id == mock_dataset.id
        assert response.name == mock_dataset.name
        mock_get_dataset_by_id.assert_called_once_with(
            session=mock_session, id=dataset_id
        )
        mock_get_dataset_counts.assert_called_once()

    async def test_read_dataset_not_found(
        self, mock_session, mock_user, mock_get_dataset_by_id
    ):
        """Prueba de error al leer un dataset que no existe."""

        # Configuración.
        mock_get_dataset_by_id.return_value = None
        dataset_id = uuid.uuid4()

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_dataset(
                session=mock_session,
                current_user=mock_user,
                dataset_id=dataset_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail

    async def test_read_dataset_unauthorized(
        self, mock_session, mock_user, mock_get_dataset_by_id, mock_dataset
    ):
        """Prueba de error al leer un dataset al que el usuario no tiene acceso."""

        # Configuración.
        other_user_id = uuid.uuid4()
        mock_dataset.user_id = other_user_id  # Dataset pertenece a otro usuario.
        mock_get_dataset_by_id.return_value = mock_dataset
        dataset_id = mock_dataset.id

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_dataset(
                session=mock_session,
                current_user=mock_user,
                dataset_id=dataset_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "privileges" in exc_info.value.detail

    async def test_read_dataset_label_details_success(
        self,
        mock_session,
        mock_user,
        mock_get_dataset_by_id,
        mock_dataset,
        mock_get_dataset_label_details,
        mock_dataset_label_details,
    ):
        """Prueba de lectura exitosa de detalles de etiquetas de un dataset."""

        # Configuración.
        mock_dataset.user_id = mock_user.id  # Dataset pertenece al usuario.
        mock_get_dataset_by_id.return_value = mock_dataset
        mock_get_dataset_label_details.return_value = mock_dataset_label_details
        dataset_id = mock_dataset.id

        # Ejecución.
        response = await read_dataset_label_details(
            session=mock_session,
            current_user=mock_user,
            dataset_id=dataset_id,
        )

        # Verificación.
        assert response.dataset_id == mock_dataset_label_details["dataset_id"]
        assert len(response.categories) == len(mock_dataset_label_details["categories"])
        assert hasattr(response.categories[0], "name")
        assert hasattr(response.categories[0], "image_count")
        mock_get_dataset_by_id.assert_called_once_with(
            session=mock_session, id=dataset_id
        )
        mock_get_dataset_label_details.assert_called_once_with(
            session=mock_session, dataset_id=dataset_id
        )

    async def test_create_dataset_success(
        self,
        mock_session,
        mock_user,
        mock_create_dataset,
        mock_get_dataset_by_userid_and_name,
    ):
        """Prueba de creación exitosa de un dataset."""

        # Configuración.
        mock_get_dataset_by_userid_and_name.return_value = (
            None  # No existe dataset con ese nombre.
        )
        dataset_data = DatasetCreate(
            name="New Dataset",
            description="This is a new dataset",
            is_public=False,
        )
        new_dataset = MagicMock()
        new_dataset.id = uuid.uuid4()
        new_dataset.name = dataset_data.name
        mock_create_dataset.return_value = new_dataset

        # Ejecución.
        response = await create_dataset(
            session=mock_session,
            current_user=mock_user,
            dataset_in=dataset_data,
        )

        # Verificación.
        assert response.name == dataset_data.name
        mock_get_dataset_by_userid_and_name.assert_called_once_with(
            session=mock_session,
            user_id=mock_user.id,
            name=dataset_data.name,
        )
        mock_create_dataset.assert_called_once_with(
            session=mock_session,
            user_id=mock_user.id,
            dataset_in=dataset_data,
        )

    async def test_create_dataset_already_exists(
        self, mock_session, mock_user, mock_get_dataset_by_userid_and_name, mock_dataset
    ):
        """Prueba de error al crear un dataset con un nombre que ya existe."""

        # Configuración.
        mock_get_dataset_by_userid_and_name.return_value = (
            mock_dataset  # Ya existe un dataset con ese nombre.
        )
        dataset_data = DatasetCreate(
            name="Existing Dataset",
            description="This dataset already exists",
            is_public=False,
        )

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await create_dataset(
                session=mock_session,
                current_user=mock_user,
                dataset_in=dataset_data,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already has a dataset with that name" in exc_info.value.detail

    async def test_clone_public_dataset_success(
        self,
        mock_session,
        mock_user,
        mock_get_dataset_by_id,
        mock_public_dataset,
        mock_clone_dataset,
        mock_get_dataset_counts,
    ):
        """Prueba de clonación exitosa de un dataset público."""

        # Configuración.
        source_user_id = uuid.uuid4()
        mock_public_dataset.user_id = (
            source_user_id  # Dataset pertenece a otro usuario.
        )
        mock_public_dataset.is_public = True  # Aseguramos que es público.
        mock_get_dataset_by_id.return_value = mock_public_dataset

        source_user = MagicMock()
        source_user.username = "sourceuser"

        with patch("app.api.routes.datasets.get_user_by_id") as local_mock_user:

            async def mock_get_user(*args, **kwargs):
                return source_user

            local_mock_user.side_effect = mock_get_user

            # Mockear DatasetReturn para evitar la validación.
            with patch("app.api.routes.datasets.DatasetReturn") as mock_dataset_return:
                mock_return = MagicMock()
                mock_dataset_return.return_value = mock_return
                mock_return.name = "sourceuser - Public Dataset"
                mock_return.id = uuid.uuid4()

                cloned_dataset = MagicMock()
                cloned_dataset.id = uuid.uuid4()
                cloned_dataset.name = f"sourceuser - Public Dataset"
                cloned_dataset.description = "This is a public dataset"
                cloned_dataset.is_public = False
                cloned_dataset.user_id = mock_user.id
                cloned_dataset.created_at = datetime.now(timezone.utc)

                cloned_dict = {
                    "id": cloned_dataset.id,
                    "name": cloned_dataset.name,
                    "description": cloned_dataset.description,
                    "is_public": cloned_dataset.is_public,
                    "user_id": cloned_dataset.user_id,
                    "created_at": cloned_dataset.created_at,
                    "username": "sourceuser",
                    "image_count": 10,
                    "category_count": 3,
                }
                cloned_dataset.model_dump.return_value = cloned_dict

                # Configurar cómo se comporta el mock cuando se llama.
                async def mock_clone(*args, **kwargs):
                    return cloned_dataset

                mock_clone_dataset.side_effect = mock_clone

                dataset_id = mock_public_dataset.id

                # Ejecución.
                response = await clone_public_dataset(
                    dataset_id=dataset_id,
                    session=mock_session,
                    current_user=mock_user,
                )

                # Verificación.
                assert response == mock_return
                local_mock_user.assert_called_once()
                mock_clone_dataset.assert_called_once_with(
                    session=mock_session,
                    source_dataset_id=dataset_id,
                    target_user_id=mock_user.id,
                    source_username="sourceuser",
                )
                mock_get_dataset_counts.assert_called_once()

    async def test_clone_public_dataset_not_found(
        self, mock_session, mock_user, mock_get_dataset_by_id
    ):
        """Prueba de error al clonar un dataset que no existe."""

        # Configuración.
        mock_get_dataset_by_id.return_value = None
        dataset_id = uuid.uuid4()

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await clone_public_dataset(
                dataset_id=dataset_id,
                session=mock_session,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail

    async def test_clone_public_dataset_not_public(
        self, mock_session, mock_user, mock_get_dataset_by_id, mock_dataset
    ):
        """Prueba de error al clonar un dataset que no es público."""

        # Configuración.
        other_user_id = uuid.uuid4()
        mock_dataset.user_id = other_user_id  # Dataset pertenece a otro usuario.
        mock_get_dataset_by_id.return_value = mock_dataset  # No es público por defecto.
        dataset_id = mock_dataset.id

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await clone_public_dataset(
                dataset_id=dataset_id,
                session=mock_session,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not public" in exc_info.value.detail

    async def test_clone_own_dataset_error(
        self, mock_session, mock_user, mock_get_dataset_by_id, mock_public_dataset
    ):
        """Prueba de error al intentar clonar un dataset que ya es propiedad del usuario."""

        # Configuración.
        mock_public_dataset.user_id = mock_user.id  # Dataset ya pertenece al usuario.
        mock_get_dataset_by_id.return_value = mock_public_dataset
        dataset_id = mock_public_dataset.id

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await clone_public_dataset(
                dataset_id=dataset_id,
                session=mock_session,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already own this dataset" in exc_info.value.detail
