"""Prueba de humo del modelo real dentro de Docker.

Carga el modelo (pesos montados en model/weights/), clasifica las 50 fotos de la demo
y compara con simulator/manifest.csv. Mide el tiempo de carga y el de la primera foto
contra TASK_TIMEOUT_S (shared/config.py).
Uso: ver infra/docker-compose.model-smoke.yml
"""
import csv
import sys
import time
from pathlib import Path

from shared.config import TASK_TIMEOUT_S
from model.inference_real import cargar_modelo, classify

RAIZ = Path(__file__).resolve().parents[1]
MANIFEST = RAIZ / "simulator" / "manifest.csv"
FOTOS = RAIZ / "simulator" / "sample_images"


def main():
    inicio = time.perf_counter()
    cargar_modelo()
    t_carga = time.perf_counter() - inicio
    print(f"Carga del modelo: {t_carga:.1f} s")

    with MANIFEST.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    aciertos, errores, tiempos = 0, 0, []
    for i, fila in enumerate(filas):
        ruta = FOTOS / fila["zone_id"] / fila["archivo"]
        t0 = time.perf_counter()
        try:
            resultado = classify(ruta.read_bytes())
        except ValueError as e:
            errores += 1
            print(f"ERROR {ruta.name}: {e}")
            continue
        dt = time.perf_counter() - t0
        tiempos.append(dt)
        if i == 0:
            print(f"Primera foto: {dt:.2f} s")
        if resultado["label"] == fila["label"]:
            aciertos += 1

    total = len(filas)
    print(f"Aciertos: {aciertos}/{total} ({aciertos / total:.1%}), errores: {errores}")
    if tiempos:
        print(f"Tiempo por foto: promedio {sum(tiempos) / len(tiempos) * 1000:.0f} ms, máximo {max(tiempos) * 1000:.0f} ms")
    print(f"Carga + primera foto: {t_carga + tiempos[0]:.1f} s (TASK_TIMEOUT_S = {TASK_TIMEOUT_S} s)")
    sys.exit(1 if errores else 0)


main()
