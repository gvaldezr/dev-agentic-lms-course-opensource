# Pipeline de generación de cursos

Documento técnico del flujo que transforma un programa de asignatura (DOCX o PDF)
en un curso estructurado para Moodle: un archivo **JSON** con la planeación
completa y un archivo **XML** importable al banco de preguntas de Moodle.

El orquestador es la clase `CoursePipeline` en
[src/course_pipeline/pipeline.py](src/course_pipeline/pipeline.py), método `run()`.
Se ejecuta desde la CLI [scripts/run_pipeline.py](scripts/run_pipeline.py).

---

## Ejecución

```bash
python scripts/run_pipeline.py \
  --pdf "input/Comunidades virtuales_Asig3.pdf" \
  --course-name "Comunidades virtuales" \
  --skip-images
```

Argumentos relevantes:

| Argumento | Efecto |
|---|---|
| `--input-file` / `--docx` / `--pdf` | Ruta del programa de asignatura de entrada (`.docx` o `.pdf`). |
| `--course-name` | Nombre del curso (obligatorio); se usa para nombrar las salidas. |
| `--skip-images` | Omite la etapa de generación de imágenes. |
| `--skip-readings` | Omite la generación de lecturas (OpenAlex + LLM). |
| `--skip-presentations` | Omite la generación de presentaciones HTML5 por ADA. |
| `--skip-questions` | Omite la generación del banco de preguntas y del quiz de 20 ítems. |
| `--skip-checklists` | Omite la generación de listas de cotejo por entregable ADA. |

La configuración se carga desde variables de entorno (`.env`) mediante
[src/course_pipeline/config.py](src/course_pipeline/config.py): proveedor y
modelo del LLM, credenciales, directorio de salida (`OUTPUT_DIR`, por defecto
`./data/output`) y parámetros de imagen.

---

## Visión general del flujo

```
Entrada DOCX/PDF
      │
      ▼
1. Parseo del documento          docx_parser.py
      │   (ParsedCourseInput: objetivos, competencias, syllabus, metadatos)
      ▼
2. Generación instruccional      instructional_generator.py  (LLM)
      │   (CourseStructure: módulos → lecciones)
      ▼
3. Generación de imágenes        image_client.py             (opcional)
      │   (una imagen por lección)
      ▼
4. Enriquecimiento OpenAlex      openalex_enrichment.py
      │   (temas + fuentes académicas)
      ▼
5. Plan operativo                planning.py
      │   (14 semanas, 5 ADAs de proceso, sesiones 90/45)
      ▼
6. Estructura ADA                ada_structure.py
      │   (periodos → ADAs → sesiones; entregables, evidencias)
      ▼
7. Objetivos por sesión          session_objectives.py       (LLM)
      ▼
8. Lecturas por eje temático     reading_generator.py        (OpenAlex + LLM, opcional)
      ▼
9. Presentaciones por ADA        presentation_generator.py   (LLM, opcional)
      ▼
10. Banco de preguntas + quiz    question_bank_generator.py  (LLM, opcional)
      ▼
11. Escritura del JSON           data/output/<slug>_<timestamp>.json
      ▼
12. Exportación Moodle XML       moodle_xml_exporter.py
          data/output/moodle_course_<slug>_<timestamp>.xml
          data/output/moodle_quiz_<slug>_<timestamp>.xml
```

---

## Etapas del pipeline

### 1. Parseo del documento de entrada
**Módulo:** [src/course_pipeline/docx_parser.py](src/course_pipeline/docx_parser.py)

Lee el archivo `.docx` (con `python-docx`) o `.pdf` (con `pypdf`) y extrae las
secciones del programa por encabezados normalizados (sin acentos, en minúsculas):

- **Objetivos / resultados de aprendizaje**
- **Competencias** (perfil de egreso) y **competencia de la asignatura**
- **Syllabus / temario / unidades / contenidos**

Detecta también las **unidades oficiales** (para respetar su título y orden) y
extrae metadatos del programa con
[program_metadata.py](src/course_pipeline/program_metadata.py).

**Salida:** un objeto `ParsedCourseInput` con objetivos, competencias, syllabus,
contexto de planeación y metadatos. Si el documento no se puede leer, lanza
`DocxParsingError` y el pipeline se detiene.

### 2. Generación de la estructura instruccional (LLM)
**Módulo:** [src/course_pipeline/instructional_generator.py](src/course_pipeline/instructional_generator.py)

