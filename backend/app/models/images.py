import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from app.models.datasets import Dataset


class ImageBase(SQLModel):
    """Modelo base de imagen."""

    name: str = Field(min_length=1, max_length=255, description="Nombre de la imagen")
    file_path: str = Field(max_length=512, description="Ruta al archivo de imagen")
    label: str | None = Field(
        default=None, max_length=255, description="Etiqueta o clase de la imagen"
    )


# TABLA: images
class Image(ImageBase, table=True):
    """Modelo de imagen que se mapea a la tabla de la base de datos."""

    __tablename__ = "images"

    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="uq_dataset_image_name"),
    )

    id: uuid.UUID = Field(
        primary_key=True, default_factory=uuid.uuid4, description="ID de la imagen"
    )
    dataset_id: uuid.UUID = Field(
        foreign_key="datasets.id",
        nullable=False,
        ondelete="CASCADE",
        description="ID del dataset al que pertenece",
    )
    thumbnail: bytes = Field(description="Miniatura de la imagen en formato binario")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha de creación de la imagen (UTC)",
    )

    if TYPE_CHECKING:
        dataset: "Dataset" = None


class ImageCreate(ImageBase):
    """Modelo de imagen para la creación de una nueva imagen."""

    thumbnail: bytes = Field(description="Miniatura de la imagen en formato binario")


class ImageReturn(ImageBase):
    """Modelo de imagen para retornar."""

    id: uuid.UUID = Field(description="ID de la imagen")
    dataset_id: uuid.UUID = Field(description="ID del dataset al que pertenece")
    thumbnail: bytes = Field(description="Miniatura de la imagen en formato binario")
    created_at: datetime = Field(description="Fecha de creación de la imagen")


class ImagesReturn(SQLModel):
    """Modelo de imágenes para retornar (lista de imágenes con su longitud)."""

    images: list[ImageReturn]
    count: int


class ImageUpdate(SQLModel):
    """Modelo de imagen para actualizar su información."""

    name: str | None = Field(
        default=None, max_length=255, description="Nombre de la imagen"
    )
    label: str | None = Field(
        default=None, max_length=255, description="Etiqueta o clase de la imagen"
    )
