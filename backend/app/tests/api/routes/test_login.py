import pytest

from fastapi import HTTPException, status

from app.api.routes.login import login_user, recover_password, reset_password
from app.models.users import NewPassword

pytestmark = pytest.mark.asyncio


class TestLoginRoutes:

    async def test_login_user_success(
        self,
        mock_authenticate_user,
        mock_create_access_token,
        mock_session,
        mock_oauth_form,
        mock_user,
    ):
        """Prueba de inicio de sesión exitoso."""

        # Preparación
        mock_authenticate_user.return_value = mock_user
        mock_user.is_active = True
        mock_user.is_verified = True
        mock_user.id = "user_id_123"

        # Ejecución
        result = await login_user(mock_session, mock_oauth_form)

        # Verificación
        mock_authenticate_user.assert_called_once_with(
            session=mock_session,
            email_or_username=mock_oauth_form.username,
            password=mock_oauth_form.password,
        )
        mock_create_access_token.assert_called_once()
        assert result.access_token == "test_access_token"

    async def test_login_user_invalid_credentials(
        self, mock_authenticate_user, mock_session, mock_oauth_form
    ):
        """Prueba de inicio de sesión con credenciales inválidas."""

        # Preparación
        mock_authenticate_user.return_value = None

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await login_user(mock_session, mock_oauth_form)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email/username or password" in exc_info.value.detail

    async def test_login_user_inactive(
        self, mock_authenticate_user, mock_session, mock_oauth_form, mock_user
    ):
        """Prueba de inicio de sesión con usuario inactivo."""

        # Preparación
        mock_authenticate_user.return_value = mock_user
        mock_user.is_active = False
        mock_user.is_verified = True

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await login_user(mock_session, mock_oauth_form)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in exc_info.value.detail

    async def test_login_user_unverified(
        self, mock_authenticate_user, mock_session, mock_oauth_form, mock_user
    ):
        """Prueba de inicio de sesión con usuario no verificado."""

        # Preparación
        mock_authenticate_user.return_value = mock_user
        mock_user.is_active = True
        mock_user.is_verified = False

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await login_user(mock_session, mock_oauth_form)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Unverified user" in exc_info.value.detail

    async def test_recover_password_success(
        self,
        mock_login_get_user_by_email,
        mock_create_password_reset_token,
        mock_generate_password_reset_email,
        mock_session,
        mock_background_tasks,
        mock_user,
        mock_email_data,
    ):
        """Prueba de recuperación de contraseña exitosa."""

        # Preparación
        mock_login_get_user_by_email.return_value = mock_user
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_generate_password_reset_email.return_value = mock_email_data

        # Ejecución
        result = await recover_password(
            mock_session, "test@example.com", mock_background_tasks
        )

        # Verificación
        mock_login_get_user_by_email.assert_called_once_with(
            session=mock_session, email="test@example.com"
        )
        mock_create_password_reset_token.assert_called_once_with(
            email="test@example.com"
        )
        mock_generate_password_reset_email.assert_called_once_with(
            email_to="test@example.com", username="Test User", token="test_reset_token"
        )
        mock_background_tasks.add_task.assert_called_once()
        assert result.message == "Password recovery email sent"

    async def test_recover_password_without_full_name(
        self,
        mock_login_get_user_by_email,
        mock_create_password_reset_token,
        mock_generate_password_reset_email,
        mock_session,
        mock_background_tasks,
        mock_user,
        mock_email_data,
    ):
        """Prueba de recuperación de contraseña para usuario sin nombre completo."""

        # Preparación
        mock_login_get_user_by_email.return_value = mock_user
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = None
        mock_generate_password_reset_email.return_value = mock_email_data

        # Ejecución
        result = await recover_password(
            mock_session, "test@example.com", mock_background_tasks
        )

        # Verificación
        mock_generate_password_reset_email.assert_called_once_with(
            email_to="test@example.com",
            username="testuser",
            token="test_reset_token",
        )
        assert result.message == "Password recovery email sent"

    async def test_recover_password_user_not_found(
        self,
        mock_login_get_user_by_email,
        mock_session,
        mock_background_tasks,
    ):
        """Prueba de recuperación de contraseña para usuario inexistente."""

        # Preparación
        mock_login_get_user_by_email.return_value = None

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await recover_password(
                mock_session, "nonexistent@example.com", mock_background_tasks
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in exc_info.value.detail

    async def test_reset_password_success(
        self,
        mock_verify_password_reset_token,
        mock_login_get_user_by_email,
        mock_verify_password,
        mock_hash_password,
        mock_update_password,
        mock_session,
        mock_user,
    ):
        """Prueba de restablecimiento de contraseña exitoso."""

        # Preparación
        mock_verify_password_reset_token.return_value = "test@example.com"
        mock_login_get_user_by_email.return_value = mock_user
        mock_user.is_active = True
        mock_verify_password.return_value = False  # La contraseña es diferente
        mock_update_password.return_value = mock_user

        body = NewPassword(token="valid_token", new_password="NewSecurePassword123!")

        # Ejecución
        result = await reset_password(mock_session, body)

        # Verificación
        mock_verify_password_reset_token.assert_called_once_with(token="valid_token")
        mock_login_get_user_by_email.assert_called_once_with(
            session=mock_session, email="test@example.com"
        )
        mock_verify_password.assert_called_once()
        mock_hash_password.assert_called_once_with(password="NewSecurePassword123!")
        mock_update_password.assert_called_once_with(
            session=mock_session, user=mock_user, new_password="hashed_new_password"
        )
        assert result.message == "Password updated successfully"

    async def test_reset_password_invalid_token(
        self, mock_verify_password_reset_token, mock_session
    ):
        """Prueba de restablecimiento de contraseña con token inválido."""

        # Preparación
        mock_verify_password_reset_token.return_value = None

        body = NewPassword(token="invalid_token", new_password="NewSecurePassword123!")

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(mock_session, body)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in exc_info.value.detail

    async def test_reset_password_user_not_found(
        self,
        mock_verify_password_reset_token,
        mock_login_get_user_by_email,
        mock_session,
    ):
        """Prueba de restablecimiento de contraseña para usuario inexistente."""

        # Preparación
        mock_verify_password_reset_token.return_value = "nonexistent@example.com"
        mock_login_get_user_by_email.return_value = None

        body = NewPassword(token="valid_token", new_password="NewSecurePassword123!")

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(mock_session, body)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in exc_info.value.detail

    async def test_reset_password_inactive_user(
        self,
        mock_verify_password_reset_token,
        mock_login_get_user_by_email,
        mock_session,
        mock_user,
    ):
        """Prueba de restablecimiento de contraseña para usuario inactivo."""

        # Preparación
        mock_verify_password_reset_token.return_value = "test@example.com"
        mock_login_get_user_by_email.return_value = mock_user
        mock_user.is_active = False

        body = NewPassword(token="valid_token", new_password="NewSecurePassword123!")

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(mock_session, body)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in exc_info.value.detail

    async def test_reset_password_same_password(
        self,
        mock_verify_password_reset_token,
        mock_login_get_user_by_email,
        mock_verify_password,
        mock_session,
        mock_user,
    ):
        """Prueba de error al intentar restablecer la misma contraseña."""

        # Preparación
        mock_verify_password_reset_token.return_value = "test@example.com"
        mock_login_get_user_by_email.return_value = mock_user
        mock_user.is_active = True
        mock_verify_password.return_value = True  # Misma contraseña

        body = NewPassword(token="valid_token", new_password="SamePassword123!")

        # Ejecución y verificación
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(mock_session, body)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot reuse" in exc_info.value.detail
