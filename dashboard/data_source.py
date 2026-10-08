"""De dónde salen los datos del dashboard.

USE_FAKE_DATA=1 (por defecto en Fase 1) -> datos falsos de fake_data.py
USE_FAKE_DATA=0                          -> coordinador real en COORDINATOR_URL

Para conectar al coordinador real (Fase 2) solo se cambia la variable.
Todo se valida con los modelos de shared/contracts.py: si el coordinador
manda otra forma, truena aquí y no en medio de la pantalla.
"""

import os

import requests

from shared.config import COORDINATOR_URL
from shared.contracts import NodeInfo, Result, Task

from dashboard import fake_data

USE_FAKE = os.getenv("USE_FAKE_DATA", "1") == "1"
TIMEOUT_S = 3

STATS_KEYS = ["total_tasks", "pending", "assigned", "done", "failed", "nodes_alive", "nodes_dead"]


def _get(path: str):
    r = requests.get(f"{COORDINATOR_URL}{path}", timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def load() -> dict:
    """Devuelve {"nodes", "results", "tasks", "stats"} ya validados."""
    raw = fake_data.generate() if USE_FAKE else {
        "nodes": _get("/nodes"),
        "results": _get("/results"),
        "tasks": _get("/tasks"),
        "stats": _get("/stats"),
    }
    return {
        "nodes": [NodeInfo.model_validate(n) for n in raw["nodes"]],
        "results": [Result.model_validate(r) for r in raw["results"]],
        "tasks": [Task.model_validate(t) for t in raw["tasks"]],
        "stats": {k: int(raw["stats"].get(k, 0)) for k in STATS_KEYS},
    }
