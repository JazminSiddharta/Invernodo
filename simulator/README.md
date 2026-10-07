# simulator (Jhonny)

Simulador de cámaras del invernadero: manda las fotos de `sample_images/` al coordinador (`POST /tasks`) con su `zone_id`.

## Qué hay aquí

- `main.py`: el simulador. Usa `COORDINATOR_URL` de `shared/config.py` (por defecto `http://localhost:8000`).
- `sample_images/`: 50 fotos de tomate (PlantVillage) en `zona-1` a `zona-5`, 10 por zona y 2 por etiqueta. El nombre de la subcarpeta es el `zone_id`.
- `manifest.csv`: lista de esas 50 fotos con zona, etiqueta correcta, carpeta de origen y nombre de archivo.
- `tools/build_sample_images.py`: script que armó `sample_images/` y `manifest.csv` (no hace falta correrlo de nuevo).
- `requirements.txt`: dependencias con versión exacta.

## Cómo correrlo solo (sin la API real)

Desde la raíz del repo, con Python 3.11:

1. Instalar (una vez): `py -3.11 -m pip install -r simulator/requirements.txt`
2. En una terminal, el coordinador falso: `py -3.11 tests/fake_coordinator.py`
3. En otra terminal: `py -3.11 -m simulator.main --intervalo 0.1`

Debe terminar con `Listo: 50 enviadas, 0 fallidas`.

Opciones: `--intervalo` (segundos entre fotos, 0.5 por defecto), `--veces` (pasadas completas) y `--carpeta`.

## Con Docker

```bash
docker compose -f infra/docker-compose.simulator.yml up --build --abort-on-container-exit --exit-code-from simulator
docker compose -f infra/docker-compose.simulator.yml down
```