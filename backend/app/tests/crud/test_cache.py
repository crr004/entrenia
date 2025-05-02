import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.crud.cache import invalidate_dataset_cache, update_dataset_cache
from app.models.datasets import Dataset

pytestmark = pytest.mark.asyncio


class TestCacheFunctions:
    async def test_invalidate_dataset_cache_success(self, mock_session):
        """Prueba de invalidación exitosa de la caché de un dataset."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = 10
        mock_dataset.cached_category_count = 5
        mock_dataset.cache_updated_at = datetime.now(timezone.utc)
        mock_dataset.__class__ = Dataset

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Ejecución.
        await invalidate_dataset_cache(session=mock_session, dataset_id=dataset_id)

        # Verificación.
        mock_session.get.assert_called_once_with(Dataset, dataset_id)
        assert mock_dataset.cached_image_count is None
        assert mock_dataset.cached_category_count is None
        assert mock_dataset.cache_updated_at is None
        mock_session.add.assert_called_once_with(mock_dataset)

        # Verificar que se han llamado los métodos asíncronos.
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    async def test_invalidate_dataset_cache_dataset_not_found(self, mock_session):
        """Prueba de invalidación de caché cuando el dataset no existe."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_session.get = AsyncMock(return_value=None)

        # Ejecución.
        await invalidate_dataset_cache(session=mock_session, dataset_id=dataset_id)

        # Verificación.
        assert mock_session.get.call_count == 1
        assert mock_session.add.call_count == 0
        assert mock_session.commit.call_count == 0
        assert mock_session.refresh.call_count == 0

    async def test_update_dataset_cache_success(self, mock_session):
        """Prueba de actualización exitosa de la caché de un dataset."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = None
        mock_dataset.cached_category_count = None
        mock_dataset.cache_updated_at = None
        mock_dataset.__class__ = Dataset

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Guardar la hora actual para verificar después.
        before_update = datetime.now(timezone.utc)

        # Ejecución.
        await update_dataset_cache(
            session=mock_session,
            dataset_id=dataset_id,
            image_count=15,
            category_count=7,
        )

        # Verificación.
        mock_session.get.assert_called_once_with(Dataset, dataset_id)
        assert mock_dataset.cached_image_count == 15
        assert mock_dataset.cached_category_count == 7
        assert mock_dataset.cache_updated_at is not None
        assert mock_dataset.cache_updated_at >= before_update
        mock_session.add.assert_called_once_with(mock_dataset)

        # Verificamos que se han llamado los métodos asíncronos.
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    async def test_update_dataset_cache_dataset_not_found(self, mock_session):
        """Prueba de actualización de caché cuando el dataset no existe."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_session.get = AsyncMock(return_value=None)

        # Ejecución.
        await update_dataset_cache(
            session=mock_session,
            dataset_id=dataset_id,
            image_count=15,
            category_count=7,
        )

        # Verificación.
        assert mock_session.get.call_count == 1
        assert mock_session.add.call_count == 0
        assert mock_session.commit.call_count == 0
        assert mock_session.refresh.call_count == 0

    async def test_update_dataset_cache_partial(self, mock_session):
        """Prueba de actualización parcial (solo image_count) de la caché de un dataset."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = None
        mock_dataset.cached_category_count = 5  # Ya tiene un valor previo.
        mock_dataset.cache_updated_at = None
        mock_dataset.__class__ = Dataset

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Ejecución.
        await update_dataset_cache(
            session=mock_session,
            dataset_id=dataset_id,
            image_count=20,  # Actualizar solo el conteo de imágenes.
        )

        # Verificación.
        mock_session.get.assert_called_once_with(Dataset, dataset_id)
        assert mock_dataset.cached_image_count == 20
        assert mock_dataset.cached_category_count == 5  # Permanece sin cambios.
        assert mock_dataset.cache_updated_at is not None
        mock_session.add.assert_called_once_with(mock_dataset)
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    async def test_update_dataset_cache_only_category(self, mock_session):
        """Prueba de actualización parcial (solo category_count) de la caché de un dataset."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = 10  # Ya tiene un valor previo.
        mock_dataset.cached_category_count = None
        mock_dataset.cache_updated_at = None
        mock_dataset.__class__ = Dataset

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Ejecución.
        await update_dataset_cache(
            session=mock_session,
            dataset_id=dataset_id,
            category_count=8,  # Actualizar solo el conteo de categorías.
        )

        # Verificación.
        mock_session.get.assert_called_once_with(Dataset, dataset_id)
        assert mock_dataset.cached_image_count == 10  # Permanece sin cambios.
        assert mock_dataset.cached_category_count == 8
        assert mock_dataset.cache_updated_at is not None
        mock_session.add.assert_called_once_with(mock_dataset)
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    async def test_update_dataset_cache_with_datetime_verification(self, mock_session):
        """Prueba que verifica que la fecha de actualización de caché se actualiza correctamente."""

        # Configuración.
        dataset_id = uuid.uuid4()
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.__class__ = Dataset

        # Fecha inicial antigua.
        old_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        mock_dataset.cache_updated_at = old_date

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Ejecución.
        with patch("app.crud.cache.datetime") as mock_datetime:
            # Fijar una fecha específica para la prueba.
            mock_now = datetime(2023, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = datetime

            await update_dataset_cache(
                session=mock_session, dataset_id=dataset_id, image_count=25
            )

            # Verificación.
            assert mock_dataset.cache_updated_at == mock_now
            assert mock_dataset.cache_updated_at != old_date
            assert mock_session.commit.call_count == 1
            assert mock_session.refresh.call_count == 1
