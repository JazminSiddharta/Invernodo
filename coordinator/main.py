import uuid

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from coordinator import store

app = FastAPI(title="Invernodo Coordinator")

# Permite que el dashboard de JP pueda consultar esta API desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NodeRequest(BaseModel):
    node_id: str


class ClaimRequest(BaseModel):
    node_id: str


@app.get("/health")
def health():
    return {"ok": True}


# ---------- Nodos ----------

@app.post("/nodes/register")
def register_node(body: NodeRequest):
    store.register_node(body.node_id)
    return {"ok": True}


@app.post("/nodes/{node_id}/heartbeat")
def node_heartbeat(node_id: str):
    if not store.heartbeat(node_id):
        raise HTTPException(status_code=404, detail="Nodo no registrado")
    return {"ok": True}


@app.get("/nodes")
def list_nodes():
    return store.get_nodes()


# ---------- Tareas ----------

@app.post("/tasks")
async def create_task(file: UploadFile = File(...), zone_id: str = Form(...)):
    task_id = str(uuid.uuid4())
    contenido = await file.read()
    store.image_path(task_id).write_bytes(contenido)  # primero la imagen
    store.create_task(zone_id, task_id)               # luego la tarea
    return {"task_id": task_id}


@app.post("/tasks/claim")
def claim_task(body: ClaimRequest):
    task = store.claim_task(body.node_id)
    if task is None:
        return Response(status_code=204)
    return task


@app.get("/tasks/{task_id}/image")
def get_image(task_id: str):
    if not store.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Tarea no existe")
    return FileResponse(store.image_path(task_id))