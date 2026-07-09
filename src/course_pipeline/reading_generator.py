from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests

from . import llm_client
from .config import Settings


logger = logging.getLogger("course_pipeline.readings")

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
MAX_YEARS_OLD = 5
SOURCES_PER_TOPIC = 5

STUDENT_PROFILE = (
    "Estudiantes de preparatoria (Prepa 1) de Merida, Yucatan, Mexico, "
    "de 16 a 17 anos, con nivel socioeconomico variable."
)

READING_SYSTEM_PROMPT = (
    "Actua como docente de bachillerato experto en redaccion didactica accesible. "
    "Escribes lecturas de fundamentacion para jovenes mexicanos de preparatoria. "
    "Usas lenguaje claro, cercano y motivador, evitas tecnicismos innecesarios y, "
    "cuando los usas, los explicas. Incluyes ejemplos cercanos a la vida cotidiana "
    "de Merida, Yucatan. No inventas datos de las fuentes proporcionadas: solo te "
    "apoyas en sus titulos y temas para fundamentar la lectura."
)


class ReadingGenerationError(Exception):
    pass


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""

    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions.append((idx, word))

    positions.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positions)


def search_openalex_sources(
    topic: str,
    api_key: str,
    timeout_seconds: int,
    max_years_old: int = MAX_YEARS_OLD,
    per_page: int = SOURCES_PER_TOPIC,
) -> list[dict[str, Any]]:
    """Search OpenAlex for recent sources (<= max_years_old) for a given topic."""
    current_year = datetime.now(timezone.utc).year
    from_year = current_year - max_years_old + 1

    params = {
        "search": topic,
        "filter": f"from_publication_date:{from_year}-01-01",
        "sort": "relevance_score:desc",
        "per_page": per_page,
    }
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ReadingGenerationError(f"Error consultando OpenAlex para '{topic}': {exc}") from exc
    except ValueError as exc:
        raise ReadingGenerationError(f"Respuesta OpenAlex no valida para '{topic}': {exc}") from exc

    results = data.get("results", []) or []
    sources: list[dict[str, Any]] = []
    for work in results[:per_page]:
        authorships = work.get("authorships", []) or []
        author_names = [
            (a.get("author", {}) or {}).get("display_name", "")
            for a in authorships[:3]
            if (a.get("author", {}) or {}).get("display_name")
        ]
        primary_location = work.get("primary_location", {}) or {}
        source_info = primary_location.get("source", {}) or {}

        source = {
            "titulo": work.get("title") or work.get("display_name") or "Sin titulo",
            "anio": work.get("publication_year"),
            "doi": work.get("doi"),
            "openalex_id": work.get("id"),
            "autores": author_names,
            "fuente": source_info.get("display_name"),
            "resumen": _reconstruct_abstract(work.get("abstract_inverted_index")),
        }
        source["referencia_apa"] = _format_apa(source)
        sources.append(source)

    return sources


_STOPWORDS = {
    "para", "como", "este", "esta", "estos", "estas", "esto", "sino", "sobre",
    "entre", "desde", "hasta", "donde", "cuando", "porque", "pero", "solo",
    "sólo", "todo", "toda", "todos", "todas", "muy", "más", "mas", "menos",
    "del", "los", "las", "una", "uno", "unas", "unos", "con", "sin", "que",
    "qué", "cual", "cuál", "cuales", "cuáles", "ser", "son", "está", "estan",
    "están", "trata", "punto", "exactamente", "implica", "debemos", "nuestros",
    "nuestras", "sus", "esto", "aquí", "ahí", "allá", "hay", "ese", "esa",
}


def _keywords_from_text(text: str, max_words: int = 6) -> str:
    """Extract up to `max_words` meaningful keywords for an OpenAlex search query."""
    words = re.findall(r"[\wáéíóúñÁÉÍÓÚÑ]+", text.lower())
    keywords = [w for w in words if len(w) > 3 and w not in _STOPWORDS]
    return " ".join(keywords[:max_words])


