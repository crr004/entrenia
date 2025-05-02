import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.classifiers import (
    Classifier,
    ClassifierCreate,
    ClassifierUpdate,
    ClassifierTrainingStatus,
)

from app.crud.classifiers import (
    get_classifier_by_id,
    get_classifier_by_userid_and_name,
    create_classifier,
    update_classifier,
    delete_classifier,
    update_classifier_training_status,
    get_classifiers_sorted,
)

pytestmark = pytest.mark.asyncio


class TestClassifiersCrud:

    async def test_get_classifier_by_id(self, mock_session):
        """Prueba obtener un clasificador por su ID."""

        # Preparación.
        classifier_id = uuid.uuid4()
        mock_classifier = MagicMock(spec=Classifier)

        mock_scalar_result = MagicMock()
        mock_scalar_result.first.return_value = mock_classifier

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalar_result

        mock_session.execute = AsyncMock(return_value=mock_result)

        # Ejecución.
        result = await get_classifier_by_id(session=mock_session, id=classifier_id)

        # Verificación.
        mock_session.execute.assert_called_once()
        assert result == mock_classifier

    async def test_get_classifier_by_userid_and_name(self, mock_session):
        """Prueba obtener un clasificador por ID de usuario y nombre."""

        # Preparación.
        user_id = uuid.uuid4()
        name = "Test Classifier"
        mock_classifier = MagicMock(spec=Classifier)

        mock_scalar_result = MagicMock()
        mock_scalar_result.first.return_value = mock_classifier

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalar_result

        mock_session.execute = AsyncMock(return_value=mock_result)

        # Ejecución.
        result = await get_classifier_by_userid_and_name(
            session=mock_session, user_id=user_id, name=name
        )

        # Verificación.
        mock_session.execute.assert_called_once()
        assert result == mock_classifier

    async def test_create_classifier(self, mock_session):
        """Prueba crear un nuevo clasificador."""

        # Preparación.
        user_id = uuid.uuid4()
        dataset_id = uuid.uuid4()
        classifier_data = ClassifierCreate(
            name="Test Classifier",
            description="Test Description",
            dataset_name="Test Dataset",
            dataset_id=dataset_id,
            architecture="efficientnetb3",
            model_parameters={"epochs": 20, "batch_size": 32},
        )

        # Mock para start_training_task.
        with patch(
            "app.crud.classifiers.start_training_task", return_value=True
        ) as mock_train:
            # Ejecución.
            result = await create_classifier(
                session=mock_session, user_id=user_id, classifier_in=classifier_data
            )

            # Verificación.
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
            mock_train.assert_called_once()

            assert isinstance(result, Classifier)
            assert result.name == "Test Classifier"
            assert result.status == ClassifierTrainingStatus.TRAINING

    async def test_update_classifier(self, mock_session):
        """Prueba actualizar un clasificador existente."""

        # Preparación.
        mock_classifier = MagicMock()
        mock_classifier.name = "Old Name"
        mock_classifier.description = "Old Description"
        mock_classifier.sqlmodel_update = MagicMock()

        update_data = ClassifierUpdate(
            name="New Name",
            description="New Description",
        )

        # Ejecución.
        result = await update_classifier(
            session=mock_session,
            classifier=mock_classifier,
            classifier_data=update_data,
        )

        # Verificación.
        mock_classifier.sqlmodel_update.assert_called_once()
        mock_session.add.assert_called_once_with(mock_classifier)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result == mock_classifier

    async def test_update_classifier_training_status(self, mock_session):
        """Prueba actualizar el estado de entrenamiento de un clasificador."""

        # Preparación.
        classifier_id = uuid.uuid4()
        mock_classifier = MagicMock()
        metrics = {"accuracy": 0.95, "precision": 0.92}

        # Mock para get_classifier_by_id.
        with patch(
            "app.crud.classifiers.get_classifier_by_id", return_value=mock_classifier
        ) as mock_get:
            mock_get.return_value = mock_classifier

            # Ejecución.
            result = await update_classifier_training_status(
                session=mock_session,
                classifier_id=classifier_id,
                status=ClassifierTrainingStatus.TRAINED,
                metrics=metrics,
            )

            # Verificación.
            mock_get.assert_called_once_with(session=mock_session, id=classifier_id)
            assert result == mock_classifier
            assert mock_classifier.status == ClassifierTrainingStatus.TRAINED
            assert mock_classifier.metrics == metrics
            assert mock_classifier.trained_at is not None
            mock_session.add.assert_called_once_with(mock_classifier)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    async def test_update_classifier_training_status_not_found(self, mock_session):
        """Prueba actualizar el estado de entrenamiento de un clasificador que no existe."""

        # Preparación.
        classifier_id = uuid.uuid4()

        # Mock para get_classifier_by_id.
        with patch(
            "app.crud.classifiers.get_classifier_by_id", return_value=None
        ) as mock_get:
            # Ejecución.
            result = await update_classifier_training_status(
                session=mock_session,
                classifier_id=classifier_id,
                status=ClassifierTrainingStatus.FAILED,
            )

            # Verificación.
            mock_get.assert_called_once_with(session=mock_session, id=classifier_id)
            assert result is None
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()
            mock_session.refresh.assert_not_called()

    async def test_delete_classifier_no_files(self, mock_session):
        """Prueba eliminar un clasificador sin archivos asociados."""

        # Preparación.
        mock_classifier = MagicMock()
        mock_classifier.file_path = None

        # Ejecución.
        await delete_classifier(session=mock_session, classifier=mock_classifier)

        # Verificación.
        mock_session.delete.assert_called_once_with(mock_classifier)
        mock_session.commit.assert_called_once()

    async def test_delete_classifier_with_files(self, mock_session):
        """Prueba eliminar un clasificador con archivos asociados."""

        # Preparación.
        mock_classifier = MagicMock()
        mock_classifier.file_path = "models/test_model"

        # Mock para os.path y funciones de eliminación de archivos.
        with patch("app.crud.classifiers.os.path.exists", return_value=True), patch(
            "app.crud.classifiers.os.remove"
        ) as mock_remove, patch("app.crud.classifiers.os.rmdir") as mock_rmdir, patch(
            "app.crud.classifiers.MEDIA_ROOT", "/app/media"
        ), patch(
            "app.crud.classifiers.os.path.join",
            side_effect=lambda *args: (
                f"{args[0]}/{args[1]}" if len(args) > 1 else args[0]
            ),
        ):

            # Ejecución.
            await delete_classifier(session=mock_session, classifier=mock_classifier)

            # Verificación.
            mock_remove.assert_any_call("/app/media/models/test_model/model.keras")
            mock_remove.assert_any_call("/app/media/models/test_model/metadata.json")
            mock_rmdir.assert_called_once()
            mock_session.delete.assert_called_once_with(mock_classifier)
            mock_session.commit.assert_called_once()

    async def test_get_classifiers_sorted_user_view(self, mock_session):
        """Prueba obtener clasificadores ordenados (vista de usuario)."""

        # Preparación.
        user_id = uuid.uuid4()
        mock_classifier1 = MagicMock()
        mock_classifier2 = MagicMock()

        # Configurar el resultado simulado para execute.
        result_mock = MagicMock()
        result_mock.return_value = [
            (mock_classifier1, "user1"),
            (mock_classifier2, "user2"),
        ]
        mock_session.execute = AsyncMock(
            side_effect=[MagicMock(scalar_one=lambda: 2), result_mock()]
        )

        # Ejecución.
        classifiers, count = await get_classifiers_sorted(
            session=mock_session,
            skip=0,
            limit=10,
            search="test",
            sort_by="name",
            sort_order="asc",
            user_id=user_id,
            admin_view=False,
        )

        # Verificación.
        assert (
            mock_session.execute.call_count == 2
        )  # Una llamada para count, otra para query.
        assert count == 2
        assert len(classifiers) == 2
        assert classifiers[0][0] == mock_classifier1
        assert classifiers[0][1] == "user1"
        assert classifiers[1][0] == mock_classifier2
        assert classifiers[1][1] == "user2"

    async def test_get_classifiers_sorted_admin_view(self, mock_session):
        """Prueba obtener clasificadores ordenados (vista de admin)."""

        # Preparación.
        mock_classifier1 = MagicMock()
        mock_classifier2 = MagicMock()

        # Configurar el resultado simulado para execute.
        result_mock = MagicMock()
        result_mock.return_value = [
            (mock_classifier1, "user1"),
            (mock_classifier2, "user2"),
        ]
        mock_session.execute = AsyncMock(
            side_effect=[MagicMock(scalar_one=lambda: 2), result_mock()]
        )

        # Ejecución.
        classifiers, count = await get_classifiers_sorted(
            session=mock_session,
            skip=0,
            limit=10,
            search=None,
            sort_by="created_at",
            sort_order="desc",
            user_id=None,
            admin_view=True,
        )

        # Verificación.
        assert (
            mock_session.execute.call_count == 2
        )  # Una llamada para count, otra para query.
        assert count == 2
        assert len(classifiers) == 2
        assert classifiers[0][0] == mock_classifier1
        assert classifiers[1][0] == mock_classifier2
