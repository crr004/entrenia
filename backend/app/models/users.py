import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from pydantic import EmailStr


class UserBase(SQLModel):
    """Modelo base de usuario."""

    email: EmailStr = Field(
        unique=True, index=True, max_length=255, description="Email del usuario"
    )
    username: str = Field(
        unique=True,
        index=True,
        min_length=3,
        max_length=20,
        description="Nombre de usuario",
    )
    full_name: str | None = Field(
        max_length=255, description="Nombre completo del usuario", default=None
    )
    is_active: bool = Field(default=True, description="Usuario activo")
    is_admin: bool = Field(default=False, description="Usuario administrador")
    is_verified: bool = Field(default=True, description="Usuario verificado")


# TABLA: users
class User(UserBase, table=True):
    """Modelo de usuario que se mapea a la tabla de la base de datos."""

    __tablename__ = "users"

    id: uuid.UUID = Field(
        primary_key=True, default_factory=uuid.uuid4, description="ID del usuario"
    )
    password: str = Field(
        max_length=255, description="Contraseña del usuario (haseada)"
    )
    created_at: datetime = Field(
        default=datetime.now(timezone.utc),
        description="Fecha de creación del usuario",
    )


class UserCreate(UserBase):
    """Modelo de usuario para la creación de un nuevo usuario."""

    password: str = Field(
        min_length=9, max_length=50, description="Contraseña del usuario (sin hashear)"
    )


class UserRegister(SQLModel):
    """Modelo de usuario para el registro de un nuevo usuario."""

    email: EmailStr = Field(max_length=255, description="Email del usuario")
    username: str = Field(min_length=3, max_length=20, description="Nombre de usuario")
    full_name: str | None = Field(
        max_length=255, description="Nombre completo del usuario", default=None
    )
    password: str = Field(
        min_length=9, max_length=50, description="Contraseña del usuario (sin hashear)"
    )


class UserReturn(UserBase):
    """Modelo de usuario para retornar."""

    id: uuid.UUID = Field(description="ID del usuario")
    created_at: datetime = Field(description="Fecha de creación del usuario")


class UsersReturn(SQLModel):
    """Modelo de usuarios para retornar (lista de todos los usuarios con su longitud)."""

    users: list[UserReturn]
    count: int


class UserUpdate(UserBase):
    """Modelo de usuario para actualizar su información (admin)."""

    email: EmailStr | None = Field(
        max_length=255, description="Email del usuario", default=None
    )
    password: str | None = Field(
        min_length=9,
        max_length=50,
        description="Contraseña del usuario (sin hashear)",
        default=None,
    )


class UserUpdateOwn(SQLModel):
    """Modelo de usuario para actualizar su propia información."""

    full_name: str | None = Field(
        max_length=255, description="Nombre completo del usuario", default=None
    )
    username: str | None = Field(
        min_length=3, max_length=20, description="Nombre de usuario", default=None
    )


class UserUpdatePassword(SQLModel):
    """Modelo de usuario para actualizar su contraseña."""

    current_password: str = Field(
        min_length=9, max_length=50, description="Contraseña del usuario (sin hashear)"
    )
    new_password: str = Field(
        min_length=9,
        max_length=50,
        description="Nueva contraseña del usuario (sin hashear)",
    )
