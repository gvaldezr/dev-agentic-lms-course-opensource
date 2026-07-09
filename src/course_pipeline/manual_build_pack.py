from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any


def _slugify(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or fallback


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _join_list(values: list[Any] | None) -> str:
    if not values:
        return ""
    lines = [f"- {_safe_text(v)}" for v in values if _safe_text(v)]
    return "\n".join(lines)


def _parse_phase(value: Any) -> tuple[str, str]:
    """Devuelve (duracion, instrucciones) para inicio/desarrollo/cierre.

    Acepta dict directo o cadena con dict serializado."""
    if value is None:
        return "", ""

    if isinstance(value, dict):
        mins = _safe_text(value.get("duracion_min"))
        instr = _safe_text(value.get("instrucciones"))
        if not instr:
            instr = _safe_text(value)
        return mins, instr

    if isinstance(value, str):
        txt = value.strip()
        if txt.startswith("{") and "instrucciones" in txt:
            try:
                parsed = ast.literal_eval(txt)
                if isinstance(parsed, dict):
                    return _parse_phase(parsed)
            except Exception:
                pass
        return "", txt

    return "", _safe_text(value)


def _render_ada_html(ada: dict[str, Any]) -> str:
    nombre = _html_escape(_safe_text(ada.get("nombre")))
    objetivo = _html_escape(_safe_text(ada.get("objetivo")))
    resultado = _html_escape(_safe_text(ada.get("resultado_aprendizaje")))
    tipo = _html_escape(_safe_text(ada.get("tipo_actividad")))

    sesiones = ada.get("sesiones_desarrolladas") or []
    lecturas = ada.get("lecturas_fundamentacion") or []
    presentacion = ada.get("presentacion") or {}
    presentacion_html = _safe_text(presentacion.get("html"))

    wrap_s = "font-family:'Segoe UI',system-ui,sans-serif;max-width:980px;margin:0 auto;color:#333;line-height:1.6;background:#f8f9fa;padding:18px;border-radius:10px;"
    h1_s = "margin:0 0 10px 0;color:#002f6c;font-weight:800;font-size:2rem;"
    hr_s = "border:none;border-top:2px solid #d7dde6;margin:18px 0;"
    section_s = "background:#fff;border:1px solid #d8dde6;border-radius:10px;padding:14px 16px;margin:0 0 12px 0;"
    h2_s = "margin:0 0 10px 0;color:#002f6c;font-size:1.2rem;border-bottom:2px solid #D4AF37;padding-bottom:6px;"
    details_s = "margin:10px 0;border:1px solid #d8dde6;border-radius:8px;background:#fff;"
    summary_s = "cursor:pointer;font-weight:700;color:#002f6c;padding:10px 12px;background:#f1f4f8;border-radius:8px;"
    body_s = "padding:10px 12px 12px 12px;"
    pre_s = "white-space:pre-wrap;background:#f8f9fb;border:1px solid #e2e7f0;border-radius:6px;padding:10px;"
    note_s = "background:#fff7e6;border-left:4px solid #D4AF37;padding:10px 12px;border-radius:6px;"

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append("<html lang=\"es\"><head><meta charset=\"utf-8\">")
    parts.append("<title>Contenido ADA</title></head><body>")
    parts.append(f"<div style=\"{wrap_s}\">")

    parts.append(f"<h1 style=\"{h1_s}\">{nombre or 'ADA'}</h1>")
    parts.append(f"<section style=\"{section_s}\">")
    parts.append(f"<h2 style=\"{h2_s}\">Ficha</h2>")
    parts.append(f"<p><b>Tipo:</b> {tipo or 'N/A'}</p>")
    parts.append(f"<p><b>Objetivo:</b> {objetivo or 'N/A'}</p>")
    parts.append(f"<p><b>Resultado de aprendizaje:</b> {resultado or 'N/A'}</p>")
    parts.append("</section>")

    parts.append(f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">Sesiones</h2>")
    if sesiones:
        for s in sesiones:
            n = _html_escape(_safe_text(s.get("sesion") or s.get("numero") or ""))
            tema = _html_escape(_safe_text(s.get("tema")))
            obj = _html_escape(_safe_text(s.get("objetivo_aprendizaje")))
            inicio_min, inicio_txt = _parse_phase(s.get("inicio"))
            des_min, des_txt = _parse_phase(s.get("desarrollo"))
            cierre_min, cierre_txt = _parse_phase(s.get("cierre"))
            summary = f"Sesion {n}"
            if tema:
                summary += f" · {tema}"
            parts.append(f"<details style=\"{details_s}\">")
            parts.append(f"<summary style=\"{summary_s}\">{summary}</summary>")
            parts.append(f"<div style=\"{body_s}\">")
            if tema:
                parts.append(f"<p><b>Tema:</b> {tema}</p>")
            if obj:
                parts.append(f"<p><b>Objetivo de sesion:</b> {obj}</p>")
            if inicio_txt:
                pref = f"({inicio_min} min) " if inicio_min else ""
                parts.append(f"<p><b>Inicio:</b> {_html_escape(pref + inicio_txt)}</p>")
            if des_txt:
                pref = f"({des_min} min) " if des_min else ""
                parts.append(f"<p><b>Desarrollo:</b> {_html_escape(pref + des_txt)}</p>")
            if cierre_txt:
                pref = f"({cierre_min} min) " if cierre_min else ""
                parts.append(f"<p><b>Cierre:</b> {_html_escape(pref + cierre_txt)}</p>")
            parts.append("</div>")
            parts.append("</details>")
    else:
        parts.append("<p>Sin sesiones registradas.</p>")
    parts.append("</section>")

    parts.append(f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">Presentacion</h2>")
    if presentacion_html:
        parts.append(f"<p style=\"{note_s}\"><strong>Nota:</strong> Moodle puede eliminar estilos y iframes por seguridad.</p>")
        parts.append("<p>Usa el archivo <code>presentacion.html</code> de esta ADA y cargalo como recurso <strong>Archivo</strong> o <strong>URL</strong> en Moodle.</p>")
        parts.append("<p>Ruta en este paquete: <code>adas/&lt;ada_slug&gt;/presentacion.html</code></p>")
    else:
        parts.append("<p>Sin presentacion disponible.</p>")
    parts.append("</section>")

    parts.append(f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">Lecturas por eje</h2>")
    if lecturas:
        for idx, lectura in enumerate(lecturas, start=1):
            eje = _html_escape(_safe_text(lectura.get("fundamento")))
            texto = _html_escape(_safe_text(lectura.get("lectura")))
            refs = lectura.get("referencias_apa") or []
            parts.append(f"<details style=\"{details_s}\">")
            parts.append(f"<summary style=\"{summary_s}\">{idx}. {eje or 'Eje tematico'}</summary>")
            parts.append(f"<div style=\"{body_s}\">")
            if texto:
                parts.append(f"<pre style=\"{pre_s}\">{texto}</pre>")
            if refs:
                parts.append("<h4>Referencias (APA)</h4><ul>")
                for ref in refs:
                    parts.append(f"<li>{_html_escape(_safe_text(ref))}</li>")
                parts.append("</ul>")
            parts.append("</div>")
            parts.append("</details>")
    else:
        parts.append("<p>Sin lecturas registradas.</p>")
    parts.append("</section>")
    parts.append("</div>")

    parts.append("</body></html>")
    return "".join(parts)


def _render_entregable_txt(ada: dict[str, Any]) -> str:
    nombre = _safe_text(ada.get("nombre"))
    objetivo = _safe_text(ada.get("objetivo"))
    resultado = _safe_text(ada.get("resultado_aprendizaje"))
    instrumento = _safe_text(ada.get("instrumento_evaluacion"))
    evidencias = ada.get("evidencias_aprendizaje") or []
    contenidos = ada.get("contenidos_a_desarrollar") or []

    sections = [
        f"ADA: {nombre}",
        "",
        f"Objetivo: {objetivo}",
        f"Resultado de aprendizaje: {resultado}",
        "",
        "Contenidos a desarrollar:",
        _join_list(contenidos) or "- N/A",
        "",
        "Evidencias de aprendizaje:",
        _join_list(evidencias) or "- N/A",
        "",
        f"Instrumento de evaluacion sugerido: {instrumento or 'N/A'}",
    ]
    return "\n".join(sections).strip() + "\n"


def _collect_all_adas(ada_structure: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not ada_structure:
        return []

    all_adas: list[dict[str, Any]] = []
    for periodo in ada_structure.get("periodos") or []:
        periodo_num = periodo.get("periodo")
        for idx, ada in enumerate(periodo.get("adas") or [], start=1):
            item = dict(ada)
            item["periodo"] = periodo_num
            item["orden_en_periodo"] = idx
            all_adas.append(item)

        fase = periodo.get("fase_proyecto_integrador") or {}
        integradora = fase.get("ada_integradora_producto")
        if integradora:
            item = dict(integradora)
            item["periodo"] = periodo_num
            item["orden_en_periodo"] = "integradora"
            all_adas.append(item)

    return all_adas


def export_manual_build_pack(
    output_dir: Path,
    slug: str,
    timestamp: str,
    course_name: str,
    ada_structure: dict[str, Any] | None,
    question_bank: list[dict[str, Any]] | None,
    quiz_items: list[dict[str, Any]] | None,
) -> Path:
    pack_dir = output_dir / f"manual_build_pack_{slug}_{timestamp}"
    adas_dir = pack_dir / "adas"
    adas_dir.mkdir(parents=True, exist_ok=True)

    all_adas = _collect_all_adas(ada_structure)
    outline = {
        "curso": course_name,
        "timestamp": timestamp,
        "total_periodos": len((ada_structure or {}).get("periodos") or []),
        "total_adas": len(all_adas),
        "total_reactivos_banco": len(question_bank or []),
        "total_reactivos_quiz": len(quiz_items or []),
        "adas": [],
    }

    checklist_lines = [
        "# Checklist de publicacion Moodle (sin API)",
        "",
        f"Curso: {course_name}",
        f"Paquete: {pack_dir.name}",
        "",
        "## Pasos recomendados",
        "",
        "1. Crear secciones del curso por periodo y ADA.",
        "2. Importar banco y quiz desde los XML generados por el pipeline.",
        "3. Por cada ADA, crear una Pagina o Libro y pegar el contenido de `contenido.html`.",
        "4. Crear una Tarea por ADA y usar `entregable.txt` como base de instrucciones.",
        "5. Verificar orden, fechas, criterios y visibilidad para estudiantes.",
        "",
        "## Mapeo ADA -> archivos",
        "",
    ]

    for idx, ada in enumerate(all_adas, start=1):
        ada_name = _safe_text(ada.get("nombre")) or f"ADA {idx}"
        ada_slug = f"{idx:02d}_{_slugify(ada_name, fallback=f'ada_{idx:02d}') }"
        ada_path = adas_dir / ada_slug
        ada_path.mkdir(parents=True, exist_ok=True)

        contenido_html = _render_ada_html(ada)
        entregable_txt = _render_entregable_txt(ada)
        presentacion_html = _safe_text((ada.get("presentacion") or {}).get("html"))

        contenido_path = ada_path / "contenido.html"
        entregable_path = ada_path / "entregable.txt"
        presentacion_path = ada_path / "presentacion.html"
        contenido_path.write_text(contenido_html, encoding="utf-8")
        entregable_path.write_text(entregable_txt, encoding="utf-8")
        if presentacion_html:
            presentacion_path.write_text(presentacion_html, encoding="utf-8")

        outline["adas"].append(
            {
                "periodo": ada.get("periodo"),
                "orden_en_periodo": ada.get("orden_en_periodo"),
                "nombre": ada_name,
                "tipo_actividad": _safe_text(ada.get("tipo_actividad")),
                "sesiones": len(ada.get("sesiones_desarrolladas") or []),
                "lecturas": len(ada.get("lecturas_fundamentacion") or []),
                "carpeta": str((Path("adas") / ada_slug).as_posix()),
                "contenido_html": str((Path("adas") / ada_slug / "contenido.html").as_posix()),
                "entregable_txt": str((Path("adas") / ada_slug / "entregable.txt").as_posix()),
                "presentacion_html": (
                    str((Path("adas") / ada_slug / "presentacion.html").as_posix()) if presentacion_html else ""
                ),
            }
        )
        extra = " + `adas/{}/presentacion.html`".format(ada_slug) if presentacion_html else ""
        checklist_lines.append(
            f"- {ada_name}: `adas/{ada_slug}/contenido.html` + `adas/{ada_slug}/entregable.txt`{extra}"
        )

    outline_path = pack_dir / "outline_curso.json"
    checklist_path = pack_dir / "checklist_publicacion.md"
    outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
    checklist_path.write_text("\n".join(checklist_lines).strip() + "\n", encoding="utf-8")

    return pack_dir
