"""Generacion de objetivos de aprendizaje por sesion.

Las sesiones se derivan de la estructura ADA (``estructura_curso_adas``) y del
plan operativo (``planeacion_operativa``). Este modulo pide al LLM un objetivo
por sesion y los adjunta en todos los lugares relevantes del payload. Si el LLM
falla, se generan objetivos deterministas a partir del tema del ADA y la etapa
de la sesion para que el pipeline nunca quede sin objetivos.
"""

from __future__ import annotations

import json
import re

import requests

from . import llm_client
from .config import Settings
from .instructional_generator import InstructionalGenerator, InstructionalGenerationError


_SYSTEM_PROMPT = (
    "Eres un disenador instruccional senior. Para cada sesion de clase debes redactar "
    "UN objetivo de aprendizaje especifico, observable y medible, en una sola oracion que "
    "comience con un verbo en infinitivo. Manten coherencia con el ADA y el tema de cada sesion. "
    "Responde EXCLUSIVAMENTE en JSON con la forma: "
    '{"objetivos": {"1": "...", "2": "..."}} donde la clave es el numero de sesion.'
)


def _collect_sessions(ada_structure: dict) -> list[dict]:
    sessions: list[dict] = []
    for periodo in ada_structure.get("periodos", []):
        adas = list(periodo.get("adas", []))
        fase = periodo.get("fase_proyecto_integrador") or {}
        fase_ada = fase.get("ada_integradora_producto")
        if isinstance(fase_ada, dict):
            adas.append(fase_ada)
        for ada in adas:
            for sesion in ada.get("sesiones_desarrolladas", []):
                numero = sesion.get("sesion")
                if numero is None:
                    continue
                sessions.append(
                    {
                        "sesion": int(numero),
                        "semana": sesion.get("semana"),
                        "ada": ada.get("nombre"),
                        "tema": ada.get("objetivo") or ada.get("resultado_aprendizaje"),
                        "hito": sesion.get("hito"),
                        "tipo_actividad": ada.get("tipo_actividad"),
                    }
                )
    sessions.sort(key=lambda item: item["sesion"])
    return sessions


def _fallback_objectives(sessions: list[dict]) -> dict[int, str]:
    objetivos: dict[int, str] = {}
    for sesion in sessions:
        tema_raw = (sesion.get("tema") or "los contenidos del ADA").strip()
        match = re.search(r"asociada a '([^']+)'", tema_raw)
        tema = match.group(1).strip() if match else tema_raw
        tema = re.sub(r"\s+mediante actividades guiadas y evaluables\.?$", "", tema).strip()
        tema = tema.rstrip(".") or "los contenidos del ADA"
        if sesion.get("hito") == "cierre":
            objetivos[sesion["sesion"]] = (
                f"Consolidar y demostrar el dominio de {tema} mediante la entrega y evaluacion de evidencias."
            )
        else:
            objetivos[sesion["sesion"]] = (
                f"Avanzar en el desarrollo de {tema} mediante practica guiada y colaborativa con retroalimentacion."
            )
    return objetivos


