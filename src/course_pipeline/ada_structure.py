from __future__ import annotations

import re
from math import ceil
from typing import Any

from .schemas import CourseStructure

# Tiempo efectivo semanal: 1 sesion de 90 min + 1 sesion de 45 min.
SESSION_MINUTES_PATTERN = [90, 45]


def _session_total_minutes(session_number: int) -> int:
    """Minutos de la sesion segun su posicion dentro de la semana (patron 90/45)."""
    index = (session_number - 1) % len(SESSION_MINUTES_PATTERN)
    return SESSION_MINUTES_PATTERN[index]


def _session_block_durations(total_min: int) -> tuple[int, int, int]:
    """Reparte los minutos de la sesion en inicio / desarrollo / cierre."""
    edge = int(round((total_min / 6) / 5) * 5) or 5
    desarrollo = total_min - 2 * edge
    return edge, desarrollo, edge


def _split_minutes(total: int, count: int) -> list[int]:
    if count <= 0:
        return []
    base = total // count
    rem = total % count
    chunks = [base + (1 if idx < rem else 0) for idx in range(count)]
    return [max(1, item) for item in chunks]


def _build_block_activities(
    block: str,
    minutes: int,
    lesson_title: str,
    activity_text: str,
    objective_text: str,
) -> list[str]:
    if block == "inicio":
        templates = [
            "El docente realiza pase de lista y recupera el proposito de la sesion.",
            f"El docente presenta el tema '{lesson_title}' y vincula el contenido con el resultado de aprendizaje del ADA.",
            "El grupo activa conocimientos previos con preguntas detonadoras y ejemplos cercanos.",
            f"Se explican los criterios de trabajo y el objetivo especifico: {objective_text}",
        ]
    elif block == "desarrollo":
        templates = [
            f"El docente modela conceptos clave del tema '{lesson_title}' con apoyo de ejemplos aplicados.",
            f"El alumnado desarrolla la actividad central: {activity_text}",
            "Se organiza trabajo colaborativo para analizar, discutir y resolver el reto de la sesion.",
            "El docente acompana el proceso, orienta decisiones y retroalimenta avances parciales.",
            "Cada equipo o estudiante integra hallazgos en un producto de trabajo verificable.",
        ]
    else:
        templates = [
            "El grupo comparte conclusiones y evidencia avances con base en los criterios definidos.",
            "El docente retroalimenta resultados y precisa mejoras para la siguiente sesion.",
            "Se registra una breve reflexion individual sobre el aprendizaje logrado.",
        ]

    chunk_minutes = _split_minutes(minutes, len(templates))
    return [f"{template} ({mins} minutos)" for template, mins in zip(templates, chunk_minutes)]


def _infer_session_specific_objective(
    lesson_title: str,
    session_offset: int,
    total_sessions: int,
) -> str:
    if session_offset == 0:
        return (
            f"Identificar los elementos fundamentales de {lesson_title} mediante analisis guiado "
            "para establecer la base conceptual del ADA."
        )
    if session_offset == total_sessions - 1:
        return (
            f"Integrar aprendizajes sobre {lesson_title} en una evidencia de desempeno "
            "que demuestre el logro del resultado de aprendizaje."
        )
    return (
        f"Aplicar los conceptos de {lesson_title} en actividades colaborativas y de analisis "
        "para fortalecer el avance del entregable del ADA."
    )


def _build_session_summary(
    lesson_title: str,
    activity_text: str,
    foundations: list[str],
) -> list[str]:
    summary = [
        f"Aspectos esenciales de {lesson_title}.",
        f"Aplicacion del contenido en la actividad: {activity_text}",
    ]
    summary.extend(f"{item}." if not str(item).strip().endswith(".") else str(item) for item in foundations[:4])
    return summary


