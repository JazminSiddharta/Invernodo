import sys

import requests

BASE = "http://127.0.0.1:8000"
NODE = "nodo-test"
ZONA = "zona-test"
IMAGEN = b"bytes-de-imagen-falsa"


def check(nombre, condicion):
    if condicion:
        print("OK     " + nombre)
    else:
        print("FALLO  " + nombre)
        sys.exit(1)


# 1. Servidor vivo
r = requests.get(BASE + "/health")
check("health responde 200", r.status_code == 200)

# 2. Nodos
r = requests.post(BASE + "/nodes/register", json={"node_id": NODE})
check("register nodo responde 200", r.status_code == 200)

r = requests.post(BASE + "/nodes/" + NODE + "/heartbeat")
check("heartbeat de nodo registrado responde 200", r.status_code == 200)

r = requests.post(BASE + "/nodes/nodo-fantasma/heartbeat")
check("heartbeat de nodo desconocido responde 404", r.status_code == 404)

# 3. Crear tarea
r = requests.post(
    BASE + "/tasks",
    files={"file": ("test.jpg", IMAGEN, "image/jpeg")},
    data={"zone_id": ZONA},
)
check("crear tarea responde 200", r.status_code == 200)
task_id = r.json()["task_id"]

# 4. Claim
r = requests.post(BASE + "/tasks/claim", json={"node_id": NODE})
check("claim responde 200", r.status_code == 200)
tarea = r.json()
check("la tarea es la que creamos", tarea["task_id"] == task_id)
check("tarea queda ASSIGNED", tarea["status"] == "ASSIGNED")
check("tarea asignada al nodo", tarea["assigned_to"] == NODE)
check("attempts es 1", tarea["attempts"] == 1)

r = requests.post(BASE + "/tasks/claim", json={"node_id": NODE})
check("segundo claim responde 204 (ya no hay tareas)", r.status_code == 204)

# 5. Imagen
r = requests.get(BASE + "/tasks/" + task_id + "/image")
check("imagen responde 200", r.status_code == 200)
check("la imagen descargada es igual a la subida", r.content == IMAGEN)

r = requests.get(BASE + "/tasks/inventado/image")
check("imagen de tarea inexistente responde 404", r.status_code == 404)

# 6. Resultado
resultado = {
    "task_id": task_id,
    "node_id": NODE,
    "zone_id": ZONA,
    "label": "sana",
    "confidence": 0.9,
    "latency_ms": 120,
}
r = requests.post(BASE + "/tasks/inventado/result", json=resultado)
check("resultado con task_id distinto responde 400", r.status_code == 400)

r = requests.post(BASE + "/tasks/" + task_id + "/result", json=resultado)
check("resultado correcto responde 200", r.status_code == 200)

fantasma = dict(resultado, task_id="inventado")
r = requests.post(BASE + "/tasks/inventado/result", json=fantasma)
check("resultado de tarea inexistente responde 404", r.status_code == 404)

# 7. Lecturas
# El nodo debe seguir vivo: avisamos justo antes de revisar los stats
r = requests.post(BASE + "/nodes/" + NODE + "/heartbeat")
check("heartbeat antes de los stats responde 200", r.status_code == 200)
stats = requests.get(BASE + "/stats").json()
check("stats: total_tasks es 1", stats["total_tasks"] == 1)
check("stats: done es 1", stats["done"] == 1)
check("stats: nodes_alive es 1", stats["nodes_alive"] == 1)

r = requests.get(BASE + "/results")
check("results tiene 1 resultado", len(r.json()) == 1)

nodos = requests.get(BASE + "/nodes").json()
check("el nodo suma 1 tarea hecha", nodos[0]["tasks_done"] == 1)


tareas = requests.get(BASE + "/tasks").json()
check("GET /tasks lista 1 tarea", len(tareas) == 1)
check("la tarea quedó DONE con attempts 1", tareas[0]["status"] == "DONE" and tareas[0]["attempts"] == 1)

resultados = requests.get(BASE + "/results").json()
check("el resultado trae completed_at", resultados[0]["completed_at"] is not None)


print()
print("TODAS LAS PRUEBAS PASARON")