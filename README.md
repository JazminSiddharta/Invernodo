# Invernodo

Clasificador de imágenes distribuido para invernadero. Recibe fotos de hojas de tomate y dice si están sanas o con problema (`sana`, `hongo`, `plaga`, `virus` o `bacteria`). Varios nodos trabajadores se reparten las fotos; si uno se cae, el coordinador reasigna sus tareas y no se pierde ninguna imagen.

## Cómo está armado

| Pieza | Carpeta | Qué hace |
|---|---|---|
| Simulador de cámaras | `simulator/` | Manda las 50 fotos de ejemplo de `sample_images/` (2 pasadas = 100 imágenes) al coordinador |
| Coordinador | `coordinator/` | Recibe las fotos, las reparte, vigila que los nodos sigan vivos y reasigna las tareas de un nodo caído. Guarda su estado en SQLite |
| Nodos trabajadores (workers) | `worker/` | Piden una foto, la clasifican con el modelo y entregan el resultado |
| Modelo de IA | `model/` | MobileNetV2 (Keras/TensorFlow) entrenado con hojas de tomate de PlantVillage: 97.4 % en validación y 46/50 en las fotos de ejemplo |
| Dashboard | `dashboard/` | Página web (Streamlit) con nodos vivos o caídos, resultados y alertas por zona |
| Docker | `infra/` | `docker-compose.yml` que levanta todo con un solo comando |
| Contratos compartidos | `shared/` | Constantes, formatos y etiquetas que usan todas las piezas |
| Pruebas | `tests/` | Prueba de humo del modelo y pruebas de caos |

Cada carpeta tiene su propio README con más detalle.

## Requisitos

- **Docker Desktop** instalado y abierto (abajo a la izquierda debe decir "Engine running").
- **Git**.
- Los **pesos del modelo** (`modelo_tomate_ft.keras`). No van en Git por su tamaño: se bajan de Google Drive (el enlace está en `model/README.md`). Si no tienes acceso a la carpeta, pídeselo a Abi.

## Cómo levantarlo (de cero)

1. Clonar el repo y entrar a la carpeta:

```
   git clone https://github.com/JazminSiddharta/Invernodo.git
   cd Invernodo
```

2. Crear la carpeta `model/weights/` y poner dentro `modelo_tomate_ft.keras`. Debe quedar así: `model/weights/modelo_tomate_ft.keras`.

3. Levantar todo, desde la raíz del repo:

```
   docker compose -f infra/docker-compose.yml up --build
```

   **La primera vez tarda entre 10 y 20 minutos** (en una prueba desde cero fueron unos 15) y ocupa varios GB de disco, porque Docker descarga e instala TensorFlow para cada servicio. No cortes el proceso: mientras construye, los puertos 8000 y 8501 todavía no responden. Las siguientes veces es mucho más rápido. Al arrancar, los workers cargan el modelo (de 15 a 60 s) y luego se registran en el coordinador. El simulador manda las 100 fotos y termina; los demás servicios siguen corriendo. La terminal se queda mostrando logs: es normal, no la cierres.

4. Comprobar que funciona:
   - Dashboard: http://localhost:8501 (si Chrome ofrece traducir la página, recházalo: traduce mal las etiquetas; debe mostrar los 2 nodos vivos y los resultados llegando).
   - Estado del coordinador: http://localhost:8000/stats. Debe llegar a `"done": 100`, con `"failed": 0` y `"nodes_alive": 2`. Con las 100 fotos tarda unos 5 minutos.

5. Apagar: Ctrl + C en la terminal y luego

```
   docker compose -f infra/docker-compose.yml down -v
```

   El `-v` borra el estado guardado del coordinador. Sin él, las tareas de la corrida anterior se quedan en su base de datos y la siguiente prueba empieza con ellas.

Si los pesos están en otra carpeta, define `WEIGHTS_DIR` antes de levantar. En Windows (Command Prompt): `set WEIGHTS_DIR=C:\ruta\a\weights`.

## Probar la tolerancia a fallos

`tests/chaos.py` levanta el sistema, manda las 100 fotos y provoca una falla (necesita Python 3.11 y Docker abierto; borra el estado del coordinador):

```
py -3.11 tests/chaos.py worker       # mata un worker a media tarea: otro toma su tarea y terminan las 100
py -3.11 tests/chaos.py coordinador  # reinicia el coordinador a media carga: retoma desde SQLite
```

Más detalle en `tests/README.md`.

## Problemas comunes

- **Un worker se cae al arrancar o dice que no encuentra el modelo:** falta `model/weights/modelo_tomate_ft.keras`.
- **Un contenedor sale con código 137:** a Docker le falta memoria. En Docker Desktop > Settings > Resources sube la memoria asignada.
- **Un puerto está ocupado** (8000 u 8501): cierra el programa que lo usa, o apaga una corrida anterior con el `down -v` de arriba.
- **Los números no empiezan en cero:** quedó estado de una corrida anterior. Apaga con `down -v`.

## Equipo

Jazmin (coordinador y repositorio), Abi (modelo), Angie (worker), JP (dashboard) y Jhonny (infraestructura con Docker, simulador y pruebas de caos).