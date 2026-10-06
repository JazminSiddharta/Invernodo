import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from shared.config import HEARTBEAT_TIMEOUT_S, MAX_RETRIES, TASK_TIMEOUT_S
from shared.contracts import NodeInfo, NodeStatus, Result, Task, TaskStatus

# Carpeta donde se guardan las imágenes (no se sube a GitHub)
IMAGES_DIR = Path("coordinator/data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Archivo de la base de datos. Para pruebas se usa ":memory:" (empieza vacía)
DB_PATH = os.getenv("INVERNODO_DB", "coordinator/data/invernodo.db")
if DB_PATH != ":memory:":
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Candado: evita que dos hilos usen la base de datos al mismo tiempo
_lock = threading.Lock()

_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.executescript(
    """
    CREATE TABLE IF NOT EXISTS nodes (
        node_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        last_heartbeat REAL NOT NULL,
        tasks_done INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        zone_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        assigned_to TEXT,
        deadline REAL
    );
    CREATE TABLE IF NOT EXISTS results (
        task_id TEXT PRIMARY KEY,
        node_id TEXT NOT NULL,
        zone_id TEXT NOT NULL,
        label TEXT NOT NULL,
        confidence REAL NOT NULL,
        latency_ms REAL NOT NULL,
        completed_at REAL
    );
    """
)
_db.commit()


def image_path(task_id):
    return IMAGES_DIR / task_id


# ---------- Nodos ----------

def register_node(node_id):
    with _lock:
        _db.execute(
            "INSERT INTO nodes (node_id, status, last_heartbeat) VALUES (?, ?, ?) "
            "ON CONFLICT(node_id) DO UPDATE SET "
            "status = excluded.status, last_heartbeat = excluded.last_heartbeat",
            (node_id, NodeStatus.ALIVE.value, time.time()),
        )
        _db.commit()


def heartbeat(node_id):
    with _lock:
        cur = _db.execute(
            "UPDATE nodes SET status = ?, last_heartbeat = ? WHERE node_id = ?",
            (NodeStatus.ALIVE.value, time.time(), node_id),
        )
        _db.commit()
        return cur.rowcount > 0


def get_nodes():
    with _lock:
        filas = _db.execute("SELECT * FROM nodes ORDER BY rowid").fetchall()
        return [NodeInfo(**dict(f)) for f in filas]


def mark_dead_nodes():
    """Marca DEAD a los nodos sin heartbeat reciente. Devuelve sus ids."""
    with _lock:
        limite = time.time() - HEARTBEAT_TIMEOUT_S
        filas = _db.execute(
            "SELECT node_id FROM nodes WHERE status = ? AND last_heartbeat < ?",
            (NodeStatus.ALIVE.value, limite),
        ).fetchall()
        muertos = [f["node_id"] for f in filas]
        if muertos:
            _db.executemany(
                "UPDATE nodes SET status = ? WHERE node_id = ?",
                [(NodeStatus.DEAD.value, n) for n in muertos],
            )
            _db.commit()
        return muertos


# ---------- Tareas ----------

def create_task(zone_id, task_id=None):
    with _lock:
        task = Task(
            task_id=task_id or str(uuid.uuid4()),
            zone_id=zone_id,
            created_at=time.time(),
        )
        _db.execute(
            "INSERT INTO tasks (task_id, zone_id, created_at, attempts, status) "
            "VALUES (?, ?, ?, 0, ?)",
            (task.task_id, task.zone_id, task.created_at, TaskStatus.PENDING.value),
        )
        _db.commit()
        return task


def claim_task(node_id):
    """Da la tarea PENDING más vieja al nodo. Devuelve None si no hay."""
    with _lock:
        fila = _db.execute(
            "SELECT task_id FROM tasks WHERE status = ? ORDER BY created_at LIMIT 1",
            (TaskStatus.PENDING.value,),
        ).fetchone()
        if fila is None:
            return None
        _db.execute(
            "UPDATE tasks SET status = ?, assigned_to = ?, "
            "attempts = attempts + 1, deadline = ? WHERE task_id = ?",
            (TaskStatus.ASSIGNED.value, node_id, time.time() + TASK_TIMEOUT_S, fila["task_id"]),
        )
        _db.commit()
        fila = _db.execute("SELECT * FROM tasks WHERE task_id = ?", (fila["task_id"],)).fetchone()
        return Task(**dict(fila))


def reassign_tasks():
    """Devuelve a PENDING las tareas cuyo nodo murió o cuyo plazo venció.
    Si ya se agotaron los intentos, la tarea pasa a FAILED."""
    with _lock:
        ahora = time.time()
        filas = _db.execute(
            "SELECT * FROM tasks WHERE status = ?", (TaskStatus.ASSIGNED.value,)
        ).fetchall()
        movidas = []
        for f in filas:
            nodo = _db.execute(
                "SELECT status FROM nodes WHERE node_id = ?", (f["assigned_to"],)
            ).fetchone()
            nodo_muerto = nodo is not None and nodo["status"] == NodeStatus.DEAD.value
            plazo_vencido = f["deadline"] is not None and ahora > f["deadline"]
            if nodo_muerto or plazo_vencido:
                if f["attempts"] >= MAX_RETRIES:
                    nuevo = TaskStatus.FAILED.value
                else:
                    nuevo = TaskStatus.PENDING.value
                _db.execute(
                    "UPDATE tasks SET status = ?, assigned_to = NULL, deadline = NULL "
                    "WHERE task_id = ?",
                    (nuevo, f["task_id"]),
                )
                movidas.append(f["task_id"])
        if movidas:
            _db.commit()
        return movidas


def task_exists(task_id):
    with _lock:
        fila = _db.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return fila is not None


def get_tasks():
    with _lock:
        filas = _db.execute("SELECT * FROM tasks ORDER BY rowid").fetchall()
        return [Task(**dict(f)) for f in filas]


def save_result(result):
    """Guarda el resultado. Devuelve 'saved', 'duplicate' o 'not_found'."""
    with _lock:
        fila = _db.execute(
            "SELECT status FROM tasks WHERE task_id = ?", (result.task_id,)
        ).fetchone()
        if fila is None:
            return "not_found"
        if fila["status"] == TaskStatus.DONE.value:
            return "duplicate"  # el primer resultado gana
        result.completed_at = time.time()  # la hora la pone el coordinador
        _db.execute(
            "INSERT OR REPLACE INTO results "
            "(task_id, node_id, zone_id, label, confidence, latency_ms, completed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (result.task_id, result.node_id, result.zone_id, result.label,
             result.confidence, result.latency_ms, result.completed_at),
        )
        _db.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (TaskStatus.DONE.value, result.task_id),
        )
        _db.execute(
            "UPDATE nodes SET tasks_done = tasks_done + 1 WHERE node_id = ?",
            (result.node_id,),
        )
        _db.commit()
        return "saved"


def get_results():
    with _lock:
        filas = _db.execute("SELECT * FROM results ORDER BY rowid").fetchall()
        return [Result(**dict(f)) for f in filas]


def _contar(tabla, status):
    return _db.execute(
        "SELECT COUNT(*) FROM " + tabla + " WHERE status = ?", (status.value,)
    ).fetchone()[0]


def get_stats():
    with _lock:
        total = _db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        return {
            "total_tasks": total,
            "pending": _contar("tasks", TaskStatus.PENDING),
            "assigned": _contar("tasks", TaskStatus.ASSIGNED),
            "done": _contar("tasks", TaskStatus.DONE),
            "failed": _contar("tasks", TaskStatus.FAILED),
            "nodes_alive": _contar("nodes", NodeStatus.ALIVE),
            "nodes_dead": _contar("nodes", NodeStatus.DEAD),
        }