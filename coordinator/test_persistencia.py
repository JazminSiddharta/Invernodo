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


def tareas_p():
    return [t for t in requests.get(BASE + "/tasks").json() if t["zone_id"] == "zona-p"]


modo = sys.argv[1] if len(sys.argv) > 1 else ""

if modo == "crear":
    requests.post(BASE + "/nodes/register", json={"node_id": "nodo-p"})
    requests.post(
        BASE + "/tasks",
        files={"file": ("f.jpg", b"imagen-persistente", "image/jpeg")},
        data={"zone_id": "zona-p"},
    )
    r = requests.post(BASE + "/tasks/claim", json={"node_id": "nodo-p"})
    check("nodo-p toma la tarea", r.status_code == 200)
    print()
    print("Ahora APAGA el servidor (Ctrl + C) y vuelve a prenderlo SIN borrar nada.")
    print("Luego corre: python coordinator/test_persistencia.py revisar")

elif modo == "revisar":
    t = tareas_p()
    check("la tarea sobrevivio al reinicio", len(t) == 1)
    check("conserva attempts 1", t[0]["attempts"] == 1)
    print("Esperando 9 segundos para que el vigilante note que nodo-p no volvio...")
    time.sleep(9)
    t = tareas_p()
    check("la tarea volvio a PENDING", t[0]["status"] == "PENDING")
    nodos = {n["node_id"]: n for n in requests.get(BASE + "/nodes").json()}
    check("nodo-p sigue en la lista y quedo DEAD", nodos["nodo-p"]["status"] == "DEAD")
    print()
    print("PERSISTENCIA OK: el coordinador recordo todo despues de reiniciar")

else:
    print("Uso: python coordinator/test_persistencia.py crear   (o)   revisar")