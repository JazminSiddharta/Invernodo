"""Arma simulator/sample_images/ (50 fotos de tomate de PlantVillage) y simulator/manifest.csv.

Uso (desde la raíz del repo):
  py -3.11 simulator/tools/build_sample_images.py "<ruta a la carpeta color>"
"""
import csv
import json
import random
import shutil
import sys
from pathlib import Path

ZONAS = 5
POR_ETIQUETA = 10  # 10 fotos x 5 etiquetas = 50
SEED = 42          # mismo resultado cada vez que se corre

# palabra clave en el nombre de la carpeta -> etiqueta de shared/labels.json
REGLAS = [
    ("healthy", "sana"),
    ("early_blight", "hongo"),
    ("late_blight", "hongo"),
    ("leaf_mold", "hongo"),
    ("septoria", "hongo"),
    ("target_spot", "hongo"),
    ("spider", "plaga"),
    ("mosaic", "virus"),
    ("yellow_leaf_curl", "virus"),
    ("bacterial", "bacteria"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit('Uso: py -3.11 simulator/tools/build_sample_images.py "<ruta a la carpeta color>"')
    color = Path(sys.argv[1])
    repo = Path(__file__).resolve().parents[2]
    destino = repo / "simulator" / "sample_images"
    manifest = repo / "simulator" / "manifest.csv"
    etiquetas = json.loads((repo / "shared" / "labels.json").read_text(encoding="utf-8"))

    if destino.exists():
        sys.exit(f"{destino} ya existe. Muévela o bórrala y vuelve a correr.")

    # 1. Agrupar las carpetas de tomate por etiqueta
    por_etiqueta = {e: [] for e in etiquetas}
    for carpeta in sorted(p for p in color.iterdir() if p.is_dir() and p.name.lower().startswith("tomato___")):
        nombre = carpeta.name.lower()
        etiqueta = next((e for clave, e in REGLAS if clave in nombre), None)
        if etiqueta is None:
            sys.exit(f"Carpeta sin regla: {carpeta.name}")
        if etiqueta not in por_etiqueta:
            sys.exit(f"La etiqueta '{etiqueta}' no está en shared/labels.json")
        por_etiqueta[etiqueta].append(carpeta)
    for etiqueta, carpetas in por_etiqueta.items():
        if not carpetas:
            sys.exit(f"No encontré carpetas para la etiqueta '{etiqueta}'")

    # 2. Elegir 10 fotos por etiqueta, repartidas entre sus carpetas
    rng = random.Random(SEED)
    elegidas = {}
    for etiqueta, carpetas in por_etiqueta.items():
        base, resto = divmod(POR_ETIQUETA, len(carpetas))
        lista = []
        for i, carpeta in enumerate(carpetas):
            cuantas = base + (1 if i < resto else 0)
            archivos = sorted(f.name for f in carpeta.iterdir() if f.suffix.lower() in (".jpg", ".jpeg"))
            for archivo in rng.sample(archivos, cuantas):
                lista.append((carpeta, archivo))
        rng.shuffle(lista)
        elegidas[etiqueta] = lista

    # 3. Repartir en zonas y copiar
    por_zona = POR_ETIQUETA // ZONAS
    filas = []
    for z in range(ZONAS):
        zona = f"zona-{z + 1}"
        (destino / zona).mkdir(parents=True)
        for etiqueta, lista in elegidas.items():
            for carpeta, archivo in lista[z * por_zona:(z + 1) * por_zona]:
                final = destino / zona / archivo
                if final.exists():
                    sys.exit(f"Nombre repetido: {archivo}")
                shutil.copy2(carpeta / archivo, final)
                filas.append((zona, etiqueta, carpeta.name, archivo))

    # 4. Lista de lo que se eligió (para Abi y para las pruebas)
    with manifest.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["zone_id", "label", "carpeta_origen", "archivo"])
        escritor.writerows(filas)
    print(f"Listo: {len(filas)} fotos en {destino}")


main()
