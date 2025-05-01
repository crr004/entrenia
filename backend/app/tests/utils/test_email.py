from app.utils.email import generate_new_account_email, EmailData


def test_generate_new_account_email(mock_env_vars):
    """Prueba de generación de un email para nueva cuenta."""

    # Preparación.
    email_to = "user@example.com"
    username = "testuser"
    token = "testtoken"

    # Ejecución.
    email_data = generate_new_account_email(
        email_to=email_to, username=username, token=token
    )

    # Verificación.
    assert isinstance(email_data, EmailData)
    assert email_data.subject == "TestApp - Nueva cuenta de testuser"
    assert "testuser" in email_data.html_content
    assert "https://example.com/landing?token=testtoken" in email_data.html_content
