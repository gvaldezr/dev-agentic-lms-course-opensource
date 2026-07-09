from __future__ import annotations

from math import ceil
from typing import Any


def build_operational_plan(
    total_weeks: int = 15,
    periods: int = 3,
    adas_per_period: int = 2,
    session_minutes: list[int] | None = None,
    template_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Tiempo efectivo: cada semana tiene una sesion de 90 min y una de 45 min.
    session_minutes = list(session_minutes) if session_minutes else [90, 45]
    sessions_per_week = len(session_minutes)
    minutes_per_week = sum(session_minutes)
    sessions_total = total_weeks * sessions_per_week
    minutes_total = total_weeks * minutes_per_week
    hours_total = round(minutes_total / 60, 2)

    base_weeks = total_weeks // periods
    extra_weeks = total_weeks % periods

    period_items: list[dict[str, Any]] = []
    week_cursor = 1
    session_cursor = 1

    for period_index in range(1, periods + 1):
        period_weeks = base_weeks + (1 if period_index <= extra_weeks else 0)
        period_start_week = week_cursor
        period_end_week = week_cursor + period_weeks - 1
        period_sessions = period_weeks * sessions_per_week

        adas: list[dict[str, Any]] = []
        ada_session_span = max(1, period_sessions // (adas_per_period + 1))
        ada_start = session_cursor

        for ada_index in range(1, adas_per_period + 1):
            ada_end = min(ada_start + ada_session_span - 1, session_cursor + period_sessions - 1)
            adas.append(
                {
                    "nombre": f"ADA {period_index}.{ada_index}",
                    "sesion_inicio": ada_start,
                    "sesion_fin": ada_end,
                    "duracion_sesiones": max(1, ada_end - ada_start + 1),
                }
            )
            ada_start = ada_end + 1

        integrator_start = max(session_cursor, ada_start)
        integrator_end = session_cursor + period_sessions - 1

        period_items.append(
            {
                "periodo": period_index,
                "semanas": {
                    "inicio": period_start_week,
                    "fin": period_end_week,
                    "cantidad": period_weeks,
                },
                "adas": adas,
                "fase_proyecto_integrador": {
                    "nombre": f"Fase PI {period_index}",
                    "sesion_inicio": integrator_start,
                    "sesion_fin": integrator_end,
                    "duracion_sesiones": max(1, integrator_end - integrator_start + 1),
                },
            }
        )

        week_cursor = period_end_week + 1
        session_cursor = integrator_end + 1

    return {
        "reglas": {
            "semanas_totales": total_weeks,
            "periodos_proceso": periods,
            "adas_por_periodo": adas_per_period,
            "sesiones_por_semana": sessions_per_week,
            "minutos_por_sesion": session_minutes,
            "minutos_por_semana": minutes_per_week,
            "sesiones_totales": sessions_total,
            "minutos_totales": minutes_total,
            "horas_totales": hours_total,
        },
        "periodizacion": period_items,
        "contexto_plantilla": template_context or {},
    }
