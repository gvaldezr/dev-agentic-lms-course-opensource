from __future__ import annotations

import json
import logging
import math
import random
import re
from typing import Any

import requests

from . import llm_client
from .config import Settings


logger = logging.getLogger("course_pipeline.questions")


class QuestionGenerationError(Exception):
    pass


STUDENT_PROFILE = (
    "Estudiantes de preparatoria de Merida, Yucatan, Mexico, de 16 a 18 anos."
)

QUESTION_SYSTEM_PROMPT = (
    "Actua como especialista en evaluacion educativa y construccion de reactivos "
    "(item writing) para bachillerato. Dominas la taxonomia de Anderson y Krathwohl. "
    "Redactas reactivos de OPCION MULTIPLE de NIVEL APLICACION: cada pregunta plantea "
    "un escenario o caso nuevo donde el estudiante debe APLICAR un concepto de la "
    "lectura (no solo recordarlo ni definirlo). Escribes distractores de ALTO NIVEL: "
    "plausibles, homogeneos en forma y longitud con la respuesta correcta, basados en "
    "errores conceptuales comunes o confusiones tipicas; nunca uses 'todas las "
    "anteriores', 'ninguna de las anteriores' ni pistas gramaticales. Te apoyas "
    "UNICAMENTE en la lectura proporcionada, sin inventar datos externos. Escribes en "
    "espanol claro y cercano al estudiante."
)

# Objetivo minimo de reactivos del banco global.
TARGET_BANK_SIZE = 60
# Items solicitados por lectura (se ajusta para superar el objetivo global).
MIN_ITEMS_PER_READING = 2
MAX_ITEMS_PER_READING = 4
MAX_READING_CHARS = 2200

# Semilla fija para reproducibilidad (barajado de opciones y seleccion del quiz).
RANDOM_SEED = 20250101
QUIZ_SIZE = 20


