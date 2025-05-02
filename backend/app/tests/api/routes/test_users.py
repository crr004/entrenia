import pytest
import uuid
from unittest.mock import MagicMock

from fastapi import HTTPException, status


from app.api.routes.users import (
    admin_read_users,
    admin_create_user,
    update_user_own,
    read_user_own,
    admin_update_user,
    admin_delete_user,
)
from app.models.users import UserCreate, UserUpdateOwn, UserUpdate

pytestmark = pytest.mark.asyncio


class TestUserRoutes:

    async def test_admin_read_users_success(
        self, mock_get_all_users, mock_session, mock_users_list
    ):
        """Prueba de obtención exitosa de todos los usuarios."""

        # Configuración.
        mock_get_all_users.return_value = mock_users_list

        # Ejecución.
        response = await admin_read_users(session=mock_session, skip=0, limit=100)

        # Verificación.
        assert response == mock_users_list
        mock_get_all_users.assert_called_once_with(
            session=mock_session,
            skip=0,
            limit=100,
            search=None,
            sort_by="created_at",
            sort_order="desc",
        )

    async def test_admin_create_user_success(
        self,
        mock_users_get_user_by_email,
        mock_users_get_user_by_username,
        mock_users_create_user,
        mock_create_verify_account_token,
        mock_generate_new_account_email,
        mock_session,
        mock_background_tasks,
        mock_user,
    ):
        """Prueba de creación exitosa de usuario por parte del administrador."""

        # Preparación.
        mock_users_get_user_by_email.return_value = None
        mock_users_get_user_by_username.return_value = None
        mock_users_create_user.return_value = mock_user

        user_data = UserCreate(
            email="new@example.com",
            password="SecurePassword123!",
            username="newuser",
            full_name="New User",
            is_admin=False,
        )

        # Ejecución.
        result = await admin_create_user(
            session=mock_session,
            user_in=user_data,
            background_tasks=mock_background_tasks,
        )

        # Verificación.
        mock_users_get_user_by_email.assert_called_once()
        mock_users_get_user_by_username.assert_called_once()
        mock_users_create_user.assert_called_once()
        mock_create_verify_account_token.assert_called_once()
        mock_generate_new_account_email.assert_called_once()
        mock_background_tasks.add_task.assert_called_once()
        assert result == mock_user

    async def test_admin_create_user_existing_email(
        self,
        mock_users_get_user_by_email,
        mock_session,
        mock_background_tasks,
        mock_user,
    ):
        """Prueba de error al crear usuario con correo existente."""

        # Preparación.
        mock_users_get_user_by_email.return_value = mock_user

        user_data = UserCreate(
            email="existing@example.com",
            password="SecurePassword123!",
            username="newuser",
            full_name="New User",
            is_admin=False,
        )

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_create_user(
                session=mock_session,
                user_in=user_data,
                background_tasks=mock_background_tasks,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in exc_info.value.detail

    async def test_admin_create_user_existing_username(
        self,
        mock_users_get_user_by_email,
        mock_users_get_user_by_username,
        mock_session,
        mock_background_tasks,
        mock_user,
    ):
        """Prueba de error al crear usuario con nombre de usuario existente."""

        # Preparación.
        mock_users_get_user_by_email.return_value = None
        mock_users_get_user_by_username.return_value = mock_user

        user_data = UserCreate(
            email="new@example.com",
            password="SecurePassword123!",
            username="existinguser",
            full_name="New User",
            is_admin=False,
        )

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_create_user(
                session=mock_session,
                user_in=user_data,
                background_tasks=mock_background_tasks,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in exc_info.value.detail

    async def test_admin_update_user_success(
        self,
        mock_get_user_by_id,
        mock_get_user_by_email,
        mock_get_user_by_username,
        mock_update_user_by_admin,
        mock_session,
        mock_user,
        mock_uuid,
    ):
        """Prueba de actualización exitosa de usuario por parte del administrador."""

        # Preparación.
        mock_get_user_by_id.return_value = mock_user
        mock_get_user_by_email.return_value = None
        mock_get_user_by_username.return_value = None
        mock_update_user_by_admin.return_value = mock_user

        user_data = UserUpdate(
            email="updated@example.com",
            username="updateduser",
            full_name="Updated User",
            is_admin=True,
            is_active=True,
            is_verified=True,
        )

        # Ejecución.
        result = await admin_update_user(
            session=mock_session, user_id=mock_uuid, user_in=user_data
        )

        # Verificación.
        mock_get_user_by_id.assert_called_once_with(session=mock_session, id=mock_uuid)
        mock_update_user_by_admin.assert_called_once_with(
            session=mock_session, db_user=mock_user, user_in=user_data
        )
        assert result == mock_user

    async def test_admin_update_user_not_found(
        self, mock_get_user_by_id, mock_session, mock_uuid
    ):
        """Prueba de error al actualizar usuario que no existe."""

        # Preparación.
        mock_get_user_by_id.return_value = None

        user_data = UserUpdate(email="updated@example.com", username="updateduser")

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_update_user(
                session=mock_session, user_id=mock_uuid, user_in=user_data
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in exc_info.value.detail

    async def test_admin_update_user_existing_email(
        self,
        mock_users_get_user_by_id,
        mock_users_get_user_by_email,
        mock_session,
        mock_user,
        mock_uuid,
    ):
        """Prueba de error al actualizar usuario con correo ya existente."""

        # Preparación.
        mock_users_get_user_by_id.return_value = mock_user

        other_user = MagicMock()
        other_user.id = uuid.uuid4()
        mock_users_get_user_by_email.return_value = other_user

        user_data = UserUpdate(
            email="existing@example.com",
            username="updateduser",
            full_name="Updated User",
            is_admin=False,
            is_active=True,
            is_verified=True,
        )

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_update_user(
                session=mock_session, user_id=mock_uuid, user_in=user_data
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in exc_info.value.detail

    async def test_admin_delete_user_success(
        self,
        mock_get_user_by_id,
        mock_delete_user,
        mock_session,
        mock_user,
        mock_admin_user,
        mock_uuid,
    ):
        """Prueba de eliminación exitosa de usuario por parte del administrador."""

        # Preparación.
        mock_get_user_by_id.return_value = mock_user

        # Ejecución.
        result = await admin_delete_user(
            session=mock_session, user_id=mock_uuid, current_user=mock_admin_user
        )

        # Verificación.
        mock_get_user_by_id.assert_called_once_with(session=mock_session, id=mock_uuid)
        mock_delete_user.assert_called_once_with(session=mock_session, user=mock_user)
        assert result.message == "User deleted successfully"

    async def test_admin_delete_user_not_found(
        self, mock_get_user_by_id, mock_session, mock_admin_user, mock_uuid
    ):
        """Prueba de error al eliminar usuario que no existe."""

        # Preparación.
        mock_get_user_by_id.return_value = None

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_delete_user(
                session=mock_session, user_id=mock_uuid, current_user=mock_admin_user
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in exc_info.value.detail

    async def test_admin_delete_self(
        self, mock_get_user_by_id, mock_session, mock_admin_user, mock_uuid
    ):
        """Prueba de error al intentar que un administrador se elimine a sí mismo."""

        # Preparación.
        mock_get_user_by_id.return_value = mock_admin_user

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await admin_delete_user(
                session=mock_session, user_id=mock_uuid, current_user=mock_admin_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not allowed to delete themselves" in exc_info.value.detail

    async def test_read_user_own(self, mock_user):
        """Prueba de lectura de los datos del propio usuario."""

        # Ejecución.
        result = await read_user_own(current_user=mock_user)

        # Verificación.
        assert result == mock_user

    async def test_update_user_own_success(
        self,
        mock_users_get_user_by_username,
        mock_users_update_user,
        mock_session,
        mock_user,
    ):
        """Prueba de actualización exitosa de los datos del propio usuario."""

        # Preparación.
        mock_users_get_user_by_username.return_value = None
        mock_users_update_user.return_value = mock_user

        user_data = UserUpdateOwn(username="newusername", full_name="New Full Name")

        # Ejecución.
        result = await update_user_own(
            session=mock_session, user_in=user_data, current_user=mock_user
        )

        # Verificación.
        mock_users_get_user_by_username.assert_called_once()
        mock_users_update_user.assert_called_once()
        assert result == mock_user

    async def test_update_user_own_invalid_full_name(self, mock_session, mock_user):
        """Prueba de error al actualizar con un nombre completo inválido."""

        # Preparación.
        user_data = UserUpdateOwn(full_name="Invalid Name123$")

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await update_user_own(
                session=mock_session, user_in=user_data, current_user=mock_user
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid characters" in exc_info.value.detail

    async def test_update_user_own_invalid_username(self, mock_session, mock_user):
        """Prueba de error al actualizar con un nombre de usuario inválido."""

        # Preparación.
        user_data = UserUpdateOwn(username="123_456")

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await update_user_own(
                session=mock_session, user_in=user_data, current_user=mock_user
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

        assert "username can only contain" in exc_info.value.detail.lower()

    async def test_regular_user_cant_access_admin_functions(self, mock_user):
        """Prueba de que los usuarios regulares no pueden acceder a las funciones de administrador."""

        # Preparación.
        from app.crud.users import get_current_admin

        mock_user.is_admin = False

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "enough privileges" in exc_info.value.detail.lower()

    async def test_regular_user_cant_read_all_users(self, mock_user, mock_session):
        """Prueba que los usuarios normales no pueden leer todos los usuarios porque no son administradores."""

        # Preparación.
        from app.api.routes.users import admin_read_users
        from app.crud.users import get_current_admin

        mock_user.is_admin = False

        # Se simula la función de verificación admin que se ejecuta mediante dependencia.
        # Normalmente esto ocurriría dentro de FastAPI, pero aquí se simula directamente.
        async def simulate_endpoint_call():
            # Esto fallará porque el usuario no es admin.
            await get_current_admin(current_user=mock_user)
            return await admin_read_users(session=mock_session, skip=0, limit=100)

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await simulate_endpoint_call()

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "enough privileges" in exc_info.value.detail.lower()

    async def test_regular_user_cant_create_users(
        self, mock_user, mock_session, mock_background_tasks
    ):
        """Prueba que los usuarios normales no pueden crear nuevos usuarios porque no son administradores."""

        # Preparación.
        from app.api.routes.users import admin_create_user
        from app.crud.users import get_current_admin

        mock_user.is_admin = False

        user_data = UserCreate(
            email="new@example.com",
            password="SecurePassword123!",
            username="newuser",
            full_name="New User",
            is_admin=False,
        )

        # Se simula la función de verificación admin que se ejecuta mediante dependencia.
        async def simulate_endpoint_call():
            # Esto fallará porque el usuario no es admin.
            await get_current_admin(current_user=mock_user)
            return await admin_create_user(
                session=mock_session,
                user_in=user_data,
                background_tasks=mock_background_tasks,
            )

        # Ejecución y verificación.
        with pytest.raises(HTTPException) as exc_info:
            await simulate_endpoint_call()

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "enough privileges" in exc_info.value.detail.lower()
