from tensorflow import keras
from keras.applications import ResNet50  # type: ignore[import]
from keras import layers
import tensorflow as tf
import numpy as np


def create_model(input_shape, num_classes):
    """Crea un modelo ResNet50 con transfer learning.

    Args:
        input_shape: Forma de la entrada (alto, ancho, canales).
        num_classes: Número de clases.

    Returns:
        Modelo de Keras sin compilar.
    """

    # Entrada del modelo.
    inputs = keras.Input(shape=input_shape)

    # Modelo base.
    base_model = ResNet50(
        include_top=False, weights="imagenet", input_shape=input_shape, pooling="avg"
    )

    # Congelar todas las capas del modelo base.
    base_model.trainable = False

    # Conectar las capas.
    x = base_model(inputs)
    x = layers.Dropout(0.2)(x)  # Añadir dropout para regularización.

    # Cabeza clasificadora.
    if num_classes == 2:
        outputs = layers.Dense(1, activation="sigmoid")(x)
    else:
        outputs = layers.Dense(num_classes, activation="softmax")(x)

    # Crear y retornar el modelo.
    model = keras.Model(inputs=inputs, outputs=outputs)

    return model


def train(train_ds, val_ds, num_classes, epochs=20, learning_rate=0.001):
    """Entrena el modelo ResNet50 con transfer learning.

    Args:
        train_ds: Dataset de entrenamiento.
        val_ds: Dataset de validación.
        num_classes: Número de clases.
        epochs: Número de épocas para el entrenamiento.
        learning_rate: Tasa de aprendizaje para el optimizador.

    Returns:
        model: Modelo entrenado.
        history: Historial del entrenamiento.
    """

    # Obtener la forma de entrada del primer lote.
    for images, _ in train_ds.take(1):
        input_shape = images.shape[1:]
        break

    # Crear modelo.
    model = create_model(input_shape=input_shape, num_classes=num_classes)

    # Configurar pérdida y métricas.
    if num_classes == 2:
        loss = tf.keras.losses.BinaryCrossentropy(from_logits=False)
        metrics = [tf.keras.metrics.BinaryAccuracy(name="accuracy")]
    else:
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
        metrics = [tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")]

    # Compilar modelo.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate), loss=loss, metrics=metrics
    )

    # Callbacks.
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        ),
    ]

    # Entrenamiento completo.
    history = model.fit(
        train_ds, validation_data=val_ds, epochs=epochs, callbacks=callbacks
    )

    return model, history
