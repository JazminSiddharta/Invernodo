"""Reglas de alertas del dashboard (no cambian shared/).

- CRÍTICA: un resultado con etiqueta distinta de "sana" y confianza alta.
- ZONA EN RIESGO: muchas detecciones no sanas de la misma zona en poco tiempo.

Los umbrales están aquí arriba para ajustarlos fácil en la demo.
"""

import time
from dataclasses import dataclass

from shared.contracts import Result

CRITICAL_CONFIDENCE = 0.90   # confianza mínima para alerta crítica
ZONE_WINDOW_S = 300          # ventana de tiempo para alerta de zona (5 min)
ZONE_MIN_DETECTIONS = 5      # detecciones no sanas en la ventana para alertar
HEALTHY_LABEL = "sana"


@dataclass
class Alert:
    level: str      # "CRÍTICA" o "ZONA"
    zone_id: str
    message: str
    when: float | None


def compute(results: list[Result], now: float | None = None) -> list[Alert]:
    now = now or time.time()
    alerts: list[Alert] = []

    # 1) Críticas: una por resultado.
    for r in results:
        if r.label != HEALTHY_LABEL and r.confidence >= CRITICAL_CONFIDENCE:
            alerts.append(Alert(
                level="CRÍTICA", zone_id=r.zone_id, when=r.completed_at,
                message=f"{r.zone_id}: {r.label} con {r.confidence:.0%} de confianza ({r.node_id})",
            ))

    # 2) Zona en riesgo: solo resultados con completed_at dentro de la ventana.
    recent: dict[str, list[Result]] = {}
    for r in results:
        if r.label != HEALTHY_LABEL and r.completed_at is not None and now - r.completed_at <= ZONE_WINDOW_S:
            recent.setdefault(r.zone_id, []).append(r)
    for zone, rs in sorted(recent.items()):
        if len(rs) >= ZONE_MIN_DETECTIONS:
            top = max({r.label for r in rs}, key=lambda lb: sum(r.label == lb for r in rs))
            alerts.append(Alert(
                level="ZONA", zone_id=zone, when=max(r.completed_at for r in rs),
                message=f"{zone} con posible {top}: {len(rs)} detecciones en {ZONE_WINDOW_S // 60} min",
            ))

    # Zona primero, luego las más recientes (las que no tienen hora al final).
    alerts.sort(key=lambda a: (a.level != "ZONA", -(a.when or 0)))
    return alerts
