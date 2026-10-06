import sys
import time

import requests

BASE = "http://127.0.0.1:8000"
IMAGEN = b"imagen-falsa"


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


# nodo-a toma una tarea y luego "se muere" (no manda heartbeat)
requests.post(BASE + "/nodes/register", json={"node_id": "nodo-a"})
r = requests.post(
    BASE + "/tasks",
    files={"file": ("f.jpg", IMAGEN, "image/jpeg")},
    data={"zone_id": "zona-f"},
)
task_id = r.json()["task_id"]

r = requests.post(BASE + "/tasks/claim", json={"node_id": "nodo-a"})
check("nodo-a toma la tarea", r.status_code == 200 and r.json()["task_id"] == task_id)

print("Esperando 9 segundos sin heartbeat de nodo-a...")
time.sleep(9)

t = buscar_tarea(task_id)
check("la tarea volvio a PENDING", t["status"] == "PENDING")
check("la tarea ya no tiene nodo asignado", t["assigned_to"] is None)

nodos = {n["node_id"]: n for n in requests.get(BASE + "/nodes").json()}
check("nodo-a quedo DEAD", nodos["nodo-a"]["status"] == "DEAD")

# nodo-b recoge la misma tarea
requests.post(BASE + "/nodes/register", json={"node_id": "nodo-b"})
r = requests.post(BASE + "/tasks/claim", json={"node_id": "nodo-b"})
check("nodo-b recibe la misma tarea", r.status_code == 200 and r.json()["task_id"] == task_id)
check("attempts es 2", r.json()["attempts"] == 2)

resultado = {
    "task_id": task_id,
    "node_id": "nodo-b",
    "zone_id": "zona-f",
    "label": "sana",
    "confidence": 0.9,
    "latency_ms": 100,
}
r = requests.post(BASE + "/tasks/" + task_id + "/result", json=resultado)
check("nodo-b entrega el resultado", r.status_code == 200)
check("la tarea termina en DONE", buscar_tarea(task_id)["status"] == "DONE")

print()
print("FAILOVER OK: la tarea sobrevivio a la caida de un nodo")