def _build_query_candidates(topic: str, contenidos: list[str] | None) -> list[str]:
    """Build progressively simpler queries to maximize chances of recent results."""
    candidates: list[str] = [topic]

    words = [w for w in re.findall(r"[\wáéíóúñÁÉÍÓÚÑ]+", topic) if len(w) > 3]
    if len(words) >= 3:
        candidates.append(" ".join(words[:3]))
    if len(words) >= 2:
        candidates.append(" ".join(words[:2]))

    for contenido in contenidos or []:
        keywords = _keywords_from_text(contenido)
        if keywords:
            candidates.append(keywords)

    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        key = c.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def search_openalex_with_fallback(
    topic: str,
    api_key: str,
    timeout_seconds: int,
    contenidos: list[str] | None = None,
    target: int = SOURCES_PER_TOPIC,
) -> tuple[list[dict[str, Any]], str | None]:
    """Search OpenAlex trying several queries until `target` unique sources are found.

    Returns (sources, last_error). Sources are deduplicated by openalex_id/title.
    """
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    last_error: str | None = None

    for query in _build_query_candidates(topic, contenidos):
        if len(collected) >= target:
            break
        try:
            found = search_openalex_sources(
                topic=query,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                per_page=target,
            )
        except ReadingGenerationError as exc:
            last_error = str(exc)
            logger.warning("OpenAlex fallo para query '%s': %s", query, exc)
            continue

        for src in found:
            key = (src.get("openalex_id") or src.get("titulo") or "").lower()
            if key and key not in seen_ids:
                seen_ids.add(key)
                collected.append(src)
                if len(collected) >= target:
                    break

    return collected[:target], last_error


def _format_apa(source: dict[str, Any]) -> str:
    """Format a single OpenAlex source as an APA 7th-edition style reference."""
    autores = source.get("autores") or []
    if autores:
        formatted_authors = []
        for full_name in autores:
            parts = full_name.split()
            if len(parts) >= 2:
                apellido = parts[-1]
                iniciales = " ".join(f"{p[0]}." for p in parts[:-1] if p)
                formatted_authors.append(f"{apellido}, {iniciales}")
            else:
                formatted_authors.append(full_name)
        if len(formatted_authors) == 1:
            autor_str = formatted_authors[0]
        elif len(formatted_authors) == 2:
            autor_str = f"{formatted_authors[0]} y {formatted_authors[1]}"
        else:
            autor_str = ", ".join(formatted_authors[:-1]) + f" y {formatted_authors[-1]}"
    else:
        autor_str = "Autoría colectiva"

    anio = source.get("anio") or "s. f."
    titulo = (source.get("titulo") or "Sin título").rstrip(".")
    fuente = source.get("fuente")
    doi = source.get("doi")

    ref = f"{autor_str} ({anio}). {titulo}."
    if fuente:
        ref += f" *{fuente}*."
    if doi:
        ref += f" {doi}"
    return ref.strip()


