from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from course_pipeline.config import Settings
from course_pipeline.docx_parser import DocxParsingError
from course_pipeline.instructional_generator import InstructionalGenerationError
from course_pipeline.pipeline import CoursePipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline DOCX/PDF -> JSON -> Imagenes -> Moodle XML")
    parser.add_argument("--input-file", help="Ruta al archivo de entrada (.docx o .pdf)")
    parser.add_argument("--docx", help="Compatibilidad: ruta al archivo .docx")
    parser.add_argument("--pdf", help="Ruta al archivo .pdf")
    parser.add_argument("--course-name", required=True, help="Nombre del curso")
    parser.add_argument("--skip-images", action="store_true", help="Omite generacion de imagenes")
    parser.add_argument(
        "--skip-readings",
        action="store_true",
        help="Omite la generacion de lecturas de fundamentacion (OpenAlex + LLM)",
    )
    parser.add_argument(
        "--skip-presentations",
        action="store_true",
        help="Omite la generacion de presentaciones HTML5 por ADA",
    )
    parser.add_argument(
        "--skip-questions",
        action="store_true",
        help="Omite la generacion del banco de preguntas y el quiz",
    )
    args = parser.parse_args()
    args.input_file = args.input_file or args.docx or args.pdf
    if not args.input_file:
        parser.error("Debes indicar --input-file (o --docx / --pdf)")
    return args


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    pipeline = CoursePipeline(settings)

    try:
        result = pipeline.run(
            input_path=Path(args.input_file).resolve(),
            course_name=args.course_name,
            skip_images=args.skip_images,
            skip_readings=args.skip_readings,
            skip_presentations=args.skip_presentations,
            skip_questions=args.skip_questions,
        )
    except (DocxParsingError, InstructionalGenerationError) as exc:
        logging.error("Pipeline fallo: %s", exc)
        return 1
    except Exception as exc:  # pragma: no cover
        logging.exception("Error inesperado: %s", exc)
        return 1

    logging.info("JSON generado en: %s", result["json_output"])
    logging.info("Moodle XML generado en: %s", result["xml_output"])
    if result.get("quiz_output"):
        logging.info("Moodle Quiz XML generado en: %s", result["quiz_output"])
    if result.get("manual_pack_output"):
        logging.info("Manual Build Pack generado en: %s", result["manual_pack_output"])
    if result["warnings"]:
        logging.warning("Pipeline finalizo con advertencias (%d)", len(result["warnings"]))
        for warning in result["warnings"]:
            logging.warning("- %s", warning)
    else:
        logging.info("Pipeline finalizo sin advertencias")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
