"""Prueba de caos del CP3 (Fase 3).

Escenario "worker": mata worker-2 justo cuando tiene una tarea ASSIGNED y verifica que las
100 terminen en DONE (la tarea del worker muerto se reasigna: attempts >= 2).
Escenario "coordinador": reinicia el coordinador a media carga y verifica que retome desde SQLite.

Uso (desde la raíz del repo, con Docker Desktop abierto). Empieza con "down -v": borra el estado.
  py -3.11 tests/chaos.py worker
  py -3.11 tests/chaos.py coordinador
"""
import json
import subprocess
import sys
import time
import urllib.request
from collections import Counter

BASE = "http://localhost:8000"
COMPOSE = ["docker", "compose", "-f", "infra/docker-compose.yml"]
TOTAL = 100
LIMITE_S = 2400  # tiempo máximo para que las 100 queden listas


def compose(*args, capture=False):
    return subprocess.run(COMPOSE + list(args), check=True, text=True, capture_output=capture)


def get(ruta):
    with urllib.request.urlopen(BASE + ruta, timeout=5) as r:
        return json.load(r)


def esperar(condicion, descripcion, limite_s, cada_s=1.0):
    inicio = time.time()
    while time.time() - inicio < limite_s:
        try:
            valor = condicion()
            if valor:
                return valor
        except Exception:
            pass  # el coordinador puede estar arrancando o reiniciándose
        time.sleep(cada_s)
    sys.exit(f"FALLO: se agotó el tiempo esperando {descripcion}")


def preparar():
    print("Limpiando (down -v) y levantando coordinador y 2 workers...")
    compose("down", "-v")
    compose("up", "-d", "coordinator", "worker-1", "worker-2")
    esperar(lambda: get("/stats"), "al coordinador", 120)
    esperar(lambda: get("/stats")["nodes_alive"] == 2, "a que los 2 workers se registren", 300)
    print("Mandando las 100 fotos (simulador)...")
    salida = compose("run", "--rm", "simulator", capture=True).stdout.strip().splitlines()
    print(salida[-1] if salida else "(sin salida del simulador)")


def escenario_worker():
    print("Esperando que worker-2 tenga una tarea ASSIGNED para matarlo en ese instante...")

    def tarea_en_curso():
        for t in get("/tasks"):
            if t["status"] == "ASSIGNED" and t.get("assigned_to") == "nodo-2":
                return t["task_id"]

    victima = esperar(tarea_en_curso, "una tarea asignada a nodo-2", 180, cada_s=0.1)
    compose("kill", "worker-2")
    print(f"worker-2 muerto con la tarea {victima} en curso")
    return {"victima": victima}


def escenario_coordinador():
    esperar(lambda: get("/stats")["done"] >= 30, "30 tareas listas", 600, cada_s=2)
    antes = get("/stats")
    print(f"Reiniciando el coordinador (done={antes['done']})...")
    compose("restart", "coordinator")
    esperar(lambda: get("/stats"), "a que el coordinador vuelva", 120)
    despues = get("/stats")
    print(f"Tras el reinicio: total_tasks={despues['total_tasks']}, done={despues['done']}")
    return {"retomo": despues["total_tasks"] == TOTAL and despues["done"] >= antes["done"]}


def terminar(escenario, datos, inicio):
    print("Esperando a que las 100 queden en DONE...")
    ultimo = 0
    while time.time() - inicio < LIMITE_S:
        try:
            s = get("/stats")
        except Exception:
            time.sleep(2)
            continue
        if time.time() - ultimo > 10:
            print(f"  done={s['done']} asignadas={s['assigned']} pendientes={s['pending']} "
                  f"failed={s['failed']} vivos={s['nodes_alive']} muertos={s['nodes_dead']}")
            ultimo = time.time()
        if s["done"] >= TOTAL or s["failed"] > 0:
            break
        time.sleep(1)

    stats, tareas, resultados = get("/stats"), get("/tasks"), get("/results")
    estados = Counter(t["status"] for t in tareas)
    intentos = Counter(t["attempts"] for t in tareas)
    unicos = len({r["task_id"] for r in resultados})
    checks = {
        f"{TOTAL} tareas en DONE": estados == {"DONE": TOTAL},
        "0 tareas FAILED": stats["failed"] == 0,
        f"{TOTAL} resultados sin duplicados": len(resultados) == TOTAL and unicos == TOTAL,
    }
    if escenario == "worker":
        victima = next((t for t in tareas if t["task_id"] == datos["victima"]), None)
        checks["worker-2 detectado como DEAD"] = stats["nodes_dead"] >= 1
        checks["la tarea del worker muerto se reasignó (attempts >= 2)"] = bool(victima) and victima["attempts"] >= 2
    else:
        checks["retomó tras reiniciar el coordinador"] = datos["retomo"]

    print(f"\nTiempo total: {time.time() - inicio:.0f} s | estados: {dict(estados)} | intentos: {dict(intentos)}")
    for nombre, ok in checks.items():
        print(("PASA  " if ok else "FALLA ") + nombre)
    if escenario == "worker" and not checks["la tarea del worker muerto se reasignó (attempts >= 2)"]:
        print("Si solo falla la reasignación, worker-2 alcanzó a terminar su tarea antes de morir: corre el script otra vez.")
    sys.exit(0 if all(checks.values()) else 1)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("worker", "coordinador"):
        sys.exit("Uso: py -3.11 tests/chaos.py worker|coordinador")
    escenario = sys.argv[1]
    inicio = time.time()
    preparar()
    datos = escenario_worker() if escenario == "worker" else escenario_coordinador()
    terminar(escenario, datos, inicio)


main()