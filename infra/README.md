# infra (Jhonny)

Docker para levantar el sistema Invernodo con un solo comando.

## Qué hay aquí

- `Dockerfile.python`: receta base con Python 3.11 para todos los servicios. Copia `shared/`, `model/` y la carpeta del servicio. TensorFlow se instala solo en los workers (`EXTRA_REQUIREMENTS`).
- `Dockerfile.python.dockerignore`: deja fuera los pesos y las imágenes locales del coordinador.
- `docker-compose.yml`: el sistema completo: `coordinator` (puerto 8000), `worker-1`, `worker-2`, `dashboard` (puerto 8501, Streamlit) y `simulator` (manda 100 fotos y termina).
- `docker-compose.simulator.yml`: prueba del simulador solo, con el coordinador falso de `tests/`.
- `docker-compose.model-smoke.yml`: prueba de humo del modelo real dentro de Docker.

## Requisitos

- Docker Desktop instalado y abierto (abajo a la izquierda debe decir "Engine running").
- Los pesos `modelo_tomate_ft.keras` en `model/weights/` (se bajan de Google Drive, ver `model/README.md`; no van en Git). Si están en otra carpeta: `set WEIGHTS_DIR=C:\ruta\a\weights` antes de correr.

## Cómo correrlo

Desde la raíz del repo (la carpeta `Invernodo`):

```bash
docker compose -f infra/docker-compose.yml up --build
```

Orden de arranque: el coordinador (listo cuando responde `GET /stats`), luego los workers (cargan el modelo y se registran), el dashboard y el simulador, que manda 100 fotos y termina. Los demás servicios siguen corriendo.

- Dashboard: http://localhost:8501
- Coordinador: http://localhost:8000/stats (cuando `done` llega a 100, ya se procesaron todas)

## Cómo apagarlo

1. En la terminal, presiona `Ctrl + C`.
2. Luego:

```bash
docker compose -f infra/docker-compose.yml down
```

Si un worker sale con código 137, a Docker le falta memoria: en Docker Desktop > Settings > Resources sube la memoria asignada.

## Variables de entorno

| Servicio | Variable | Valor |
|---|---|---|
| worker-1 | `NODE_ID` | `nodo-1` |
| worker-2 | `NODE_ID` | `nodo-2` |
| worker-1, worker-2, simulator, dashboard | `COORDINATOR_URL` | `http://coordinator:8000` |
| dashboard | `USE_FAKE_DATA` | `0` (lee del coordinador real) |

Las constantes (tiempos, reintentos) viven solo en `shared/config.py`.