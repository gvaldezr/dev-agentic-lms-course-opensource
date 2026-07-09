"""Extraccion de los datos generales del programa de asignatura (PDF oficial).

El programa oficial de la asignatura (PDF de entrada) contiene secciones
numeradas (1. Datos generales, 2. Contexto, ... 12. Perfil docente) con
informacion que la plantilla de Planeacion Didactica requiere pero que no
formaba parte del ``course_structure.json``. Este modulo extrae esos campos a
partir del texto plano del documento.
"""

from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return normalized.strip().lower()


# Encabezados numerados conocidos del programa de asignatura.
# El orden importa: "competencias del perfil de egreso" debe evaluarse antes
# que "competencia de la asignatura".
_HEADINGS: tuple[tuple[str, str], ...] = (
    ("datos generales", "_datos"),
    ("contexto de la asignatura", "contexto"),
    ("relacion con otras asignaturas", "relacion"),
    ("competencias del perfil de egreso", "perfil_egreso"),
    ("experiencias de aprendizaje", "experiencias"),
    ("competencia de la asignatura", "_competencia"),
    ("contenidos esenciales", "_contenidos"),
    ("estrategias de ensenanza", "estrategias_ensenanza"),
    ("estrategias generales de evaluacion", "evaluacion"),
    ("descripcion general de las practicas", "practicas"),
    ("referencias sugeridas", "referencias"),
    ("perfil deseable del docente", "perfil_docente"),
)

# Viñetas de unidad. Incluye los glifos Unicode habituales y los caracteres del
# área de uso privado (PUA) que pypdf produce cuando Word usa la fuente Symbol/
# Wingdings para los bullets (p. ej. ``\uf0b7`` para ``•``). Sin esto, las
# unidades cuyas viñetas no son ``•`` se anexan como continuación y se pierden.
_BULLET_RE = re.compile(
    r"^(?:[\u2022\u2023\u2043\u2219\u25AA\u25A0\u25CF\u25CB\u25E6\u00B7\u2756\u2666\uF0B7\uF0A7\uF06C\uF0D8]\s*|[\-\*]\s+)"
)


def _strip_leading_number(normalized: str) -> str:
    return re.sub(r"^\d{1,2}[.)]\s*", "", normalized).strip()


def _detect_heading(line: str) -> str | None:
    candidate = _strip_leading_number(_normalize(line))
    for keyword, key in _HEADINGS:
        if candidate.startswith(keyword):
            return key
    return None


def _split_numbered_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in lines:
        if not raw.strip():
            continue
        key = _detect_heading(raw)
        if key is not None:
            current = key
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections.setdefault(current, []).append(raw)
    return sections


def _join_paragraph(lines: list[str]) -> str | None:
    joined = " ".join(line.strip() for line in lines if line.strip())
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined or None


def _merge_bullets(lines: list[str]) -> list[str]:
    items: list[str] = []
    current: str | None = None
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        if _BULLET_RE.match(text):
            if current:
                items.append(re.sub(r"\s+", " ", current).strip())
            current = _BULLET_RE.sub("", text)
        elif current is None:
            current = text
        else:
            current += " " + text
    if current:
        items.append(re.sub(r"\s+", " ", current).strip())
    return [item for item in items if item]


def _value_after(lines: list[str], pattern: str, allow_next_line: bool = False) -> str | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for index, line in enumerate(lines):
        match = regex.search(line)
        if match:
            value = line[match.end():].strip(" :\t").strip()
            if not value and allow_next_line:
                # El valor se desbordó a la siguiente línea no vacía (ej. PSP/PSE).
                for following in lines[index + 1:]:
                    if following.strip():
                        value = following.strip()
                        break
            if value:
                return re.sub(r"\s+", " ", value).strip()
    return None


def _value_requisitos(lines: list[str]) -> str | None:
    """La etiqueta 'Requisitos académicos previos' se parte en dos líneas."""
    for index, line in enumerate(lines):
        if "requisitos acad" in _normalize(line):
            candidate = line
            if index + 1 < len(lines):
                candidate = f"{line} {lines[index + 1]}"
            match = re.search(r"requisitos acad[eé]micos\s+previos\s+(.+)", candidate, re.IGNORECASE)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()
    return None


def _parse_datos_generales(lines: list[str]) -> dict | None:
    datos: dict = {}
    mapping = {
        "tipo_creditos": r"tipo de cr[eé]ditos",
        "numero_creditos": r"n[uú]mero de cr[eé]ditos",
        "duracion_total_horas": r"duraci[oó]n total en horas",
        "ubicacion": r"ubicaci[oó]n\b",
    }
    for field, pattern in mapping.items():
        value = _value_after(lines, pattern)
        if value:
            datos[field] = value

    requisitos = _value_requisitos(lines)
    if requisitos:
        datos["requisitos_previos"] = requisitos

    horas: dict = {}
    horas_map = {
        "HCP": r"\(HCP\)",
        "HEI": r"\(HEI\)",
        "practicas_formativas_laboratorios": r"pr[aá]cticas formativas \(laboratorios\)",
        "PSP": r"\(PSP\**\)",
        "PSE": r"\(PSE\**\)",
    }
    for field, pattern in horas_map.items():
        # PSP/PSE traen el valor en la siguiente línea.
        allow_next = field in {"PSP", "PSE"}
        value = _value_after(lines, pattern, allow_next_line=allow_next)
        if value:
            horas[field] = value
    if horas:
        datos["distribucion_horas"] = horas

    return datos or None


_CONTENIDOS_SUBTEMA_RE = re.compile(r"^o\s+", re.IGNORECASE)


