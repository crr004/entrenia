from dataclasses import dataclass
from jinja2 import Template
from pathlib import Path
from typing import Any
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Clase para almacenar los datos de un email."""

    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """Renderiza un template de email con los datos proporcionados.

    Args:
        template_name (str): Nombre del template a renderizar.
        context (dict[str, Any]): Datos para renderizar el template.

    Returns:
        str: Contenido HTML del email renderizado.
    """

    template_str = (
        Path(__file__).parent.parent / "templates" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """Envía un email.

    Args:
        email_to (str): Dirección de email a la que se enviará el mensaje.
        subject (str): Asunto del email.
        html_content (str): Contenido HTML del email
    """

    try:
        api_key = os.environ["SENDGRID_API_KEY"]
        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        from_email = os.environ["EMAILS_FROM_EMAIL"]

        data = {
            "personalizations": [{"to": [{"email": email_to}]}],
            "from": {"email": from_email, "name": os.environ["APP_NAME"]},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_content}],
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(
            f"Message sent to {email_to}. SendGrid response: {response.status_code}"
        )
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}. Error: {str(e)}")
        raise


def generate_new_account_email(email_to: str, username: str, token: str) -> EmailData:
    """Genera un email para notificar a un usuario que se ha creado una nueva cuenta.

    Args:
        email_to (str): Dirección de email del destinatario.
        username (str): Nombre de usuario.
        token (str): Token de verificación de cuenta.

    Returns:
        EmailData: Datos del email generado.
    """

    project_name = os.environ["APP_NAME"]
    subject = f"{project_name} - Nueva cuenta de {username}"
    frontend_url = os.environ["LANDING_FRONTEND_URL"]
    link = f"{frontend_url}?token={token}"
    html_content = render_email_template(
        template_name="email_new_acc.html",
        context={
            "project_name": project_name,
            "username": username,
            "email": email_to,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_email(
    email_to: str, username: str, token: str
) -> EmailData:
    """Genera un email para un usuario que quiere restablecer su contraseña.

    Args:
        email_to (str): Dirección de email del destinatario.
        username (str): Nombre de usuario.
        token (str): Token de restablecimiento de contraseña.

    Returns:
        EmailData: Datos del email generado.
    """

    project_name = os.environ["APP_NAME"]
    subject = f"{project_name} - Restablecimiento de contraseña para {username}"
    frontend_url = os.environ["PASSWORD_RESET_FRONTEND_URL"]
    link = f"{frontend_url}?token={token}"
    expire_mins = int(os.environ["PASSWORD_RESET_TOKEN_EXPIRE"])
    expire_hours = str(int(expire_mins / 60))
    html_content = render_email_template(
        template_name="email_password_reset.html",
        context={
            "project_name": project_name,
            "username": username,
            "email": email_to,
            "valid_hours": expire_hours,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)
