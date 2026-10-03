# API del coordinador (puerto 8000)

| Endpoint | Quién lo usa | Envía | Responde |
|---|---|---|---|
| POST /tasks | simulador | multipart: `file` (imagen) + `zone_id` (texto) | {"task_id": "..."} |
| POST /nodes/register | worker | {"node_id": "nodo-1"} | {"ok": true} |
| POST /nodes/{node_id}/heartbeat | worker | nada | {"ok": true} |
| POST /tasks/claim | worker | {"node_id": "nodo-1"} | Task (JSON) o 204 si no hay tareas |
| GET /tasks/{task_id}/image | worker | nada | los bytes de la imagen |
| POST /tasks/{task_id}/result | worker | Result (JSON) | {"ok": true} |
| GET /nodes | dashboard | nada | lista de NodeInfo |
| GET /results | dashboard | nada | lista de Result |
| GET /stats | dashboard | nada | {"total_tasks", "pending", "assigned", "done", "failed", "nodes_alive", "nodes_dead"} |

Todos los formatos (Task, Result, NodeInfo) están en `shared/contracts.py`.
Las constantes están en `shared/config.py`. Nadie las copia a otro lado.