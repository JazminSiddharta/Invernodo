# Coordinador (Jazmin)

API que recibe imágenes, las reparte entre nodos, vigila que sigan vivos y guarda los resultados.
Los endpoints están en `shared/API.md`.

## Cómo correrlo (desde la RAÍZ del repo, no desde coordinator/)

1. Usar Python 3.11 y un entorno virtual (fuera de OneDrive si el repo está ahí).
2. Instalar: `pip install -r coordinator/requirements.txt`
3. Prender: `uvicorn coordinator.main:app --reload`
4. Probar en el navegador: http://localhost:8000/docs

Todo se guarda en `coordinator/data/invernodo.db` (no se sube a GitHub). Para empezar de cero: apagar el servidor y borrar ese archivo.

## Tolerancia a fallos (lo hace solo)

- Un nodo sin heartbeat durante 6 s pasa a DEAD. No se borra: si manda un heartbeat, vuelve a ALIVE.
- Una tarea ASSIGNED cuyo nodo murió, o que pasó su plazo de 15 s, vuelve a PENDING.
- Después de 3 intentos la tarea pasa a FAILED y ya no se reparte.
- Un resultado de una tarea que ya estaba DONE se ignora: responde 200 con `"duplicate": true` (gana el primero).
- Todo está en SQLite: el coordinador sobrevive a un reinicio.

## Reglas para los workers

- Mandar un heartbeat cada 2 s, en un hilo aparte (si la inferencia tarda, el heartbeat no se debe detener).
- Terminar cada tarea en menos de 15 s; si no, se reasigna a otro nodo.
- Si el heartbeat responde 404, volver a registrarse.

## Pruebas

Los scripts de `coordinator/` esperan un servidor recién prendido y con la base VACÍA. Para eso, prender con base temporal en memoria (PowerShell):

`$env:INVERNODO_DB=":memory:"; uvicorn coordinator.main:app --reload`

Reiniciar el servidor antes de cada script:

- `python coordinator/test_api.py`: camino feliz (26 pruebas).
- `python coordinator/test_failover.py`: un nodo muere y otro termina su tarea (~10 s).
- `python coordinator/test_failed.py`: una tarea que se cae 3 veces queda FAILED (~30 s).
- `python coordinator/test_persistencia.py crear` y luego `revisar`: este NO usa `:memory:`. Entre `crear` y `revisar` hay que apagar y volver a prender el servidor.