Envía al LLM las secciones extraídas con un *system prompt* de **Diseñador
Instruccional Senior** (metodología DUA). El modelo transforma objetivos,
competencias y syllabus en una estructura modular. Si recibe unidades oficiales,
crea **exactamente un módulo por unidad**, respetando título y orden.

Por cada lección genera: `titulo`, `objetivo` (verbo observable), `texto`
didáctico, `actividad` de evaluación y `prompt_imagen` en inglés (estilo ícono
minimalista, sin texto).

**Salida:** un objeto `CourseStructure` (`curso` + `modulos[].lecciones[]`).
Si la respuesta no es válida, lanza `InstructionalGenerationError`.

### 3. Generación de imágenes (opcional)
**Módulo:** [src/course_pipeline/image_client.py](src/course_pipeline/image_client.py)

Por cada lección de cada módulo genera una imagen a partir de `prompt_imagen` y
guarda la ruta relativa en `lesson.image_path`. Se omite con `--skip-images`.

Es tolerante a fallos: si una imagen falla, registra una **advertencia** y el
pipeline continúa sin esa imagen. Las imágenes se guardan en
`data/output/assets/images/`.

### 4. Enriquecimiento académico con OpenAlex
**Módulo:** [src/course_pipeline/openalex_enrichment.py](src/course_pipeline/openalex_enrichment.py)

A partir del texto de entrada deriva los **temas clave** (eliminando *stopwords*
en español) y construye una carga (*payload*) con fuentes académicas de OpenAlex.
Este resultado se fusiona en el *payload* de salida.

### 5. Construcción del plan operativo
**Módulo:** [src/course_pipeline/planning.py](src/course_pipeline/planning.py)

Genera la malla temporal del curso de forma determinista:
**14 semanas, 5 ADAs de proceso en total, sin fase integradora, 2 sesiones por
semana, con patrón de minutos por sesión `[90, 45]`**. Calcula totales de
sesiones, minutos y horas, y reparte semanas y sesiones en los ADAs.

**Salida:** `planeacion_operativa` en el *payload*.

### 6. Construcción de la estructura ADA
**Módulo:** [src/course_pipeline/ada_structure.py](src/course_pipeline/ada_structure.py)

Combina la `CourseStructure` (módulos/lecciones) con el plan operativo para
producir el modelo **centrado en ADAs** (Actividades de Aprendizaje), que es la
estructura canónica que consumen el SPA y el exportador XML:

```
estructura_curso_adas
└── periodos[]
    ├── adas[]                         (tipo_actividad: proceso)
    │   ├── objetivo, resultado_aprendizaje
    │   ├── contenidos_a_desarrollar, fundamentos_tematicos_requeridos
    │   ├── evidencias_aprendizaje[], instrumento_evaluacion
    │   └── sesiones_desarrolladas[]   (tema, inicio, desarrollo, cierre…)
    └── fase_proyecto_integrador
        └── ada_integradora_producto   (tipo_actividad: producto)
```

Cada ADA deriva sus **evidencias de aprendizaje** y **fundamentos temáticos** del
título y la actividad de la lección correspondiente.

### 7. Objetivos de aprendizaje por sesión (LLM)
**Módulo:** [src/course_pipeline/session_objectives.py](src/course_pipeline/session_objectives.py)

Recorre todas las sesiones de la estructura ADA y pide al LLM **un objetivo por
sesión** (observable, medible, en una sola oración que inicia con verbo en
infinitivo). Los adjunta en cada sesión.

Tolerante a fallos: si el LLM falla, genera objetivos **deterministas** a partir
del tema del ADA y la etapa de la sesión, de modo que ninguna sesión queda sin
objetivo. Las incidencias se acumulan como advertencias.

### 8. Lecturas de fundamentación por eje temático (opcional, LLM)
**Módulo:** [src/course_pipeline/reading_generator.py](src/course_pipeline/reading_generator.py)

Por cada ADA, y por cada **eje temático / fundamento**, consulta OpenAlex
(fuentes de los últimos 5 años, ~5 por tema), reconstruye los *abstracts* y pide
al LLM una **lectura didáctica** dirigida al perfil estudiantil, con referencias
en formato **APA 7.ª edición**.

Cada lectura se adjunta en `lecturas_fundamentacion[]` del ADA (campos:
`fundamento`, `lectura`, `referencias_apa`, `fuentes_openalex`, etc.).
Se omite con `--skip-readings`.

