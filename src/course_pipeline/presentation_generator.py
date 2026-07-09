from __future__ import annotations

import html
import json
import logging
import re
from typing import Any

import requests

from . import llm_client
from .config import Settings


logger = logging.getLogger("course_pipeline.presentations")


class PresentationGenerationError(Exception):
    pass


STUDENT_PROFILE = (
    "Estudiantes de preparatoria de 5.º semestre de la Universidad Autonoma de "
    "Yucatan (UADY), de 16 a 18 anos, en Merida, Yucatan, Mexico."
)

PRESENTATION_SYSTEM_PROMPT = (
    "Eres un disenador experto de presentaciones y storyteller especializado en "
    "comunicacion educativa. Dominas tecnicas de pitch (gancho, problema, solucion, "
    "evidencia, llamada a la accion), copywriting persuasivo y narrativa visual. "
    "Disenas presentaciones para jovenes de preparatoria: claras, motivadoras, con "
    "ritmo, ejemplos cercanos a su vida en Merida y mensajes memorables. Cada "
    "diapositiva tiene UNA idea central, texto breve y de alto impacto. Evitas "
    "parrafos largos y tecnicismos sin explicar. No inventas datos que no esten en "
    "las lecturas proporcionadas."
)

MAX_SLIDES = 12
MIN_SLIDES = 7
MAX_READING_CHARS = 1800


