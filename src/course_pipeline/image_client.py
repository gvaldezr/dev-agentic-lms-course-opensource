from __future__ import annotations

import base64
import hashlib
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from .config import Settings


class ImageGenerationError(Exception):
    pass


class StableDiffusionImageClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_image(self, prompt: str, images_dir: Path, filename_prefix: str) -> Optional[Path]:
        if not self.settings.image_api_url:
            raise ImageGenerationError("IMAGE_API_URL no esta configurado")

        images_dir.mkdir(parents=True, exist_ok=True)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
        output_path = images_dir / f"{filename_prefix}_{prompt_hash}.png"
        if output_path.exists():
            return output_path

        headers = {"Content-Type": "application/json"}
        if self.settings.image_api_key:
            headers["Authorization"] = f"Bearer {self.settings.image_api_key}"

        payload = {
            "prompt": prompt,
            "width": self.settings.image_width,
            "height": self.settings.image_height,
        }

        response = None
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = requests.post(
                    self.settings.image_api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.settings.image_timeout_seconds,
                )
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 ** (attempt - 1))

        if response is None:
            raise ImageGenerationError(
                f"Error llamando al endpoint de imagenes tras 3 intentos: {last_error}"
            ) from last_error

        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("image/"):
            output_path.write_bytes(response.content)
            return output_path

        try:
            data = response.json()
        except ValueError as exc:
            raise ImageGenerationError("La respuesta de imagen no es JSON ni binaria") from exc

        if data.get("image_base64"):
            image_bytes = base64.b64decode(data["image_base64"])
            output_path.write_bytes(image_bytes)
            return output_path

        if data.get("image_url"):
            return self._download_image(data["image_url"], output_path)

        raise ImageGenerationError("No se encontro image_base64 ni image_url en la respuesta")

    def _download_image(self, image_url: str, output_path: Path) -> Path:
        try:
            response = requests.get(image_url, timeout=self.settings.image_timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ImageGenerationError(f"No se pudo descargar image_url: {exc}") from exc

        output_path.write_bytes(response.content)
        return output_path


class LocalCliImageClient:
    """Generate images with a local stable-diffusion.cpp `sd-cli` binary."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_image(self, prompt: str, images_dir: Path, filename_prefix: str) -> Optional[Path]:
        cli_path = Path(self.settings.image_cli_path)
        model_path = Path(self.settings.image_model_path)

        if not self.settings.image_cli_path or not cli_path.exists():
            raise ImageGenerationError(
                f"IMAGE_CLI_PATH no valido o no existe: {self.settings.image_cli_path}"
            )
        if not self.settings.image_model_path or not model_path.exists():
            raise ImageGenerationError(
                f"IMAGE_MODEL_PATH no valido o no existe: {self.settings.image_model_path}"
            )

        images_dir.mkdir(parents=True, exist_ok=True)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
        output_path = images_dir / f"{filename_prefix}_{prompt_hash}.png"
        if output_path.exists():
            return output_path

        style_suffix = self.settings.image_style_suffix
        full_prompt = f"{style_suffix}, {prompt}".strip() if style_suffix else prompt

        lora_dir = self.settings.image_lora_dir
        lora_tag = self.settings.image_lora_tag
        if lora_dir and lora_tag:
            full_prompt = f"{full_prompt} {lora_tag}".strip()

        cmd = [
            str(cli_path),
            "-m", str(model_path),
            "-p", full_prompt,
            "-o", str(output_path),
            "--steps", str(self.settings.image_steps),
            "-H", str(self.settings.image_height),
            "-W", str(self.settings.image_width),
            "--cfg-scale", str(self.settings.image_cfg_scale),
            "--seed", str(self.settings.image_seed),
            "--sampling-method", self.settings.image_sampling_method,
        ]
        if self.settings.image_negative_prompt:
            cmd += ["--negative-prompt", self.settings.image_negative_prompt]
        if lora_dir:
            cmd += ["--lora-model-dir", lora_dir]
            if self.settings.image_lora_apply_mode:
                cmd += ["--lora-apply-mode", self.settings.image_lora_apply_mode]

        env = os.environ.copy()
        if self.settings.image_lib_dir:
            existing = env.get("DYLD_LIBRARY_PATH", "")
            env["DYLD_LIBRARY_PATH"] = (
                f"{self.settings.image_lib_dir}:{existing}" if existing else self.settings.image_lib_dir
            )

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.settings.image_timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ImageGenerationError(
                f"sd-cli excedio el timeout de {self.settings.image_timeout_seconds}s"
            ) from exc
        except OSError as exc:
            raise ImageGenerationError(f"No se pudo ejecutar sd-cli: {exc}") from exc

        if result.returncode != 0:
            tail = (result.stderr or result.stdout or "").strip()[-500:]
            raise ImageGenerationError(f"sd-cli fallo (codigo {result.returncode}): {tail}")

        if not output_path.exists():
            tail = (result.stderr or result.stdout or "").strip()[-500:]
            raise ImageGenerationError(f"sd-cli no genero la imagen esperada. Salida: {tail}")

        return output_path


def build_image_client(settings: Settings):
    """Return the configured image client based on IMAGE_BACKEND."""
    if settings.image_backend in {"local_cli", "cli", "local", "sd-cli"}:
        return LocalCliImageClient(settings)
    return StableDiffusionImageClient(settings)
