from enum import Enum
from typing import Optional
from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "PENDING"    # esperando a que un nodo la tome
    ASSIGNED = "ASSIGNED"  # un nodo la está procesando
    DONE = "DONE"          # terminada
    FAILED = "FAILED"      # falló MAX_RETRIES veces


class NodeStatus(str, Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"


# Todos los tiempos son timestamps Unix en segundos (float),
# y SIEMPRE los pone el coordinador (así no importa la hora de cada compu).

class Task(BaseModel):
    task_id: str                       # uuid
    zone_id: str                       # ej. "zona-1"
    created_at: float
    attempts: int = 0
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None  # node_id o None
    deadline: Optional[float] = None


class Result(BaseModel):
    task_id: str
    node_id: str
    zone_id: str
    label: str          # una de las etiquetas de labels.json
    confidence: float   # entre 0 y 1
    latency_ms: float


class NodeInfo(BaseModel):
    node_id: str
    status: NodeStatus
    last_heartbeat: float
    tasks_done: int = 0