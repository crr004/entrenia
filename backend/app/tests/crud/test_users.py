import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from jwt.exceptions import InvalidTokenError

from fastapi import HTTPException, status

from app.crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    get_all_users,
    get_current_user,
    get_current_admin,
    update_user,
    update_user_by_admin,
    update_password,
    delete_user,
)
from app.models.users import User, UserCreate, UsersReturn, UserUpdate

pytestmark = pytest.mark.asyncio


class TestUsersCRUD:
    async def test_create_user(self, mock_session, mock_crud_hash_password):
        """Prueba de creación de usuario con contraseña cifrada."""

        # Preparación
        user_in = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="password123",
            is_admin=False,
        )

        # Ejecución
        result = await create_user(session=mock_session, user_in=user_in)

        # Verificación
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_crud_hash_password.assert_called_once_with(password=user_in.password)

    async def test_get_user_by_email_found(self, mock_session, mock_user):
        """Prueba de obtención de usuario por email cuando el usuario existe."""

        # Preparación
        email = "test@example.com"

        # Crear una cadena de mocks personalizada para esta prueba específica
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = mock_user

        execute_result = MagicMock()
        execute_result.scalars = MagicMock(return_value=scalars_mock)

        # Reemplazar el método execute para esta prueba
        original_execute = mock_session.execute

        async def mock_execute(*args, **kwargs):
            return execute_result

        mock_session.execute = AsyncMock(side_effect=mock_execute)

        # Ejecución
        result = await get_user_by_email(session=mock_session, email=email)

        # Verificación
        assert result is mock_user

        # Restaurar método execute original
        mock_session.execute = original_execute

    async def test_get_user_by_email_not_found(self, mock_session):
        """Prueba de obtención de usuario por email cuando el usuario no existe."""

        # Preparación
        email = "nonexistent@example.com"
        mock_session.execute.return_value.scalars.return_value.first.return_value = None

        # Ejecución
        result = await get_user_by_email(session=mock_session, email=email)

        # Verificación
        assert result is None
        mock_session.execute.assert_called_once()

    async def test_get_user_by_username_found(self, mock_session, mock_user):
        """Prueba de obtención de usuario por nombre de usuario cuando el usuario existe."""

        # Preparación
        username = "testuser"

        # Crear una cadena de mocks personalizada para esta prueba específica
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = mock_user

        execute_result = MagicMock()
        execute_result.scalars = MagicMock(return_value=scalars_mock)

        # Reemplazar el método execute para esta prueba
        original_execute = mock_session.execute

        async def mock_execute(*args, **kwargs):
            return execute_result

        mock_session.execute = AsyncMock(side_effect=mock_execute)

        # Ejecución
        result = await get_user_by_username(session=mock_session, username=username)

        # Verificación
        assert result is mock_user

        # Restaurar método execute original
        mock_session.execute = original_execute

    async def test_get_user_by_username_not_found(self, mock_session):
        """Prueba de obtención de usuario por nombre de usuario cuando el usuario no existe."""

        # Preparación
        username = "nonexistent"
        mock_session.execute.return_value.scalars.return_value.first.return_value = None

        # Ejecución
        result = await get_user_by_username(session=mock_session, username=username)

        # Verificación
        assert result is None
        mock_session.execute.assert_called_once()

    async def test_get_user_by_id_found(self, mock_session, mock_user):
        """Prueba de obtención de usuario por ID cuando el usuario existe."""

        # Preparación
        user_id = uuid.uuid4()
        mock_session.get.return_value = mock_user

        # Ejecución
        result = await get_user_by_id(session=mock_session, id=user_id)

        # Verificación
        assert result is mock_user
        mock_session.get.assert_called_once()

    async def test_get_user_by_id_not_found(self, mock_session):
        """Prueba de obtención de usuario por ID cuando el usuario no existe."""

        # Preparación
        user_id = uuid.uuid4()
        mock_session.get.return_value = None

        # Ejecución
        result = await get_user_by_id(session=mock_session, id=user_id)

        # Verificación
        assert result is None
        mock_session.get.assert_called_once()

    async def test_get_all_users(self, mock_session):
        """Prueba de obtención de todos los usuarios con paginación."""

        # Preparación
        # Crear instancias reales de User en lugar de MagicMocks
        user1 = User(
            email="user1@example.com",
            username="user1",
            full_name="User One",
            password="hash1",
            id=uuid.uuid4(),
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            full_name="User Two",
            password="hash2",
            id=uuid.uuid4(),
        )
        user3 = User(
            email="user3@example.com",
            username="user3",
            full_name="User Three",
            password="hash3",
            id=uuid.uuid4(),
        )
        mock_users = [user1, user2, user3]

        # Configurar el resultado de la consulta de conteo
        count_execute_result = MagicMock()
        count_execute_result.scalar.return_value = 10

        # Configurar el resultado de la consulta de usuarios
        users_execute_result = MagicMock()
        users_result = [(user,) for user in mock_users]
        users_execute_result.all.return_value = users_result

        # Configurar los efectos secundarios para devolver diferentes mocks para cada llamada a execute
        mock_session.execute.side_effect = [count_execute_result, users_execute_result]

        # Ejecución
        result = await get_all_users(session=mock_session, skip=0, limit=3)

        # Verificación
        assert isinstance(result, UsersReturn)
        assert result.count == 10
        assert len(result.users) == 3
        assert mock_session.execute.call_count == 2

    async def test_get_current_user_success(
        self,
        mock_session,
        mock_user,
        mock_crud_jwt_decode,
        mock_crud_token_data,
        mock_crud_get_user_by_id,
    ):
        """Prueba de obtención del usuario actual con token válido y usuario activo y verificado."""

        # Preparación
        token = "valid.jwt.token"
        mock_crud_jwt_decode.return_value = mock_crud_token_data
        mock_crud_get_user_by_id.return_value = mock_user
        mock_user.is_active = True
        mock_user.is_verified = True

        # Ejecución
        result = await get_current_user(session=mock_session, token=token)

        # Verificación
        assert result is mock_user
        mock_crud_jwt_decode.assert_called_once()
        mock_crud_get_user_by_id.assert_called_once_with(
            session=mock_session, id=mock_crud_token_data["sub"]
        )

    async def test_get_current_user_invalid_token(
        self, mock_session, mock_crud_jwt_decode
    ):
        """Prueba de excepción cuando el token es inválido."""

        # Preparación
        token = "invalid.jwt.token"
        mock_crud_jwt_decode.side_effect = InvalidTokenError("Invalid token")

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(session=mock_session, token=token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_validation_error(
        self, mock_session, mock_crud_jwt_decode
    ):
        """Prueba de excepción cuando los datos del token son inválidos."""

        # Preparación
        token = "valid.but.malformed.token"
        mock_crud_jwt_decode.return_value = {
            "invalid": "data"
        }  # Faltan campos requeridos

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(session=mock_session, token=token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_wrong_token_type(
        self, mock_session, mock_crud_jwt_decode, mock_crud_invalid_token_data
    ):
        """Prueba de excepción cuando el tipo de token no es 'auth'."""

        # Preparación
        token = "wrong.type.token"
        mock_crud_jwt_decode.return_value = mock_crud_invalid_token_data

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(session=mock_session, token=token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_not_found(
        self,
        mock_session,
        mock_crud_jwt_decode,
        mock_crud_token_data,
    ):
        """Prueba de excepción cuando no se encuentra el usuario."""

        # Preparación
        token = "valid.jwt.token"
        mock_crud_jwt_decode.return_value = mock_crud_token_data

        with patch("app.crud.users.get_user_by_id") as local_mock_get_user:
            # Configurar la función para devolver None en esta prueba
            async def return_none(*args, **kwargs):
                return None

            local_mock_get_user.side_effect = return_none

            # Ejecución y Verificación
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(session=mock_session, token=token)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "User not found" in exc_info.value.detail

    async def test_get_current_user_inactive(
        self,
        mock_session,
        mock_user,
        mock_crud_jwt_decode,
        mock_crud_token_data,
        mock_crud_get_user_by_id,
    ):
        """Prueba de excepción cuando el usuario está inactivo."""

        # Preparación
        token = "valid.jwt.token"
        mock_crud_jwt_decode.return_value = mock_crud_token_data
        mock_crud_get_user_by_id.return_value = mock_user
        mock_user.is_active = False
        mock_user.is_verified = True

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(session=mock_session, token=token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in exc_info.value.detail

    async def test_get_current_user_unverified(
        self,
        mock_session,
        mock_user,
        mock_crud_jwt_decode,
        mock_crud_token_data,
        mock_crud_get_user_by_id,
    ):
        """Prueba de excepción cuando el usuario no está verificado."""

        # Preparación
        token = "valid.jwt.token"
        mock_crud_jwt_decode.return_value = mock_crud_token_data
        mock_crud_get_user_by_id.return_value = mock_user
        mock_user.is_active = True
        mock_user.is_verified = False

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(session=mock_session, token=token)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Unverified user" in exc_info.value.detail

    async def test_get_current_admin_success(self, mock_admin_user):
        """Prueba de obtención del administrador actual cuando el usuario es administrador."""

        # Preparación - Usando el fixture mock_admin_user

        # Ejecución
        result = await get_current_admin(current_user=mock_admin_user)

        # Verificación
        assert result is mock_admin_user

    async def test_get_current_admin_not_admin(self, mock_user):
        """Prueba de excepción cuando el usuario no es administrador."""

        # Preparación
        mock_user.is_admin = False

        # Ejecución y Verificación
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "doesn't have enough privileges" in exc_info.value.detail

    async def test_update_user(self, mock_session, mock_user):
        """Prueba de actualización de datos de usuario."""

        # Preparación
        user_data = {"full_name": "Updated Name"}
        extra_data = {"custom_field": "custom_value"}

        # Ejecución
        result = await update_user(
            session=mock_session,
            user=mock_user,
            user_data=user_data,
            extra_data=extra_data,
        )

        # Verificación
        assert result is mock_user
        mock_user.sqlmodel_update.assert_called_once()
        mock_session.add.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    async def test_update_user_by_admin(
        self, mock_session, mock_user, mock_crud_hash_password
    ):
        """Prueba de actualización de usuario por administrador incluyendo cambio de contraseña."""

        # Preparación
        user_in = UserUpdate(
            email="updated@example.com",
            username="updateduser",
            full_name="Updated User",
            password="newpassword123",
            is_admin=True,
            is_active=True,
            is_verified=True,
        )

        # Ejecución
        with patch("app.crud.users.update_user") as mock_update_user:
            mock_update_user.return_value = mock_user
            result = await update_user_by_admin(
                session=mock_session, db_user=mock_user, user_in=user_in
            )

        # Verificación
        assert result is mock_user
        mock_crud_hash_password.assert_called_once_with(password="newpassword123")
        mock_update_user.assert_called_once()

    async def test_update_user_by_admin_no_password(self, mock_session, mock_user):
        """Prueba de actualización de usuario por administrador sin cambiar contraseña."""

        # Preparación
        user_in = UserUpdate(
            email="updated@example.com",
            username="updateduser",
            full_name="Updated User",
            is_admin=True,
            is_active=True,
            is_verified=True,
        )

        # Ejecución
        with patch("app.crud.users.update_user") as mock_update_user:
            mock_update_user.return_value = mock_user
            result = await update_user_by_admin(
                session=mock_session, db_user=mock_user, user_in=user_in
            )

        # Verificación
        assert result is mock_user
        mock_update_user.assert_called_once()

    async def test_update_password(self, mock_session, mock_user):
        """Prueba de actualización de contraseña de usuario."""

        # Preparación
        new_password = "new_hashed_password"

        # Ejecución
        result = await update_password(
            session=mock_session, user=mock_user, new_password=new_password
        )

        # Verificación
        assert result is mock_user
        assert mock_user.password == new_password
        mock_session.add.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()

    async def test_delete_user(self, mock_session, mock_user):
        """Prueba de eliminación de usuario."""

        # Preparación

        # Ejecución
        await delete_user(session=mock_session, user=mock_user)

        # Verificación
        mock_session.delete.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()
