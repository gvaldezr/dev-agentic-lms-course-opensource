from __future__ import annotations

import json
import re

import requests

from . import llm_client
from .config import Settings
from .schemas import CourseStructure, ParsedCourseInput


class InstructionalGenerationError(Exception):
    pass


SYSTEM_PROMPT = """Actua como un Disenador Instruccional Senior experto en la metodologia DUA y en creacion de cursos para Moodle.
Tu tarea es transformar Objetivos, Competencias y Syllabus en una estructura modular.
Si se te entrega una lista de UNIDADES oficiales, debes crear EXACTAMENTE un modulo por cada unidad,
respetando su titulo y su orden tal cual se te entregan (no inventes, no fusiones, no reordenes unidades).
Para cada leccion genera:
1. titulo
2. objetivo de aprendizaje de la leccion, redactado con un verbo observable (1 oracion)
3. texto didactico motivador, en parrafos cortos
4. actividad de evaluacion practica
5. prompt_imagen en ingles, siguiendo ESTRICTAMENTE estas reglas de estilo:
   - Describe UNA sola escena tipo icono, simple y metaforica, con muy pocos elementos.
   - Usa formas geometricas grandes y simples (un personaje, un objeto principal, a lo sumo 2-3 elementos pequenos).
   - Deja mucho espacio vacio alrededor; composicion limpia y minimalista.
   - PROHIBIDO incluir texto, palabras, letras, numeros, etiquetas, infografias, tableros, dashboards, graficas, calendarios, interfaces de usuario, pantallas o collages.
   - Termina siempre el prompt con la frase exacta: "very few elements, lots of empty space, no text."
   - Ejemplo de estilo correcto: "A calm character holding an umbrella that shields a chat bubble from one small storm cloud, very few elements, lots of empty space, no text."
Responde exclusivamente en JSON con la estructura:
{
  \"curso\": \"nombre del curso\",
  \"modulos\": [
    {
      \"titulo\": \"...\",
      \"lecciones\": [
        {
          \"titulo\": \"...\",
          \"objetivo\": \"...\",
          \"texto\": \"...\",
          \"actividad\": \"...\",
          \"prompt_imagen\": \"...\"
        }
      ]
    }
  ]
}
"""


class InstructionalGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, parsed_input: ParsedCourseInput) -> CourseStructure:
        user_prompt = self._build_user_prompt(parsed_input)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            headers = llm_client.build_llm_headers(self.settings)
            response = requests.post(
                llm_client.resolve_llm_url(self.settings),
                headers=headers,
                json=llm_client.build_chat_payload(self.settings, messages, temperature=0.3),
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except llm_client.LLMConfigError as exc:
            raise InstructionalGenerationError(str(exc)) from exc
        except requests.RequestException as exc:
            raise InstructionalGenerationError(f"Error de comunicacion con LLM: {exc}") from exc

        response_data = self._decode_response_json(response)
        content = self._extract_content(response_data)
        json_text = self._extract_json(content)

        try:
            decoded = json.loads(json_text)
            course = CourseStructure.model_validate(decoded)
        except Exception as exc:
            raise InstructionalGenerationError(f"JSON del LLM invalido: {exc}") from exc

        if not course.curso.strip():
            course.curso = parsed_input.course_name

        self._enforce_unit_titles(course, parsed_input)

        return course

    @staticmethod
    def _enforce_unit_titles(course: CourseStructure, parsed_input: ParsedCourseInput) -> None:
        """Garantiza que los modulos se llamen como las unidades oficiales del PDF."""
        unidades = parsed_input.unidades
        if not unidades:
            return
        unit_titles = [str(u.get("titulo", "")).strip() for u in unidades if str(u.get("titulo", "")).strip()]
        if not unit_titles:
            return

        modules = course.modulos
        # Si el LLM devolvio mas modulos que unidades, fusiona los excedentes en el ultimo.
        if len(modules) > len(unit_titles):
            keep = modules[: len(unit_titles)]
            for extra in modules[len(unit_titles):]:
                keep[-1].lecciones.extend(extra.lecciones)
            modules = keep
        course.modulos = modules

        for index, title in enumerate(unit_titles):
            if index < len(course.modulos):
                course.modulos[index].titulo = title

    def _build_user_prompt(self, parsed_input: ParsedCourseInput) -> str:
        objectives = "\n".join(f"- {item}" for item in parsed_input.objectives)
        competencies = "\n".join(f"- {item}" for item in parsed_input.competencies)

        units_text = ""
        if parsed_input.unidades:
            lines: list[str] = []
            for index, unidad in enumerate(parsed_input.unidades, start=1):
                titulo = str(unidad.get("titulo", "")).strip()
                subtemas = unidad.get("subtemas") or []
                lines.append(f"{index}. {titulo}")
                for subtema in subtemas:
                    lines.append(f"   - {subtema}")
            units_block = "\n".join(lines)
            units_text = (
                "\n\nUNIDADES OFICIALES (contenidos esenciales del programa):\n"
                f"{units_block}\n"
                f"Crea EXACTAMENTE {len(parsed_input.unidades)} modulos, uno por unidad, "
                "usando esos titulos en ese mismo orden. Usa los subtemas como referencia "
                "para distribuir las lecciones dentro de cada modulo."
            )

        planning_text = ""
        if parsed_input.planning_context:
            planning_text = (
                "\n\nContexto de planeacion detectado en plantilla:\n"
                f"- {json.dumps(parsed_input.planning_context, ensure_ascii=False)}\n"
                "- Debes alinear la propuesta a 16 semanas, 3 periodos, 2 ADAS por periodo "
                "y una fase de proyecto integrador final por periodo."
            )

        return (
            f"Nombre del curso: {parsed_input.course_name}\n\n"
            f"Objetivos:\n{objectives}\n\n"
            f"Competencias:\n{competencies}\n\n"
            f"Syllabus:\n{parsed_input.syllabus}\n"
            f"{units_text}"
            f"{planning_text}\n\n"
            "Entrega SOLO JSON valido, sin markdown ni explicaciones adicionales."
        )

    @staticmethod
    def _extract_content(response_data: dict) -> str:
        # OpenAI-compatible responses.
        if "choices" in response_data and response_data["choices"]:
            maybe_content = response_data["choices"][0].get("message", {}).get("content", "")
            if maybe_content:
                return maybe_content

        # Ollama /api/chat non-stream response format.
        maybe_ollama_content = response_data.get("message", {}).get("content", "")
        if maybe_ollama_content:
            return str(maybe_ollama_content)

        if "output_text" in response_data:
            return str(response_data["output_text"])

        if "content" in response_data:
            return str(response_data["content"])

        raise InstructionalGenerationError(
            "No se pudo extraer contenido del response del LLM. "
            "Verifica que el endpoint retorne formato OpenAI o formato Ollama /api/chat"
        )

    @staticmethod
    def _decode_response_json(response: requests.Response) -> dict:
        try:
            return response.json()
        except Exception:
            # Some servers can still respond with newline-delimited JSON chunks.
            text = response.text.strip()
            if not text:
                raise InstructionalGenerationError("Respuesta vacia del LLM")

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in reversed(lines):
                try:
                    maybe_json = json.loads(line)
                except Exception:
                    continue
                if isinstance(maybe_json, dict):
                    return maybe_json

            raise InstructionalGenerationError("No se pudo decodificar JSON de la respuesta del LLM")

    @staticmethod
    def _extract_json(text: str) -> str:
        trimmed = text.strip()
        if trimmed.startswith("{") and trimmed.endswith("}"):
            return trimmed

        fenced = re.search(r"```json\s*(\{.*\})\s*```", trimmed, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1)

        generic = re.search(r"(\{.*\})", trimmed, flags=re.DOTALL)
        if generic:
            return generic.group(1)

        raise InstructionalGenerationError("No se encontro un bloque JSON en la respuesta del LLM")
