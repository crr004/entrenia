from app.ml.models import xception_mini, resnet50, efficientnetb3

# Diccionario que mapea nombres de arquitecturas a sus módulos.
AVAILABLE_MODELS = {
    "xception_mini": xception_mini,
    "resnet50": resnet50,
    "efficientnetb3": efficientnetb3,
}
