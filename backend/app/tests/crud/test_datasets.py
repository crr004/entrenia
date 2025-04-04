import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


from app.crud.datasets import (
    get_dataset_by_id,
    create_dataset,
    update_dataset,
    get_dataset_counts,
    get_dataset_by_userid_and_name,
    get_image_count,
    get_category_count,
    get_unlabeled_images,
    label_images_with_csv,
    delete_dataset,
)
from app.models.datasets import Dataset, DatasetCreate, DatasetUpdate

pytestmark = pytest.mark.asyncio


class TestDatasetsCRUD:

    async def test_get_dataset_by_id_success(self, mock_session):
        """Prueba de obtención exitosa de un dataset por ID."""
        # Configuración
        dataset_id = uuid.uuid4()

        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.name = "Test Dataset"
        mock_dataset.description = "Test Description"
        mock_dataset.user_id = uuid.uuid4()
        mock_dataset.__class__ = Dataset

        mock_session.get = AsyncMock(return_value=mock_dataset)

        # Ejecución
        result = await get_dataset_by_id(session=mock_session, id=dataset_id)

        # Verificación
        assert result is mock_dataset
        mock_session.get.assert_called_once_with(Dataset, dataset_id)

    async def test_get_dataset_by_id_not_found(self, mock_session):
        """Prueba cuando el dataset no existe."""
        # Configuración
        dataset_id = uuid.uuid4()

        mock_session.get = AsyncMock(return_value=None)

        # Ejecución
        result = await get_dataset_by_id(session=mock_session, id=dataset_id)

        # Verificación
        assert result is None
        mock_session.get.assert_called_once_with(Dataset, dataset_id)

    async def test_create_dataset_success(self, mock_session):
        """Prueba de creación exitosa de un dataset."""
        # Configuración
        user_id = uuid.uuid4()

        dataset_create = DatasetCreate(
            name="New Dataset", description="New Dataset Description", is_public=False
        )

        mock_dataset = MagicMock()
        mock_dataset.id = uuid.uuid4()
        mock_dataset.name = dataset_create.name
        mock_dataset.description = dataset_create.description
        mock_dataset.is_public = dataset_create.is_public
        mock_dataset.user_id = user_id
        mock_dataset.__class__ = Dataset

        with patch("app.crud.datasets.Dataset.model_validate") as mock_validate:
            mock_validate.return_value = mock_dataset

            # Ejecución
            result = await create_dataset(
                session=mock_session, user_id=user_id, dataset_in=dataset_create
            )

            # Verificación
            assert result is mock_dataset
            mock_validate.assert_called_once()
            mock_session.add.assert_called_once_with(mock_dataset)
            assert mock_session.commit.call_count == 1
            assert mock_session.refresh.call_count == 1

    async def test_update_dataset_success(self, mock_session):
        """Prueba de actualización exitosa de un dataset."""
        # Configuración
        dataset = MagicMock()
        dataset.id = uuid.uuid4()
        dataset.name = "Original Name"
        dataset.description = "Original Description"
        dataset.is_public = False
        dataset.__class__ = Dataset

        dataset_update = DatasetUpdate(
            name="Updated Name", description="Updated Description", is_public=True
        )

        # Ejecución
        result = await update_dataset(
            session=mock_session, dataset=dataset, dataset_data=dataset_update
        )

        # Verificación
        assert result is dataset
        dataset.sqlmodel_update.assert_called_once_with(dataset_update)
        mock_session.add.assert_called_once_with(dataset)
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    async def test_get_dataset_counts_with_cache(self, mock_session):
        """Prueba de obtención de conteos de dataset usando caché."""
        # Configuración
        dataset_id = uuid.uuid4()
        cached_image_count = 10
        cached_category_count = 5

        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = cached_image_count
        mock_dataset.cached_category_count = cached_category_count
        mock_dataset.__class__ = Dataset

        with patch("app.crud.datasets.get_dataset_by_id") as mock_get_dataset:

            async def mock_get_dataset_impl(*args, **kwargs):
                return mock_dataset

            mock_get_dataset.side_effect = mock_get_dataset_impl

            # Ejecución
            result = await get_dataset_counts(
                session=mock_session, dataset_id=dataset_id
            )

            # Verificación
            assert result["image_count"] == cached_image_count
            assert result["category_count"] == cached_category_count
            mock_get_dataset.assert_called_once_with(
                session=mock_session, id=dataset_id
            )

    async def test_get_dataset_counts_without_cache(self, mock_session):
        """Prueba de obtención de conteos de dataset recalculando (sin usar caché)."""
        # Configuración
        dataset_id = uuid.uuid4()
        image_count = 15
        category_count = 7

        # Dataset sin caché (valores None)
        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.cached_image_count = None
        mock_dataset.cached_category_count = None
        mock_dataset.__class__ = Dataset

        # Dataset después de actualizar la caché
        updated_dataset = MagicMock()
        updated_dataset.id = dataset_id
        updated_dataset.cached_image_count = image_count
        updated_dataset.cached_category_count = category_count
        updated_dataset.__class__ = Dataset

        with patch("app.crud.datasets.get_dataset_by_id") as mock_get_dataset:
            get_dataset_calls = 0

            async def mock_get_dataset_impl(*args, **kwargs):
                nonlocal get_dataset_calls
                get_dataset_calls += 1
                if get_dataset_calls == 1:
                    return mock_dataset
                else:
                    return updated_dataset

            mock_get_dataset.side_effect = mock_get_dataset_impl

            with patch(
                "app.crud.datasets.update_dataset_cache_with_calculation"
            ) as mock_update_cache:

                async def mock_update_cache_impl(*args, **kwargs):
                    return

                mock_update_cache.side_effect = mock_update_cache_impl

                # Ejecución
                result = await get_dataset_counts(
                    session=mock_session, dataset_id=dataset_id
                )

                # Verificación
                assert result["image_count"] == image_count
                assert result["category_count"] == category_count
                assert mock_get_dataset.call_count == 2
                mock_update_cache.assert_called_once_with(
                    session=mock_session, dataset_id=dataset_id, force_update=True
                )

    async def test_get_dataset_by_userid_and_name_success(self, mock_session):
        """Prueba de obtención exitosa de un dataset por ID de usuario y nombre."""
        # Configuración
        user_id = uuid.uuid4()
        name = "Test Dataset"

        mock_dataset = MagicMock()
        mock_dataset.id = uuid.uuid4()
        mock_dataset.name = name
        mock_dataset.user_id = user_id
        mock_dataset.__class__ = Dataset

        # Configurar el resultado de la consulta
        execute_result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.first.return_value = mock_dataset
        execute_result.scalars.return_value = scalars_result

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución
        with patch("app.crud.datasets.select") as mock_select:
            mock_select.return_value = MagicMock()

            result = await get_dataset_by_userid_and_name(
                session=mock_session, user_id=user_id, name=name
            )

            # Verificación
            assert result is mock_dataset
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()

    async def test_get_image_count_success(self, mock_session):
        """Prueba de obtención exitosa del conteo de imágenes de un dataset."""
        # Configuración
        dataset_id = uuid.uuid4()
        expected_count = 15

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = expected_count

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución
        with patch("app.crud.datasets.select") as mock_select, patch(
            "app.crud.datasets.func"
        ) as mock_func:

            mock_select.return_value = MagicMock()
            mock_func.count = MagicMock(return_value="count_expression")

            result = await get_image_count(session=mock_session, dataset_id=dataset_id)

            # Verificación
            assert result == expected_count
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()

    async def test_get_category_count_success(self, mock_session):
        """Prueba de obtención exitosa del conteo de categorías distintas de un dataset."""
        # Configuración
        dataset_id = uuid.uuid4()
        expected_count = 7

        # Configurar el resultado de la consulta
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = expected_count

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución
        with patch("app.crud.datasets.select") as mock_select, patch(
            "app.crud.datasets.func"
        ) as mock_func, patch("app.crud.datasets.distinct") as mock_distinct:

            mock_select.return_value = MagicMock()
            mock_func.count = MagicMock(return_value="count_expression")
            mock_distinct.return_value = "distinct_expression"

            result = await get_category_count(
                session=mock_session, dataset_id=dataset_id
            )

            # Verificación
            assert result == expected_count
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()
            mock_func.count.assert_called_once()
            mock_distinct.assert_called_once()

    async def test_get_unlabeled_images(self, mock_session):
        """Prueba de obtención exitosa de imágenes sin etiquetar de un dataset."""
        # Configuración
        dataset_id = uuid.uuid4()

        # Crear algunas imágenes sin etiqueta para el resultado
        mock_images = []
        for i in range(3):
            img = MagicMock()
            img.id = uuid.uuid4()
            img.name = f"unlabeled_{i}.jpg"
            img.file_path = f"images/unlabeled_{i}.jpg"
            img.dataset_id = dataset_id
            img.label = None
            img.thumbnail = f"base64_thumbnail_{i}"
            mock_images.append(img)

        # Configurar el resultado de la consulta
        execute_result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.all.return_value = mock_images
        execute_result.scalars.return_value = scalars_result

        mock_session.execute = AsyncMock(return_value=execute_result)

        # Ejecución
        with patch("app.crud.datasets.select") as mock_select:
            mock_select.return_value = MagicMock()

            result = await get_unlabeled_images(
                session=mock_session, dataset_id=dataset_id
            )

            # Verificación
            assert result == mock_images
            mock_session.execute.assert_called_once()
            mock_select.assert_called_once()
            mock_select.return_value.where.assert_called()

    async def test_label_images_with_csv(self, mock_session):
        """Prueba de etiquetado de imágenes con datos CSV."""
        # Configuración
        dataset_id = uuid.uuid4()

        # Datos de etiquetas desde el CSV
        labels_data = [
            {"image_name": "image1.jpg", "label": "cat"},
            {"image_name": "image2.jpg", "label": "dog"},
            {"image_name": "nonexistent.jpg", "label": "bird"},
        ]

        with patch(
            "app.crud.datasets.get_image_by_datasetid_and_name"
        ) as mock_get_image:

            async def mock_get_image_impl(session, dataset_id, name):
                if name in ["image1.jpg", "image2.jpg"]:
                    mock_img = MagicMock()
                    mock_img.name = name
                    return mock_img
                return None

            mock_get_image.side_effect = mock_get_image_impl

            with patch("app.crud.datasets.update_image") as mock_update_image:

                async def mock_update_impl(session, image, image_data):
                    return image

                mock_update_image.side_effect = mock_update_impl

                # Ejecución
                result = await label_images_with_csv(
                    session=mock_session, dataset_id=dataset_id, labels_data=labels_data
                )

                # Verificación
                assert (
                    result["labeled_count"] == 2
                )  # Solo dos imágenes fueron etiquetadas
                assert result["not_found_count"] == 1  # Una imagen no fue encontrada
                assert (
                    len(result["not_found_details"]) == 1
                )  # Detalle de la imagen no encontrada
                assert "nonexistent.jpg" in result["not_found_details"][0]
                assert mock_get_image.call_count == 3  # Se buscaron las tres imágenes
                assert (
                    mock_update_image.call_count == 2
                )  # Solo se actualizaron dos imágenes

    async def test_delete_dataset_success(self, mock_session):
        """Prueba de eliminación exitosa de un dataset."""
        # Configuración
        dataset = MagicMock()
        dataset.id = uuid.uuid4()
        dataset.__class__ = Dataset

        # Mock para select y execute que devuelve imágenes asociadas al dataset
        mock_images = []
        for i in range(3):
            img = MagicMock()
            img.id = uuid.uuid4()
            img.file_path = f"images/image_{i}.jpg"
            mock_images.append(img)

        execute_result = MagicMock()
        scalars_result = MagicMock()
        scalars_result.all.return_value = mock_images
        execute_result.scalars.return_value = scalars_result

        with patch("app.crud.datasets.select") as mock_select, patch(
            "app.crud.datasets.os.path.exists"
        ) as mock_exists, patch("app.crud.datasets.os.remove") as mock_remove:

            mock_select.return_value = MagicMock()
            mock_session.execute = AsyncMock(return_value=execute_result)
            mock_exists.return_value = True  # Simular que los archivos existen

            # Ejecución
            await delete_dataset(session=mock_session, dataset=dataset)

            # Verificación
            mock_session.execute.assert_called_once()
            mock_session.delete.assert_called_once_with(dataset)
            mock_session.commit.assert_called_once()

            assert mock_exists.call_count == len(mock_images)
            assert mock_remove.call_count == len(mock_images)
