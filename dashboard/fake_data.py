"""Datos falsos con la forma EXACTA de shared/contracts.py y shared/API.md.

Sirven para la Fase 1: el dashboard funciona sin el coordinador real.
Incluye a propósito un nodo DEAD, tareas reasignadas (attempts > 1),
una tarea FAILED y resultados sin completed_at, para probar todos los casos.
"""

import json
import random
import time
import uuid
from pathlib import Path

from shared.contracts import NodeInfo, NodeStatus, Result, Task, TaskStatus

LABELS = json.loads(
    (Path(__file__).resolve().parent.parent / "shared" / "labels.json").read_text(encoding="utf-8")
)
ZONES = ["zona-1", "zona-2", "zona-3", "zona-4"]


def generate(seed: int = 42) -> dict:
    """Devuelve lo mismo que devolverían GET /nodes, /results, /tasks y /stats."""
    rng = random.Random(seed)
    now = time.time()

    nodes = [
        NodeInfo(node_id="nodo-1", status=NodeStatus.ALIVE, last_heartbeat=now - 1.2, tasks_done=0),
        NodeInfo(node_id="nodo-2", status=NodeStatus.ALIVE, last_heartbeat=now - 0.6, tasks_done=0),
        NodeInfo(node_id="nodo-3", status=NodeStatus.DEAD, last_heartbeat=now - 45.0, tasks_done=0),
    ]

    tasks: list[Task] = []
    results: list[Result] = []

    for i in range(60):
        zone = rng.choice(ZONES)
        created = now - rng.uniform(5, 600)
        task_id = str(uuid.uuid4())

        # Zona 3 con muchos problemas, para que salga la alerta de zona.
        if zone == "zona-3":
            label = rng.choices(LABELS, weights=[1, 2, 6, 1, 1])[0]
        else:
            label = rng.choices(LABELS, weights=[7, 2, 1, 1, 1])[0]

        if i < 4:  # pendientes / asignadas
            status = TaskStatus.PENDING if i < 2 else TaskStatus.ASSIGNED
            tasks.append(Task(task_id=task_id, zone_id=zone, created_at=created, attempts=0 if i < 2 else 1,
                              status=status, assigned_to=None if i < 2 else "nodo-1",
                              deadline=None if i < 2 else now + 10))
            continue
        if i == 4:  # una que falló 3 veces
            tasks.append(Task(task_id=task_id, zone_id=zone, created_at=created, attempts=3,
                              status=TaskStatus.FAILED))
            continue

        attempts = 2 if i % 9 == 0 else 1  # algunas reasignadas (venían de nodo-3)
        node = rng.choice(["nodo-1", "nodo-2"]) if attempts > 1 else rng.choice(["nodo-1", "nodo-2", "nodo-3"])
        completed = created + rng.uniform(0.5, 5)
        tasks.append(Task(task_id=task_id, zone_id=zone, created_at=created, attempts=attempts,
                          status=TaskStatus.DONE, assigned_to=node))
        results.append(Result(
            task_id=task_id, node_id=node, zone_id=zone, label=label,
            confidence=round(rng.uniform(0.55, 0.99), 3),
            latency_ms=round(rng.uniform(80, 900), 1),
            completed_at=None if i % 17 == 0 else completed,  # completed_at es opcional
        ))

    for n in nodes:
        n.tasks_done = sum(1 for r in results if r.node_id == n.node_id)

    stats = {
        "total_tasks": len(tasks),
        "pending": sum(t.status == TaskStatus.PENDING for t in tasks),
        "assigned": sum(t.status == TaskStatus.ASSIGNED for t in tasks),
        "done": sum(t.status == TaskStatus.DONE for t in tasks),
        "failed": sum(t.status == TaskStatus.FAILED for t in tasks),
        "nodes_alive": sum(n.status == NodeStatus.ALIVE for n in nodes),
        "nodes_dead": sum(n.status == NodeStatus.DEAD for n in nodes),
    }

    return {
        "nodes": [n.model_dump(mode="json") for n in nodes],
        "results": [r.model_dump(mode="json") for r in results],
        "tasks": [t.model_dump(mode="json") for t in tasks],
        "stats": stats,
    }


if __name__ == "__main__":
    # python -m dashboard.fake_data  -> guarda un ejemplo en dashboard/sample_data.json
    out = Path(__file__).resolve().parent / "sample_data.json"
    out.write_text(json.dumps(generate(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado en {out}")