def _extract_llm_text(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        if not text:
            raise QuestionGenerationError("Respuesta vacia del LLM al generar reactivos")
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

    raise QuestionGenerationError("No se pudo extraer texto de la respuesta del LLM")


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise QuestionGenerationError("La respuesta del LLM no contiene un objeto JSON valido")

    candidate = cleaned[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise QuestionGenerationError(f"JSON de reactivos invalido: {exc}") from exc


def _collect_readings(ada_structure: dict[str, Any]) -> list[dict[str, str]]:
    """Aplana todas las lecturas del curso en un unico corpus etiquetado con su ADA/eje."""
    corpus: list[dict[str, str]] = []
    for periodo in ada_structure.get("periodos") or []:
        adas: list[dict[str, Any]] = list(periodo.get("adas") or [])
        fase = periodo.get("fase_proyecto_integrador") or {}
        integradora = fase.get("ada_integradora_producto")
        if integradora:
            adas.append(integradora)
        for ada in adas:
            ada_name = ada.get("nombre", "ADA")
            for reading in ada.get("lecturas_fundamentacion") or []:
                lectura = (reading.get("lectura") or "").strip()
                if not lectura:
                    continue
                corpus.append(
                    {
                        "ada": ada_name,
                        "eje": (reading.get("fundamento") or "Eje tematico").strip(),
                        "lectura": lectura,
                    }
                )
    return corpus


def _request_items_for_reading(
    settings: Settings,
    reading: dict[str, str],
    num_items: int,
) -> list[dict[str, Any]]:
    lectura = reading["lectura"][:MAX_READING_CHARS]
    user_prompt = (
        f"ADA: {reading['ada']}\n"
        f"Eje tematico: {reading['eje']}\n"
        f"Publico: {STUDENT_PROFILE}\n\n"
        "Lectura de fundamentacion (unica fuente permitida):\n"
        f"{lectura}\n\n"
        f"Redacta {num_items} reactivos de OPCION MULTIPLE de NIVEL APLICACION basados "
        "UNICAMENTE en esta lectura. Cada reactivo debe plantear un escenario o caso "
        "nuevo donde el estudiante aplique un concepto de la lectura. Cada reactivo "
        "tiene EXACTAMENTE una respuesta correcta y TRES distractores de alto nivel "
        "(plausibles, homogeneos, del mismo largo aproximado que la correcta).\n"
        "Devuelve EXCLUSIVAMENTE un objeto JSON valido con esta forma exacta:\n"
        "{\n"
        '  "reactivos": [\n'
        "    {\n"
        '      "pregunta": "enunciado con el escenario/caso de aplicacion",\n'
        '      "correcta": "texto de la opcion correcta",\n'
        '      "distractores": ["distractor 1", "distractor 2", "distractor 3"],\n'
        '      "retroalimentacion_general": "idea clave que refuerza el aprendizaje",\n'
        '      "justificacion_correcta": "por que la opcion correcta es la adecuada"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Reglas: no uses 'todas las anteriores' ni 'ninguna de las anteriores'; no "
        "numeres ni etiquetes las opciones (sin A), B), 1., etc.); no uses markdown ni "
        "HTML dentro de los textos. Responde solo el JSON."
    )

    messages = [
        {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        headers = llm_client.build_llm_headers(settings)
        response = requests.post(
            llm_client.resolve_llm_url(settings),
            headers=headers,
            json=llm_client.build_chat_payload(settings, messages, temperature=0.7),
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
    except llm_client.LLMConfigError as exc:
        raise QuestionGenerationError(str(exc)) from exc
    except requests.RequestException as exc:
        raise QuestionGenerationError(f"Error de comunicacion con LLM: {exc}") from exc

    text = _extract_llm_text(response).strip()
    if not text:
        raise QuestionGenerationError("El LLM devolvio reactivos vacios")

    payload = _extract_json_object(text)
    reactivos = payload.get("reactivos")
    if not isinstance(reactivos, list) or not reactivos:
        raise QuestionGenerationError("La respuesta no contiene reactivos")
    return reactivos


def _normalize_item(
    raw: dict[str, Any],
    ada: str,
    eje: str,
    item_id: str,
    rng: random.Random,
) -> dict[str, Any] | None:
    """Valida un reactivo del LLM, arma las 4 opciones y baraja su orden."""
    pregunta = str(raw.get("pregunta") or "").strip()
    correcta = str(raw.get("correcta") or "").strip()
    distractores_raw = raw.get("distractores") or []
    distractores = [str(d).strip() for d in distractores_raw if str(d).strip()]

    # Deduplica distractores que coincidan con la correcta o entre si.
    seen: set[str] = {correcta.lower()}
    distractores_unicos: list[str] = []
    for distractor in distractores:
        key = distractor.lower()
        if key not in seen:
            seen.add(key)
            distractores_unicos.append(distractor)

    if not pregunta or not correcta or len(distractores_unicos) < 3:
        return None

    opciones = [correcta] + distractores_unicos[:3]
    rng.shuffle(opciones)
    indice_correcta = opciones.index(correcta)

    return {
        "id": item_id,
        "ada": ada,
        "eje": eje,
        "nivel": "aplicacion",
        "pregunta": pregunta,
        "opciones": opciones,
        "indice_correcta": indice_correcta,
        "retroalimentacion_general": str(raw.get("retroalimentacion_general") or "").strip(),
        "justificacion_correcta": str(raw.get("justificacion_correcta") or "").strip(),
    }


def build_question_bank(
    settings: Settings,
    ada_structure: dict[str, Any],
    target: int = TARGET_BANK_SIZE,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Genera un banco global de al menos `target` reactivos de opcion multiple
    (nivel aplicacion) a partir de todas las lecturas del curso.

    Debe ejecutarse DESPUES de generar las lecturas. Devuelve (banco, advertencias).
    """
    warnings: list[str] = []
    corpus = _collect_readings(ada_structure)
    if not corpus:
        warnings.append(
            "No hay lecturas disponibles para generar el banco de preguntas; etapa omitida."
        )
        return [], warnings

    per_reading = max(
        MIN_ITEMS_PER_READING,
        min(MAX_ITEMS_PER_READING, math.ceil(target / len(corpus))),
    )

    rng = random.Random(RANDOM_SEED)
    bank: list[dict[str, Any]] = []
    counter = 0

    for reading in corpus:
        try:
            reactivos = _request_items_for_reading(settings, reading, per_reading)
        except QuestionGenerationError as exc:
            warning = (
                f"Fallo generacion de reactivos para '{reading['ada']}' / "
                f"'{reading['eje']}': {exc}"
            )
            warnings.append(warning)
            logger.warning(warning)
            continue

        for raw in reactivos:
            counter += 1
            item = _normalize_item(
                raw=raw,
                ada=reading["ada"],
                eje=reading["eje"],
                item_id=f"Q{counter:03d}",
                rng=rng,
            )
            if item:
                bank.append(item)

    if len(bank) < target:
        warnings.append(
            f"El banco genero {len(bank)} reactivos validos (objetivo {target})."
        )

    return bank, warnings


def select_quiz(
    bank: list[dict[str, Any]],
    size: int = QUIZ_SIZE,
    seed: int = RANDOM_SEED,
) -> list[dict[str, Any]]:
    """Selecciona `size` reactivos del banco de forma estratificada por ADA
    (reparto equilibrado entre temas) con semilla fija reproducible."""
    if not bank:
        return []

    rng = random.Random(seed)

    grupos: dict[str, list[dict[str, Any]]] = {}
    for item in bank:
        grupos.setdefault(item.get("ada", "ADA"), []).append(item)

    # Baraja dentro de cada ADA de forma determinista.
    for ada in sorted(grupos):
        rng.shuffle(grupos[ada])

    seleccion: list[dict[str, Any]] = []
    adas_ordenados = sorted(grupos)
    # Ronda round-robin entre ADAs hasta completar el tamano del quiz.
    while len(seleccion) < min(size, len(bank)):
        avanzo = False
        for ada in adas_ordenados:
            if grupos[ada]:
                seleccion.append(grupos[ada].pop())
                avanzo = True
                if len(seleccion) >= size:
                    break
        if not avanzo:
            break

    return seleccion[:size]
