import jwt
from datetime import timedelta, datetime, timezone

from app.utils.tokens import (
    create_access_token,
    verify_password_reset_token,
    create_password_reset_token,
)


class TestTokens:
    def test_create_access_token(self, mock_env_vars):
        """Prueba de creación de un token de acceso."""

        # Preparación
        user_id = "test123"
        expires_delta = timedelta(minutes=30)

        # Ejecución
        token = create_access_token(subject=user_id, expires_delta=expires_delta)

        # Decodificación y verificación
        decoded = jwt.decode(token, "test_secret_key_123", algorithms=["HS256"])

        # Verificación
        assert decoded["sub"] == user_id
        assert decoded["type"] == "auth"
        assert isinstance(decoded["exp"], int)
        # Verificar que el tiempo de expiración está en el futuro
        assert datetime.fromtimestamp(decoded["exp"], tz=timezone.utc) > datetime.now(
            timezone.utc
        )

    def test_verify_password_reset_token_valid(self, mock_env_vars):
        """Prueba de verificación de un token válido de restablecimiento de contraseña."""

        # Preparación
        email = "test@example.com"
        token = create_password_reset_token(email=email)

        # Ejecución
        result = verify_password_reset_token(token=token)

        # Verificación
        assert result == email

    def test_verify_password_reset_token_invalid(self, mock_env_vars):
        """Prueba de verificación de un token inválido de restablecimiento de contraseña."""

        # Preparación - Crear token con tipo incorrecto
        email = "test@example.com"
        wrong_token = jwt.encode(
            {
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "sub": email,
                "type": "wrong_type",
            },
            "test_secret_key_123",
            algorithm="HS256",
        )

        # Ejecución
        result = verify_password_reset_token(token=wrong_token)

        # Verificación
        assert result is None
