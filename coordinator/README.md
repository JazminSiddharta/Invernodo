# Coordinador (Jazmin)

API que recibe imágenes, las reparte entre nodos y guarda los resultados.
Los endpoints están en `shared/API.md`.

## Cómo correrlo (desde la RAÍZ del repo, no desde coordinator/)

1. Usar Python 3.11 y un entorno virtual (fuera de OneDrive si el repo está ahí).
2. Instalar: `pip install -r coordinator/requirements.txt`
3. Prender: `uvicorn coordinator.main:app --reload`
4. Probar en el navegador: http://localhost:8000/docs

## Probar que todo funciona

Con el servidor recién prendido, en otra terminal:

`python coordinator/test_api.py`

Debe terminar con `TODAS LAS PRUEBAS PASARON`.

## Ojo

- Por ahora todo se guarda en memoria: al reiniciar el servidor se olvida todo.
- El script de pruebas solo se puede correr una vez por cada arranque del servidor.
- Falta (Fase 3): detectar nodos muertos, reasignar tareas, reintentos y guardar en SQLite.