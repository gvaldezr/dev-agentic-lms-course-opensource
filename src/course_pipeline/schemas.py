from __future__ import annotations

from typing import Any
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ParsedCourseInput(BaseModel):
    course_name: str = Field(min_length=1)
    objectives: list[str] = Field(min_length=1)
    competencies: list[str] = Field(min_length=1)
    syllabus: str = Field(min_length=1)
    course_competency: str | None = None
    planning_context: dict[str, Any] | None = None
    program_metadata: dict[str, Any] | None = None
    unidades: list[dict[str, Any]] | None = None


class Lesson(BaseModel):
    titulo: str = Field(min_length=1)
    texto: str = Field(min_length=1)
    actividad: str = Field(min_length=1)
    prompt_imagen: str = Field(min_length=1)
    objetivo: Optional[str] = None
    image_path: Optional[str] = None


class Module(BaseModel):
    titulo: str = Field(min_length=1)
    lecciones: list[Lesson] = Field(min_length=1)


class CourseStructure(BaseModel):
    curso: str = Field(min_length=1)
    modulos: list[Module] = Field(min_length=1)

    @field_validator("modulos")
    @classmethod
    def validate_modules_not_empty(cls, value: list[Module]) -> list[Module]:
        if not value:
            raise ValueError("Debe existir al menos un modulo")
        return value
