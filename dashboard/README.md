# Dashboard — responsable: JP

Página web (Streamlit) que muestra nodos vivos/caídos, contadores, alertas,
resultados por zona y tareas reasignadas. Lee del coordinador
(`GET /nodes`, `/results`, `/tasks`, `/stats`).

## Cómo correrlo (sin Docker)

Desde la raíz del repo, con Python 3.11 y un entorno virtual activo:

```
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Se abre en http://localhost:8501

## Datos falsos vs. coordinador real

- `USE_FAKE_DATA=1` (por defecto): usa datos inventados de `fake_data.py`.
- `USE_FAKE_DATA=0`: lee del coordinador en `COORDINATOR_URL` (de `shared/config.py`).

En PowerShell:

```
$env:USE_FAKE_DATA="0"
$env:COORDINATOR_URL="http://127.0.0.1:8000"
streamlit run dashboard/app.py
```

En Windows usa `127.0.0.1` y no `localhost`: con `localhost` cada petición tarda ~2 s y la página parpadea.

## Archivos

- `app.py`: la página.
- `data_source.py`: trae los datos (falsos o reales) y los valida con `shared/contracts.py`.
- `fake_data.py`: datos falsos con la forma exacta del contrato (incluye un nodo DEAD y tareas reasignadas).
- `alerts.py`: reglas de alertas. Umbrales arriba del archivo.

## Alertas

- **CRÍTICA**: etiqueta distinta de "sana" con confianza ≥ 90 %.
- **ZONA**: 5 o más detecciones no sanas en la misma zona en los últimos 5 minutos.