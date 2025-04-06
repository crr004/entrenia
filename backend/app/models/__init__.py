"""Inicializa los modelos de la aplicación y define sus relaciones."""

from sqlmodel import Relationship

from app.models.users import User
from app.models.datasets import Dataset
from app.models.images import Image
from app.models.classifiers import Classifier

from app.models.users import (
    UserBase,
    UserCreate,
    UserRegister,
    UserReturn,
    UsersReturn,
    UserUpdate,
    UserUpdateOwn,
    UserUpdatePassword,
    NewPassword,
)
from app.models.datasets import (
    DatasetBase,
    DatasetCreate,
    DatasetReturn,
    DatasetsReturn,
    DatasetUpdate,
)
from app.models.images import (
    ImageBase,
    ImageCreate,
    ImageReturn,
    ImagesReturn,
    ImageUpdate,
)
from app.models.classifiers import (
    ClassifierBase,
    ClassifierCreate,
    ClassifierReturn,
    ClassifiersReturn,
    ClassifierUpdate,
    ClassifierTrainingResult,
    ClassifierTrainingStatus,
    ClassifierPredictionRequest,
    ClassifierPredictionResult,
)

# Definir las relaciones.
User.datasets = Relationship(back_populates="user", cascade_delete=True)
User.classifiers = Relationship(back_populates="user", cascade_delete=True)

Dataset.user = Relationship(back_populates="datasets")
Dataset.images = Relationship(back_populates="images", cascade_delete=True)
Dataset.classifiers = Relationship(back_populates="dataset")

Image.dataset = Relationship(back_populates="images")

Classifier.user = Relationship(back_populates="classifiers")
Classifier.dataset = Relationship(back_populates="classifiers")

# Exportar todos los modelos.
__all__ = [
    "User",
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserReturn",
    "UsersReturn",
    "UserUpdate",
    "UserUpdateOwn",
    "UserUpdatePassword",
    "NewPassword",
    "Dataset",
    "DatasetBase",
    "DatasetCreate",
    "DatasetReturn",
    "DatasetsReturn",
    "DatasetUpdate",
    "Image",
    "ImageBase",
    "ImageCreate",
    "ImageReturn",
    "ImagesReturn",
    "ImageUpdate",
    "Classifier",
    "ClassifierBase",
    "ClassifierCreate",
    "ClassifierReturn",
    "ClassifiersReturn",
    "ClassifierUpdate",
    "ClassifierTrainingResult",
    "ClassifierTrainingStatus",
    "ClassifierPredictionRequest",
    "ClassifierPredictionResult",
]
