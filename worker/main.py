
import os
import requests
import time
import threading

from model.inference_real import cargar_modelo, classify

NODE_ID = os.getenv("NODE_ID", "nodo-angie")
COORDINATOR_URL = os.getenv(
    "COORDINATOR_URL",
    "http://localhost:8000"
).rstrip("/")


def registrar_worker():
    url = f"{COORDINATOR_URL}/nodes/register"

    datos = {
        "node_id": NODE_ID
    }

    try:
        respuesta = requests.post(
            url,
            json=datos,
            timeout=10
        )

        respuesta.raise_for_status()

        print("Worker registrado correctamente")
        print(respuesta.json())

        return True

    except requests.RequestException as error:
        print(f"Error al registrar Worker: {error}")
        return False


def enviar_heartbeat():
    url = f"{COORDINATOR_URL}/nodes/{NODE_ID}/heartbeat"

    try:
        respuesta = requests.post(
            url,
            timeout=10
        )

        respuesta.raise_for_status()

        print(f"Heartbeat enviado por {NODE_ID}")
        return True

    except requests.RequestException as error:
        print(f"Error al enviar heartbeat: {error}")
        return False


def solicitar_tarea():
    url = f"{COORDINATOR_URL}/tasks/claim"

    datos = {
        "node_id": NODE_ID
    }

    try:
        respuesta = requests.post(
            url,
            json=datos,
            timeout=10
        )

        if respuesta.status_code == 204:
            print("No hay tareas pendientes.")
            return None

        respuesta.raise_for_status()

        tarea = respuesta.json()

        print(f"Tarea recibida: {tarea['task_id']}")
        print(f"Zona: {tarea['zone_id']}")

        return tarea

    except requests.RequestException as error:
        print(f"Error al solicitar tarea: {error}")
        return None

    except (ValueError, KeyError, TypeError) as error:
        print(f"Respuesta de tarea no válida: {error}")
        return None


def descargar_imagen(task_id):
    url = f"{COORDINATOR_URL}/tasks/{task_id}/image"

    try:
        respuesta = requests.get(
            url,
            timeout=30
        )

        respuesta.raise_for_status()

        imagen = respuesta.content

        if not imagen:
            print("La imagen recibida está vacía.")
            return None

        print(f"Imagen descargada: {len(imagen)} bytes")

        return imagen

    except requests.RequestException as error:
        print(f"Error al descargar imagen: {error}")
        return None


def clasificar_imagen(imagen):
    if not imagen:
        print("No se puede clasificar una imagen vacía.")
        return None

    inicio = time.perf_counter()

    try:
        prediccion = classify(imagen)

        latencia = round(
            (time.perf_counter() - inicio) * 1000,
            2
        )

        resultado = {
            "label": prediccion["label"],
            "confidence": float(prediccion["confidence"]),
            "latency_ms": latencia
        }

        print(f"Clasificación real: {resultado['label']}")
        print(f"Confianza: {resultado['confidence']}")
        print(f"Latencia: {latencia} ms")

        return resultado

    except Exception as error:
        print(f"Error al clasificar imagen: {error}")
        return None

def enviar_resultado(tarea, clasificacion):
    if not tarea or not clasificacion:
        print("No hay un resultado válido para enviar.")
        return False

    task_id = tarea["task_id"]

    url = f"{COORDINATOR_URL}/tasks/{task_id}/result"

    datos = {
        "task_id": task_id,
        "node_id": NODE_ID,
        "zone_id": tarea["zone_id"],
        "label": clasificacion["label"],
        "confidence": clasificacion["confidence"],
        "latency_ms": clasificacion["latency_ms"]
    }

    try:
        respuesta = requests.post(
            url,
            json=datos,
            timeout=10
        )

        respuesta.raise_for_status()

        print(f"Resultado enviado correctamente: {task_id}")
        print(respuesta.json())

        return True

    except requests.RequestException as error:
        print(f"Error al enviar resultado: {error}")
        return False


def procesar_tarea():
    tarea = solicitar_tarea()

    if tarea is None:
        return False

    task_id = tarea["task_id"]

    imagen = descargar_imagen(task_id)

    if imagen is None:
        print(f"No se pudo descargar la imagen: {task_id}")
        return False

    clasificacion = clasificar_imagen(imagen)

    if clasificacion is None:
        print(f"No se pudo clasificar la tarea: {task_id}")
        return False

    if enviar_resultado(tarea, clasificacion):
        print(f"Tarea completada: {task_id}")
        return True

    print(f"No se pudo enviar el resultado: {task_id}")
    return False


def ciclo_heartbeat(detener):
    while not detener.wait(2):
        enviar_heartbeat()


if __name__ == "__main__":
    print(f"Iniciando Worker: {NODE_ID}")
    print(f"Coordinador: {COORDINATOR_URL}")

    print("Cargando modelo de TensorFlow...")

    try:
        cargar_modelo()
        print("Modelo cargado correctamente.")

    except Exception as error:
        print(f"Error al cargar el modelo: {error}")
        raise SystemExit(1)

    if registrar_worker():
        print("Worker registrado. Iniciando procesamiento...")

        detener = threading.Event()

        hilo_heartbeat = threading.Thread(
            target=ciclo_heartbeat,
            args=(detener,),
            daemon=True
        )

        hilo_heartbeat.start()

        try:
            while True:
                procesar_tarea()
                time.sleep(5)

        except KeyboardInterrupt:
            print("\nDeteniendo Worker...")

        finally:
            detener.set()
            hilo_heartbeat.join(timeout=2)
            print("Worker detenido.")

    else:
        print("No se pudo registrar el Worker.")
