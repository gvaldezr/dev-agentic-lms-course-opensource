# Moodle Course Package Automation (Python)

Pipeline para transformar un programa de asignatura (`.docx` o `.pdf`) en:

- Un JSON con planeacion operativa, estructura ADA, lecturas y presentaciones.
- Un XML principal de Moodle con estructura por ADA y banco de preguntas.
- Un XML adicional con un quiz de 20 items derivado del banco.

## Estado actual del proyecto

- Planeacion operativa: 15 semanas, 2 sesiones por semana, patron de duracion `[90, 45]` minutos.
- Estructura didactica: 3 periodos, ADAs de proceso y fase integradora de producto.
- Lecturas por eje tematico (OpenAlex + LLM) y presentaciones HTML5 por ADA.
- Banco de preguntas de aplicacion (opcion multiple con 4 opciones y distractores de alto nivel).
- Quiz estratificado de 20 items a partir del banco.
- SPA con 3 vistas: `Planeacion didactica`, `Construccion Moodle`, `Banco de preguntas / Quiz`.

## Estructura principal

- `src/course_pipeline/config.py`: configuracion y variables de entorno.
- `src/course_pipeline/schemas.py`: modelos y validacion.
- `src/course_pipeline/docx_parser.py`: extraccion desde DOCX/PDF (`pypdf` para PDF).
- `src/course_pipeline/instructional_generator.py`: estructura modular via LLM.
- `src/course_pipeline/planning.py`: reglas operativas (15 semanas, sesiones 90/45).
- `src/course_pipeline/ada_structure.py`: construccion de estructura centrada en ADAs.
- `src/course_pipeline/session_objectives.py`: objetivos de aprendizaje por sesion.
- `src/course_pipeline/reading_generator.py`: lecturas de fundamentacion por eje.
- `src/course_pipeline/presentation_generator.py`: presentaciones HTML5 por ADA.
- `src/course_pipeline/question_bank_generator.py`: banco de reactivos y quiz.
- `src/course_pipeline/manual_build_pack.py`: paquete de apoyo para montaje manual en Moodle.
- `src/course_pipeline/moodle_xml_exporter.py`: exportacion Moodle XML (curso + quiz).
- `src/course_pipeline/pipeline.py`: orquestador end-to-end.
- `scripts/run_pipeline.py`: CLI.
- `spa/index.html`: visualizador local del JSON.

## Uso rapido

1. Crear entorno e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables:

```bash
cp .env.example .env
# Ajustar LLM_PROVIDER, LLM_MODEL, LLM_API_KEY y demas parametros
```

3. Ejecutar pipeline (sin imagenes, recomendado para pruebas rapidas):

```bash
python scripts/run_pipeline.py \
	--pdf "input/Comunidades virtuales_Asig3.pdf" \
	--course-name "Comunidades virtuales" \
	--skip-images
```

## Argumentos CLI relevantes

- `--input-file` / `--docx` / `--pdf`: ruta del documento de entrada.
- `--course-name`: nombre del curso para nombrar salidas.
- `--skip-images`: omite generacion de imagenes.
- `--skip-readings`: omite lecturas de fundamentacion.
- `--skip-presentations`: omite presentaciones HTML.
- `--skip-questions`: omite banco de preguntas y quiz.

## Salidas

Por ejecucion se generan archivos con `<slug>_<timestamp>`:

- `data/output/<slug>_<timestamp>.json`
- `data/output/moodle_course_<slug>_<timestamp>.xml`
- `data/output/moodle_quiz_<slug>_<timestamp>.xml`
- `data/output/manual_build_pack_<slug>_<timestamp>/`

Adicionalmente, si no se omiten imagenes:

- `data/output/assets/images/*`

El JSON incluye, entre otros, estos bloques:

- `course_structure`
- `planeacion_operativa`
- `estructura_curso_adas`
- `banco_preguntas`
- `quiz`

El `manual_build_pack` incluye, entre otros:

- `outline_curso.json` (mapa de secciones/ADAs para montar en Moodle)
- `checklist_publicacion.md` (pasos operativos)
- `adas/*/contenido.html` (contenido listo para recurso Pagina/Libro)
- `adas/*/entregable.txt` (base para actividad Tarea)

## Visualizacion SPA

Levantar servidor local:

```bash
python -m http.server 8000
```

Abrir:

- `http://localhost:8000/spa/`

La vista `Banco de preguntas / Quiz` permite:

- Responder el quiz interactivo y calificar (`Puntaje X / 20`).
- Ver retroalimentacion y justificacion por reactivo.
- Explorar el banco completo y revelar respuesta correcta por item.

## Importacion en Moodle

Consulta la guia paso a paso en `MOODLE_IMPORT.md`.
