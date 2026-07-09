"""Capa de abstraccion del proveedor LLM.

Permite elegir entre generacion con Ollama (local/remoto) o la API de OpenAI
(o cualquier endpoint compatible con `chat/completions`) mediante la variable de
entorno ``LLM_PROVIDER``. Centraliza la construccion de la peticion (URL, headers
y payload) y la extraccion del contenido para que todos los generadores compartan
exactamente la misma logica de proveedor.
"""

from __future__ import annotations

from typing import Any

from .config import Settings

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class LLMConfigError(RuntimeError):
    """Error de configuracion del proveedor LLM (falta URL, API key, etc.)."""


def is_openai(settings: Settings) -> bool:
    return settings.llm_provider == "openai"


def resolve_llm_url(settings: Settings) -> str:
    """Devuelve la URL del endpoint segun el proveedor configurado."""
    if settings.llm_api_url:
        return settings.llm_api_url
    return DEFAULT_OPENAI_URL if is_openai(settings) else DEFAULT_OLLAMA_URL


def resolve_llm_model(settings: Settings) -> str:
    if settings.llm_model:
        return settings.llm_model
    return DEFAULT_OPENAI_MODEL if is_openai(settings) else "default"


def build_llm_headers(settings: Settings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if is_openai(settings) and not settings.llm_api_key:
        raise LLMConfigError("LLM_API_KEY es obligatorio cuando LLM_PROVIDER=openai")
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    return headers


def build_chat_payload(
    settings: Settings,
    messages: list[dict[str, str]],
    temperature: float,
) -> dict[str, Any]:
    """Construye el payload con el formato esperado por cada proveedor.

    - Ollama espera la temperatura dentro de ``options``.
    - OpenAI (y compatibles) la esperan en el nivel superior.
    """
    model = resolve_llm_model(settings)
    if is_openai(settings):
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
    return {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }


def extract_chat_content(data: Any) -> str:
    """Extrae el texto de la respuesta, tolerando formato OpenAI y Ollama."""
    if not isinstance(data, dict):
        return ""

    choices = data.get("choices")
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return str(content)

    message = data.get("message", {})
    if isinstance(message, dict) and message.get("content"):
        return str(message["content"])

    return ""
