import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.images import ImageReturn

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
    # Campos para la denormalización.
    cached_image_count: int | None = Field(
        default=None, description="Número de imágenes en caché"
    )
    cached_category_count: int | None = Field(
        default=None, description="Número de categorías en caché"
    )
    cache_updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True)),
        default=None,
        description="Fecha de última actualización de la caché",
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
    username: str | None = Field(
        default=None, description="Nombre de usuario del propietario"
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
    is_public: bool | None = Field(
        default=None, description="Indica si el dataset es público"
    )


class DatasetCategoryDetail(SQLModel):
    """Modelo de detalles de una categoría en un dataset."""

    name: str = Field(description="Nombre de la categoría")
    image_count: int = Field(description="Número de imágenes en esta categoría")


class DatasetLabelDetailsReturn(SQLModel):
    """Modelo para retornar detalles de las etiquetas y categorías de un dataset."""

    dataset_id: uuid.UUID = Field(description="ID del dataset")
    categories: list[DatasetCategoryDetail] = Field(
        description="Detalles de cada categoría del dataset"
    )
    count: int = Field(description="Número total de categorías en el dataset")
    labeled_images: int = Field(
        description="Número de imágenes etiquetadas en el dataset"
    )
    unlabeled_images: int = Field(
        description="Número de imágenes sin etiquetar en el dataset"
    )


class DatasetUploadResult(SQLModel):
    """Modelo para el resultado de la carga de imágenes en un dataset."""

    message: str = Field(description="Mensaje de éxito")
    processed_images: int = Field(
        description="Número de imágenes procesadas correctamente"
    )
    skipped_images: int = Field(
        description="Número de imágenes omitidas por ya existir"
    )
    invalid_images: int = Field(description="Número de imágenes inválidas")
    labels_applied: int = Field(
        description="Número de etiquetas aplicadas correctamente"
    )
    labels_skipped: int = Field(description="Número de etiquetas no aplicadas")
    invalid_image_details: list[str] = Field(
        default=[], description="Detalles de imágenes inválidas"
    )
    duplicated_image_details: list[str] = Field(
        default=[], description="Detalles de imágenes duplicadas"
    )
    skipped_label_details: list[str] = Field(
        default=[], description="Detalles de etiquetas no aplicadas"
    )


class UnlabeledImagesResponse(SQLModel):
    """Modelo para la respuesta de imágenes sin etiquetar."""

    images: list[ImageReturn] = Field(description="Lista de imágenes sin etiquetar")


class CsvLabelData(SQLModel):
    """Modelo para los datos de etiquetado CSV."""

    labels: list[dict] = Field(description="Lista de pares {image_name, label}")


class CsvLabelingResponse(SQLModel):
    """Modelo para la respuesta del etiquetado CSV."""

    labeled_count: int = Field(
        description="Número de imágenes etiquetadas correctamente"
    )
    not_found_count: int = Field(description="Número de imágenes no encontradas")
    not_found_details: list[str] = Field(
        default=[], description="Detalles de imágenes no encontradas"
    )
