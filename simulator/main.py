"""Simulador de cámaras: manda las fotos de sample_images/ al coordinador.

Uso (desde la raíz del repo):
  py -3.11 -m simulator.main                          # una pasada, 0.5 s entre fotos
  py -3.11 -m simulator.main --intervalo 0.1 --veces 2
"""
import argparse
import random
import sys
import time
from pathlib import Path

import requests

from shared.config import COORDINATOR_URL

CARPETA_FOTOS = Path(__file__).resolve().parent / "sample_images"
INTENTOS = 5            # intentos por foto si el coordinador no responde
ESPERA_REINTENTO_S = 2
TIMEOUT_S = 10


def listar_fotos(carpeta):
    """Devuelve [(zone_id, ruta)], donde zone_id es el nombre de la subcarpeta."""
    fotos = []
    for zona in sorted(p for p in carpeta.iterdir() if p.is_dir()):
        for foto in sorted(zona.iterdir()):
            if foto.suffix.lower() in (".jpg", ".jpeg"):
                fotos.append((zona.name, foto))
    return fotos


def enviar(zona, foto):
    """Manda una foto a POST /tasks. Devuelve el task_id, o None si no se pudo."""
    for intento in range(1, INTENTOS + 1):
        try:
            with foto.open("rb") as f:
                r = requests.post(
                    f"{COORDINATOR_URL}/tasks",
                    files={"file": (foto.name, f, "image/jpeg")},
                    data={"zone_id": zona},
                    timeout=TIMEOUT_S,
                )
            r.raise_for_status()
            return r.json()["task_id"]
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"  intento {intento}/{INTENTOS} fallo: {e}")
            time.sleep(ESPERA_REINTENTO_S)
    return None


def main():
    parser = argparse.ArgumentParser(description="Simulador de cámaras de Invernodo")
    parser.add_argument("--intervalo", type=float, default=0.5, help="segundos entre fotos")
    parser.add_argument("--veces", type=int, default=1, help="cuántas pasadas completas")
    parser.add_argument("--carpeta", type=Path, default=CARPETA_FOTOS)
    args = parser.parse_args()

    fotos = listar_fotos(args.carpeta)
    if not fotos:
        sys.exit(f"No hay fotos en {args.carpeta}")
    print(f"Coordinador: {COORDINATOR_URL} | fotos: {len(fotos)} | pasadas: {args.veces}")

    enviadas, fallidas = 0, 0
    for _ in range(args.veces):
        random.shuffle(fotos)
        for zona, foto in fotos:
            task_id = enviar(zona, foto)
            if task_id:
                enviadas += 1
                print(f"[{enviadas}] {zona} {foto.name} -> {task_id}")
            else:
                fallidas += 1
                print(f"FALLO {zona} {foto.name}")
            time.sleep(args.intervalo)

    print(f"Listo: {enviadas} enviadas, {fallidas} fallidas")
    sys.exit(1 if fallidas else 0)


if __name__ == "__main__":
    main()
