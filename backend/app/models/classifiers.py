import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Dict, Any, List

from sqlalchemy import Column, DateTime, UniqueConstraint, JSON
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.datasets import Dataset


class ClassifierTrainingStatus(str, Enum):
    """Estado del entrenamiento de un modelo."""

    NOT_TRAINED = "not_trained"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"


class ClassifierBase(SQLModel):
    """Modelo base de clasificador."""

    name: str = Field(
        min_length=1, max_length=255, description="Nombre del clasificador"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Descripción del clasificador"
    )


# TABLA: classifiers
class Classifier(ClassifierBase, table=True):
    """Modelo de clasificador que se mapea a la tabla de la base de datos."""

    __tablename__ = "classifiers"

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_classifier_name"),
    )

    id: uuid.UUID = Field(
        primary_key=True, default_factory=uuid.uuid4, description="ID del clasificador"
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        nullable=False,
        ondelete="CASCADE",
        description="ID del usuario propietario",
    )
    dataset_id: uuid.UUID | None = Field(
        foreign_key="datasets.id",
        nullable=True,
        ondelete="SET NULL",
        description="ID del dataset utilizado para entrenar (puede ser NULL si el dataset fue eliminado)",
    )
    status: ClassifierTrainingStatus = Field(
        default=ClassifierTrainingStatus.NOT_TRAINED,
        description="Estado actual del entrenamiento",
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha de creación del clasificador (UTC)",
    )
    trained_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True)),
        default=None,
        description="Fecha en que se completó el entrenamiento (UTC)",
    )
    architecture: str = Field(
        default=None,
        description="Tipo de arquitectura del modelo",
    )
    metrics: Dict[str, float] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="Métricas del entrenamiento en formato JSON",
    )
    model_parameters: Dict[str, Any] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="Parámetros utilizados para entrenar el modelo",
    )
    file_path: str | None = Field(
        default=None, description="Ruta al archivo del modelo entrenado"
    )

    if TYPE_CHECKING:
        user: "User" = None
        dataset: "Dataset" = None


class ClassifierCreate(ClassifierBase):
    """Modelo de clasificador para la creación de un nuevo clasificador."""

    dataset_name: str = Field(description="Nombre del dataset utilizado para entrenar")
    dataset_id: uuid.UUID | None = Field(
        default=None, description="ID del dataset utilizado para entrenar"
    )
    architecture: str = Field(description="Tipo de arquitectura del modelo a entrenar")
    model_parameters: Dict[str, Any] | None = Field(
        default=None, description="Parámetros para el entrenamiento del modelo"
    )


class ClassifierReturn(ClassifierBase):
    """Modelo de clasificador para retornar."""

    id: uuid.UUID = Field(description="ID del clasificador")
    user_id: uuid.UUID = Field(description="ID del usuario propietario")
    dataset_id: uuid.UUID | None = Field(
        description="ID del dataset utilizado para entrenar"
    )
    status: ClassifierTrainingStatus = Field(
        description="Estado actual del entrenamiento"
    )
    created_at: datetime = Field(description="Fecha de creación del clasificador")
    username: str | None = Field(
        default=None, description="Nombre de usuario del propietario"
    )


class ClassifierDetailReturn(ClassifierReturn):
    """Modelo de clasificador para retornar en vista detallada."""

    dataset_name: str | None = Field(
        default=None, description="Nombre del dataset utilizado"
    )
    trained_at: datetime | None = Field(
        default=None, description="Fecha en que se completó el entrenamiento"
    )
    metrics: Dict[str, float] | None = Field(
        default=None, description="Métricas del entrenamiento"
    )
    model_parameters: Dict[str, Any] | None = Field(
        default=None, description="Parámetros utilizados para entrenar el modelo"
    )


class ClassifiersReturn(SQLModel):
    """Modelo de clasificadores para retornar (lista de clasificadores con su longitud)."""

    classifiers: List[ClassifierReturn]
    count: int


class ClassifierUpdate(SQLModel):
    """Modelo de clasificador para actualizar su información."""

    name: str | None = Field(
        default=None, max_length=255, description="Nombre del clasificador"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Descripción del clasificador"
    )


class ClassifierTrainingResult(SQLModel):
    """Modelo para el resultado del entrenamiento de un clasificador."""

    id: uuid.UUID = Field(description="ID del clasificador")
    status: ClassifierTrainingStatus = Field(
        description="Estado final del entrenamiento"
    )
    metrics: Dict[str, float] | None = Field(description="Métricas del entrenamiento")
    trained_at: datetime | None = Field(
        description="Fecha en que se completó el entrenamiento"
    )
    error_message: str | None = Field(
        default=None, description="Mensaje de error si el entrenamiento falló"
    )


class ClassifierPredictionRequest(SQLModel):
    """Modelo para solicitar una predicción con un clasificador entrenado."""

    image_data: str = Field(description="Imagen en formato base64 para clasificar")


class ClassifierPredictionResult(SQLModel):
    """Modelo para el resultado de una predicción."""

    predicted_class: str = Field(description="Clase predicha por el modelo")
    confidence: float = Field(description="Confianza de la predicción (0-1)")
    all_predictions: Dict[str, float] = Field(
        description="Todas las predicciones con sus probabilidades"
    )
