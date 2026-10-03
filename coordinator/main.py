from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/health")
def health():
    return {"ok": True}


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