"""Dashboard de Invernodo (Streamlit).

Correr desde la raíz del repo:
    streamlit run dashboard/app.py
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# Permite "from shared..." y "from dashboard..." corriendo desde cualquier carpeta.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time  # noqa: E402

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import alerts, data_source  # noqa: E402
from shared.config import COORDINATOR_URL  # noqa: E402

REFRESH_S = 2
TZ = ZoneInfo(os.getenv("DASHBOARD_TZ", "America/Mexico_City"))

# Mismo orden que shared/labels.json. "sana" en verde, problemas en tonos cálidos.
LABEL_COLORS = {
    "sana": "#2e9e5b",
    "hongo": "#d98c1f",
    "plaga": "#c9372c",
    "virus": "#8e44ad",
    "bacteria": "#2b6cb0",
}

st.set_page_config(page_title="Invernodo", page_icon="🌿", layout="wide")


def fmt_time(ts: float | None) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime("%H:%M:%S") if ts else "—"


@st.fragment(run_every=REFRESH_S)
def render() -> None:
    try:
        data = data_source.load()
    except Exception as e:  # coordinador caído o respuesta con otra forma
        st.error(f"No pude leer el coordinador en {COORDINATOR_URL}: {e}")
        return

    nodes, results, tasks, stats = data["nodes"], data["results"], data["tasks"], data["stats"]
    now = time.time()

    # ---- Contadores (/stats) ----
    c = st.columns(7)
    c[0].metric("Tareas", stats["total_tasks"])
    c[1].metric("Pendientes", stats["pending"])
    c[2].metric("Asignadas", stats["assigned"])
    c[3].metric("Listas", stats["done"])
    c[4].metric("Fallidas", stats["failed"])
    c[5].metric("Nodos vivos", stats["nodes_alive"])
    c[6].metric("Nodos caídos", stats["nodes_dead"])

    left, right = st.columns([3, 2])

    # ---- Nodos (/nodes) ----
    with left:
        st.subheader("Nodos")
        df_nodes = pd.DataFrame([{
            "Nodo": n.node_id,
            "Estado": n.status.value,
            "Último latido": f"hace {now - n.last_heartbeat:.0f} s",
            "Tareas hechas": n.tasks_done,
        } for n in nodes])
        if df_nodes.empty:
            st.info("Sin nodos registrados.")
        else:
            def color_row(row):
                bad = row["Estado"] == "DEAD"
                return ["background-color: #7f1d1d; color: white" if bad else ""] * len(row)
            st.dataframe(df_nodes.style.apply(color_row, axis=1), hide_index=True, width="stretch")

    # ---- Alertas ----
    with right:
        st.subheader("Alertas")
        found = alerts.compute(results, now)
        if not found:
            st.success("Sin alertas.")
        for a in found[:8]:
            (st.error if a.level == "ZONA" else st.warning)(f"**{a.level}** · {a.message} · {fmt_time(a.when)}")
        if len(found) > 8:
            st.caption(f"+{len(found) - 8} alertas más")

    # ---- Vista por zona (/results) ----
    st.subheader("Por zona")
    if results:
        df_res = pd.DataFrame([r.model_dump(mode="json") for r in results])
        counts = df_res.groupby(["zone_id", "label"]).size().reset_index(name="fotos")
        chart = alt.Chart(counts).mark_bar().encode(
            x=alt.X("zone_id:N", title="Zona", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("fotos:Q", title="Fotos"),
            color=alt.Color("label:N", title="Etiqueta",
                            scale=alt.Scale(domain=list(LABEL_COLORS), range=list(LABEL_COLORS.values()))),
            order=alt.Order("label_order:Q"),
            tooltip=["zone_id", "label", "fotos"],
        ).transform_calculate(
            label_order=f"indexof({list(LABEL_COLORS)}, datum.label)"
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("Aún no hay resultados.")

    # ---- Reasignadas (/tasks) y últimos resultados ----
    a, b = st.columns(2)
    with a:
        reassigned = [t for t in tasks if t.attempts > 1]
        st.subheader(f"Tareas reasignadas ({len(reassigned)})")
        st.dataframe(pd.DataFrame([{
            "Tarea": t.task_id[:8], "Zona": t.zone_id, "Intentos": t.attempts,
            "Estado": t.status.value, "Nodo final": t.assigned_to or "—",
        } for t in reassigned]), hide_index=True, width="stretch")
    with b:
        st.subheader("Últimos resultados")
        latest = sorted(results, key=lambda r: r.completed_at or 0, reverse=True)[:15]
        st.dataframe(pd.DataFrame([{
            "Hora": fmt_time(r.completed_at), "Zona": r.zone_id, "Etiqueta": r.label,
            "Confianza": f"{r.confidence:.0%}", "Nodo": r.node_id, "Latencia ms": r.latency_ms,
        } for r in latest]), hide_index=True, width="stretch")

    st.caption(f"Fuente: {'datos falsos' if data_source.USE_FAKE else COORDINATOR_URL} · "
               f"se actualiza cada {REFRESH_S} s · {fmt_time(now)}")


st.title("🌿 Invernodo")
render()
