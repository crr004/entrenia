import os
import json
from typing import Dict, Any

from tensorflow import keras


def save_trained_model(
    model, models_dir: str, metadata: Dict[str, Any], classifier_id: str
) -> str:
    """Guarda un modelo entrenado.

    Args:
        model: Modelo entrenado de TensorFlow/Keras.
        models_dir: Directorio donde guardar los modelos.
        metadata: Metadatos del modelo (clases, métricas, etc.).
        classifier_id: ID del clasificador (para usar como nombre del directorio).

    Returns:
        str: Ruta relativa donde se guardó el modelo.
    """

    model_dir = os.path.join(models_dir, classifier_id)
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "model.keras")
    model.save(model_path)

    # Guardar metadatos en formato JSON.
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Ruta relativa desde el directorio de medios.
    relative_path = os.path.join("models", classifier_id)

    return relative_path


def load_model(model_path: str):
    """Carga un modelo guardado.

    Args:
        model_path: Ruta al modelo guardado.

    Returns:
        Modelo cargado.
    """

    return keras.models.load_model(model_path)


def load_model_metadata(model_dir: str) -> Dict[str, Any]:
    """Carga los metadatos de un modelo.

    Args:
        model_dir: Directorio donde está guardado el modelo.

    Returns:
        Dict: Metadatos del modelo.
    """

    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, "r") as f:
        return json.load(f)
