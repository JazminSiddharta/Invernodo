# infra (Jhonny)

Docker para levantar todo el sistema Invernodo con un solo comando.

## Qué hay aquí

- `Dockerfile.python`: receta base con Python 3.11 para `coordinator`, `worker`, `simulator` y `dashboard`. Copia `shared/` y la carpeta del servicio.
- `docker-compose.yml`: levanta 5 servicios: `coordinator`, `worker-1`, `worker-2`, `simulator` y `dashboard`.

**Estado (Fase 0):** los servicios están vacíos y solo se quedan vivos (`sleep`). El código real de cada quien se conecta en las fases siguientes.

## Requisitos

- Docker Desktop instalado y abierto (abajo a la izquierda debe decir "Engine running").

## Cómo correrlo

Desde la raíz del repo (la carpeta `Invernodo`):

```bash
docker compose -f infra/docker-compose.yml up --build
```

La primera vez tarda 1 a 3 minutos. Cuando termina, la terminal se queda quieta: es normal. En Docker Desktop > Containers debe aparecer el grupo `infra` con 5 contenedores.

## Cómo apagarlo

1. En la terminal, presiona `Ctrl + C`.
2. Luego:

```bash
docker compose -f infra/docker-compose.yml down
```

## Variables de entorno

| Servicio | Variable | Valor |
|---|---|---|
| worker-1 | `NODE_ID` | `nodo-1` |
| worker-2 | `NODE_ID` | `nodo-2` |
| worker-1, worker-2, simulator, dashboard | `COORDINATOR_URL` | `http://coordinator:8000` |

El coordinador publica el puerto 8000. Las constantes (tiempos, reintentos) viven solo en `shared/config.py`.