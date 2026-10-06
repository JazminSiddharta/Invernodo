import threading
import time
import uuid
from pathlib import Path

from shared.config import HEARTBEAT_TIMEOUT_S, MAX_RETRIES, TASK_TIMEOUT_S
from shared.contracts import NodeInfo, NodeStatus, Result, Task, TaskStatus

# Carpeta donde se guardan las imágenes (no se sube a GitHub)
IMAGES_DIR = Path("coordinator/data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# El "cuaderno": todo vive en estos diccionarios (en memoria, por ahora)
_tasks = {}    # task_id -> Task
_nodes = {}    # node_id -> NodeInfo
_results = {}  # task_id -> Result

# Candado: evita que dos nodos modifiquen los datos al mismo tiempo
_lock = threading.Lock()


def image_path(task_id):
    return IMAGES_DIR / task_id


# ---------- Nodos ----------

def register_node(node_id):
    with _lock:
        node = _nodes.get(node_id)
        if node is None:
            _nodes[node_id] = NodeInfo(
                node_id=node_id,
                status=NodeStatus.ALIVE,
                last_heartbeat=time.time(),
            )
        else:
            node.status = NodeStatus.ALIVE
            node.last_heartbeat = time.time()


def heartbeat(node_id):
    with _lock:
        node = _nodes.get(node_id)
        if node is None:
            return False
        node.status = NodeStatus.ALIVE
        node.last_heartbeat = time.time()
        return True


def get_nodes():
    with _lock:
        return list(_nodes.values())


def mark_dead_nodes():
    """Marca DEAD a los nodos sin heartbeat reciente. Devuelve sus ids."""
    with _lock:
        ahora = time.time()
        muertos = []
        for node in _nodes.values():
            if node.status == NodeStatus.ALIVE and ahora - node.last_heartbeat > HEARTBEAT_TIMEOUT_S:
                node.status = NodeStatus.DEAD
                muertos.append(node.node_id)
        return muertos
    
    
# ---------- Tareas ----------

def create_task(zone_id, task_id=None):
    with _lock:
        task = Task(
            task_id=task_id or str(uuid.uuid4()),
            zone_id=zone_id,
            created_at=time.time(),
        )
        _tasks[task.task_id] = task
        return task


def claim_task(node_id):
    """Da la tarea PENDING más vieja al nodo. Devuelve None si no hay."""
    with _lock:
        pendientes = [t for t in _tasks.values() if t.status == TaskStatus.PENDING]
        if not pendientes:
            return None
        task = min(pendientes, key=lambda t: t.created_at)
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = node_id
        task.attempts += 1
        task.deadline = time.time() + TASK_TIMEOUT_S
        return task


def reassign_tasks():
    """Devuelve a PENDING las tareas cuyo nodo murió o cuyo plazo venció.
    Si ya se agotaron los intentos, la tarea pasa a FAILED."""
    with _lock:
        ahora = time.time()
        movidas = []
        for task in _tasks.values():
            if task.status != TaskStatus.ASSIGNED:
                continue
            nodo = _nodes.get(task.assigned_to)
            nodo_muerto = nodo is not None and nodo.status == NodeStatus.DEAD
            plazo_vencido = task.deadline is not None and ahora > task.deadline
            if nodo_muerto or plazo_vencido:
                if task.attempts >= MAX_RETRIES:
                    task.status = TaskStatus.FAILED
                else:
                    task.status = TaskStatus.PENDING
                task.assigned_to = None
                task.deadline = None
                movidas.append(task.task_id)
        return movidas


def task_exists(task_id):
    with _lock:
        return task_id in _tasks
    

def get_tasks():
    with _lock:
        return list(_tasks.values())


def save_result(result):
    """Guarda el resultado. Devuelve False si la tarea no existe."""
    with _lock:
        task = _tasks.get(result.task_id)
        if task is None:
            return False
        result.completed_at = time.time()  # la hora la pone el coordinador
        task.status = TaskStatus.DONE
        _results[result.task_id] = result
        node = _nodes.get(result.node_id)
        if node is not None:
            node.tasks_done += 1
        return True


def get_results():
    with _lock:
        return list(_results.values())


def get_stats():
    with _lock:
        tareas = list(_tasks.values())
        nodos = list(_nodes.values())
        return {
            "total_tasks": len(tareas),
            "pending": sum(1 for t in tareas if t.status == TaskStatus.PENDING),
            "assigned": sum(1 for t in tareas if t.status == TaskStatus.ASSIGNED),
            "done": sum(1 for t in tareas if t.status == TaskStatus.DONE),
            "failed": sum(1 for t in tareas if t.status == TaskStatus.FAILED),
            "nodes_alive": sum(1 for n in nodos if n.status == NodeStatus.ALIVE),
            "nodes_dead": sum(1 for n in nodos if n.status == NodeStatus.DEAD),
        }