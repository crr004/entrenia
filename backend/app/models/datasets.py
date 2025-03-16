import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.images import Image


class DatasetBase(SQLModel):
    """Modelo base de dataset."""

    name: str = Field(min_length=1, max_length=255, description="Nombre del dataset")
    description: str | None = Field(
        default=None, max_length=1000, description="Descripción del dataset"
    )
    is_public: bool = Field(
        default=False, description="Indica si el dataset es público"
    )


# TABLA: datasets
class Dataset(DatasetBase, table=True):
    """Modelo de dataset que se mapea a la tabla de la base de datos."""

    __tablename__ = "datasets"

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_dataset_name"),)

    id: uuid.UUID = Field(
        primary_key=True, default_factory=uuid.uuid4, description="ID del dataset"
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        nullable=False,
        ondelete="CASCADE",
        description="ID del usuario propietario",
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha de creación del dataset (UTC)",
    )

    if TYPE_CHECKING:
        user: "User" = None
        images: list["Image"] = []


class DatasetCreate(DatasetBase):
    """Modelo de dataset para la creación de un nuevo dataset."""

    pass


class DatasetReturn(DatasetBase):
    """Modelo de dataset para retornar."""

    id: uuid.UUID = Field(description="ID del dataset")
    user_id: uuid.UUID = Field(description="ID del usuario propietario")
    created_at: datetime = Field(description="Fecha de creación del dataset")
    image_count: int = Field(default=0, description="Número de imágenes en el dataset")
    category_count: int = Field(
        default=0, description="Número de categorías en el dataset"
    )


class DatasetsReturn(SQLModel):
    """Modelo de datasets para retornar (lista de datasets con su longitud)."""

    datasets: list[DatasetReturn]
    count: int


class DatasetUpdate(SQLModel):
    """Modelo de dataset para actualizar su información."""

    name: str | None = Field(
        default=None, max_length=255, description="Nombre del dataset"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Descripción del dataset"
    )
