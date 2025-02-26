import emails
from dataclasses import dataclass
from jinja2 import Template
from pathlib import Path
from typing import Any
import os
import logging

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

    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(os.environ["APP_NAME"], os.environ["EMAILS_FROM_EMAIL"]),
    )
    smtp_options = {
        "user": os.environ["SMTP_USER"],
        "password": os.environ["SMTP_PASSWORD"],
        "host": os.environ["SMTP_HOST"],
        "port": int(os.environ["SMTP_PORT"]),
    }
    if os.environ["SMTP_TLS"] == "True":
        smtp_options["tls"] = True
        smtp_options["ssl"] = False
    elif os.environ["SMTP_SSL"] == "True":
        smtp_options["ssl"] = True
        smtp_options["tls"] = False

    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"Message sent to {email_to}. Server response: {response}")


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """Genera un email para notificar a un usuario que se ha creado una nueva cuenta.

    Args:
        email_to (str): Dirección de email del destinatario.
        username (str): Nombre de usuario.
        password (str): Contraseña de la nueva cuenta.

    Returns:
        EmailData: Datos del email generado.
    """

    project_name = os.environ["APP_NAME"]
    subject = f"{project_name} - Nueva cuenta de {username}"
    html_content = render_email_template(
        template_name="email_new_acc.html",
        context={
            "project_name": project_name,
            "username": username,
            "password": password,
            "email": email_to,
            "link": os.environ["FRONTEND_URL"],
        },
    )
    return EmailData(html_content=html_content, subject=subject)
