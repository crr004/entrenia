from sqlmodel import SQLModel


class Message(SQLModel):
    """Modelo para mensajes de respuesta."""

    message: str
