# model/ - Modelo de IA (Abi)

Clasifica fotos de hojas de plantas. Lo usan los nodos trabajadores (`worker/`).

## Estado actual (Fase 0)

`inference.py` es un **stub**: devuelve una etiqueta al azar. Sirve para que el
worker pueda desarrollarse sin esperar el modelo real. La version real
(Fase 1-2) mantiene exactamente la misma funcion.

## Como usarlo

```python
from model.inference import classify

resultado = classify(image_bytes)
# {"label": "plaga", "confidence": 0.93}
```

- `image_bytes`: contenido de la imagen en bytes.
- `label`: una de las etiquetas de `shared/labels.json`.
- `confidence`: numero entre 0 y 1.

## Probarlo rapido

Desde la raiz del repo:

```
python model/inference.py
```

Debe imprimir una etiqueta y una confianza al azar. No requiere instalar nada.

## Notas

- Las etiquetas viven en `shared/labels.json` (no se editan desde aqui).
- Los pesos del modelo real NO se suben a GitHub; se comparten por Google Drive
  y se guardan en `model/weights/`.
- Framework del modelo real: por definir (se avisa al grupo).