def _build_duration_label(session_numbers: list[int]) -> str:
    if not session_numbers:
        return "0 sesiones"

    mins = [_session_total_minutes(number) for number in session_numbers]
    n90 = sum(1 for m in mins if m == 90)
    n45 = sum(1 for m in mins if m == 45)
    total = len(mins)

    parts: list[str] = []
    if n90:
        parts.append(f"{n90} sesion{'es' if n90 != 1 else ''} de 90 minutos")
    if n45:
        parts.append(f"{n45} sesion{'es' if n45 != 1 else ''} de 45 minutos")

    return f"{total} sesiones ({' y '.join(parts)})"


def _extract_activity_number(ada_name: str) -> int | None:
    match = re.search(r"(\d+)", ada_name or "")
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _build_evidencias_aprendizaje(
    resultados_aprendizaje: list[str],
    acciones_base: list[str],
    tipo_actividad: str,
    instrumento: str,
) -> list[str]:
    """Genera evidencias en formato de productos completos, alineadas a los
    resultados de aprendizaje del ADA."""
    instrumento_l = (instrumento or "instrumento de evaluacion").lower()

    products: list[str] = []
    source = acciones_base if acciones_base else resultados_aprendizaje
    for idx, action in enumerate(source[:4], start=1):
        clean = re.sub(r"\s+", " ", str(action).strip()).rstrip(".")
        if not clean:
            continue
        products.append(
            f"Producto {idx} (entregable completo): {clean}."
        )

    if not products:
        products.append(
            f"Producto integrador completo alineado al objetivo del ADA (evaluado con {instrumento_l})."
        )

    products.append(
        f"Compilado final de evidencias con trazabilidad de mejoras y criterios cumplidos ({instrumento_l})."
    )

    if tipo_actividad == "producto":
        products.append(
            "Presentacion o defensa del producto final con argumentacion de decisiones y resultados."
        )

    return products


def _split_learning_actions(activity_text: str) -> list[str]:
    chunks = re.split(r"\.|\n|;", activity_text or "")
    actions: list[str] = []
    for chunk in chunks:
        clean = re.sub(r"\s+", " ", chunk).strip(" .")
        if len(clean) >= 20:
            actions.append(clean)
    # Deduplicar conservando orden.
    return list(dict.fromkeys(actions))


def _build_strategic_objective(
    foundations: list[str],
    tipo_actividad: str,
) -> str:
    focus = [f for f in foundations[:2] if f]
    focus_txt = " y ".join(focus) if focus else "la gestion estrategica de comunidades digitales"

    if tipo_actividad == "producto":
        return (
            f"Integrar de forma estrategica los aprendizajes de {focus_txt} para desarrollar un producto final "
            "con impacto comunicativo, criterios de calidad y pertinencia para comunidades virtuales."
        )

    return (
        f"Analizar y aplicar de forma estrategica los principios de {focus_txt} para disenar, monitorear "
        "y optimizar acciones orientadas al engagement de comunidades virtuales."
    )


def _build_learning_outcomes(actions: list[str]) -> list[str]:
    verbs = ["Sintetizar", "Evaluar", "Determinar", "Proponer"]
    outcomes: list[str] = []

    for idx, action in enumerate(actions[:4]):
        verb = verbs[idx] if idx < len(verbs) else "Aplicar"
        clean = re.sub(r"\s+", " ", action).strip(" .")
        outcomes.append(f"{verb} productos verificables asociados a: {clean}.")

    if not outcomes:
        outcomes.append("Aplicar criterios estrategicos de comunicacion digital en un producto verificable.")

    return outcomes


