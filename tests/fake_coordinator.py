"""Coordinador falso para probar el simulador sin la API real.

Uso (desde la raíz del repo):
  py -3.11 tests/fake_coordinator.py
Responde POST /tasks con un task_id y GET /stats con cuántas fotos recibió.
"""
import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PUERTO = 8000
recibidas = []


class Handler(BaseHTTPRequestHandler):
    def _json(self, codigo, datos):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        if self.path != "/tasks":
            return self._json(404, {"error": "no existe"})
        cuerpo = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        zona = re.search(rb'name="zone_id"\r\n\r\n([^\r]+)', cuerpo)
        archivo = re.search(rb'filename="([^"]+)"', cuerpo)
        if not zona or not archivo:
            return self._json(400, {"error": "falta file o zone_id"})
        task_id = str(uuid.uuid4())
        recibidas.append({"task_id": task_id, "zone_id": zona.group(1).decode(), "archivo": archivo.group(1).decode()})
        print(f"[{len(recibidas)}] {recibidas[-1]['zone_id']} {recibidas[-1]['archivo']} -> {task_id}")
        self._json(200, {"task_id": task_id})

    def do_GET(self):
        if self.path == "/stats":
            return self._json(200, {"total_tasks": len(recibidas)})
        self._json(404, {"error": "no existe"})

    def log_message(self, *args):
        pass  # sin el ruido de cada petición


if __name__ == "__main__":
    print(f"Coordinador falso escuchando en http://localhost:{PUERTO}")
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
    