### 9. Presentaciones HTML5 por ADA (opcional, LLM)
**Módulo:** [src/course_pipeline/presentation_generator.py](src/course_pipeline/presentation_generator.py)

Se ejecuta **después** de las lecturas (las usa como insumo). Por cada ADA pide
al LLM un **deck de pitch** (gancho, idea, ejemplo, actividad, cierre) orientado
a estudiantes de 5.º semestre de preparatoria de la UADY, aplicando storytelling
y copywriting. Renderiza un documento **HTML5 autocontenido e incrustable en
Moodle** (CSS y JS *inline*, navegación con flechas y barra de progreso).

Cada deck se guarda en `ada["presentacion"]`:
`{ titulo, subtitulo, num_diapositivas, slides[], html }`.
Se omite con `--skip-presentations`. Tolerante a fallos: ante un error, guarda
una presentación vacía con un `aviso` y continúa.

### 10. Banco de preguntas y quiz (opcional, LLM)
**Módulo:** [src/course_pipeline/question_bank_generator.py](src/course_pipeline/question_bank_generator.py)

Si no se usa `--skip-readings` ni `--skip-questions`, el pipeline construye un
**banco de reactivos de aplicación** a partir de las lecturas generadas.

- Reactivos de opción múltiple con 4 opciones.
- Distractores de alto nivel.
- Orden aleatorio de respuestas.
- Retroalimentación general y justificación de la correcta.

Luego selecciona un **quiz de 20 ítems** estratificado por ADA.

### 11. Escritura del JSON de salida
El *payload* completo se serializa en:

```
data/output/<slug>_<YYYYMMDD_HHMMSS>.json
```

donde `<slug>` se deriva del `--course-name` (minúsculas, sin acentos,
separadores `_`). Contiene: `course_structure` (módulos/lecciones),
`planeacion_operativa`, `estructura_curso_adas`, `banco_preguntas`, `quiz`,
datos de OpenAlex y, si aplica, `programa_asignatura`.

### 12. Exportación al XML de Moodle
**Módulo:** [src/course_pipeline/moodle_xml_exporter.py](src/course_pipeline/moodle_xml_exporter.py)

Genera un banco de preguntas Moodle (`<quiz>`) **centrado en ADAs**. Por cada ADA:

1. Una **categoría** con el nombre del ADA.
2. Una **página de contenido** (`description`) por cada sesión.
3. Una **página con la presentación** HTML5 incrustada (`iframe srcdoc`).
4. Una **página de lectura** (`description`) por cada eje temático.
5. **Un único entregable** evaluable (`essay`) por ADA.

La salida se escribe en:

```
data/output/moodle_course_<slug>_<YYYYMMDD_HHMMSS>.xml
data/output/moodle_quiz_<slug>_<YYYYMMDD_HHMMSS>.xml
```

El JSON y ambos XML comparten el mismo `slug` y `timestamp`, de modo que cada
ejecución queda emparejada y no sobrescribe las anteriores.

---

## Salidas y visualización

| Salida | Ruta | Uso |
|---|---|---|
| JSON del curso | `data/output/<slug>_<timestamp>.json` | Fuente de datos del SPA y del XML. |
| XML de Moodle (curso + banco) | `data/output/moodle_course_<slug>_<timestamp>.xml` | Importable al banco de preguntas de Moodle. |
| XML de Moodle (quiz 20 ítems) | `data/output/moodle_quiz_<slug>_<timestamp>.xml` | Importable al banco de preguntas de Moodle. |
| Imágenes | `data/output/assets/images/` | Ilustraciones por lección (si no se omiten). |

El SPA en [spa/index.html](spa/index.html) lee el JSON y ofrece tres vistas:
**Planeación didáctica**, **Construcción Moodle** y
**Banco de preguntas / Quiz** (interactiva, con calificación y retroalimentación).

Para servir el SPA localmente:

```bash
python -m http.server 8000
# abrir http://localhost:8000/spa/
```

---

## Manejo de errores y advertencias

- **Errores que detienen el pipeline:** fallo de parseo (`DocxParsingError`) y
  fallo de la generación instruccional (`InstructionalGenerationError`).
- **Etapas tolerantes a fallos** (acumulan advertencias y continúan): imágenes,
  objetivos por sesión, lecturas y presentaciones.
- Al finalizar, la CLI reporta la ruta del JSON, la ruta del XML y la lista de
  advertencias (si las hubo).
