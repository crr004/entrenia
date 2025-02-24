import uuid
from sqlmodel import Field, SQLModel
from pydantic import EmailStr
from datetime import datetime


class UserBase(SQLModel):
    """Modelo base de usuario."""

    email: EmailStr = Field(
        unique=True, index=True, max_length=255, description="Email del usuario"
    )
    username: str = Field(max_length=30, description="Nombre de usuario")
    full_name: str | None = Field(
        max_length=255, description="Nombre completo del usuario"
    )
    is_active: bool = Field(default=True, description="Usuario activo")
    is_admin: bool = Field(default=False, description="Usuario administrador")
    is_verified: bool = Field(default=False, description="Usuario verificado")


# TABLA: users
class User(UserBase, table=True):
    """Modelo de usuario que se mapea a la tabla de la base de datos"""

    __tablename__ = "users"

    id: uuid.UUID = Field(
        primary_key=True, default=uuid.uuid4, description="ID del usuario"
    )
    password: str = Field(
        max_length=255, description="Contraseña del usuario (haseada)"
    )
    created_at: datetime = Field(
        default=datetime.now(), description="Fecha de creación del usuario"
    )