def _extract_llm_text(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        if not text:
            raise PresentationGenerationError("Respuesta vacia del LLM al generar presentacion")
        return text

    if "choices" in data and data["choices"]:
        content = data["choices"][0].get("message", {}).get("content", "")
        if content:
            return str(content)

    ollama_content = data.get("message", {}).get("content", "")
    if ollama_content:
        return str(ollama_content)

    if "content" in data:
        return str(data["content"])

    raise PresentationGenerationError("No se pudo extraer texto de la respuesta del LLM")


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise PresentationGenerationError("La respuesta del LLM no contiene un objeto JSON valido")

    candidate = cleaned[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise PresentationGenerationError(f"JSON de presentacion invalido: {exc}") from exc


def _build_readings_block(readings: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, reading in enumerate(readings, start=1):
        fundamento = (reading.get("fundamento") or f"Eje {idx}").strip()
        lectura = (reading.get("lectura") or "").strip()
        if lectura:
            lectura_short = lectura[:MAX_READING_CHARS]
            lines.append(f"EJE {idx}: {fundamento}\n{lectura_short}")
        else:
            lines.append(f"EJE {idx}: {fundamento}\n(sin texto de lectura disponible)")
    return "\n\n".join(lines) if lines else "(sin lecturas disponibles)"


def _build_deliverable_block(ada: dict[str, Any]) -> str:
    """Resume el entregable unico del ADA (objetivo, evidencias, instrumento) para
    que la presentacion prepare al estudiante a producirlo."""
    lines: list[str] = []

    tipo = (ada.get("tipo_actividad") or "").strip()
    if tipo:
        lines.append(f"Tipo de actividad: {tipo}")

    resultado = (ada.get("resultado_aprendizaje") or "").strip()
    if resultado:
        lines.append(f"Resultado de aprendizaje: {resultado}")

    evidencias = ada.get("evidencias_aprendizaje")
    if isinstance(evidencias, str):
        evidencias_list = [evidencias]
    else:
        evidencias_list = [str(e).strip() for e in (evidencias or []) if str(e).strip()]
    if evidencias_list:
        evidencias_txt = "\n".join(f"- {e}" for e in evidencias_list)
        lines.append(f"Evidencias de aprendizaje a entregar:\n{evidencias_txt}")

    instrumento = (ada.get("instrumento_evaluacion") or "").strip()
    if instrumento:
        lines.append(f"Instrumento de evaluacion: {instrumento}")

    contenidos = ada.get("contenidos_a_desarrollar")
    if isinstance(contenidos, list) and contenidos:
        contenidos_txt = ", ".join(str(c).strip() for c in contenidos if str(c).strip())
        if contenidos_txt:
            lines.append(f"Contenidos a desarrollar: {contenidos_txt}")

    return "\n".join(lines) if lines else "(sin entregable especificado)"


def _request_slides(
    settings: Settings,
    ada_name: str,
    objetivo: str,
    readings_block: str,
    deliverable_block: str,
) -> dict[str, Any]:
    user_prompt = (
        f"ADA: {ada_name}\n"
        f"Objetivo de aprendizaje: {objetivo or 'No especificado'}\n\n"
        f"Publico: {STUDENT_PROFILE}\n\n"
        "Lecturas de fundamentacion del ADA (una por eje tematico):\n"
        f"{readings_block}\n\n"
        "Entregable unico del ADA (lo que el estudiante debe producir y como se evalua):\n"
        f"{deliverable_block}\n\n"
        "Disena una presentacion con narrativa de pitch basada en estas lecturas y "
        "orientada a que el estudiante comprenda y logre producir el entregable unico "
        "del ADA. Apoyate UNICAMENTE en la informacion proporcionada (lecturas y "
        "entregable). Aplica storytelling (gancho -> tension/problema -> ideas clave -> "
        "ejemplo cercano a Merida -> que se espera del entregable -> llamada a la accion) "
        "y copywriting persuasivo.\n"
        f"Genera entre {MIN_SLIDES} y {MAX_SLIDES} diapositivas.\n"
        "Devuelve EXCLUSIVAMENTE un objeto JSON valido con esta forma exacta:\n"
        "{\n"
        '  "titulo": "titulo potente y atractivo del deck",\n'
        '  "subtitulo": "frase corta de apoyo",\n'
        '  "slides": [\n'
        '    {"tipo": "portada|gancho|idea|ejemplo|actividad|cierre",\n'
        '     "titulo": "titulo de la diapositiva (max 8 palabras)",\n'
        '     "subtitulo": "opcional, frase corta",\n'
        '     "contenido": "opcional, 1-2 frases de alto impacto",\n'
        '     "vinetas": ["punto breve", "punto breve"],\n'
        '     "cita": "opcional, frase memorable entre comillas",\n'
        '     "nota_orador": "guia breve para quien expone"}\n'
        "  ]\n"
        "}\n"
        "Reglas: la primera diapositiva es tipo 'portada'; la ultima es tipo 'cierre' "
        "con una llamada a la accion clara. Usa 'vinetas' con 2-4 puntos como maximo y "
        "frases cortas. No uses markdown ni HTML dentro de los textos. Responde solo el JSON."
    )

    messages = [
        {"role": "system", "content": PRESENTATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        headers = llm_client.build_llm_headers(settings)
        response = requests.post(
            llm_client.resolve_llm_url(settings),
            headers=headers,
            json=llm_client.build_chat_payload(settings, messages, temperature=0.8),
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
    except llm_client.LLMConfigError as exc:
        raise PresentationGenerationError(str(exc)) from exc
    except requests.RequestException as exc:
        raise PresentationGenerationError(f"Error de comunicacion con LLM: {exc}") from exc

    text = _extract_llm_text(response).strip()
    if not text:
        raise PresentationGenerationError("El LLM devolvio una presentacion vacia")

    deck = _extract_json_object(text)
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        raise PresentationGenerationError("La presentacion no contiene diapositivas")
    return deck


def _e(value: Any) -> str:
    return html.escape(str(value or "").strip())


def _render_slide(slide: dict[str, Any], index: int, total: int) -> str:
    tipo = _e(slide.get("tipo") or "idea") or "idea"
    titulo = _e(slide.get("titulo"))
    subtitulo = _e(slide.get("subtitulo"))
    contenido = _e(slide.get("contenido"))
    cita = _e(slide.get("cita"))
    vinetas = slide.get("vinetas") or []

    parts: list[str] = []
    if subtitulo:
        parts.append(f'<p class="s-sub">{subtitulo}</p>')
    if titulo:
        tag = "h1" if tipo == "portada" else "h2"
        parts.append(f'<{tag} class="s-title">{titulo}</{tag}>')
    if contenido:
        parts.append(f'<p class="s-text">{contenido}</p>')
    if isinstance(vinetas, list) and vinetas:
        items = "".join(f"<li>{_e(v)}</li>" for v in vinetas if str(v).strip())
        if items:
            parts.append(f'<ul class="s-list">{items}</ul>')
    if cita:
        parts.append(f'<blockquote class="s-quote">{cita}</blockquote>')

    active = " active" if index == 0 else ""
    return (
        f'<section class="slide t-{tipo}{active}" data-index="{index}">'
        f'<div class="s-inner">{"".join(parts)}</div>'
        f'<span class="s-counter">{index + 1} / {total}</span>'
        f"</section>"
    )


def render_presentation_html(deck: dict[str, Any], ada_name: str) -> str:
    titulo = _e(deck.get("titulo")) or _e(ada_name)
    slides = deck.get("slides") or []
    total = len(slides)
    slides_html = "".join(_render_slide(s, i, total) for i, s in enumerate(slides))

    return (
        "<!DOCTYPE html>"
        '<html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{titulo}</title>"
        "<style>"
        ":root{--navy:#0b1e3f;--navy2:#13294f;--gold:#c9a24a;--ink:#0b1e3f;--paper:#f7f5ef;}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{height:100%;}"
        "body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--navy);color:#fff;}"
        ".deck{position:relative;width:100%;height:100vh;min-height:420px;overflow:hidden;}"
        ".slide{position:absolute;inset:0;display:none;padding:6% 8%;flex-direction:column;justify-content:center;"
        "background:linear-gradient(135deg,var(--navy) 0%,var(--navy2) 100%);}"
        ".slide.active{display:flex;animation:fade .45s ease;}"
        "@keyframes fade{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:none;}}"
        ".s-inner{max-width:900px;margin:0 auto;width:100%;}"
        ".s-sub{color:var(--gold);font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:.85rem;margin-bottom:.8rem;}"
        ".s-title{font-size:clamp(1.6rem,4.5vw,3.2rem);line-height:1.1;margin-bottom:1rem;}"
        ".t-portada .s-title{font-size:clamp(2rem,6vw,4rem);}"
        ".s-text{font-size:clamp(1rem,2.4vw,1.5rem);line-height:1.5;color:#e8edf6;max-width:760px;}"
        ".s-list{list-style:none;margin-top:1.2rem;display:grid;gap:.8rem;}"
        ".s-list li{position:relative;padding-left:1.8rem;font-size:clamp(1rem,2.2vw,1.35rem);line-height:1.4;color:#eef2f9;}"
        ".s-list li::before{content:'';position:absolute;left:0;top:.55em;width:.7rem;height:.7rem;border-radius:50%;background:var(--gold);}"
        ".s-quote{margin-top:1.4rem;border-left:4px solid var(--gold);padding:.4rem 0 .4rem 1.2rem;font-style:italic;"
        "font-size:clamp(1.1rem,2.6vw,1.6rem);color:#fff;}"
        ".t-portada{background:radial-gradient(circle at 70% 20%,rgba(201,162,74,.25),transparent 55%),"
        "linear-gradient(135deg,var(--navy) 0%,#08152c 100%);}"
        ".t-cierre{background:linear-gradient(135deg,#10254a 0%,var(--gold) 320%);}"
        ".s-counter{position:absolute;bottom:1.1rem;right:1.4rem;font-size:.8rem;color:rgba(255,255,255,.55);}"
        ".bar{position:absolute;left:0;bottom:0;height:5px;background:var(--gold);transition:width .35s ease;z-index:5;}"
        ".nav{position:absolute;bottom:1rem;left:50%;transform:translateX(-50%);display:flex;gap:.6rem;z-index:6;}"
        ".nav button{border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.08);color:#fff;"
        "width:42px;height:42px;border-radius:50%;font-size:1.1rem;cursor:pointer;transition:.2s;}"
        ".nav button:hover{background:var(--gold);border-color:var(--gold);color:var(--navy);}"
        "</style></head><body>"
        f'<div class="deck" id="deck">{slides_html}'
        '<div class="bar" id="bar"></div>'
        '<div class="nav"><button id="prev" aria-label="Anterior">&#8592;</button>'
        '<button id="next" aria-label="Siguiente">&#8594;</button></div>'
        "</div>"
        "<script>"
        "(function(){var s=document.querySelectorAll('.slide');var i=0;var bar=document.getElementById('bar');"
        "function show(n){i=Math.max(0,Math.min(s.length-1,n));s.forEach(function(el,k){el.classList.toggle('active',k===i);});"
        "bar.style.width=((i+1)/s.length*100)+'%';}"
        "document.getElementById('next').onclick=function(){show(i+1);};"
        "document.getElementById('prev').onclick=function(){show(i-1);};"
        "document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key===' '){show(i+1);}"
        "else if(e.key==='ArrowLeft'){show(i-1);}});"
        "show(0);})();"
        "</script></body></html>"
    )


def build_presentation_for_ada(settings: Settings, ada: dict[str, Any]) -> dict[str, Any]:
    """Build an embeddable HTML5 presentation for one ADA based on its readings."""
    ada_name = ada.get("nombre", "ADA")
    objetivo = ada.get("objetivo", "")
    readings = ada.get("lecturas_fundamentacion") or []

    readings_block = _build_readings_block(readings)
    deliverable_block = _build_deliverable_block(ada)
    deck = _request_slides(settings, ada_name, objetivo, readings_block, deliverable_block)
    deck_html = render_presentation_html(deck, ada_name)

    return {
        "titulo": deck.get("titulo") or ada_name,
        "subtitulo": deck.get("subtitulo") or "",
        "num_diapositivas": len(deck.get("slides") or []),
        "slides": deck.get("slides") or [],
        "html": deck_html,
    }


def attach_presentations_to_ada_structure(
    settings: Settings,
    ada_structure: dict[str, Any],
) -> list[str]:
    """Generate and attach an HTML5 presentation to every ADA (process + integrative).

    Must run AFTER readings are attached. Returns a list of warning messages.
    """
    warnings: list[str] = []

    def process_ada(ada: dict[str, Any]) -> None:
        ada_name = ada.get("nombre", "ADA")
        try:
            ada["presentacion"] = build_presentation_for_ada(settings, ada)
        except PresentationGenerationError as exc:
            warning = f"Generacion de presentacion fallo para '{ada_name}': {exc}"
            warnings.append(warning)
            logger.warning(warning)
            ada["presentacion"] = {
                "titulo": ada_name,
                "subtitulo": "",
                "num_diapositivas": 0,
                "slides": [],
                "html": "",
                "aviso": str(exc),
            }

    for period in ada_structure.get("periodos", []):
        for ada in period.get("adas", []) or []:
            process_ada(ada)

        fase = period.get("fase_proyecto_integrador")
        if isinstance(fase, dict):
            integradora = fase.get("ada_integradora_producto")
            if isinstance(integradora, dict):
                process_ada(integradora)

    return warnings