def _parse_contenidos(lines: list[str]) -> list[dict] | None:
    """Convierte 'Contenidos esenciales' en unidades (•) con subtemas (o)."""
    unidades: list[dict] = []
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        if _BULLET_RE.match(text):
            unidades.append(
                {"titulo": re.sub(r"\s+", " ", _BULLET_RE.sub("", text)).strip(), "subtemas": []}
            )
        elif _CONTENIDOS_SUBTEMA_RE.match(text) and unidades:
            subtema = re.sub(r"\s+", " ", _CONTENIDOS_SUBTEMA_RE.sub("", text)).strip()
            if subtema:
                unidades[-1]["subtemas"].append(subtema)
        elif unidades:
            # Continuación de un subtema o título envuelto.
            if unidades[-1]["subtemas"]:
                unidades[-1]["subtemas"][-1] += " " + text
            else:
                unidades[-1]["titulo"] += " " + text
    unidades = [u for u in unidades if u["titulo"]]
    return unidades or None


def _parse_perfil_egreso(lines: list[str]) -> dict | None:
    buckets: dict[str, list[str]] = {"genericas": [], "disciplinares": []}
    current = "genericas"
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        normalized = _normalize(text)
        if normalized.startswith("genericas"):
            current = "genericas"
            continue
        if normalized.startswith("disciplinares"):
            current = "disciplinares"
            continue
        is_new = bool(re.match(r"^\d+\.\s", text)) or bool(re.match(r"^[A-ZÁÉÍÓÚÑ]{2,}\d", text))
        if is_new or not buckets[current]:
            buckets[current].append(text)
        else:
            buckets[current][-1] += " " + text
    result = {
        key: [re.sub(r"\s+", " ", item).strip() for item in values]
        for key, values in buckets.items()
        if values
    }
    return result or None


def _parse_evaluacion(lines: list[str]) -> dict | None:
    out: dict = {}
    current: str | None = None
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        normalized = _normalize(text)
        if normalized.startswith("evaluacion de proceso"):
            current = "proceso"
            match = re.search(r"(\d+)\s*%", text)
            out["proceso"] = {"porcentaje": int(match.group(1)) if match else None, "items": []}
            continue
        if normalized.startswith("evaluacion de producto"):
            current = "producto"
            match = re.search(r"(\d+)\s*%", text)
            out["producto"] = {"porcentaje": int(match.group(1)) if match else None, "items": []}
            continue
        if current is None:
            continue
        if _BULLET_RE.match(text):
            out[current]["items"].append(_BULLET_RE.sub("", text).strip())
        elif out[current]["items"]:
            out[current]["items"][-1] += " " + text
    return out or None


def _parse_referencias(lines: list[str]) -> dict | None:
    buckets: dict[str, list[str]] = {"basicas": [], "complementarias": []}
    current: str | None = None
    new_ref_comma = re.compile(r"^[A-ZÁÉÍÓÚÑ][^,\n]{0,40},")
    new_ref_year = re.compile(r"^[A-ZÁÉÍÓÚÑ].{0,50}\(\d{4}\)")
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        normalized = _normalize(text)
        if normalized.startswith("basicas"):
            current = "basicas"
            continue
        if normalized.startswith("complementarias"):
            current = "complementarias"
            continue
        if current is None:
            continue
        is_new = bool(new_ref_comma.match(text)) or bool(new_ref_year.match(text))
        if is_new or not buckets[current]:
            buckets[current].append(text)
        else:
            buckets[current][-1] += " " + text
    result = {
        key: [re.sub(r"\s+", " ", item).strip() for item in values]
        for key, values in buckets.items()
        if values
    }
    return result or None


def extract_program_metadata(text: str) -> dict | None:
    """Extrae los datos generales del programa de asignatura desde texto plano."""
    lines = text.splitlines()
    sections = _split_numbered_sections(lines)

    metadata: dict = {}

    datos = _parse_datos_generales(lines)
    if datos:
        metadata["datos_generales"] = datos

    if sections.get("contexto"):
        contexto = _join_paragraph(sections["contexto"])
        if contexto:
            metadata["contexto_asignatura"] = contexto

    if sections.get("relacion"):
        relacion = _join_paragraph(sections["relacion"])
        if relacion:
            metadata["relacion_otras_asignaturas"] = relacion

    if sections.get("_contenidos"):
        contenidos = _parse_contenidos(sections["_contenidos"])
        if contenidos:
            metadata["contenidos_esenciales"] = contenidos

    if sections.get("perfil_egreso"):
        perfil = _parse_perfil_egreso(sections["perfil_egreso"])
        if perfil:
            metadata["competencias_perfil_egreso"] = perfil

    if sections.get("experiencias"):
        experiencias = _merge_bullets(sections["experiencias"])
        if experiencias:
            metadata["experiencias_aprendizaje"] = experiencias

    if sections.get("estrategias_ensenanza"):
        estrategias = _merge_bullets(sections["estrategias_ensenanza"])
        if estrategias:
            metadata["estrategias_ensenanza_sugeridas"] = estrategias

    if sections.get("evaluacion"):
        evaluacion = _parse_evaluacion(sections["evaluacion"])
        if evaluacion:
            metadata["estrategias_evaluacion"] = evaluacion

    if sections.get("practicas"):
        practicas = _join_paragraph(sections["practicas"])
        if practicas:
            metadata["practicas_formativas"] = practicas

    if sections.get("referencias"):
        referencias = _parse_referencias(sections["referencias"])
        if referencias:
            metadata["referencias_sugeridas"] = referencias

    if sections.get("perfil_docente"):
        perfil_docente = _merge_bullets(sections["perfil_docente"])
        if perfil_docente:
            metadata["perfil_docente"] = perfil_docente

    return metadata or None
