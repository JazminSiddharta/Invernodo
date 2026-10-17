
import os
import requests
import time
import threading
import math

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

        if respuesta.status_code == 404:
            print("Worker no encontrado en el coordinador.")
            print("Intentando registrar nuevamente...")

            if registrar_worker():
                print("Worker reconectado correctamente.")
                return True

            print("No se pudo registrar. Se intentará de nuevo.")
            return False

        respuesta.raise_for_status()

        print(f"Heartbeat enviado por {NODE_ID}")
        return True

    except requests.RequestException as error:
        print(f"Error al enviar heartbeat: {error}")
        print("Se intentará nuevamente en el siguiente ciclo.")
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
        print("No se puede clasificar una imagen vacia.")
        return None

    inicio = time.perf_counter()

    try:
        prediccion = classify(imagen)

        if not isinstance(prediccion, dict):
            print("El modelo devolvio un resultado invalido.")
            return None

        label = prediccion["label"]
        confidence = prediccion["confidence"]

        if not isinstance(label, str) or not label.strip():
            print("La etiqueta de clasificacion no es valida.")
            return None

        if isinstance(confidence, bool):
            print("La confianza no es valida.")
            return None

        confidence = float(confidence)

        if not math.isfinite(confidence):
            print("La confianza contiene un valor no finito.")
            return None

        if not 0 <= confidence <= 1:
            print("La confianza esta fuera del rango permitido.")
            return None

        latencia = round(
            (time.perf_counter() - inicio) * 1000,
            2
        )

        resultado = {
            "label": label,
            "confidence": confidence,
            "latency_ms": latencia
        }

        print(f"Clasificacion real: {resultado['label']}")
        print(f"Confianza: {resultado['confidence']}")
        print(f"Latencia: {latencia} ms")

        return resultado

    except Exception as error:
        print(f"Error al clasificar imagen: {error}")
        return None



def enviar_resultado(tarea, clasificacion):
    if not isinstance(tarea, dict) or not isinstance(clasificacion, dict):
        print("No hay un resultado valido para enviar.")
        return False

    task_id = tarea.get("task_id")
    zone_id = tarea.get("zone_id")
    label = clasificacion.get("label")
    confidence = clasificacion.get("confidence")
    latency_ms = clasificacion.get("latency_ms")

    if not all(
        isinstance(valor, str) and valor.strip()
        for valor in (task_id, zone_id, label)
    ):
        print("Datos incompletos de la tarea.")
        return False

    try:
        if isinstance(confidence, bool) or isinstance(latency_ms, bool):
            print("Valores numericos invalidos.")
            return False

        confidence = float(confidence)
        latency_ms = float(latency_ms)

        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            print("Confianza invalida.")
            return False

        if not math.isfinite(latency_ms) or latency_ms < 0:
            print("Latencia invalida.")
            return False

    except (ValueError, TypeError):
        print("Error en los datos de clasificacion.")
        return False

    url = f"{COORDINATOR_URL}/tasks/{task_id}/result"

    datos = {
        "task_id": task_id,
        "node_id": NODE_ID,
        "zone_id": zone_id,
        "label": label,
        "confidence": confidence,
        "latency_ms": latency_ms
    }

    try:
        respuesta = requests.post(
            url,
            json=datos,
            timeout=10
        )

        if respuesta.status_code in (404, 409, 410):
            print(
                f"Resultado rechazado por el coordinador. "
                f"HTTP {respuesta.status_code}"
            )
            return False

        respuesta.raise_for_status()

        print(f"Resultado enviado correctamente: {task_id}")

        if respuesta.content:
            try:
                print(respuesta.json())
            except ValueError:
                print("Respuesta recibida sin JSON.")

        return True

    except requests.Timeout:
        print("Tiempo de espera agotado al enviar el resultado.")
        print("La entrega no pudo confirmarse.")
        return False

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


def ciclo_heartbeat(detener, registrado):
    while not detener.is_set():
        try:
            if not registrado.is_set():
                print("Intentando conectar con el coordinador...")

                if registrar_worker():
                    registrado.set()
                    print("Worker conectado correctamente.")

            else:
                if not enviar_heartbeat():
                    registrado.clear()
                    print("Conexion perdida. Se intentara reconectar.")

        except Exception as error:
            registrado.clear()
            print(f"Error inesperado en heartbeat: {error}")

        detener.wait(2)


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

    detener = threading.Event()
    registrado = threading.Event()

    hilo_heartbeat = threading.Thread(
        target=ciclo_heartbeat,
        args=(detener, registrado),
        daemon=True
    )

    hilo_heartbeat.start()

    try:
        while True:
            if not registrado.is_set():
                print("Esperando conexion con el coordinador...")
                detener.wait(2)
                continue

            try:
                procesar_tarea()

            except Exception as error:
                print(f"Error inesperado al procesar tarea: {error}")

            detener.wait(5)

    except KeyboardInterrupt:
        print("\nDeteniendo Worker...")

    finally:
        detener.set()
        hilo_heartbeat.join(timeout=12)
        print("Worker detenido.")