from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from .config import Settings
from .ada_structure import build_ada_course_structure
from .docx_parser import DocxParsingError, parse_course_file
from .image_client import ImageGenerationError, build_image_client
from .instructional_generator import InstructionalGenerationError, InstructionalGenerator
from .manual_build_pack import export_manual_build_pack
from .moodle_xml_exporter import MoodleXmlExporter
from .openalex_enrichment import build_openalex_payload
from .planning import build_operational_plan
from .presentation_generator import attach_presentations_to_ada_structure
from .question_bank_generator import build_question_bank, select_quiz
from .reading_generator import attach_readings_to_ada_structure
from .session_objectives import generate_and_attach_session_objectives


class CoursePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("course_pipeline")
        self.generator = InstructionalGenerator(settings)
        self.image_client = build_image_client(settings)
        self.exporter = MoodleXmlExporter()

    def run(
        self,
        input_path: Path,
        course_name: str,
        skip_images: bool = False,
        skip_readings: bool = False,
        skip_presentations: bool = False,
        skip_questions: bool = False,
    ) -> dict:
        self.settings.ensure_output_dirs()
        warnings: list[str] = []

        try:
            parsed = parse_course_file(file_path=input_path, course_name=course_name)
        except DocxParsingError:
            raise

        try:
            course = self.generator.generate(parsed)
        except InstructionalGenerationError:
            raise

        images_dir = self.settings.output_dir / "assets" / "images"

        if not skip_images:
            for module_index, module in enumerate(course.modulos, start=1):
                for lesson_index, lesson in enumerate(module.lecciones, start=1):
                    prefix = f"m{module_index}_l{lesson_index}"
                    try:
                        image_path = self.image_client.generate_image(
                            prompt=lesson.prompt_imagen,
                            images_dir=images_dir,
                            filename_prefix=prefix,
                        )
                        if image_path:
                            lesson.image_path = str(image_path.relative_to(self.settings.output_dir))
                    except ImageGenerationError as exc:
                        warning = (
                            f"Fallo imagen en modulo {module_index}, leccion {lesson_index}: {exc}. "
                            "La exportacion continua sin imagen en esta leccion."
                        )
                        warnings.append(warning)
                        self.logger.warning(warning)

        slug = re.sub(r"[^a-z0-9]+", "_", course_name.lower()).strip("_") or "curso"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output_path = self.settings.output_dir / f"{slug}_{timestamp}.json"
        output_payload = course.model_dump(mode="json")
        output_payload.update(
            build_openalex_payload(
                parsed_input=parsed,
                api_key=self.settings.openalex_api_key,
            )
        )
        output_payload["planeacion_operativa"] = build_operational_plan(
            total_weeks=15,
            periods=3,
            adas_per_period=2,
            session_minutes=[90, 45],
            template_context=parsed.planning_context,
        )
        output_payload["estructura_curso_adas"] = build_ada_course_structure(
            course=course,
            operational_plan=output_payload["planeacion_operativa"],
        )

        session_warnings = generate_and_attach_session_objectives(
            settings=self.settings,
            ada_structure=output_payload["estructura_curso_adas"],
            operational_plan=output_payload["planeacion_operativa"],
            course_name=course.curso,
        )
        warnings.extend(session_warnings)

        if parsed.program_metadata:
            output_payload["programa_asignatura"] = parsed.program_metadata

        if not skip_readings:
            reading_warnings = attach_readings_to_ada_structure(
                settings=self.settings,
                ada_structure=output_payload["estructura_curso_adas"],
            )
            warnings.extend(reading_warnings)

            if not skip_presentations:
                presentation_warnings = attach_presentations_to_ada_structure(
                    settings=self.settings,
                    ada_structure=output_payload["estructura_curso_adas"],
                )
                warnings.extend(presentation_warnings)

        question_bank: list[dict] = []
        quiz_items: list[dict] = []
        if not skip_readings and not skip_questions:
            question_bank, question_warnings = build_question_bank(
                settings=self.settings,
                ada_structure=output_payload["estructura_curso_adas"],
            )
            warnings.extend(question_warnings)
            quiz_items = select_quiz(question_bank)
            output_payload["banco_preguntas"] = question_bank
            output_payload["quiz"] = quiz_items

        json_output_path.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        xml_output_path = self.settings.output_dir / f"moodle_course_{slug}_{timestamp}.xml"
        self.exporter.export(
            course=course,
            output_file=xml_output_path,
            ada_structure=output_payload.get("estructura_curso_adas"),
            question_bank=question_bank,
            question_bank_category=f"Banco de preguntas - {course.curso}",
        )

        quiz_output_path: str | None = None
        if quiz_items:
            quiz_path = self.settings.output_dir / f"moodle_quiz_{slug}_{timestamp}.xml"
            self.exporter.export_quiz(
                items=quiz_items,
                output_file=quiz_path,
                category=f"Quiz - {course.curso}",
            )
            quiz_output_path = str(quiz_path)

        manual_pack_path = export_manual_build_pack(
            output_dir=self.settings.output_dir,
            slug=slug,
            timestamp=timestamp,
            course_name=course.curso,
            ada_structure=output_payload.get("estructura_curso_adas"),
            question_bank=question_bank,
            quiz_items=quiz_items,
        )

        return {
            "json_output": str(json_output_path),
            "xml_output": str(xml_output_path),
            "quiz_output": quiz_output_path,
            "manual_pack_output": str(manual_pack_path),
            "images_dir": str(images_dir),
            "warnings": warnings,
        }
