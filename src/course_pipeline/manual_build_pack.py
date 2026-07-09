from __future__ import annotations

import ast
import json
import os
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


def _iter_ada_refs(ada_structure: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not ada_structure:
        return []

    refs: list[dict[str, Any]] = []
    for periodo in ada_structure.get("periodos") or []:
        refs.extend(periodo.get("adas") or [])
        fase = periodo.get("fase_proyecto_integrador") or {}
        integradora = fase.get("ada_integradora_producto")
        if isinstance(integradora, dict):
            refs.append(integradora)
    return refs


def _detect_github_pages_base_url(repo_root: Path) -> str:
    explicit = (os.getenv("GITHUB_PAGES_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit

    git_config = repo_root / ".git" / "config"
    if not git_config.exists():
        return ""

    try:
        content = git_config.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    match = re.search(r"url\s*=\s*(.+)", content)
    if not match:
        return ""

    remote = match.group(1).strip()

    https_match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not https_match:
        return ""

    owner = https_match.group(1)
    repo = https_match.group(2)
    if repo.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner}.github.io"
    return f"https://{owner}.github.io/{repo}"


def publish_presentations_to_github_pages(
    ada_structure: dict[str, Any] | None,
    slug: str,
    timestamp: str,
    repo_root: Path,
    github_pages_base_url: str | None = None,
) -> dict[str, Any]:
    """Publica presentaciones en `docs/` y adjunta URL publica en cada ADA.

    Retorna un resumen de publicacion para trazabilidad.
    """
    base_url = (github_pages_base_url or "").strip().rstrip("/")
    if not base_url:
        base_url = _detect_github_pages_base_url(repo_root)

    docs_root = repo_root / "docs"
    publish_root = docs_root / "presentaciones" / slug / timestamp
    publish_root.mkdir(parents=True, exist_ok=True)
    (docs_root / ".nojekyll").write_text("", encoding="utf-8")

    total = 0
    published = 0
    items: list[dict[str, str]] = []
    for idx, ada in enumerate(_iter_ada_refs(ada_structure), start=1):
        total += 1
        presentacion_html = _safe_text((ada.get("presentacion") or {}).get("html"))
        ada_name = _safe_text(ada.get("nombre")) or f"ADA {idx}"
        ada_slug = f"{idx:02d}_{_slugify(ada_name, fallback=f'ada_{idx:02d}') }"
        if not presentacion_html:
            ada["presentacion_public_url"] = ""
            continue

        target_dir = publish_root / ada_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "index.html"
        target_file.write_text(presentacion_html, encoding="utf-8")

        rel = f"presentaciones/{slug}/{timestamp}/{ada_slug}/"
        public_url = f"{base_url}/{rel}" if base_url else rel
        ada["presentacion_public_url"] = public_url
        items.append({"ada": ada_name, "url": public_url, "path": str(target_file)})
        published += 1

    return {
        "base_url": base_url,
        "slug": slug,
        "timestamp": timestamp,
        "total_adas": total,
        "presentaciones_publicadas": published,
        "items": items,
    }


def _render_ada_html(ada: dict[str, Any]) -> str:
    nombre_raw = _safe_text(ada.get("nombre"))
    nombre = _html_escape(nombre_raw)
    actividad_no = _safe_text(ada.get("actividad_numero"))
    titulo_actividad = _html_escape(_safe_text(ada.get("titulo_actividad")))
    objetivo = _html_escape(_safe_text(ada.get("objetivo")))
    resultado = _html_escape(_safe_text(ada.get("resultado_aprendizaje")))
    tipo = _html_escape(_safe_text(ada.get("tipo_actividad")))
    duracion = _html_escape(_safe_text(ada.get("duracion")))
    puntaje = _html_escape(_safe_text(ada.get("puntaje") or "10"))
    contenidos = ada.get("contenidos_a_desarrollar") or []
    estrategias = ada.get("estrategias_ensenanza_aprendizaje") or []
    descripcion_actividad = _html_escape(_safe_text(ada.get("descripcion_actividad")))

    sesiones = ada.get("sesiones_desarrolladas") or []
    lecturas = ada.get("lecturas_fundamentacion") or []
    presentacion = ada.get("presentacion") or {}
    presentacion_html = _safe_text(presentacion.get("html"))
    presentacion_public_url = _safe_text(ada.get("presentacion_public_url"))
    lista = ada.get("lista_cotejo_entregable") or {}
    criterios = lista.get("criterios") or []

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

    if actividad_no:
        parts.append(f"<h1 style=\"{h1_s}\">ACTIVIDAD No. {actividad_no}</h1>")
    else:
        parts.append(f"<h1 style=\"{h1_s}\">{nombre or 'ACTIVIDAD'}</h1>")
    parts.append(f"<section style=\"{section_s}\">")
    parts.append(f"<h2 style=\"{h2_s}\">{titulo_actividad or nombre_raw or 'Actividad'}</h2>")
    parts.append(f"<p><b>Tipo:</b> {tipo or 'N/A'}</p>")
    parts.append(f"<p><b>Duracion:</b> {duracion or 'N/A'}</p>")
    parts.append(f"<p><b>Puntaje:</b> {puntaje} puntos</p>")
    parts.append(f"<p><b>Objetivo:</b> {objetivo or 'N/A'}</p>")
    parts.append(f"<p><b>Resultado de aprendizaje:</b> {resultado or 'N/A'}</p>")
    if contenidos:
        parts.append("<h3>Contenidos</h3><ul>")
        for item in contenidos:
            parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
        parts.append("</ul>")
    if estrategias:
        parts.append("<h3>Estrategias de ensenanza y aprendizaje</h3><ul>")
        for item in estrategias:
            parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
        parts.append("</ul>")
    if descripcion_actividad:
        parts.append(f"<p><b>Descripcion de la actividad:</b> {descripcion_actividad}</p>")
    parts.append("</section>")

    parts.append(f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">Lista de cotejo del entregable</h2>")
    if criterios:
        parts.append("<ol style=\"margin:0;padding-left:22px;\">")
        for c in criterios:
            crit = _html_escape(_safe_text(c.get("criterio")))
            val = _html_escape(_safe_text(c.get("valor") or "1"))
            parts.append(f"<li style=\"margin:8px 0;\">{crit} <span style=\"color:#666;\">({val} pt)</span></li>")
        parts.append("</ol>")
        parts.append("<p style=\"color:#555;\"><em>Escala sugerida: Cumple / No cumple.</em></p>")
    else:
        parts.append("<p>Sin lista de cotejo disponible.</p>")
    parts.append("</section>")

    parts.append(
        f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">DESCRIPCION DE LA ACTIVIDAD</h2>"
    )
    if sesiones:
        for s in sesiones:
            n = _html_escape(_safe_text(s.get("sesion") or s.get("numero") or ""))
            tema = _html_escape(_safe_text(s.get("tema")))
            obj = _html_escape(
                _safe_text(s.get("objetivo_especifico") or s.get("objetivo") or s.get("objetivo_aprendizaje"))
            )
            resumen = s.get("resumen_datos_esenciales") or []
            inicio_list = s.get("inicio_actividades") or []
            des_list = s.get("desarrollo_actividades") or []
            cierre_list = s.get("cierre_actividades") or []
            inicio_min, inicio_txt = _parse_phase(s.get("inicio"))
            des_min, des_txt = _parse_phase(s.get("desarrollo"))
            cierre_min, cierre_txt = _parse_phase(s.get("cierre"))
            total_min = _html_escape(_safe_text(s.get("duracion_min")))
            summary = f"SESION {n}"
            if total_min:
                summary += f" ({total_min} minutos)"
            if tema:
                summary += f" · {tema}"
            parts.append(f"<details style=\"{details_s}\">")
            parts.append(f"<summary style=\"{summary_s}\">{summary}</summary>")
            parts.append(f"<div style=\"{body_s}\">")
            if tema:
                parts.append(f"<p><b>Tema:</b> {tema}</p>")
            if obj:
                parts.append(f"<p><b>Objetivo especifico:</b> {obj}</p>")
            if resumen:
                parts.append("<p><b>Resumen de los datos esenciales de los temas a tratar</b></p><ul>")
                for item in resumen:
                    parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
                parts.append("</ul>")

            parts.append(f"<p><b>INICIO ({_html_escape(inicio_min or '')} minutos)</b></p>")
            if inicio_list:
                parts.append("<ol>")
                for item in inicio_list:
                    parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
                parts.append("</ol>")
            elif inicio_txt:
                parts.append(f"<p>{_html_escape(inicio_txt)}</p>")

            parts.append(f"<p><b>DESARROLLO ({_html_escape(des_min or '')} minutos)</b></p>")
            if des_list:
                parts.append("<ol>")
                for item in des_list:
                    parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
                parts.append("</ol>")
            elif des_txt:
                parts.append(f"<p>{_html_escape(des_txt)}</p>")

            parts.append(f"<p><b>CIERRE ({_html_escape(cierre_min or '')} minutos)</b></p>")
            if cierre_list:
                parts.append("<ol>")
                for item in cierre_list:
                    parts.append(f"<li>{_html_escape(_safe_text(item))}</li>")
                parts.append("</ol>")
            elif cierre_txt:
                parts.append(f"<p>{_html_escape(cierre_txt)}</p>")
            parts.append("</div>")
            parts.append("</details>")
    else:
        parts.append("<p>Sin sesiones registradas.</p>")
    parts.append("</section>")

    parts.append(f"<hr style=\"{hr_s}\"><section style=\"{section_s}\"><h2 style=\"{h2_s}\">Presentacion</h2>")
    if presentacion_public_url:
        iframe_style = (
            "width:100%;height:560px;border:1px solid #c9a24a;border-radius:8px;"
            "background:#0b1e3f;"
        )
        safe_url = _html_escape(presentacion_public_url)
        parts.append("<p>Presentacion embebida desde GitHub Pages:</p>")
        parts.append(
            f"<iframe src=\"{safe_url}\" style=\"{iframe_style}\" "
            "loading=\"lazy\" referrerpolicy=\"no-referrer\" "
            "title=\"Presentacion ADA\"></iframe>"
        )
        parts.append(f"<p>Si no carga el iframe, abre: <a href=\"{safe_url}\" target=\"_blank\" rel=\"noopener\">{safe_url}</a></p>")
    elif presentacion_html:
        parts.append(f"<p style=\"{note_s}\"><strong>Nota:</strong> Presentacion disponible localmente; publica primero en GitHub Pages para iframe remoto.</p>")
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
    lista = ada.get("lista_cotejo_entregable") or {}
    criterios = lista.get("criterios") or []

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
        "",
        "Lista de cotejo del entregable:",
        "\n".join(
            [
                f"- [{c.get('id','')}] {str(c.get('criterio','')).strip()} ({c.get('valor',1)} pt)"
                for c in criterios
                if str(c.get("criterio", "")).strip()
            ]
        )
        or "- N/A",
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
                "presentacion_public_url": _safe_text(ada.get("presentacion_public_url")),
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
