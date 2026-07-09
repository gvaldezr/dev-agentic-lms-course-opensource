"""Generate only the lesson images from an existing course_structure.json.

Reuses the configured image backend (see .env) without re-running the LLM or
OpenAlex steps. Updates each lesson's `image_path` in place and rewrites the JSON.

Usage:
    PYTHONPATH=src python scripts/generate_images_only.py \
        [--json data/output/course_structure.json] [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from course_pipeline.config import Settings  # noqa: E402
from course_pipeline.image_client import ImageGenerationError, build_image_client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="Ruta al course_structure.json")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerar aunque la leccion ya tenga image_path",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.ensure_output_dirs()

    json_path = Path(args.json) if args.json else settings.output_dir / "course_structure.json"
    if not json_path.exists():
        print(f"No existe el JSON: {json_path}", file=sys.stderr)
        return 1

    data = json.loads(json_path.read_text(encoding="utf-8"))
    modulos = data.get("modulos", [])
    images_dir = settings.output_dir / "assets" / "images"

    client = build_image_client(settings)
    print(f"Backend: {settings.image_backend} | modelo: {Path(settings.image_model_path).name}")
    if settings.image_lora_dir and settings.image_lora_tag:
        print(f"LoRA: {settings.image_lora_tag} ({settings.image_lora_apply_mode})")

    total = sum(len(m.get("lecciones", [])) for m in modulos)
    done = 0
    failures = 0
    t_start = time.time()

    for mi, module in enumerate(modulos, start=1):
        for li, lesson in enumerate(module.get("lecciones", []), start=1):
            done += 1
            prompt = (lesson.get("prompt_imagen") or "").strip()
            label = f"[{done}/{total}] m{mi}_l{li}"
            if not prompt:
                print(f"{label} sin prompt_imagen, omitido")
                continue
            if lesson.get("image_path") and not args.force:
                print(f"{label} ya tiene image_path, omitido (usa --force para regenerar)")
                continue

            t0 = time.time()
            try:
                image_path = client.generate_image(
                    prompt=prompt,
                    images_dir=images_dir,
                    filename_prefix=f"m{mi}_l{li}",
                )
            except ImageGenerationError as exc:
                failures += 1
                print(f"{label} FALLO: {exc}", file=sys.stderr)
                continue

            if image_path:
                lesson["image_path"] = str(image_path.relative_to(settings.output_dir))
                print(f"{label} OK en {time.time() - t0:.1f}s -> {lesson['image_path']}")
            else:
                failures += 1
                print(f"{label} no devolvio ruta de imagen", file=sys.stderr)

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    elapsed = time.time() - t_start
    print(
        f"\nListo: {total - failures}/{total} imagenes en {elapsed / 60:.1f} min. "
        f"JSON actualizado: {json_path}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
