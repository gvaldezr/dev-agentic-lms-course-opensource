from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .schemas import ParsedCourseInput


SPANISH_STOPWORDS = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "y",
    "o",
    "en",
    "para",
    "con",
    "por",
    "del",
    "al",
    "un",
    "una",
    "que",
    "se",
    "su",
    "sus",
    "a",
    "como",
    "sobre",
    "mediante",
    "entre",
}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def infer_course_competency(parsed_input: ParsedCourseInput) -> str:
    if parsed_input.course_competency and parsed_input.course_competency.strip():
        return parsed_input.course_competency.strip()

    if not parsed_input.competencies:
        return ""

    filtered = []
    for item in parsed_input.competencies:
        norm = _normalize(item)
        if norm.startswith(("genericas", "disciplinares", "cdb", "competencias")):
            continue
        if re.match(r"^\d+[\.)]", norm):
            continue
        if len(item.split()) < 6:
            continue
        filtered.append(item.strip())

    if filtered:
        return filtered[0]

    return parsed_input.competencies[0].strip()


def infer_openalex_keywords(parsed_input: ParsedCourseInput, max_keywords: int = 12) -> list[str]:
    raw_topics: list[str] = []

    for line in parsed_input.syllabus.splitlines():
        cleaned = line.strip(" -\t")
        # Elimina marcadores de viñeta/subtema al inicio ("o ", "•", "·", etc.)
        cleaned = re.sub(r"^[\u2022\u25E6\u25AA\u00B7o]\s+", "", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            continue
        if len(cleaned.split()) >= 2:
            raw_topics.append(cleaned)

    competency = infer_course_competency(parsed_input)
    if competency:
        raw_topics.append(competency)

    # Prefer phrase-like topics from syllabus first.
    phrase_keywords: list[str] = []
    seen = set()
    for topic in raw_topics:
        norm = _normalize(topic)
        if norm in seen:
            continue
        seen.add(norm)
        phrase_keywords.append(topic)
        if len(phrase_keywords) >= max_keywords:
            return phrase_keywords

    # Fallback to token frequency if phrase extraction is scarce.
    corpus = " ".join(raw_topics)
    tokens = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}", corpus)
    token_counter = Counter(
        token.lower()
        for token in tokens
        if _normalize(token) not in SPANISH_STOPWORDS
    )

    for token, _ in token_counter.most_common(max_keywords):
        if token not in phrase_keywords:
            phrase_keywords.append(token)
        if len(phrase_keywords) >= max_keywords:
            break

    return phrase_keywords


def build_openalex_payload(parsed_input: ParsedCourseInput, api_key: str) -> dict:
    competencia = infer_course_competency(parsed_input)
    keywords = infer_openalex_keywords(parsed_input)

    suggested_queries = [
        f'title_and_abstract.search:"{kw}"' for kw in keywords[:8]
    ]

    return {
        "competencia_curso": competencia,
        "conceptos_clave_openalex": keywords,
        "openalex": {
            "base_url": "https://api.openalex.org/works",
            "api_key": api_key,
            "consultas_sugeridas": suggested_queries,
            "filtros_recomendados": {
                "default_search_field": "title_and_abstract.search",
                "use_mailto_or_api_key": True,
            },
        },
    }
