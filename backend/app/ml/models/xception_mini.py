from tensorflow import keras
from keras import layers
import tensorflow as tf


def create_model(input_shape, num_classes):
    """Crea una versión reducida del modelo Xception.

    Args:
        input_shape: Forma de la entrada (alto, ancho, canales).
        num_classes: Número de clases.

    Returns:
        Modelo de Keras sin compilar.
    """

    inputs = keras.Input(shape=input_shape)

    # Capa de entrada.
    x = layers.Rescaling(1.0 / 255)(inputs)
    x = layers.Conv2D(128, 3, strides=2, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    previous_block_activation = x  # Guardar la activación para la proyección residual.

    for size in [256, 512, 728]:
        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(size, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.Activation("relu")(x)
        x = layers.SeparableConv2D(size, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)

        x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

        # Proyección residual.
        residual = layers.Conv2D(size, 1, strides=2, padding="same")(
            previous_block_activation
        )
        x = layers.add([x, residual])  # Suma de la proyección residual.
        previous_block_activation = (
            x  # Guardar la activación para la proyección residual.
        )

    x = layers.SeparableConv2D(1024, 3, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.25)(x)

    # Capa de salida.
    if num_classes == 2:
        outputs = layers.Dense(1, activation="sigmoid")(x)
    else:
        outputs = layers.Dense(num_classes, activation="softmax")(x)

    return keras.Model(inputs, outputs)


def train(
    train_ds, val_ds, num_classes, epochs: int = 20, learning_rate: float = 0.001
):
    """Entrena el modelo Xception Mini con parámetros personalizables.

    Args:
        train_ds: Dataset de entrenamiento.
        val_ds: Dataset de validación.
        num_classes: Número de clases.
        epochs: Número de épocas de entrenamiento.
        learning_rate: Tasa de aprendizaje para el optimizador.

    Returns:
        modelo entrenado, historial de entrenamiento.
    """

    # Obtener la forma de entrada de las imágenes del primer lote.
    for images, _ in train_ds.take(1):
        input_shape = images[0].shape
        break

    # Crear modelo.
    model = create_model(input_shape=input_shape, num_classes=num_classes)

    # Crear optimizador.
    optimizer = tf.keras.optimizers.Adam(learning_rate)

    # Compilar modelo.
    # Usar BinaryCrossentropy para clasificación binaria y SparseCategoricalCrossentropy para multiclase.
    if num_classes == 2:
        loss = tf.keras.losses.BinaryCrossentropy(from_logits=False)
        metrics = [tf.keras.metrics.BinaryAccuracy(name="accuracy")]
    else:
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
        metrics = [tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")]

    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    # Entrenar el modelo.

    # Usar EarlyStopping para evitar el sobreajuste.
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        ),
    ]

    history = model.fit(
        train_ds, epochs=epochs, validation_data=val_ds, callbacks=callbacks
    )

    return model, history
