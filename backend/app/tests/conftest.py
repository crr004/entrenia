import sys
import pytest
import warnings
import uuid
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient


# Ignorar advertencias de deprecación de 'crypt', ya que lo usa passlib internamente
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=".*'crypt' is deprecated.*"
)

# Añado la ruta de la app al path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Configuración de pytest para ejecutar pruebas asíncronas
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock de variables de entorno."""

    monkeypatch.setenv("APP_NAME", "TestApp")
    monkeypatch.setenv("EMAILS_FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("SMTP_USER", "smtp_user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp_password")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_TLS", "True")
    monkeypatch.setenv("SMTP_SSL", "False")
    monkeypatch.setenv("LANDING_FRONTEND_URL", "https://example.com/landing")
    monkeypatch.setenv("PASSWORD_RESET_FRONTEND_URL", "https://example.com/reset")
    monkeypatch.setenv("PASSWORD_RESET_TOKEN_EXPIRE", "60")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_123")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE", "30")


def make_async_mock(mock):
    """Función auxiliar para hacer que un mock devuelva valores directamente en lugar de corutinas."""

    async def _async_return(*args, **kwargs):
        return mock.return_value

    mock.side_effect = _async_return

    if (
        isinstance(mock, MagicMock)
        and hasattr(mock, "return_value")
        and isinstance(mock.return_value, MagicMock)
    ):
        if any(name in mock._mock_name for name in ["get_user_by", "get_all_users"]):
            result_mock = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.first.return_value = mock.return_value
            result_mock.scalars.return_value = scalars_mock

            async def _session_execute(*args, **kwargs):
                return result_mock

            if hasattr(mock, "execute"):
                mock.execute = AsyncMock(side_effect=_session_execute)

    return mock


@pytest.fixture
def mock_session():
    """Fixture para mockear SQLAlchemy AsyncSession."""

    mock = MagicMock(spec=AsyncSession)

    async def _async_execute(*args, **kwargs):
        if not hasattr(mock_session, "_execute_results"):
            mock_session._execute_results = []
        if mock_session._execute_results:
            return mock_session._execute_results.pop(0)

        scalars_mock = MagicMock()
        scalars_mock.first = MagicMock(return_value=None)

        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        result_mock.all = MagicMock()

        return result_mock

    mock_session = mock
    mock.execute = AsyncMock(side_effect=_async_execute)

    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.delete = AsyncMock()
    mock.get = AsyncMock()

    return mock


@pytest.fixture
def mock_background_tasks():
    """Fixture para mockear FastAPI BackgroundTasks."""

    return MagicMock()


@pytest.fixture
def mock_user():
    """Fixture para mockear un modelo User."""

    mock = MagicMock()
    mock.email = "test@example.com"
    mock.username = "testuser"
    mock.full_name = "Test User"
    mock.password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LcdYvsQGBT.7EMqCS"
    mock.is_admin = False
    mock.is_active = True
    mock.is_verified = True
    mock.id = uuid.uuid4()
    return mock


@pytest.fixture
def mock_email_data():
    """Fixture para mockear datos de email."""

    mock = MagicMock()
    mock.subject = "Test Subject"
    mock.html_content = "<p>Test Content</p>"
    return mock


@pytest.fixture
def app():
    """Crea una aplicación FastAPI de prueba."""

    from app.main import app

    return app


@pytest.fixture
def client(app):
    """Crea un cliente de prueba para la aplicación."""

    return TestClient(app)


@pytest.fixture
def mock_signup_get_user_by_email():
    """Mock para get_user_by_email en rutas de registro."""

    with patch("app.api.routes.signup.get_user_by_email") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_signup_get_user_by_username():
    """Mock para get_user_by_username en rutas de registro."""

    with patch("app.api.routes.signup.get_user_by_username") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_signup_create_user():
    """Mock para create_user en rutas de registro."""

    with patch("app.api.routes.signup.create_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_signup_create_token():
    """Mock para create_verify_account_token en rutas de registro."""

    with patch("app.api.routes.signup.create_verify_account_token") as mock:
        mock.return_value = "test_token"
        yield mock


@pytest.fixture
def mock_signup_generate_email():
    """Mock para generate_new_account_email en rutas de registro."""

    with patch("app.api.routes.signup.generate_new_account_email") as mock:
        yield mock


@pytest.fixture
def mock_signup_verify_token():
    """Mock para verify_user_verification_token en rutas de registro."""

    with patch("app.api.routes.signup.verify_user_verification_token") as mock:
        yield mock


@pytest.fixture
def mock_signup_update_user():
    """Mock para update_user en rutas de registro."""

    with patch("app.api.routes.signup.update_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_users_get_user_by_email():
    """Mock para get_user_by_email en rutas de usuarios."""

    with patch("app.api.routes.users.get_user_by_email") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_users_get_user_by_id():
    """Mock para get_user_by_id en rutas de usuarios."""

    with patch("app.api.routes.users.get_user_by_id") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_users_get_user_by_username():
    """Mock para get_user_by_username en rutas de usuarios."""

    with patch("app.api.routes.users.get_user_by_username") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_get_user_by_email():
    """Mock para get_user_by_email en rutas de registro."""

    with patch("app.api.routes.signup.get_user_by_email") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_get_user_by_username():
    """Mock para get_user_by_username en rutas de registro."""

    with patch("app.api.routes.signup.get_user_by_username") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_create_user():
    """Mock para create_user en rutas de registro."""

    with patch("app.api.routes.signup.create_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_create_token():
    """Mock para create_verify_account_token en rutas de registro."""

    with patch("app.api.routes.signup.create_verify_account_token") as mock:
        mock.return_value = "test_token"
        yield mock


@pytest.fixture
def mock_generate_email():
    """Mock para generate_new_account_email en rutas de registro."""

    with patch("app.api.routes.signup.generate_new_account_email") as mock:
        yield mock


@pytest.fixture
def mock_verify_token():
    """Mock para verify_user_verification_token en rutas de registro."""

    with patch("app.api.routes.signup.verify_user_verification_token") as mock:
        yield mock


@pytest.fixture
def mock_update_user():
    """Mock para update_user en rutas de registro."""

    with patch("app.api.routes.signup.update_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_authenticate_user():
    """Mock para authenticate_user en rutas de inicio de sesión."""

    with patch("app.api.routes.login.authenticate_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_create_access_token():
    """Mock para create_access_token en rutas de inicio de sesión."""

    with patch("app.api.routes.login.create_access_token") as mock:
        mock.return_value = "test_access_token"
        yield mock


@pytest.fixture
def mock_create_password_reset_token():
    """Mock para create_password_reset_token en rutas de inicio de sesión."""

    with patch("app.api.routes.login.create_password_reset_token") as mock:
        mock.return_value = "test_reset_token"
        yield mock


@pytest.fixture
def mock_verify_password_reset_token():
    """Mock para verify_password_reset_token en rutas de inicio de sesión."""

    with patch("app.api.routes.login.verify_password_reset_token") as mock:
        yield mock


@pytest.fixture
def mock_generate_password_reset_email():
    """Mock para generate_password_reset_email en rutas de inicio de sesión."""

    with patch("app.api.routes.login.generate_password_reset_email") as mock:
        yield mock


@pytest.fixture
def mock_hash_password():
    """Mock para hash_password en rutas de inicio de sesión."""

    with patch("app.api.routes.login.hash_password") as mock:
        mock.return_value = "hashed_new_password"
        yield mock


@pytest.fixture
def mock_verify_password():
    """Mock para verify_password en rutas de inicio de sesión."""

    with patch("app.api.routes.login.verify_password") as mock:
        yield mock


@pytest.fixture
def mock_update_password():
    """Mock para update_password en rutas de inicio de sesión."""

    with patch("app.api.routes.login.update_password") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_oauth_form():
    """Mock para OAuth2PasswordRequestForm."""

    mock = MagicMock()
    mock.username = "test@example.com"
    mock.password = "password123"
    return mock


@pytest.fixture
def mock_login_get_user_by_email():
    """Mock para get_user_by_email en rutas de inicio de sesión."""

    with patch("app.api.routes.login.get_user_by_email") as mock:

        async def mock_get_user(*args, **kwargs):
            return mock.return_value

        mock.side_effect = mock_get_user
        yield mock


@pytest.fixture
def mock_get_all_users():
    """Mock para get_all_users en rutas de usuarios."""

    with patch("app.api.routes.users.get_all_users") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_get_user_by_id():
    """Mock para get_user_by_id en rutas de usuarios."""

    with patch("app.api.routes.users.get_user_by_id") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_delete_user():
    """Mock para delete_user en rutas de usuarios."""

    with patch("app.api.routes.users.delete_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_update_user_by_admin():
    """Mock para update_user_by_admin en rutas de usuarios."""

    with patch("app.api.routes.users.update_user_by_admin") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_get_current_admin():
    """Mock para get_current_admin en rutas de usuarios."""

    with patch("app.api.routes.users.get_current_admin") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_admin_user():
    """Fixture para mockear un usuario admin."""

    mock = MagicMock()
    mock.email = "admin@example.com"
    mock.username = "adminuser"
    mock.full_name = "Admin User"
    mock.is_admin = True
    mock.id = uuid.uuid4()
    mock.is_active = True
    mock.is_verified = True
    return mock


@pytest.fixture
def mock_users_list():
    """Fixture para mockear una lista de usuarios."""

    users = MagicMock()
    users.users = [MagicMock() for _ in range(3)]
    users.total = 3
    return users


@pytest.fixture
def mock_uuid():
    """Fixture para mockear un UUID."""

    return uuid.uuid4()


@pytest.fixture
def mock_create_verify_account_token():
    """Mock para create_verify_account_token en rutas de usuarios."""

    with patch("app.api.routes.users.create_verify_account_token") as mock:
        mock.return_value = "test_verify_token"
        yield mock


@pytest.fixture
def mock_generate_new_account_email():
    """Mock para generate_new_account_email en rutas de usuarios."""

    with patch("app.api.routes.users.generate_new_account_email") as mock:
        mock.return_value = MagicMock(
            subject="Test New Account Email",
            html_content="<p>Your account has been created</p>",
        )
        yield mock


@pytest.fixture
def mock_users_create_user():
    """Mock para create_user en rutas de usuarios."""

    with patch("app.api.routes.users.create_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_users_update_user():
    """Mock para update_user en rutas de usuarios."""

    with patch("app.api.routes.users.update_user") as mock:
        yield make_async_mock(mock)


@pytest.fixture
def mock_crud_jwt_decode():
    """Mock para jwt.decode en operaciones CRUD."""

    with patch("app.crud.users.jwt.decode") as mock:
        yield mock


@pytest.fixture
def mock_crud_hash_password():
    """Mock para hash_password en operaciones CRUD."""

    with patch("app.crud.users.hash_password") as mock:
        mock.return_value = (
            "$2b$12$CwzJkf9Vq.XVXpIFZX7mu.q9q09ro8xJmOXy9c3c/4lM8V0YJQWEm"
        )
        yield mock


@pytest.fixture
def mock_crud_get_user_by_id(mock_user):
    """Mock para get_user_by_id en operaciones CRUD."""

    with patch("app.crud.users.get_user_by_id") as mock:

        async def _async_return(*args, **kwargs):
            return mock_user

        mock.side_effect = _async_return
        yield mock


@pytest.fixture
def mock_crud_token_data():
    """Mock para datos de token en pruebas de autenticación."""

    user_id = str(uuid.uuid4())
    return {"sub": user_id, "type": "auth", "exp": 1714563719}


@pytest.fixture
def mock_crud_invalid_token_data():
    """Mock para datos de token inválido en pruebas de error."""

    user_id = str(uuid.uuid4())
    return {"sub": user_id, "type": "reset", "exp": 1714563719}


@pytest.fixture
def utils_mock_verify_password():
    """Mock para verify_password en utils."""

    with patch("app.utils.users.verify_password") as mock:
        yield mock