def _infer_thematic_foundations(
    lesson_title: str,
    lesson_activity: str,
    contenidos: list[str],
) -> list[str]:
    text = " ".join([lesson_title, lesson_activity, *contenidos]).lower()

    rules: list[tuple[list[str], str]] = [
        (["community manager", "cm"], "Rol estrategico del Community Manager"),
        (["marca", "tono", "identidad"], "Comunicacion e identidad de marca"),
        (["audiencia", "comunidad", "seguidores"], "Gestion y dinamizacion de comunidades digitales"),
        (["target", "buyer persona", "segment"], "Segmentacion y perfilamiento de audiencias"),
        (["diagnost", "necesidad", "pain point"], "Diagnostico de necesidades del publico"),
        (["monitor", "escucha", "comentario"], "Monitorizacion y escucha activa digital"),
        (["contenido", "publicacion", "estrategia"], "Estrategia de contenidos en redes sociales"),
        (["conflicto", "crisis", "respuesta"], "Manejo de conflictos y atencion en entornos digitales"),
        (["evaluacion", "rubrica", "cotejo"], "Evaluacion de desempeno en actividades de comunicacion digital"),
    ]

    inferred: list[str] = []
    for keywords, label in rules:
        if any(keyword in text for keyword in keywords):
            inferred.append(label)

    if not inferred:
        inferred.append(f"Fundamentos conceptuales de {lesson_title}")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(inferred))


def _middle_session_stage(session_offset: int, total_sessions: int) -> str:
    intermediate_count = max(1, total_sessions - 2)
    intermediate_pos = max(0, session_offset - 1)

    if intermediate_count == 1:
        return "aplicacion"

    ratio = intermediate_pos / (intermediate_count - 1)
    if ratio <= 0.34:
        return "apropiacion"
    if ratio <= 0.74:
        return "aplicacion"
    return "validacion"


def _activity_focus(tipo_actividad: str) -> dict[str, str]:
    if tipo_actividad == "producto":
        return {
            "artifact": "producto final",
            "evaluation": "rubrica analitica",
            "verb": "materializar",
            "collab": "coedicion",
        }

    return {
        "artifact": "proceso de trabajo",
        "evaluation": "lista de cotejo",
        "verb": "fortalecer",
        "collab": "coordinacion",
    }


