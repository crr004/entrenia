from tensorflow import keras
from keras.applications import EfficientNetB3  # type: ignore[import]
from keras import layers
import tensorflow as tf


def create_model(input_shape, num_classes):
    """Crea un modelo EfficientNetB3 con transfer learning.

    Args:
        input_shape: Forma de la entrada (alto, ancho, canales).
        num_classes: Número de clases.

    Returns:
        Modelo de Keras sin compilar.
    """

    # Cargar modelo base preentrenado con pesos de ImageNet (sin la capa superior).
    base_model = EfficientNetB3(
        include_top=False, weights="imagenet", input_shape=input_shape
    )

    # Congelar el modelo base para el transfer learning.
    base_model.trainable = False

    # Construir el modelo.
    inputs = keras.Input(shape=input_shape)

    # Procesar las entradas a través del modelo base.
    x = base_model(inputs, training=False)

    # Añadir cabeza clasificadora.
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)  # Normalización para estabilizar entrenamiento.
    x = layers.Dropout(0.4)(x)  # Mayor dropout para reducir sobreajuste.

    # Arquitectura de cabeza clasificadora según tipo de clasificación.
    if num_classes == 2:
        # Mayor capacidad expresiva para clasificación binaria.
        x = layers.Dense(128, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(1, activation="sigmoid")(
            x
        )  # Salida binaria con 1 neurona.
    else:
        # Para clasificación multiclase.
        x = layers.Dense(256, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)

    return keras.Model(inputs, outputs)


def train(
    train_ds, val_ds, num_classes, epochs: int = 40, learning_rate: float = 0.001
):
    """Entrena el modelo EfficientNetB3 con transfer learning en dos fases.

    Args:
        train_ds: Dataset de entrenamiento.
        val_ds: Dataset de validación.
        num_classes: Número de clases.
        epochs: Número de épocas de entrenamiento (por defecto más épocas para imágenes médicas).
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

    # Configurar la compilación según el tipo de problema.
    if num_classes == 2:
        if isinstance(model.output_shape, tuple) and model.output_shape[-1] == 1:
            # Clasificación binaria con 1 neurona de salida.
            loss = tf.keras.losses.BinaryCrossentropy(from_logits=False)
            metrics = [
                tf.keras.metrics.BinaryAccuracy(name="accuracy"),
                tf.keras.metrics.AUC(name="auc"),
                tf.keras.metrics.Precision(name="precision"),
                tf.keras.metrics.Recall(name="recall"),
            ]
        else:
            loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
            metrics = [tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")]
    else:
        # Clasificación multiclase.
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
        metrics = [
            tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy"),
            tf.keras.metrics.SparseTopKCategoricalAccuracy(k=2, name="top_2_accuracy"),
        ]

    # Compilar modelo para primera fase (solo cabeza clasificadora).
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate), loss=loss, metrics=metrics
    )

    # Callbacks para el entrenamiento.
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=8, restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.2, patience=4, min_lr=learning_rate / 100
        ),
    ]

    # Entrenar el modelo (fase 1 - solo la cabeza clasificadora).
    history_head = model.fit(
        train_ds,
        epochs=epochs // 2,  # Usar la mitad de las épocas para la primera fase.
        validation_data=val_ds,
        callbacks=callbacks,
    )

    # Encontrar la capa que contiene el modelo base (EfficientNetB3).
    base_model = None
    for layer in model.layers:
        if isinstance(
            layer, keras.Model
        ):  # El modelo base es un modelo dentro del modelo principal.
            base_model = layer
            break

    if base_model is None:
        print("Base model not found.")
        return model, history_head

    base_model.trainable = True

    # Congelar bloques iniciales, dejar entrenar los últimos 30.
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    # Learning rate más bajo para fine-tuning.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate / 20),
        loss=loss,
        metrics=metrics,
    )

    # Entrenar con fine-tuning.
    try:
        history_full = model.fit(
            train_ds,
            epochs=epochs // 2,  # Usar la otra mitad de las épocas para fine-tuning.
            initial_epoch=history_head.epoch[-1] + 1,
            validation_data=val_ds,
            callbacks=callbacks,
        )

        # Combinar historiales.
        combined_history = {}
        for key in history_head.history.keys():
            if key in history_full.history:
                combined_history[key] = (
                    history_head.history[key] + history_full.history[key]
                )
            else:
                combined_history[key] = history_head.history[key]

        # Añadir cualquier métrica adicional que solo esté en history_full.
        for key in history_full.history.keys():
            if key not in combined_history:
                combined_history[key] = history_full.history[key]

    except Exception as e:
        # Si hay un error en la segunda fase, devolver solo la primera fase.
        print(f"Error en fine-tuning: {str(e)}. Devolviendo modelo de primera fase.")
        return model, history_head

    # Crear un objeto History para mayor claridad.
    history = keras.callbacks.History()
    history.set_model(model)
    history.history = combined_history

    return model, history
