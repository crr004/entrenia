import os
import numpy as np
from typing import List, Dict, Tuple, Any

import tensorflow as tf
from tensorflow import keras

AUTOTUNE = tf.data.AUTOTUNE


def prepare_dataset(
    image_paths: List[str],
    labels: List[str],
    label_to_index: Dict[str, int],
    batch_size: int,
    image_size: Tuple[int, int],
    validation_split: float = 0.2,
    seed: int = 42,
) -> Tuple[tf.data.Dataset, tf.data.Dataset, Dict[str, Any]]:
    """Prepara datasets de entrenamiento y validación a partir de rutas de imágenes.

    Args:
        image_paths: Lista de rutas a las imágenes.
        labels: Lista de etiquetas correspondientes.
        label_to_index: Mapeo de etiquetas a índices.
        batch_size: Tamaño del lote para entrenamiento.
        image_size: Tamaño al que redimensionar las imágenes (ancho, alto).
        validation_split: Proporción de datos para validación.
        seed: Semilla para reproducibilidad.

    Returns:
        train_ds: Dataset de entrenamiento.
        val_ds: Dataset de validación.
        dataset_info: Información sobre el dataset.
    """

    # Convertir etiquetas a índices numéricos.
    numeric_labels = np.array([label_to_index[label] for label in labels])

    # Calcular número de clases.
    num_classes = len(label_to_index)

    # Dividir en conjuntos de entrenamiento y validación.
    indices = np.arange(len(image_paths))
    np.random.seed(seed)
    np.random.shuffle(indices)

    val_size = int(validation_split * len(indices))
    train_indices = indices[val_size:]
    val_indices = indices[:val_size]

    train_paths = [image_paths[i] for i in train_indices]
    train_labels = [numeric_labels[i] for i in train_indices]
    val_paths = [image_paths[i] for i in val_indices]
    val_labels = [numeric_labels[i] for i in val_indices]

    # Crear datasets de TensorFlow.
    train_ds = create_dataset(train_paths, train_labels, image_size)
    val_ds = create_dataset(val_paths, val_labels, image_size)

    # Aplicar aumentación de datos al conjunto de entrenamiento.
    train_ds = apply_data_augmentation(train_ds)

    # Optimizar rendimiento de los datasets.
    train_ds = train_ds.batch(batch_size).prefetch(AUTOTUNE)
    val_ds = val_ds.batch(batch_size).prefetch(AUTOTUNE)

    # Información del dataset.
    dataset_info = {
        "num_classes": num_classes,
        "is_binary": num_classes == 2,
        "train_size": len(train_paths),
        "val_size": len(val_paths),
        "class_mapping": {str(idx): label for label, idx in label_to_index.items()},
    }

    return train_ds, val_ds, dataset_info


def create_dataset(
    image_paths: List[str], labels: List[int], image_size: Tuple[int, int]
) -> tf.data.Dataset:
    """Crea un dataset de TensorFlow a partir de rutas de imágenes y etiquetas.

    Args:
        image_paths: Lista de rutas a las imágenes.
        labels: Lista de etiquetas numéricas.
        image_size: Dimensiones a las que redimensionar las imágenes (ancho, alto).

    Returns:
        Dataset de TensorFlow.
    """

    # Crear tensor con las rutas.
    paths_ds = tf.data.Dataset.from_tensor_slices(
        tf.constant(image_paths, dtype=tf.string)
    )

    def load_and_preprocess_with_size(path):
        return load_and_preprocess_image(path, image_size)

    # Mapear función de carga y preprocesamiento.
    images_ds = paths_ds.map(load_and_preprocess_with_size, num_parallel_calls=AUTOTUNE)

    # Crear tensor con las etiquetas.
    labels_ds = tf.data.Dataset.from_tensor_slices(labels)

    # Combinar imágenes y etiquetas.
    return tf.data.Dataset.zip((images_ds, labels_ds))


def load_and_preprocess_image(path, image_size: Tuple[int, int]):
    """Carga y preprocesa una imagen desde su ruta.

    Args:
        path: Ruta de la imagen.
        image_size: Dimensiones a las que redimensionar la imagen (ancho, alto).

    Returns:
        Imagen preprocesada como tensor.
    """

    img = tf.io.read_file(path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, image_size)
    img = tf.cast(img, tf.float32) / 255.0  # Normalización.
    return img


def apply_data_augmentation(dataset):
    """Aplica aumentación de datos al dataset de entrenamiento.

    Args:
        dataset: Dataset de TensorFlow.

    Returns:
        Dataset aumentado.
    """

    # Definir capas de aumentación de datos.
    data_augmentation = keras.Sequential(
        [
            keras.layers.RandomFlip("horizontal"),
            keras.layers.RandomRotation(0.2),
            keras.layers.RandomZoom(0.2),
        ]
    )

    # Función para aplicar aumentación.
    def apply_augmentation(image, label):
        image = data_augmentation(image, training=True)
        return image, label

    return dataset.map(apply_augmentation, num_parallel_calls=AUTOTUNE)


def extract_dataset_from_db(images, media_root):
    """Extrae datos de imágenes desde objetos de base de datos.

    Args:
        images: Lista de objetos Image de la base de datos.
        media_root: Directorio raíz para archivos multimedia.

    Returns:
        image_paths: Lista de rutas a las imágenes.
        labels: Lista de etiquetas.
        label_to_index: Diccionario de mapeo de etiquetas a índices.
        index_to_label: Diccionario de mapeo de índices a etiquetas.
    """

    # Filtrar imágenes con etiqueta.
    labeled_images = [img for img in images if img.label is not None]

    if not labeled_images:
        raise ValueError("No hay imágenes etiquetadas para entrenar.")

    # Extraer rutas y etiquetas.
    image_paths = []
    labels = []

    for img in labeled_images:
        file_path = os.path.join(media_root, img.file_path)
        if os.path.exists(file_path):
            image_paths.append(file_path)
            labels.append(img.label)

    if not image_paths:
        raise ValueError("No se puede acceder a ninguna imagen etiquetada.")

    # Crear mapeo de etiquetas a índices.
    unique_labels = sorted(set(labels))
    label_to_index = {label: i for i, label in enumerate(unique_labels)}
    index_to_label = {i: label for label, i in label_to_index.items()}

    return image_paths, labels, label_to_index, index_to_label
