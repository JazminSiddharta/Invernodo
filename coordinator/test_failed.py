import sys
import time

import requests

BASE = "http://127.0.0.1:8000"


def check(nombre, condicion):
    if condicion:
        print("OK     " + nombre)
    else:
        print("FALLO  " + nombre)
        sys.exit(1)


def buscar_tarea(task_id):
    for t in requests.get(BASE + "/tasks").json():
        if t["task_id"] == task_id:
            return t


r = requests.post(
    BASE + "/tasks",
    files={"file": ("f.jpg", b"imagen-venenosa", "image/jpeg")},
    data={"zone_id": "zona-v"},
)
task_id = r.json()["task_id"]

# Tres nodos toman la misma tarea y ninguno la termina (se mueren)
for i, nodo in enumerate(["nodo-1", "nodo-2", "nodo-3"], start=1):
    requests.post(BASE + "/nodes/register", json={"node_id": nodo})
    r = requests.post(BASE + "/tasks/claim", json={"node_id": nodo})
    check(nodo + " toma la tarea (intento " + str(i) + ")",
          r.status_code == 200 and r.json()["attempts"] == i)
    print("Esperando 9 segundos sin heartbeat de " + nodo + "...")
    time.sleep(9)

t = buscar_tarea(task_id)
check("la tarea quedo FAILED", t["status"] == "FAILED")
check("attempts es 3", t["attempts"] == 3)

requests.post(BASE + "/nodes/register", json={"node_id": "nodo-4"})
r = requests.post(BASE + "/tasks/claim", json={"node_id": "nodo-4"})
check("una tarea FAILED ya no se reparte", r.status_code == 204)

stats = requests.get(BASE + "/stats").json()
check("stats: failed es 1", stats["failed"] == 1)

print()
print("FAILED OK: la tarea se rindio despues de 3 intentos")