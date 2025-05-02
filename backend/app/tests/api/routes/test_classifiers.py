import os
import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from fastapi import HTTPException, status, UploadFile

from app.api.routes.classifiers import (
    get_available_architectures,
    create_classifier,
    read_classifiers,
    read_classifier,
    read_classifier_detail,
    update_classifier,
    delete_classifier,
    download_model,
    predict_images,
)
from app.models.classifiers import (
    ClassifierCreate,
    ClassifierUpdate,
)
from app.ml.models import AVAILABLE_MODELS

pytestmark = pytest.mark.asyncio


class TestClassifierRoutes:

    async def test_get_available_architectures(self, mock_user):
        """Prueba de obtener las arquitecturas disponibles."""

        # Ejecución.
        result = await get_available_architectures(current_user=mock_user)

        # Verificación.
        assert isinstance(result, list)
        assert result == list(AVAILABLE_MODELS.keys())

    async def test_create_classifier_success(
        self,
        mock_session,
        mock_user,
        mock_get_classifier_by_userid_and_name,
        mock_create_classifier,
        mock_dataset,
    ):
        """Prueba de creación exitosa de un clasificador."""

        # Preparación.
        with patch(
            "app.api.routes.classifiers.crud_datasets.get_dataset_by_userid_and_name"
        ) as mock_get_dataset:
            mock_get_dataset.return_value = mock_dataset
            mock_get_classifier_by_userid_and_name.return_value = None

            mock_result_classifier = MagicMock()
            mock_result_classifier.id = uuid.uuid4()
            mock_result_classifier.name = "Test Classifier"
            mock_result_classifier.description = "Classifier for testing"
            mock_result_classifier.user_id = mock_user.id
            mock_result_classifier.dataset_id = uuid.uuid4()
            mock_result_classifier.status = "not_trained"
            mock_result_classifier.created_at = datetime.now(timezone.utc)

            mock_result_classifier.model_dump.return_value = {
                "id": mock_result_classifier.id,
                "name": mock_result_classifier.name,
                "description": mock_result_classifier.description,
                "user_id": mock_result_classifier.user_id,
                "dataset_id": mock_result_classifier.dataset_id,
                "status": mock_result_classifier.status,
                "created_at": mock_result_classifier.created_at,
            }

            mock_create_classifier.return_value = mock_result_classifier

            classifier_data = {
                "name": "Test Classifier",
                "description": "Classifier for testing",
                "dataset_name": "Test Dataset",
                "architecture": "efficientnetb3",
                "model_parameters": {"epochs": 20, "batch_size": 32},
            }

            with patch("app.api.routes.classifiers.ClassifierReturn") as mock_class:
                mock_return = MagicMock()
                mock_return.id = mock_result_classifier.id
                mock_return.name = mock_result_classifier.name
                mock_return.description = mock_result_classifier.description
                mock_class.return_value = mock_return

                with patch.dict(
                    "app.api.routes.classifiers.AVAILABLE_MODELS",
                    {"efficientnetb3": "some_value"},
                ):
                    # Ejecución.
                    result = await create_classifier(
                        session=mock_session,
                        current_user=mock_user,
                        classifier_in=ClassifierCreate(**classifier_data),
                    )

                    # Verificación.
                    mock_get_dataset.assert_called_once()
                    mock_get_classifier_by_userid_and_name.assert_called_once()
                    mock_create_classifier.assert_called_once()
                    mock_class.assert_called_once()
                    assert result == mock_return

    async def test_create_classifier_invalid_architecture(
        self, mock_session, mock_user
    ):
        """Prueba de error al crear un clasificador con arquitectura inválida."""

        # Crear datos de prueba con arquitectura inválida.
        classifier_data = {
            "name": "Test Classifier",
            "description": "Classifier for testing",
            "dataset_name": "Test Dataset",
            "architecture": "invalid_arch",
            "model_parameters": {"epochs": 20, "batch_size": 32},
        }

        # Ejecución y verificación.
        with patch.dict(
            "app.api.routes.classifiers.AVAILABLE_MODELS", {"valid_arch": "some_value"}
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_classifier(
                    session=mock_session,
                    current_user=mock_user,
                    classifier_in=ClassifierCreate(**classifier_data),
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid architecture" in exc_info.value.detail

    async def test_create_classifier_dataset_not_found(self, mock_session, mock_user):
        """Prueba de error al crear un clasificador con un dataset que no existe."""

        # Preparación.
        with patch(
            "app.api.routes.classifiers.crud_datasets.get_dataset_by_userid_and_name"
        ) as mock_get_dataset:
            mock_get_dataset.return_value = None

            # Crear datos de prueba.
            classifier_data = {
                "name": "Test Classifier",
                "description": "Classifier for testing",
                "dataset_name": "Nonexistent Dataset",
                "architecture": "efficientnetb3",
                "model_parameters": {"epochs": 20, "batch_size": 32},
            }

            # Ejecución y verificación.
            with patch.dict(
                "app.api.routes.classifiers.AVAILABLE_MODELS",
                {"efficientnetb3": "some_value"},
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await create_classifier(
                        session=mock_session,
                        current_user=mock_user,
                        classifier_in=ClassifierCreate(**classifier_data),
                    )

                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
                assert "not found in your datasets" in exc_info.value.detail

    async def test_create_classifier_name_exists(
        self, mock_session, mock_user, mock_classifier
    ):
        """Prueba de error al crear un clasificador con un nombre que ya existe."""

        # Preparación.
        with patch(
            "app.api.routes.classifiers.crud_datasets.get_dataset_by_userid_and_name"
        ) as mock_get_dataset:
            with patch(
                "app.api.routes.classifiers.crud_classifiers.get_classifier_by_userid_and_name"
            ) as mock_get_classifier:
                mock_get_dataset.return_value = MagicMock()
                mock_get_classifier.return_value = mock_classifier

                # Crear datos de prueba.
                classifier_data = {
                    "name": "Test Classifier",  # Nombre ya existente.
                    "description": "Classifier for testing",
                    "dataset_name": "Test Dataset",
                    "architecture": "efficientnetb3",
                    "model_parameters": {"epochs": 20, "batch_size": 32},
                }

                # Ejecución y verificación.
                with patch.dict(
                    "app.api.routes.classifiers.AVAILABLE_MODELS",
                    {"efficientnetb3": "some_value"},
                ):
                    with pytest.raises(HTTPException) as exc_info:
                        await create_classifier(
                            session=mock_session,
                            current_user=mock_user,
                            classifier_in=ClassifierCreate(**classifier_data),
                        )

                    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
                    assert (
                        "already has a classifier with that name"
                        in exc_info.value.detail
                    )

    async def test_read_classifier_success(
        self, mock_session, mock_user, mock_classifier, mock_get_classifier_by_id
    ):
        """Prueba de lectura exitosa de un clasificador."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.

        # Ejecución.
        result = await read_classifier(
            session=mock_session,
            current_user=mock_user,
            classifier_id=mock_classifier.id,
        )

        # Verificación.
        mock_get_classifier_by_id.assert_called_once_with(
            session=mock_session, id=mock_classifier.id
        )
        assert result.id == mock_classifier.id
        assert result.name == mock_classifier.name

    async def test_read_classifier_not_found(
        self, mock_session, mock_user, mock_get_classifier_by_id
    ):
        """Prueba de error al leer un clasificador que no existe."""

        # Preparación.
        mock_get_classifier_by_id.return_value = None
        classifier_id = uuid.uuid4()

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_classifier(
                session=mock_session,
                current_user=mock_user,
                classifier_id=classifier_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail

    async def test_read_classifier_unauthorized(
        self, mock_session, mock_user, mock_classifier, mock_get_classifier_by_id
    ):
        """Prueba de error al leer un clasificador sin autorización."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = uuid.uuid4()  # Usuario diferente.
        mock_user.is_admin = False  # No es admin.

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await read_classifier(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_classifier.id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "doesn't have enough privileges" in exc_info.value.detail

    async def test_read_classifier_admin_access(
        self, mock_session, mock_admin_user, mock_classifier, mock_get_classifier_by_id
    ):
        """Prueba que un admin puede leer cualquier clasificador."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = uuid.uuid4()  # Usuario diferente.

        with patch("app.api.routes.classifiers.get_user_by_id") as mock_get_user:
            user = MagicMock()
            user.username = "testuser"
            mock_get_user.return_value = user

            # Ejecución.
            result = await read_classifier(
                session=mock_session,
                current_user=mock_admin_user,
                classifier_id=mock_classifier.id,
            )

            # Verificación.
            mock_get_classifier_by_id.assert_called_once()
            mock_get_user.assert_called_once()
            assert result.id == mock_classifier.id
            assert result.username == "testuser"  # Verificar que se añadió el username.

    async def test_read_classifiers_success(
        self, mock_session, mock_user, mock_get_classifiers_sorted
    ):
        """Prueba de listado exitoso de clasificadores."""

        # Preparación.
        classifier1_data = {
            "id": uuid.uuid4(),
            "name": "Classifier 1",
            "description": "Description 1",
            "user_id": mock_user.id,
            "dataset_id": uuid.uuid4(),
            "status": "trained",
            "created_at": datetime.now(timezone.utc),
            "username": "user1",
        }

        classifier2_data = {
            "id": uuid.uuid4(),
            "name": "Classifier 2",
            "description": "Description 2",
            "user_id": mock_user.id,
            "dataset_id": uuid.uuid4(),
            "status": "not_trained",
            "created_at": datetime.now(timezone.utc),
            "username": "user2",
        }

        mock_classifier1 = MagicMock()
        mock_classifier1.model_dump.return_value = classifier1_data

        mock_classifier2 = MagicMock()
        mock_classifier2.model_dump.return_value = classifier2_data

        mock_get_classifiers_sorted.return_value = (
            [(mock_classifier1, "user1"), (mock_classifier2, "user2")],
            2,
        )

        mock_classifier_return1 = MagicMock()
        mock_classifier_return2 = MagicMock()

        mock_classifiers_return = MagicMock()
        mock_classifiers_return.classifiers = [
            mock_classifier_return1,
            mock_classifier_return2,
        ]
        mock_classifiers_return.count = 2

        with patch(
            "app.api.routes.classifiers.ClassifierReturn"
        ) as mock_classifier_class:
            mock_classifier_class.side_effect = [
                mock_classifier_return1,
                mock_classifier_return2,
            ]

            with patch(
                "app.api.routes.classifiers.ClassifiersReturn"
            ) as mock_classifiers_class:
                mock_classifiers_class.return_value = mock_classifiers_return

                # Ejecución.
                result = await read_classifiers(
                    session=mock_session,
                    current_user=mock_user,
                    skip=0,
                    limit=10,
                    search=None,
                    sort_by="name",
                    sort_order="asc",
                )

                # Verificación.
                mock_get_classifiers_sorted.assert_called_once()
                mock_classifier_class.assert_any_call(**classifier1_data)
                mock_classifier_class.assert_any_call(**classifier2_data)
                mock_classifiers_class.assert_called_once_with(
                    classifiers=[mock_classifier_return1, mock_classifier_return2],
                    count=2,
                )
                assert result == mock_classifiers_return
                assert result.count == 2
                assert len(result.classifiers) == 2

    async def test_read_classifiers_invalid_sort(self, mock_session, mock_user):
        """Prueba de error al listar clasificadores con parámetros de ordenación inválidos."""

        # Ejecución y verificación (sort_order inválido).
        with pytest.raises(HTTPException) as exc_info:
            await read_classifiers(
                session=mock_session,
                current_user=mock_user,
                sort_by="name",
                sort_order="invalid",
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid sort_order" in exc_info.value.detail

        # Ejecución y verificación (sort_by inválido).
        with pytest.raises(HTTPException) as exc_info:
            await read_classifiers(
                session=mock_session,
                current_user=mock_user,
                sort_by="invalid_field",
                sort_order="asc",
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid sort_by" in exc_info.value.detail

    async def test_read_classifier_detail_success(
        self, mock_session, mock_user, mock_classifier, mock_get_classifier_by_id
    ):
        """Prueba de lectura exitosa de detalles de un clasificador."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.

        with patch(
            "app.api.routes.classifiers.crud_datasets.get_dataset_by_id"
        ) as mock_get_dataset:
            dataset = MagicMock()
            dataset.name = "Test Dataset"
            mock_get_dataset.return_value = dataset

            # Ejecución.
            result = await read_classifier_detail(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_classifier.id,
            )

            # Verificación.
            mock_get_classifier_by_id.assert_called_once()
            mock_get_dataset.assert_called_once()
            assert result.id == mock_classifier.id
            assert result.dataset_name == "Test Dataset"
            assert result.metrics == mock_classifier.metrics

    async def test_update_classifier_success(
        self,
        mock_session,
        mock_user,
        mock_classifier,
        mock_get_classifier_by_id,
        mock_update_classifier,
    ):
        """Prueba de actualización exitosa de un clasificador."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.
        mock_classifier.name = "Original Name"

        with patch(
            "app.api.routes.classifiers.crud_classifiers.get_classifier_by_userid_and_name"
        ) as mock_get_by_name:
            mock_get_by_name.return_value = (
                None  # No hay otro clasificador con el mismo nombre.
            )

            update_data = ClassifierUpdate(
                name="Updated Name", description="Updated description"
            )
            mock_update_classifier.return_value = mock_classifier

            # Ejecución.
            result = await update_classifier(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_classifier.id,
                classifier_in=update_data,
            )

            # Verificación.
            mock_get_classifier_by_id.assert_called_once()
            mock_update_classifier.assert_called_once_with(
                session=mock_session,
                classifier=mock_classifier,
                classifier_data=update_data,
            )
            assert result is not None

    async def test_update_classifier_name_exists(
        self, mock_session, mock_user, mock_classifier, mock_get_classifier_by_id
    ):
        """Prueba de error al actualizar un clasificador con un nombre que ya existe."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.

        with patch(
            "app.api.routes.classifiers.crud_classifiers.get_classifier_by_userid_and_name"
        ) as mock_get_by_name:
            existing_classifier = MagicMock()
            existing_classifier.id = uuid.uuid4()  # ID diferente.
            mock_get_by_name.return_value = existing_classifier

            update_data = ClassifierUpdate(name="Existing Name")

            # Ejecución y verificación.
            with pytest.raises(HTTPException) as exc_info:
                await update_classifier(
                    session=mock_session,
                    current_user=mock_user,
                    classifier_id=mock_classifier.id,
                    classifier_in=update_data,
                )

            assert exc_info.value.status_code == status.HTTP_409_CONFLICT
            assert "already has a classifier with that name" in exc_info.value.detail

    async def test_delete_classifier_success(
        self,
        mock_session,
        mock_user,
        mock_classifier,
        mock_get_classifier_by_id,
        mock_delete_classifier,
    ):
        """Prueba de eliminación exitosa de un clasificador."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.

        # Ejecución.
        result = await delete_classifier(
            session=mock_session,
            current_user=mock_user,
            classifier_id=mock_classifier.id,
        )

        # Verificación.
        mock_get_classifier_by_id.assert_called_once()
        mock_delete_classifier.assert_called_once_with(
            session=mock_session, classifier=mock_classifier
        )
        assert result.message == "Classifier deleted successfully"

    async def test_download_model_success(
        self,
        mock_session,
        mock_user,
        mock_classifier,
        mock_get_classifier_by_id,
        mock_background_tasks,
    ):
        """Prueba de descarga exitosa del modelo."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.
        mock_classifier.status = "trained"
        mock_classifier.file_path = "models/test_classifier"

        with patch(
            "app.api.routes.classifiers.os.path.exists", return_value=True
        ), patch(
            "app.api.routes.classifiers.os.path.join", return_value="test_path"
        ), patch(
            "app.api.routes.classifiers.FileResponse"
        ) as mock_file_response:

            mock_file_response.return_value = "file_response"

            # Ejecución.
            result = await download_model(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_classifier.id,
                background_tasks=mock_background_tasks,
            )

            # Verificación.
            mock_get_classifier_by_id.assert_called_once()
            mock_background_tasks.add_task.assert_called_once()
            mock_file_response.assert_called_once()
            assert result == "file_response"

    async def test_download_model_not_trained(
        self,
        mock_session,
        mock_user,
        mock_untrained_classifier,
        mock_get_classifier_by_id,
        mock_background_tasks,
    ):
        """Prueba de error al descargar un modelo no entrenado."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_untrained_classifier
        mock_untrained_classifier.user_id = mock_user.id  # Mismo usuario.

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await download_model(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_untrained_classifier.id,
                background_tasks=mock_background_tasks,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Model is not available for download" in exc_info.value.detail

    async def test_predict_images_success(
        self,
        mock_session,
        mock_user,
        mock_classifier,
        mock_get_classifier_by_id,
        mock_perform_inference,
    ):
        """Prueba de inferencia exitosa."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_classifier
        mock_classifier.user_id = mock_user.id  # Mismo usuario.
        mock_classifier.status = "trained"

        # Mock de resultados de inferencia.
        inference_results = {
            "results": [
                {"filename": "test.jpg", "predicted_class": "cat", "confidence": 0.95}
            ],
            "model_name": "Test Classifier",
            "processed_images": 1,
            "classifier_id": str(mock_classifier.id),
        }
        mock_perform_inference.return_value = inference_results

        # Mock de UploadFile.
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.read = AsyncMock(return_value=b"test_image_data")

        # Ejecución.
        result = await predict_images(
            session=mock_session,
            current_user=mock_user,
            classifier_id=mock_classifier.id,
            files=[mock_file],
        )

        # Verificación.
        mock_get_classifier_by_id.assert_called_once()
        mock_perform_inference.assert_called_once()
        mock_file.read.assert_called_once()
        assert result == inference_results

    async def test_predict_images_model_not_trained(
        self,
        mock_session,
        mock_user,
        mock_untrained_classifier,
        mock_get_classifier_by_id,
    ):
        """Prueba de error al realizar inferencia con un modelo no entrenado."""

        # Preparación.
        mock_get_classifier_by_id.return_value = mock_untrained_classifier
        mock_untrained_classifier.user_id = mock_user.id  # Mismo usuario.

        # Mock de UploadFile.
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await predict_images(
                session=mock_session,
                current_user=mock_user,
                classifier_id=mock_untrained_classifier.id,
                files=[mock_file],
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "not trained or not available for inference" in exc_info.value.detail
