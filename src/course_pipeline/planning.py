from __future__ import annotations

from math import ceil
from typing import Any


def build_operational_plan(
    total_weeks: int = 14,
    periods: int = 1,
    adas_per_period: int = 2,
    total_adas: int | None = 5,
    include_integrator_phase: bool = False,
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

    if total_adas is not None and total_adas < 1:
        total_adas = 1

    # Distribucion de ADAs por periodo.
    adas_distribution: list[int] = []
    if total_adas is None:
        adas_distribution = [max(1, adas_per_period) for _ in range(periods)]
    else:
        base_adas = total_adas // periods
        extra_adas = total_adas % periods
        for period_index in range(1, periods + 1):
            adas_distribution.append(base_adas + (1 if period_index <= extra_adas else 0))

    ada_global_counter = 1

    for period_index in range(1, periods + 1):
        period_weeks = base_weeks + (1 if period_index <= extra_weeks else 0)
        period_start_week = week_cursor
        period_end_week = week_cursor + period_weeks - 1
        period_sessions = period_weeks * sessions_per_week

        adas_this_period = max(1, adas_distribution[period_index - 1])
        slots = adas_this_period + (1 if include_integrator_phase else 0)
        base_slot_sessions = period_sessions // max(1, slots)
        extra_slot_sessions = period_sessions % max(1, slots)

        slot_spans: list[tuple[int, int]] = []
        cursor = session_cursor
        for slot_index in range(slots):
            slot_len = base_slot_sessions + (1 if slot_index < extra_slot_sessions else 0)
            slot_len = max(1, slot_len)
            start = cursor
            end = start + slot_len - 1
            slot_spans.append((start, end))
            cursor = end + 1

        # Ajuste final para garantizar cobertura exacta del periodo.
        if slot_spans:
            last_start, _ = slot_spans[-1]
            slot_spans[-1] = (last_start, session_cursor + period_sessions - 1)

        adas: list[dict[str, Any]] = []
        for ada_index in range(1, adas_this_period + 1):
            ada_start, ada_end = slot_spans[ada_index - 1]
            adas.append(
                {
                    "nombre": f"ACTIVIDAD No. {ada_global_counter}",
                    "sesion_inicio": ada_start,
                    "sesion_fin": ada_end,
                    "duracion_sesiones": max(1, ada_end - ada_start + 1),
                }
            )
            ada_global_counter += 1

        integrator_payload: dict[str, Any] | None = None
        if include_integrator_phase:
            integrator_start, integrator_end = slot_spans[-1]
            integrator_payload = {
                "nombre": f"Fase PI {period_index}",
                "sesion_inicio": integrator_start,
                "sesion_fin": integrator_end,
                "duracion_sesiones": max(1, integrator_end - integrator_start + 1),
            }

        period_items.append(
            {
                "periodo": period_index,
                "semanas": {
                    "inicio": period_start_week,
                    "fin": period_end_week,
                    "cantidad": period_weeks,
                },
                "adas": adas,
                "fase_proyecto_integrador": integrator_payload,
            }
        )

        week_cursor = period_end_week + 1
        session_cursor = session_cursor + period_sessions

    return {
        "reglas": {
            "semanas_totales": total_weeks,
            "periodos_proceso": periods,
            "adas_totales": total_adas if total_adas is not None else periods * adas_per_period,
            "adas_por_periodo": adas_per_period,
            "incluye_fase_integradora": include_integrator_phase,
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