def _extract_llm_text(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        if not text:
            raise ReadingGenerationError("Respuesta vacia del LLM al generar lectura")
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

    raise ReadingGenerationError("No se pudo extraer texto de la respuesta del LLM")


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


MIN_WORDS = 500
MAX_WORDS = 600
MAX_READING_ATTEMPTS = 3


def _request_reading(settings: Settings, messages: list[dict[str, str]]) -> str:
    try:
        headers = llm_client.build_llm_headers(settings)
        response = requests.post(
            llm_client.resolve_llm_url(settings),
            headers=headers,
            json=llm_client.build_chat_payload(settings, messages, temperature=0.5),
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
    except llm_client.LLMConfigError as exc:
        raise ReadingGenerationError(str(exc)) from exc
    except requests.RequestException as exc:
        raise ReadingGenerationError(f"Error de comunicacion con LLM: {exc}") from exc

    text = _extract_llm_text(response).strip()
    if not text:
        raise ReadingGenerationError("El LLM devolvio una lectura vacia")
    return text


def generate_reading_text(
    settings: Settings,
    ada_name: str,
    foundation_topic: str,
    sources: list[dict[str, Any]],
) -> str:
    if settings.llm_provider != "openai" and not settings.llm_api_url:
        raise ReadingGenerationError("LLM_API_URL no esta configurado")

    sources_block_lines = []
    for idx, src in enumerate(sources, start=1):
        autores = ", ".join(src.get("autores") or []) or "Autoria colectiva"
        anio = src.get("anio") or "s. f."
        resumen = (src.get("resumen") or "").strip()
        resumen_short = resumen[:600] if resumen else "(sin resumen disponible)"
        sources_block_lines.append(
            f"{idx}. {src.get('titulo')} ({anio}) - {autores}. Resumen: {resumen_short}"
        )
    sources_block = "\n".join(sources_block_lines) if sources_block_lines else "(sin fuentes)"

    user_prompt = (
        f"Tema de fundamentacion: {foundation_topic}\n"
        f"ADA asociada: {ada_name}\n\n"
        f"Publico objetivo: {STUDENT_PROFILE}\n\n"
        "Fuentes recientes (menos de 5 anios) recuperadas de OpenAlex:\n"
        f"{sources_block}\n\n"
        "Redacta UNA lectura de fundamentacion en espanol con estas reglas:\n"
        f"- Extension obligatoria: entre {MIN_WORDS} y {MAX_WORDS} palabras (cuenta las palabras).\n"
        "- Dirigida directamente al estudiante, con tono cercano y motivador.\n"
        "- Lenguaje accesible para 16-17 anios; explica cualquier termino tecnico.\n"
        "- Incluye al menos un ejemplo cercano a la vida en Merida, Yucatan.\n"
        "- Integra las ideas de las fuentes sin inventar datos especificos.\n"
        "- Estructura: introduccion, desarrollo con subtemas y cierre reflexivo.\n"
        "- No incluyas titulos en markdown ni listas con vinetas, solo parrafos.\n"
        "Devuelve unicamente el texto de la lectura, sin comentarios adicionales."
    )

    messages = [
        {"role": "system", "content": READING_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    best_text = ""
    best_distance = None

    for _ in range(MAX_READING_ATTEMPTS):
        text = _request_reading(settings, messages)
        word_count = _count_words(text)

        if MIN_WORDS <= word_count <= MAX_WORDS:
            return text

        if word_count < MIN_WORDS:
            distance = MIN_WORDS - word_count
        else:
            distance = word_count - MAX_WORDS

        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_text = text

        if word_count > MAX_WORDS:
            adjustment = (
                f"La lectura anterior tiene {word_count} palabras y excede el limite. "
                f"Reescribela completa para que quede entre {MIN_WORDS} y {MAX_WORDS} palabras, "
                "recortando ideas redundantes pero conservando estructura y fuentes."
            )
        else:
            adjustment = (
                f"La lectura anterior tiene {word_count} palabras y es demasiado corta. "
                f"Reescribela completa para que quede entre {MIN_WORDS} y {MAX_WORDS} palabras, "
                "ampliando explicaciones y ejemplos sin inventar datos de las fuentes."
            )

        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": adjustment})

    return best_text


def build_reading_for_foundation(
    settings: Settings,
    ada_name: str,
    foundation_topic: str,
    contenidos: list[str] | None = None,
) -> dict[str, Any]:
    """Build a single reading entry (sources + text) for one thematic foundation."""
    sources, source_error = search_openalex_with_fallback(
        topic=foundation_topic,
        api_key=settings.openalex_api_key,
        timeout_seconds=settings.llm_timeout_seconds,
        contenidos=contenidos,
    )

    reading_text = ""
    word_count = 0
    text_error: str | None = None
    try:
        reading_text = generate_reading_text(
            settings=settings,
            ada_name=ada_name,
            foundation_topic=foundation_topic,
            sources=sources,
        )
        word_count = _count_words(reading_text)
    except ReadingGenerationError as exc:
        text_error = str(exc)
        logger.warning("Generacion de lectura fallo para '%s': %s", foundation_topic, exc)

    entry: dict[str, Any] = {
        "fundamento": foundation_topic,
        "publico_objetivo": STUDENT_PROFILE,
        "fuentes_openalex": sources,
        "referencias_apa": [s.get("referencia_apa") for s in sources if s.get("referencia_apa")],
        "lectura": reading_text,
        "conteo_palabras": word_count,
        "rango_palabras_objetivo": "500-600",
    }
    if source_error and len(sources) < SOURCES_PER_TOPIC:
        entry["aviso_fuentes"] = (
            f"Solo se encontraron {len(sources)} fuentes recientes. Ultimo error: {source_error}"
        )
    elif len(sources) < SOURCES_PER_TOPIC:
        entry["aviso_fuentes"] = f"Solo se encontraron {len(sources)} fuentes recientes para este tema."
    if text_error:
        entry["aviso_lectura"] = text_error

    return entry


def attach_readings_to_ada_structure(
    settings: Settings,
    ada_structure: dict[str, Any],
) -> list[str]:
    """Generate readings for every ADA (process + integrative) based on its foundations.

    Returns a list of warning messages encountered during generation.
    """
    warnings: list[str] = []

    def process_ada(ada: dict[str, Any]) -> None:
        foundations = ada.get("fundamentos_tematicos_requeridos") or []
        contenidos = ada.get("contenidos_a_desarrollar") or []
        readings: list[dict[str, Any]] = []
        for topic in foundations:
            entry = build_reading_for_foundation(
                settings=settings,
                ada_name=ada.get("nombre", "ADA"),
                foundation_topic=topic,
                contenidos=contenidos,
            )
            if entry.get("aviso_fuentes"):
                warnings.append(entry["aviso_fuentes"])
            if entry.get("aviso_lectura"):
                warnings.append(entry["aviso_lectura"])
            readings.append(entry)
        ada["lecturas_fundamentacion"] = readings

    for period in ada_structure.get("periodos", []):
        for ada in period.get("adas", []) or []:
            process_ada(ada)

        fase = period.get("fase_proyecto_integrador")
        if isinstance(fase, dict):
            integrative_ada = fase.get("ada_integradora_producto")
            if isinstance(integrative_ada, dict):
                process_ada(integrative_ada)

    return warnings
