"""Inicializa los modelos de la aplicación y define sus relaciones."""

from sqlmodel import Relationship

from app.models.users import User
from app.models.datasets import Dataset
from app.models.images import Image

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

# Definir las relaciones.
User.datasets = Relationship(back_populates="user", cascade_delete=True)

Dataset.user = Relationship(back_populates="datasets")

Dataset.images = Relationship(back_populates="dataset", cascade_delete=True)

Image.dataset = Relationship(back_populates="images")

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
]
