from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list[str]:
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def _build_checklist_for_ada(ada: dict[str, Any], max_items: int = 8) -> dict[str, Any]:
    nombre = str(ada.get("nombre") or "ADA").strip()
    objetivo = str(ada.get("objetivo") or "").strip()
    resultado = str(ada.get("resultado_aprendizaje") or "").strip()
    evidencias = _as_list(ada.get("evidencias_aprendizaje"))
    fundamentos = _as_list(ada.get("fundamentos_tematicos_requeridos"))

    criterios: list[str] = []

    if objetivo:
        criterios.append("El producto entregado responde al objetivo estrategico del ADA con claridad y pertinencia.")
    if resultado:
        criterios.append("El producto integra de forma coherente el resultado de aprendizaje del ADA.")

    for ev in evidencias[:4]:
        criterios.append(f"Evalua de forma completa el producto de evidencia solicitado: {ev}")

    if fundamentos:
        criterios.append(
            "El producto integra fundamentos tematicos de la unidad y justifica decisiones con base en las lecturas."
        )

    instrumento = str(ada.get("instrumento_evaluacion") or "").strip()
    if instrumento:
        criterios.append(f"Cumple los criterios del instrumento de evaluacion ({instrumento}).")

    criterios.extend(
        [
            "Presenta organizacion, redaccion y formato academico acorde al tipo de producto solicitado.",
            "Se entrega completo, en tiempo y con criterios verificables de calidad.",
        ]
    )

    # Deduplicar conservando orden.
    seen: set[str] = set()
    unique = []
    for c in criterios:
        key = c.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)

    unique = unique[:max_items] if unique else ["Entrega el producto solicitado con calidad academica."]

    items = []
    for i, c in enumerate(unique, start=1):
        items.append(
            {
                "id": f"LC{i:02d}",
                "criterio": c,
                "valor": 1,
                "cumple": None,
                "observaciones": "",
            }
        )

    return {
        "nombre": f"Lista de cotejo - {nombre}",
        "descripcion": "Instrumento para valorar el cumplimiento de criterios del entregable.",
        "total_criterios": len(items),
        "puntaje_total": len(items),
        "criterios": items,
    }


def attach_checklists_to_ada_structure(ada_structure: dict[str, Any]) -> int:
    """Adjunta `lista_cotejo_entregable` a cada ADA (incluida integradora).

    Returns:
        Cantidad de ADAs procesadas.
    """
    total = 0
    for periodo in ada_structure.get("periodos") or []:
        adas = list(periodo.get("adas") or [])
        fase = periodo.get("fase_proyecto_integrador") or {}
        integradora = fase.get("ada_integradora_producto")
        if integradora:
            adas.append(integradora)

        for ada in adas:
            ada["lista_cotejo_entregable"] = _build_checklist_for_ada(ada)
            total += 1

    return total
