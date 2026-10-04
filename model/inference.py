"""Stub de classify() - Fase 0 (Abi).

Devuelve una etiqueta al azar para que el worker (Angie) pueda trabajar
sin esperar el modelo real. Tiene la MISMA firma que tendra la version real:

    classify(image_bytes) -> {"label": "plaga", "confidence": 0.93}

En Fase 2 este archivo se reemplaza por el modelo real SIN cambiar la firma.
Solo usa la libreria estandar de Python (no hace falta instalar nada).
"""
import json
import os
import random
import sys
from pathlib import Path

# Las etiquetas viven en shared/labels.json (carpeta compartida, no se edita aqui).
_DEFAULT_LABELS_PATH = Path(__file__).resolve().parent.parent / "shared" / "labels.json"

# Solo se usa si shared/labels.json todavia no existe (antes de que Jazmin lo suba).
_TEMP_LABELS = ["sana", "plaga", "hongo", "deficiencia"]

_labels_cache = None


def _get_labels():
    global _labels_cache
    if _labels_cache is None:
        path = Path(os.environ.get("LABELS_PATH", _DEFAULT_LABELS_PATH))
        try:
            with open(path, encoding="utf-8") as f:
                _labels_cache = json.load(f)
        except FileNotFoundError:
            print(
                f"[inference stub] AVISO: no encontre {path}; uso etiquetas temporales.",
                file=sys.stderr,
            )
            _labels_cache = _TEMP_LABELS
    return _labels_cache


def classify(image_bytes: bytes) -> dict:
    """Stub: ignora la imagen y devuelve una etiqueta al azar."""
    label = random.choice(_get_labels())
    confidence = round(random.uniform(0.5, 0.99), 2)
    return {"label": label, "confidence": confidence}


if __name__ == "__main__":
    # Prueba rapida:  python model/inference.py
    print(classify(b"imagen-falsa"))