def _chat(settings: Settings, system_prompt: str, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        headers = llm_client.build_llm_headers(settings)
        response = requests.post(
            llm_client.resolve_llm_url(settings),
            headers=headers,
            json=llm_client.build_chat_payload(settings, messages, temperature=0.3),
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
    except llm_client.LLMConfigError as exc:
        raise InstructionalGenerationError(str(exc)) from exc
    except requests.RequestException as exc:
        raise InstructionalGenerationError(f"Error de comunicacion con LLM: {exc}") from exc

    response_data = InstructionalGenerator._decode_response_json(response)
    return InstructionalGenerator._extract_content(response_data)


def _generate_via_llm(settings: Settings, course_name: str, sessions: list[dict]) -> dict[int, str]:
    if settings.llm_provider != "openai" and not settings.llm_api_url:
        raise InstructionalGenerationError("LLM_API_URL no esta configurado")

    listado = "\n".join(
        f"- Sesion {s['sesion']} (semana {s.get('semana')}, {s.get('ada')}, hito {s.get('hito')}): "
        f"tema {s.get('tema')}"
        for s in sessions
    )
    user_prompt = (
        f"Curso: {course_name}\n\n"
        f"Redacta un objetivo de aprendizaje para cada una de las {len(sessions)} sesiones siguientes. "
        "Cada objetivo debe ser unico y coherente con el tema y el hito de su sesion.\n\n"
        f"Sesiones:\n{listado}\n\n"
        "Entrega SOLO JSON valido."
    )

    content = _chat(settings, _SYSTEM_PROMPT, user_prompt)
    json_text = InstructionalGenerator._extract_json(content)
    try:
        # strict=False tolera saltos de linea / tabs literales dentro de los strings,
        # que algunos modelos insertan y rompen un json.loads estricto.
        decoded = json.loads(json_text, strict=False)
    except Exception:  # noqa: BLE001
        try:
            decoded = json.loads(json_text.replace("\n", " ").replace("\t", " "), strict=False)
        except Exception as exc:  # noqa: BLE001
            raise InstructionalGenerationError(f"JSON de objetivos invalido: {exc}") from exc

    raw = decoded.get("objetivos") if isinstance(decoded, dict) else None
    if not isinstance(raw, dict):
        raise InstructionalGenerationError("El LLM no devolvio el objeto 'objetivos'")

    objetivos: dict[int, str] = {}
    for key, value in raw.items():
        try:
            numero = int(str(key).strip())
        except (TypeError, ValueError):
            continue
        texto = str(value).strip()
        if texto:
            objetivos[numero] = texto
    return objetivos


def _attach(ada_structure: dict, operational_plan: dict, objetivos: dict[int, str]) -> None:
    # Estructura ADA: objetivo por sesion desarrollada.
    for periodo in ada_structure.get("periodos", []):
        adas = list(periodo.get("adas", []))
        fase = periodo.get("fase_proyecto_integrador") or {}
        fase_ada = fase.get("ada_integradora_producto")
        if isinstance(fase_ada, dict):
            adas.append(fase_ada)
        for ada in adas:
            for sesion in ada.get("sesiones_desarrolladas", []):
                numero = sesion.get("sesion")
                if numero in objetivos:
                    sesion["objetivo"] = objetivos[numero]

    # Plan operativo: objetivos por sesion en cada ADA y fase de la periodizacion.
    for period in operational_plan.get("periodizacion", []):
        slots = list(period.get("adas", []))
        fase = period.get("fase_proyecto_integrador")
        if isinstance(fase, dict):
            slots.append(fase)
        for slot in slots:
            inicio = slot.get("sesion_inicio")
            fin = slot.get("sesion_fin")
            if not isinstance(inicio, int) or not isinstance(fin, int):
                continue
            slot["objetivos_sesiones"] = [
                {"sesion": numero, "objetivo": objetivos[numero]}
                for numero in range(inicio, fin + 1)
                if numero in objetivos
            ]


def generate_and_attach_session_objectives(
    settings: Settings,
    ada_structure: dict,
    operational_plan: dict,
    course_name: str,
) -> list[str]:
    """Genera objetivos por sesion y los adjunta. Retorna advertencias."""
    warnings: list[str] = []
    sessions = _collect_sessions(ada_structure)
    if not sessions:
        return warnings

    objetivos: dict[int, str] = {}
    try:
        objetivos = _generate_via_llm(settings, course_name, sessions)
    except InstructionalGenerationError as exc:
        warnings.append(
            f"Objetivos por sesion via LLM no disponibles ({exc}). Se usan objetivos deterministas."
        )

    fallback = _fallback_objectives(sessions)
    for numero, texto in fallback.items():
        objetivos.setdefault(numero, texto)

    _attach(ada_structure, operational_plan, objetivos)
    return warnings
