# tests (Jhonny)

## Coordinador falso

`fake_coordinator.py` imita al coordinador solo en `POST /tasks` y `GET /stats`, para probar el simulador sin la API real.

Desde la raíz del repo: `py -3.11 tests/fake_coordinator.py` (escucha en `http://localhost:8000`).

Mientras corre, `http://localhost:8000/stats` muestra cuántas fotos recibió.

Las pruebas de caos (matar un worker a media carga) llegan en la Fase 3.