def _build_session_instruction(
    lesson_title: str,
    activity_text: str,
    foundations: list[str],
    session_number: int,
    session_offset: int,
    total_sessions: int,
    tipo_actividad: str,
) -> dict[str, Any]:
    week_number = ceil(session_number / 2)
    session_total_min = _session_total_minutes(session_number)
    inicio_min, desarrollo_min, cierre_min = _session_block_durations(session_total_min)
    focus = _activity_focus(tipo_actividad=tipo_actividad)
    objective_text = _infer_session_specific_objective(
        lesson_title=lesson_title,
        session_offset=session_offset,
        total_sessions=total_sessions,
    )

    if session_offset == 0:
        inicio_instruction = (
            f"Presentar el ADA y su objetivo para '{lesson_title}', activar conocimientos previos "
            f"y compartir los criterios de evaluacion e instrumento a usar ({focus['evaluation']})."
        )
        desarrollo_instruction = (
            f"Iniciar la actividad base: {activity_text}. Guiar la comprension de consignas, "
            f"asignar roles para la {focus['collab']} y modelar un ejemplo de desempeno esperado."
        )
        cierre_instruction = (
            "Recoger evidencias diagnosticas, registrar acuerdos de trabajo y definir entregables "
            "de avance para la siguiente sesion."
        )
    elif session_offset == total_sessions - 1:
        inicio_instruction = (
            "Recapitular hallazgos de sesiones anteriores y aclarar criterios finales de calidad "
            "para el cierre del ADA."
        )
        desarrollo_instruction = (
            f"Consolidar el {focus['artifact']}, realizar revision cruzada entre pares y ajustar en funcion "
            "de la retroalimentacion recibida."
        )
        cierre_instruction = (
            "Realizar cierre reflexivo del ADA, entrega formal de evidencias y retroalimentacion "
            f"sumativa segun el instrumento definido ({focus['evaluation']})."
        )
    else:
        stage = _middle_session_stage(session_offset=session_offset, total_sessions=total_sessions)

        if stage == "apropiacion":
            inicio_instruction = (
                "Revisar avances iniciales, aclarar dudas de comprension conceptual y acordar metas "
                f"puntuales para {focus['verb']} la base del ADA."
            )
            desarrollo_instruction = (
                "Desarrollar practica guiada con ejemplos comparativos, retroalimentacion inmediata "
                f"y ajustes de desempeno centrados en criterios de {focus['artifact']}."
            )
            cierre_instruction = (
                "Documentar aprendizajes emergentes y definir tareas de profundizacion para transitar "
                "a una aplicacion mas autonoma."
            )
        elif stage == "aplicacion":
            inicio_instruction = (
                "Retomar metas de mejora de la sesion anterior y explicitar el reto aplicado de la "
                "jornada con indicadores de logro."
            )
            desarrollo_instruction = (
                "Ejecutar trabajo colaborativo orientado a resolver la actividad central, incorporando "
                f"iteraciones del {focus['artifact']} y soporte docente focalizado."
            )
            cierre_instruction = (
                "Consolidar evidencias parciales, autoevaluar avances y acordar ajustes concretos antes "
                "de la fase de validacion."
            )
        else:
            inicio_instruction = (
                "Socializar avances entre equipos, contrastar resultados con los criterios definidos "
                "y priorizar mejoras criticas previas al cierre."
            )
            desarrollo_instruction = (
                "Realizar validacion entre pares con coevaluacion estructurada, integrar observaciones y "
                f"preparar version prefinal del {focus['artifact']}."
            )
            cierre_instruction = (
                "Registrar acuerdos finales de mejora, dejar trazabilidad de cambios y organizar la "
                "entrega para la sesion de cierre."
            )

    return {
        "sesion": session_number,
        "semana": week_number,
        "hito": "cierre" if session_offset == total_sessions - 1 else "avance",
        "tipo_actividad": tipo_actividad,
        "duracion_min": session_total_min,
        "objetivo_especifico": objective_text,
        "resumen_datos_esenciales": _build_session_summary(
            lesson_title=lesson_title,
            activity_text=activity_text,
            foundations=foundations,
        ),
        "inicio": {
            "duracion_min": inicio_min,
            "instrucciones": inicio_instruction,
        },
        "desarrollo": {
            "duracion_min": desarrollo_min,
            "instrucciones": desarrollo_instruction,
        },
        "cierre": {
            "duracion_min": cierre_min,
            "instrucciones": cierre_instruction,
        },
        "inicio_actividades": _build_block_activities(
            block="inicio",
            minutes=inicio_min,
            lesson_title=lesson_title,
            activity_text=activity_text,
            objective_text=objective_text,
        ),
        "desarrollo_actividades": _build_block_activities(
            block="desarrollo",
            minutes=desarrollo_min,
            lesson_title=lesson_title,
            activity_text=activity_text,
            objective_text=objective_text,
        ),
        "cierre_actividades": _build_block_activities(
            block="cierre",
            minutes=cierre_min,
            lesson_title=lesson_title,
            activity_text=activity_text,
            objective_text=objective_text,
        ),
    }


