# Worker

# Worker — Invernodo

## Descripción

El Worker es el nodo trabajador del sistema distribuido Invernodo. Su función consiste en recibir tareas del coordinador, descargar imágenes de plantas, realizar una clasificación y enviar los resultados obtenidos.

Durante la Fase 1 se implementó un clasificador simulado (*stub*) para comprobar la comunicación entre los componentes del sistema.

## Funcionalidades implementadas

- Registro del nodo mediante `POST /nodes/register`.
- Envío periódico de heartbeat mediante `POST /nodes/{node_id}/heartbeat`.
- Solicitud de tareas mediante `POST /tasks/claim`.
- Descarga de imágenes mediante `GET /tasks/{task_id}/image`.
- Clasificación simulada de imágenes.
- Envío de resultados mediante `POST /tasks/{task_id}/result`.
- Ejecución concurrente del heartbeat utilizando `threading`.
- Manejo básico de errores de comunicación.

## Requisitos

- Python 3.11.
- Biblioteca `requests`.
- Coordinador Invernodo en funcionamiento.

## Configuración

El Worker admite las siguientes variables de entorno:

- `NODE_ID`: identificador único del Worker. Valor predeterminado: `nodo-angie`.
- `COORDINATOR_URL`: dirección del coordinador. Valor predeterminado: `http://localhost:8000`.

## Ejecución

Desde la carpeta raíz del repositorio:

```powershell
conda activate invernodo
python -m pip install requests
python worker/main.py
```

Para detener el Worker, presionar `Ctrl + C`.

## Clasificación simulada

El clasificador utiliza las etiquetas oficiales:

- sana
- hongo
- plaga
- virus
- bacteria

La clasificación y el nivel de confianza son simulados. No representan un diagnóstico real.

## Pruebas realizadas

Se realizó una prueba de integración utilizando una copia temporal del coordinador.

Resultados:

- Registro del Worker exitoso.
- Heartbeats recibidos correctamente.
- Imagen descargada: 17,509 bytes.
- Clasificación simulada: `sana`.
- Confianza simulada: `0.7177`.
- Resultado enviado correctamente.
- Tarea registrada con estado `DONE`.
- Sin tareas fallidas.

## Consideraciones

El campo `completed_at` no se envía desde el Worker, ya que el coordinador es responsable de asignarlo.

La integración del Worker con un modelo de clasificación real queda pendiente para una fase posterior.