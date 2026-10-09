# model/ - Modelo de IA (Abi)

Clasifica fotos de hojas de tomate en 5 etiquetas. Lo usan los nodos trabajadores (`worker/`).

## Estado (Fase 1)

- `inference_real.py`: **classify real** (MobileNetV2 ajustada con PlantVillage). Probado solo, con fotos de prueba.
- `inference.py`: **stub** (devuelve una etiqueta al azar). Es el que usa el worker hasta la Fase 2, cuando se cambia por el real sin modificar la firma de `classify`.

## Cómo usarlo

```python
from model.inference_real import cargar_modelo, classify

cargar_modelo()                    # una sola vez, al arrancar (tarda unos segundos)
resultado = classify(image_bytes)  # bytes de una imagen JPG o PNG
# {"label": "hongo", "confidence": 0.9731}
```

- `label`: una de las etiquetas de `shared/labels.json`.
- `confidence`: número entre 0 y 1.
- Si la imagen no se puede leer, lanza `ValueError` (el worker no debe entregar un Result en ese caso).

## Cómo correrlo (Windows)

1. Python 3.11 y un entorno virtual (fuera del repo):
   ```
   py -3.11 -m venv %USERPROFILE%\venvs\invernodo-model
   %USERPROFILE%\venvs\invernodo-model\Scripts\activate
   ```
2. Instalar dependencias (desde la raíz del repo):
   ```
   pip install -r model/requirements.txt
   ```
3. Bajar los pesos: el modelo **no está en GitHub**. Descarga `modelo_tomate_ft.keras` de Google Drive
   [https://drive.google.com/drive/folders/1x1c4HyULgPNnxX3R3jTyMyeG2bq1xUyO?usp=drive_link] y guárdalo en `model/weights/` (crea la carpeta si no existe).
4. Probarlo con una carpeta de fotos:
   ```
   python model\probar_classify.py CARPETA_CON_FOTOS
   ```
   Si los archivos se llaman `sana__00.JPG`, `hongo__01.JPG`, etc., también marca si acertó.

## Etiquetas (orden exacto de `shared/labels.json`)

`["sana", "hongo", "plaga", "virus", "bacteria"]`

| Etiqueta | Carpetas de PlantVillage (tomate) |
|---|---|
| sana | healthy |
| hongo | early blight, late blight, leaf mold, septoria, target spot |
| plaga | spider mites |
| virus | mosaic virus, yellow leaf curl virus |
| bacteria | bacterial spot |

## Cómo se entrenó

- **Datos:** PlantVillage, versión `raw/color`, solo carpetas de tomate (18,160 fotos), agrupadas en las 5 etiquetas.
- **División:** se apartaron las 50 fotos de `simulator/manifest.csv` (nunca se usan para entrenar); el resto, 80 % entrenamiento (14,488) y 20 % validación (3,622), estratificado por etiqueta, `random_state=42`.
- **Modelo:** MobileNetV2 con pesos de ImageNet, entrada 224x224, reescalado a [-1, 1] dentro del modelo, volteo y rotación como aumento de datos, `Dropout(0.2)` y capa final softmax de 5 salidas.
- **Desbalance:** pesos por clase (`balanced`): sana 2.29, hongo 0.52, plaga 2.17, virus 0.63, bacteria 1.71.
- **Etapa 1:** 5 épocas con la base congelada (Adam 1e-3). Validación: 0.892.
- **Etapa 2 (ajuste fino):** 8 épocas (Adam 1e-5), descongelando la base desde la capa 100 y dejando las BatchNorm congeladas. Mejor época: la 7 (validación 0.974).
- **Entorno:** Google Colab (T4), TensorFlow 2.21.0.

## Resultados

**Validación (3,622 fotos): accuracy 0.974**

| real \ predicho | sana | hongo | plaga | virus | bacteria |
|---|---|---|---|---|---|
| sana | 315 | 1 | 0 | 0 | 0 |
| hongo | 26 | 1351 | 16 | 4 | 8 |
| plaga | 4 | 9 | 317 | 3 | 0 |
| virus | 0 | 9 | 2 | 1131 | 2 |
| bacteria | 0 | 10 | 0 | 0 | 414 |

Recall por etiqueta: sana 0.997, hongo 0.962, plaga 0.952, virus 0.989, bacteria 0.976.
Fotos enfermas clasificadas como sana: 30 de 3,306 (0.9 %).

**Las 50 fotos de la demo (`simulator/manifest.csv`): accuracy 0.920 (46 de 50)**

| real \ predicho | sana | hongo | plaga | virus | bacteria |
|---|---|---|---|---|---|
| sana | 10 | 0 | 0 | 0 | 0 |
| hongo | 0 | 10 | 0 | 0 | 0 |
| plaga | 0 | 0 | 10 | 0 | 0 |
| virus | 0 | 0 | 1 | 9 | 0 |
| bacteria | 0 | 3 | 0 | 0 | 7 |

Errores: 3 fotos de `bacteria` clasificadas como `hongo` (confianza 0.53 a 0.81) y 1 de `virus`
(mosaico) clasificada como `plaga` (confianza 0.96).

**Limitaciones:** son fotos de laboratorio (una hoja, fondo uniforme) y PlantVillage trae fotos muy
parecidas entre sí, por lo que la validación es algo optimista. Con fotos reales de invernadero
el desempeño puede ser menor. Con solo 50 fotos de prueba, cada foto vale 2 puntos porcentuales.