def _assign_lessons_to_sessions(num_lessons: int, total_sessions: int) -> list[int]:
    """Reparte de forma equilibrada los subtemas del ADA a lo largo de sus sesiones,
    devolviendo para cada sesion el indice del subtema que aborda."""
    if num_lessons <= 0:
        return [0] * max(1, total_sessions)
    return [min(num_lessons - 1, (offset * num_lessons) // max(1, total_sessions)) for offset in range(total_sessions)]


def _build_ada_payload(
    ada_meta: dict[str, Any],
    lessons: list[tuple[str, str, str]],
    tipo_actividad: str,
) -> dict[str, Any]:
    if not lessons:
        lessons = [("", "", "")]

    primary_title, primary_text, primary_activity = lessons[0]
    multi = len(lessons) > 1

    if multi:
        contenidos: list[str] = []
        for lesson_title, lesson_text, _activity in lessons:
            paragraphs = [part.strip() for part in lesson_text.split("\n") if part.strip()]
            snippet = paragraphs[0] if paragraphs else lesson_text
            contenidos.append(f"{lesson_title}: {snippet}".strip(": ").strip())
    else:
        paragraphs = [part.strip() for part in primary_text.split("\n") if part.strip()]
        contenidos = paragraphs[:3] if paragraphs else [primary_text]

    instrumento = "Lista de cotejo" if tipo_actividad == "proceso" else "Rubrica analitica"
    total_sessions = max(1, ada_meta["duracion_sesiones"])

    fundamentos: list[str] = []
    for lesson_title, lesson_text, lesson_activity in lessons:
        paras = [part.strip() for part in lesson_text.split("\n") if part.strip()][:3]
        fundamentos.extend(
            _infer_thematic_foundations(
                lesson_title=lesson_title,
                lesson_activity=lesson_activity,
                contenidos=paras,
            )
        )
    fundamentos = list(dict.fromkeys(fundamentos))

    combined_activity = " ".join(
        dict.fromkeys(act.strip() for _t, _x, act in lessons if act and act.strip())
    ) or primary_activity

    acciones_base = _split_learning_actions(combined_activity)
    objetivo = _build_strategic_objective(
        foundations=fundamentos,
        tipo_actividad=tipo_actividad,
    )
    resultados_aprendizaje = _build_learning_outcomes(acciones_base)

    session_numbers = list(range(ada_meta["sesion_inicio"], ada_meta["sesion_fin"] + 1))
    total_sessions = max(1, len(session_numbers))
    lesson_for_session = _assign_lessons_to_sessions(len(lessons), total_sessions)

    sesiones = []
    for offset, session_number in enumerate(session_numbers):
        s_title, _s_text, s_activity = lessons[lesson_for_session[offset]]
        sesion = _build_session_instruction(
            lesson_title=s_title,
            activity_text=s_activity,
            foundations=fundamentos,
            session_number=session_number,
            session_offset=offset,
            total_sessions=total_sessions,
            tipo_actividad=tipo_actividad,
        )
        sesion["tema"] = s_title
        sesiones.append(sesion)

    activity_number = _extract_activity_number(str(ada_meta.get("nombre") or ""))
    duration_label = _build_duration_label(session_numbers)

    return {
        "nombre": ada_meta["nombre"],
        "actividad_numero": activity_number,
        "titulo_actividad": primary_title,
        "duracion": duration_label,
        "puntaje": 10,
        "tipo_actividad": tipo_actividad,
        "objetivo": objetivo,
        "resultado_aprendizaje": combined_activity,
        "resultados_aprendizaje": resultados_aprendizaje,
        "descripcion_actividad": (
            "Desarrollo progresivo de competencias mediante actividades de inicio, desarrollo y cierre "
            "en sesiones de 90 y 45 minutos, orientadas a la elaboracion del entregable del ADA."
        ),
        "contenidos_a_desarrollar": contenidos,
        "fundamentos_tematicos_requeridos": fundamentos,
        "estrategias_ensenanza_aprendizaje": [
            "Aprendizaje basado en proyectos",
            "Aprendizaje colaborativo",
            "Investigacion documental",
            "Analisis de casos",
            "Discusion guiada",
            "Elaboracion de organizadores graficos",
            "Uso de herramientas digitales para la creacion de contenidos",
        ],
        "evidencias_aprendizaje": _build_evidencias_aprendizaje(
            resultados_aprendizaje=resultados_aprendizaje,
            acciones_base=acciones_base,
            tipo_actividad=tipo_actividad,
            instrumento=instrumento,
        ),
        "instrumento_evaluacion": instrumento,
        "sesion_inicio": ada_meta["sesion_inicio"],
        "sesion_fin": ada_meta["sesion_fin"],
        "duracion_sesiones": ada_meta["duracion_sesiones"],
        "sesiones_desarrolladas": sesiones,
    }


def _partition_lessons(
    lessons: list[tuple[str, str, str]],
    num_slots: int,
) -> list[list[tuple[str, str, str]]]:
    """Reparte de forma contigua y equilibrada todas las lecciones (subtemas) entre
    los `num_slots` ADAs disponibles, garantizando que cada subtema quede asignado."""
    n = len(lessons)
    if num_slots <= 0 or n == 0:
        return []

    base, remainder = divmod(n, num_slots)
    groups: list[list[tuple[str, str, str]]] = []
    cursor = 0
    for slot in range(num_slots):
        size = base + (1 if slot < remainder else 0)
        chunk = lessons[cursor:cursor + size]
        if not chunk:
            # Hay mas ADAs que subtemas: reutiliza ciclicamente para no dejar ADAs vacias.
            chunk = [lessons[slot % n]]
        else:
            cursor += size
        groups.append(chunk)
    return groups


def build_ada_course_structure(course: CourseStructure, operational_plan: dict[str, Any]) -> dict[str, Any]:
    flat_lessons: list[tuple[str, str, str]] = []
    for module in course.modulos:
        for lesson in module.lecciones:
            flat_lessons.append((lesson.titulo, lesson.texto, lesson.actividad))

    if not flat_lessons:
        return {"periodos": []}

    periodizacion = list(operational_plan.get("periodizacion", []))

    # Conteo de "slots" (ADAs de proceso + fase integradora por periodo) en el
    # mismo orden en que se consumiran, para repartir TODOS los subtemas entre ellos.
    total_slots = 0
    for period in periodizacion:
        total_slots += len(period.get("adas", []))
        if isinstance(period.get("fase_proyecto_integrador"), dict):
            total_slots += 1

    lesson_groups = _partition_lessons(flat_lessons, total_slots)
    group_iter = iter(lesson_groups)

    def _next_group() -> list[tuple[str, str, str]]:
        try:
            return next(group_iter)
        except StopIteration:
            return [flat_lessons[0]]

    periodos_payload: list[dict[str, Any]] = []

    for period in periodizacion:
        adas_payload: list[dict[str, Any]] = []

        for ada_meta in period.get("adas", []):
            adas_payload.append(
                _build_ada_payload(
                    ada_meta=ada_meta,
                    lessons=_next_group(),
                    tipo_actividad="proceso",
                )
            )

        fase_meta = period.get("fase_proyecto_integrador")
        fase_payload = None
        if isinstance(fase_meta, dict):
            phase_name = str(fase_meta.get("nombre") or f"ADA integradora periodo {period.get('periodo', '')}").strip()
            phase_ada_meta = {
                "nombre": phase_name,
                "sesion_inicio": int(fase_meta.get("sesion_inicio", 0) or 0),
                "sesion_fin": int(fase_meta.get("sesion_fin", 0) or 0),
                "duracion_sesiones": int(fase_meta.get("duracion_sesiones", 1) or 1),
            }

            fase_payload = _build_ada_payload(
                ada_meta=phase_ada_meta,
                lessons=_next_group(),
                tipo_actividad="producto",
            )

        periodo_payload: dict[str, Any] = {
            "periodo": period.get("periodo"),
            "semanas": period.get("semanas"),
            "adas": adas_payload,
        }
        if isinstance(fase_meta, dict):
            periodo_payload["fase_proyecto_integrador"] = {
                **fase_meta,
                "ada_integradora_producto": fase_payload,
            }
        else:
            periodo_payload["fase_proyecto_integrador"] = None

        periodos_payload.append(periodo_payload)

    return {
        "periodos": periodos_payload,
        "criterios_generales": {
            "duracion_sesion_min": list(SESSION_MINUTES_PATTERN),
            "estructura_sesion": ["inicio", "desarrollo", "cierre"],
            "frecuencia_semanal": 2,
        },
    }
