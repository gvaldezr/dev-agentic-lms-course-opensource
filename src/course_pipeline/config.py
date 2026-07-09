from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_api_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_seconds: int
    image_api_url: str
    image_api_key: str
    image_timeout_seconds: int
    image_width: int
    image_height: int
    image_backend: str
    image_cli_path: str
    image_lib_dir: str
    image_model_path: str
    image_steps: int
    image_cfg_scale: float
    image_sampling_method: str
    image_seed: int
    image_lora_dir: str
    image_lora_tag: str
    image_lora_apply_mode: str
    image_style_suffix: str
    image_negative_prompt: str
    output_dir: Path
    log_level: str
    openalex_api_key: str

    @staticmethod
    def from_env() -> "Settings":
        output_dir = Path(os.getenv("OUTPUT_DIR", "./data/output")).resolve()
        return Settings(
            llm_provider=os.getenv("LLM_PROVIDER", "ollama").strip().lower() or "ollama",
            llm_api_url=os.getenv("LLM_API_URL", "").strip(),
            llm_api_key=os.getenv("LLM_API_KEY", "").strip(),
            llm_model=os.getenv("LLM_MODEL", "").strip(),
            llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            image_api_url=os.getenv("IMAGE_API_URL", "").strip(),
            image_api_key=os.getenv("IMAGE_API_KEY", "").strip(),
            image_timeout_seconds=int(os.getenv("IMAGE_TIMEOUT_SECONDS", "90")),
            image_width=int(os.getenv("IMAGE_WIDTH", "1024")),
            image_height=int(os.getenv("IMAGE_HEIGHT", "1024")),
            image_backend=os.getenv("IMAGE_BACKEND", "http").strip().lower() or "http",
            image_cli_path=_expand(os.getenv("IMAGE_CLI_PATH", "")),
            image_lib_dir=_expand(os.getenv("IMAGE_LIB_DIR", "")),
            image_model_path=_expand(os.getenv("IMAGE_MODEL_PATH", "")),
            image_steps=int(os.getenv("IMAGE_STEPS", "20")),
            image_cfg_scale=float(os.getenv("IMAGE_CFG_SCALE", "7.0")),
            image_sampling_method=os.getenv("IMAGE_SAMPLING_METHOD", "euler_a").strip() or "euler_a",
            image_seed=int(os.getenv("IMAGE_SEED", "42")),
            image_lora_dir=_expand(os.getenv("IMAGE_LORA_DIR", "")),
            image_lora_tag=os.getenv("IMAGE_LORA_TAG", "").strip(),
            image_lora_apply_mode=os.getenv("IMAGE_LORA_APPLY_MODE", "at_runtime").strip() or "at_runtime",
            image_style_suffix=os.getenv("IMAGE_STYLE_SUFFIX", "").strip(),
            image_negative_prompt=os.getenv("IMAGE_NEGATIVE_PROMPT", "").strip(),
            output_dir=output_dir,
            log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
            openalex_api_key=os.getenv("OPENALEX_API_KEY", "").strip(),
        )

    def ensure_output_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)


def _expand(value: str) -> str:
    """Expand ~ and environment variables in a path-like setting."""
    value = (value or "").strip()
    if not value:
        return ""
    return os.path.expanduser(os.path.expandvars(value))
