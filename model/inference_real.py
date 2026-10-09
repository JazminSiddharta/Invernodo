"""classify REAL (Fase 1, Abi): MobileNetV2 ajustada con hojas de tomate de PlantVillage.

Misma firma que el stub de inference.py:

    classify(image_bytes) -> {"label": "hongo", "confidence": 0.9731}

- Las etiquetas salen de shared/labels.json (el modelo devuelve un indice y
  aqui se traduce a texto con esa misma lista, en el mismo orden).
- El modelo se carga UNA sola vez. Para que la primera foto no tarde de mas
  (TASK_TIMEOUT_S = 15), conviene llamar cargar_modelo() al arrancar el worker.
- Si la imagen no se puede leer, lanza ValueError (el worker no debe entregar
  un Result en ese caso).
- Los pesos NO estan en GitHub: se bajan de Google Drive a model/weights/
  (ver model/README.md).
"""
import json
import os
import threading
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # menos mensajes de TensorFlow

IMG_SIZE = 224
_RAIZ = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("MODEL_PATH", _RAIZ / "weights" / "modelo_tomate_ft.keras"))
LABELS_PATH = Path(os.environ.get("LABELS_PATH", _RAIZ.parent / "shared" / "labels.json"))

_modelo = None
_etiquetas = None
_lock = threading.Lock()


def cargar_modelo():
    """Carga el modelo y las etiquetas una sola vez (las llamadas siguientes no hacen nada)."""
    global _modelo, _etiquetas
    with _lock:
        if _modelo is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Falta el modelo en {MODEL_PATH}. Bajalo de Google Drive "
                    "(carpeta invernodo-modelo) y guardalo en model/weights/."
                )
            import tensorflow as tf  # aqui dentro para que importar este archivo sea rapido
            from tensorflow import keras

            with open(LABELS_PATH, encoding="utf-8") as f:
                etiquetas = json.load(f)
            modelo = keras.models.load_model(MODEL_PATH, compile=False)
            if modelo.output_shape[-1] != len(etiquetas):
                raise ValueError(
                    f"El modelo tiene {modelo.output_shape[-1]} salidas pero "
                    f"labels.json tiene {len(etiquetas)} etiquetas."
                )
            modelo(tf.zeros((1, IMG_SIZE, IMG_SIZE, 3)), training=False)  # calentamiento
            _etiquetas = etiquetas
            _modelo = modelo
    return _modelo


def classify(image_bytes: bytes) -> dict:
    import tensorflow as tf

    cargar_modelo()
    try:
        img = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    except tf.errors.InvalidArgumentError as e:
        raise ValueError("No se pudo leer la imagen (bytes invalidos).") from e
    # Mismo preprocesamiento que en el entrenamiento: pixeles 0-255 a 224x224.
    # (El reescalado a [-1, 1] ya va dentro del modelo.)
    img = tf.image.resize(img, (IMG_SIZE, IMG_SIZE))
    with _lock:
        probs = _modelo(tf.expand_dims(img, 0), training=False).numpy()[0]
    idx = int(probs.argmax())
    return {"label": _etiquetas[idx], "confidence": round(float(probs[idx]), 4)}
