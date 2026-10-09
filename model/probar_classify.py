"""Prueba suelta del classify real con una carpeta de fotos.

Uso (desde la RAIZ del repo, con el entorno virtual activado):

    py -3.11 model/probar_classify.py prueba10

Si el nombre de la foto empieza con la etiqueta esperada y dos guiones bajos
(ej. sana__00.JPG), tambien marca si acerto.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.inference_real import cargar_modelo, classify  # noqa: E402

EXTENSIONES = {".jpg", ".jpeg", ".png"}


def main():
    if len(sys.argv) < 2:
        print("Uso: py -3.11 model/probar_classify.py CARPETA [maximo_de_fotos]")
        sys.exit(1)
    carpeta = Path(sys.argv[1])
    maximo = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    fotos = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in EXTENSIONES)[:maximo]
    if not fotos:
        print(f"No encontre fotos en {carpeta}")
        sys.exit(1)

    t0 = time.time()
    cargar_modelo()
    print(f"Modelo cargado en {time.time() - t0:.1f} s\n")

    aciertos = con_esperada = 0
    for foto in fotos:
        t0 = time.time()
        r = classify(foto.read_bytes())
        ms = (time.time() - t0) * 1000
        esperada = foto.name.split("__")[0] if "__" in foto.name else None
        marca = ""
        if esperada:
            con_esperada += 1
            if esperada == r["label"]:
                aciertos += 1
                marca = "  OK"
            else:
                marca = f"  (esperada: {esperada})"
        print(f"{foto.name:<22} -> {r['label']:<9} {r['confidence']:.4f}  {ms:5.0f} ms{marca}")

    if con_esperada:
        print(f"\nAciertos: {aciertos}/{con_esperada}")


if __name__ == "__main__":
    main()
