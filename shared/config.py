import os

# Tiempos (en segundos)
HEARTBEAT_INTERVAL_S = 2   # cada cuánto un nodo avisa que sigue vivo
HEARTBEAT_TIMEOUT_S = 6    # sin aviso en 6 s, el nodo se da por muerto
TASK_TIMEOUT_S = 15        # si una tarea no termina en 15 s, se reasigna
MAX_RETRIES = 3            # intentos máximos por imagen

# Se leen del entorno (cada contenedor/compu define las suyas)
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://localhost:8000")
NODE_ID = os.getenv("NODE_ID", "nodo-1")