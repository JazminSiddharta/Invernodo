# tests (Jhonny)

## Coordinador falso

`fake_coordinator.py` imita al coordinador solo en `POST /tasks` y `GET /stats`, para probar el simulador sin la API real.

Desde la raíz del repo: `py -3.11 tests/fake_coordinator.py` (escucha en `http://localhost:8000`).

## Prueba de humo del modelo

`smoke_model.py` carga el modelo real dentro de la imagen del worker (TensorFlow), clasifica las 50 fotos de `simulator/sample_images/`, las compara con `simulator/manifest.csv` y mide los tiempos contra `TASK_TIMEOUT_S`. Resultado: 46/50 (92 %), carga de 14 s en la compu de Jhonny.

Necesita los pesos en `model/weights/` y se corre con `infra/docker-compose.model-smoke.yml` (los comandos están en ese archivo).

## Pruebas de caos (CP3)

`chaos.py` levanta el sistema con Docker (`infra/docker-compose.yml`), manda las 100 fotos y provoca una falla. Hace su propio `down -v`, así que **borra el estado** del coordinador. Desde la raíz del repo, con Docker Desktop abierto:

```bash
py -3.11 tests/chaos.py worker        # mata worker-2 justo cuando tiene una tarea ASSIGNED
py -3.11 tests/chaos.py coordinador   # reinicia el coordinador con 30 tareas hechas
```

Al final imprime líneas `PASA` o `FALLA`: 100 tareas en `DONE`, 0 en `FAILED`, 100 resultados sin duplicados y, según el escenario, que el nodo muerto se detectó y su tarea se reasignó (`attempts >= 2`) o que el coordinador retomó desde SQLite.

Con un solo worker vivo las 100 fotos tardan unos 15 minutos, porque el worker espera 5 s después de cada tarea.
