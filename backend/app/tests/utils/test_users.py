import pytest
from unittest.mock import patch

from app.utils.users import authenticate_user


pytestmark = pytest.mark.asyncio


class TestUserUtils:
    async def test_authenticate_user_with_email_success(
        self, mock_session, mock_user, utils_mock_verify_password
    ):
        """Prueba de autenticación exitosa con email."""

        # Preparación.
        email = "test@example.com"
        password = "correctpassword"
        utils_mock_verify_password.return_value = True

        with patch("app.utils.users.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = mock_user

            # Ejecución.
            result = await authenticate_user(
                session=mock_session, email_or_username=email, password=password
            )

            # Verificación.
            assert result == mock_user
            mock_get_user.assert_called_once_with(session=mock_session, email=email)
            utils_mock_verify_password.assert_called_once_with(
                plain_password=password, hashed_password=mock_user.password
            )

    async def test_authenticate_user_with_username_success(
        self, mock_session, mock_user, utils_mock_verify_password
    ):
        """Prueba de autenticación exitosa con nombre de usuario."""

        # Preparación.
        username = "testuser"
        password = "correctpassword"
        utils_mock_verify_password.return_value = True

        with patch("app.utils.users.get_user_by_username") as mock_get_user:
            mock_get_user.return_value = mock_user

            # Ejecución.
            result = await authenticate_user(
                session=mock_session, email_or_username=username, password=password
            )

            # Verificación.
            assert result == mock_user
            mock_get_user.assert_called_once_with(
                session=mock_session, username=username
            )
            utils_mock_verify_password.assert_called_once_with(
                plain_password=password, hashed_password=mock_user.password
            )

    async def test_authenticate_user_wrong_password(
        self, mock_session, mock_user, utils_mock_verify_password
    ):
        """Prueba de fallo de autenticación debido a contraseña incorrecta."""

        # Preparación.
        email = "test@example.com"
        password = "wrongpassword"
        utils_mock_verify_password.return_value = False

        with patch("app.utils.users.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = mock_user

            # Ejecución.
            result = await authenticate_user(
                session=mock_session, email_or_username=email, password=password
            )

            # Verificación.
            assert result is None
            mock_get_user.assert_called_once_with(session=mock_session, email=email)
            utils_mock_verify_password.assert_called_once_with(
                plain_password=password, hashed_password=mock_user.password
            )
