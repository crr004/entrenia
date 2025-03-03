import pytest

from fastapi import HTTPException, status

from app.api.routes.signup import register_user
from app.models.users import UserRegister

pytestmark = pytest.mark.asyncio


class TestSignupRoutes:

    async def test_register_user_success(
        self,
        mock_signup_get_user_by_email,
        mock_signup_get_user_by_username,
        mock_signup_create_user,
        mock_signup_create_token,
        mock_signup_generate_email,
        mock_session,
        mock_background_tasks,
        mock_user,
        mock_email_data,
    ):
        """Prueba de registro exitoso de usuario."""

        # Preparación
        mock_signup_get_user_by_email.return_value = None
        mock_signup_get_user_by_username.return_value = None
        mock_signup_create_user.return_value = mock_user
        mock_signup_generate_email.return_value = mock_email_data

        user_data = UserRegister(
            email="test@example.com",
            password="SecurePassword123!",
            username="testuser",
            full_name="Test User",
        )

        # Ejecución
        result = await register_user(mock_session, user_data, mock_background_tasks)

        # Verificación
        mock_signup_get_user_by_email.assert_called_once_with(
            session=mock_session, email="test@example.com"
        )
        mock_signup_get_user_by_username.assert_called_once_with(
            session=mock_session, username="testuser"
        )
        mock_signup_create_user.assert_called_once()
        mock_signup_create_token.assert_called_once_with(email="test@example.com")
        mock_signup_generate_email.assert_called_once_with(
            email_to="test@example.com", username="Test User", token="test_token"
        )
        mock_background_tasks.add_task.assert_called_once()
        assert result == mock_user

    async def test_register_user_existing_email(
        self, mock_get_user_by_email, mock_session, mock_background_tasks, mock_user
    ):
        """Prueba de error al registrar usuario con correo existente."""

        # Preparación
        mock_get_user_by_email.return_value = mock_user

        user_data = UserRegister(
            email="existing@example.com",
            password="SecurePassword123!",
            username="newuser",
            full_name="New User",
        )

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_session, user_data, mock_background_tasks)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "email already exists" in exc_info.value.detail

    async def test_register_user_existing_username(
        self,
        mock_get_user_by_email,
        mock_get_user_by_username,
        mock_session,
        mock_background_tasks,
        mock_user,
    ):
        """Prueba de error al registrar usuario con nombre de usuario existente."""

        # Preparación
        mock_get_user_by_email.return_value = None
        mock_get_user_by_username.return_value = mock_user

        user_data = UserRegister(
            email="new@example.com",
            password="SecurePassword123!",
            username="existinguser",
            full_name="New User",
        )

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_session, user_data, mock_background_tasks)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "username already exists" in exc_info.value.detail

    async def test_register_user_invalid_username(
        self,
        mock_get_user_by_email,
        mock_get_user_by_username,
        mock_session,
        mock_background_tasks,
    ):
        """Prueba de error al registrar usuario con nombre de usuario inválido."""

        # Preparación
        mock_get_user_by_email.return_value = None
        mock_get_user_by_username.return_value = None

        user_data = UserRegister(
            email="new@example.com",
            password="SecurePassword123!",
            username="123",  # Inválido: necesita al menos 3 letras
            full_name="New User",
        )

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_session, user_data, mock_background_tasks)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in exc_info.value.detail

    async def test_register_user_invalid_full_name(
        self,
        mock_get_user_by_email,
        mock_get_user_by_username,
        mock_session,
        mock_background_tasks,
    ):
        """Prueba de error al registrar usuario con nombre completo inválido."""

        # Preparación
        mock_get_user_by_email.return_value = None
        mock_get_user_by_username.return_value = None

        user_data = UserRegister(
            email="new@example.com",
            password="SecurePassword123!",
            username="testuser",
            full_name="Test User123$",  # Caracteres inválidos
        )

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_session, user_data, mock_background_tasks)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "full name" in exc_info.value.detail

    async def test_register_user_without_full_name(
        self,
        mock_get_user_by_email,
        mock_get_user_by_username,
        mock_create_user,
        mock_create_token,
        mock_generate_email,
        mock_session,
        mock_background_tasks,
    ):
        """Prueba de registro de usuario sin nombre completo."""

        # Preparación
        mock_get_user_by_email.return_value = None
        mock_get_user_by_username.return_value = None

        mock_user = mock_create_user.return_value
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = None

        user_data = UserRegister(
            email="test@example.com",
            password="SecurePassword123!",
            username="testuser",
            full_name=None,
        )

        # Ejecución
        result = await register_user(mock_session, user_data, mock_background_tasks)

        # Verificación
        mock_generate_email.assert_called_once_with(
            email_to="test@example.com",
            username="testuser",
            token="test_token",
        )
        assert result == mock_user

    async def test_verify_account_success(
        self,
        mock_verify_token,
        mock_get_user_by_email,
        mock_update_user,
        mock_session,
        mock_user,
    ):
        """Prueba de verificación exitosa de cuenta."""

        # Preparación
        mock_verify_token.return_value = "test@example.com"
        mock_get_user_by_email.return_value = mock_user
        mock_user.is_verified = False
        mock_user.model_dump.return_value = {"is_verified": True}
        mock_update_user.return_value = mock_user

        # Ejecución
        from app.api.routes.signup import verify_account

        result = await verify_account(mock_session, "valid_token")

        # Verificación
        mock_verify_token.assert_called_once_with(token="valid_token")
        mock_get_user_by_email.assert_called_once_with(
            session=mock_session, email="test@example.com"
        )
        mock_user.model_dump.assert_called_once_with(exclude_unset=True)
        mock_update_user.assert_called_once()
        assert result.message == "User verified successfully"

    async def test_verify_account_invalid_token(self, mock_verify_token, mock_session):
        """Prueba de error al verificar cuenta con token inválido."""

        # Preparación
        mock_verify_token.return_value = None

        # Ejecución y verificación
        from app.api.routes.signup import verify_account

        with pytest.raises(HTTPException) as exc_info:
            await verify_account(mock_session, "invalid_token")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in exc_info.value.detail

    async def test_verify_account_user_not_found(
        self, mock_verify_token, mock_get_user_by_email, mock_session
    ):
        """Prueba de error al verificar cuenta cuando no existe el usuario."""

        # Preparación
        mock_verify_token.return_value = "nonexistent@example.com"
        mock_get_user_by_email.return_value = None

        # Ejecución y verificación
        from app.api.routes.signup import verify_account

        with pytest.raises(HTTPException) as exc_info:
            await verify_account(mock_session, "valid_token")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in exc_info.value.detail

    async def test_verify_account_already_verified(
        self, mock_verify_token, mock_get_user_by_email, mock_session, mock_user
    ):
        """Prueba de error al verificar una cuenta ya verificada."""

        # Preparación
        mock_verify_token.return_value = "test@example.com"
        mock_get_user_by_email.return_value = mock_user
        mock_user.is_verified = True

        # Ejecución y verificación
        from app.api.routes.signup import verify_account

        with pytest.raises(HTTPException) as exc_info:
            await verify_account(mock_session, "valid_token")

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already verified" in exc_info.value.detail
