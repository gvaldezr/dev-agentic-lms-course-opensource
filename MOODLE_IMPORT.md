# Instrucciones para importar el curso en Moodle

Esta guia explica como usar los archivos XML generados por el pipeline:

- `moodle_course_<slug>_<timestamp>.xml`
- `moodle_quiz_<slug>_<timestamp>.xml`
- `manual_build_pack_<slug>_<timestamp>/`

## 1) Generar los archivos

Ejecuta el pipeline (ejemplo sin imagenes):

```bash
python scripts/run_pipeline.py \
  --pdf "input/Comunidades virtuales_Asig3.pdf" \
  --course-name "Comunidades virtuales" \
  --skip-images
```

Al finalizar, revisa `data/output/` para identificar el timestamp mas reciente.

Tambien se genera una carpeta de apoyo para montaje manual:

- `manual_build_pack_<slug>_<timestamp>/`

Adicionalmente, el pipeline publica las presentaciones en `docs/presentaciones/<slug>/<timestamp>/...`
para que GitHub Pages las sirva como URL publica y puedan embederse via `iframe` en Moodle.

Requisito: habilita GitHub Pages en el repositorio (Source: `GitHub Actions`).

## 2) Importar al banco de preguntas de Moodle

1. Entra al curso en Moodle con un rol que pueda administrar preguntas.
2. Ve a `Mas` -> `Banco de preguntas` -> `Importar`.
3. En `Formato de archivo`, selecciona `Formato Moodle XML`.
4. Carga `moodle_course_<slug>_<timestamp>.xml`.
5. Importa en la categoria deseada (o una subcategoria especifica del curso).
6. Repite el proceso con `moodle_quiz_<slug>_<timestamp>.xml`.

Resultado esperado:

- Se crean categorias por ADA y una categoria de banco de preguntas.
- Se importan reactivos de opcion multiple (con respuestas mezcladas).
- Se importa una categoria con los 20 items del quiz.

## 2.1) Que contiene `moodle_course_<slug>_<timestamp>.xml`

Este archivo NO es una copia de seguridad completa del curso (`.mbz`).
Es un XML de banco de preguntas con:

- Reactivos de opcion multiple (banco).
- Preguntas tipo `description` para contenido (sesiones, lecturas, presentaciones).
- Preguntas tipo `essay` para entregables.

Por eso, al importarlo en Moodle, los elementos quedan en el banco de preguntas,
no como actividades/recursos ya creados en la pagina principal del curso.

## 3) Crear el cuestionario (actividad) en Moodle

Importar XML de preguntas NO crea automaticamente una actividad de cuestionario.
Debes crearla manualmente:

1. Activa edicion en el curso.
2. Agrega una actividad `Cuestionario`.
3. Configura nombre, intentos, calificacion y fechas.
4. Entra al cuestionario y selecciona `Editar cuestionario`.
5. Agrega preguntas desde el banco:
   - Usa la categoria del quiz de 20 items para un examen corto, o
   - Usa la categoria del banco para seleccionar reactivos personalizados.

## 4) Como incorporar los demas elementos del curso (no quiz)

Actualmente hay dos caminos:

### Opcion A (recomendada hoy): montaje manual asistido

1. Crea la estructura del curso en Moodle (secciones por periodo/ADA).
2. Usa `http://localhost:8000/spa/` con la vista `Construccion Moodle` como referencia.
3. Para cada ADA, crea en Moodle los recursos/actividades correspondientes:
  - `Pagina` o `Libro` para sesiones y lecturas.
  - `Tarea` para el entregable.
  - `Pagina` con iframe/HTML para la presentacion (si tu politica Moodle lo permite).
4. Usa las preguntas `description` y `essay` importadas como fuente de texto,
  copiando contenido al recurso/actividad equivalente.

### Uso del `manual_build_pack` (sin API)

Dentro de `manual_build_pack_<slug>_<timestamp>/`:

- `outline_curso.json`: estructura de periodos/ADAs y rutas de archivos.
- `checklist_publicacion.md`: lista operativa para publicar sin omisiones.
- `adas/<n>_<ada_slug>/contenido.html`: contenido listo para recurso `Pagina` o `Libro`.
- `adas/<n>_<ada_slug>/entregable.txt`: texto base para la actividad `Tarea`.

Cuando existe presentacion para una ADA, `contenido.html` incluye:

- `iframe` apuntando a la URL publica de GitHub Pages.
- Enlace alterno para abrir la presentacion en nueva pestana.

Flujo recomendado:

1. Importa los XML de preguntas (banco + quiz).
2. Recorre `checklist_publicacion.md`.
3. Por cada carpeta de ADA, crea recursos en Moodle usando `contenido.html`.
4. Crea la `Tarea` correspondiente con base en `entregable.txt`.
5. Valida visibilidad, orden y fechas antes de abrir a estudiantes.

### Opcion B (automatizacion completa): backup Moodle `.mbz`

Para que Moodle cree automaticamente recursos y actividades del curso completo,
se necesita generar un paquete de restauracion `.mbz` (no solo XML de preguntas).

Estado actual del proyecto:

- El pipeline no genera `.mbz` por ahora.
- Solo genera XML de banco de preguntas (`moodle_course_...xml` y `moodle_quiz_...xml`).

## 5) Validacion recomendada

1. Previsualiza 2 o 3 preguntas para validar texto y opciones.
2. Verifica que haya una sola respuesta correcta por reactivo.
3. Confirma que los comentarios (retroalimentacion y justificacion) se muestren.
4. Realiza un intento de prueba con rol de estudiante.
5. Revisa que las actividades manuales (Pagina/Libro/Tarea) correspondan a cada ADA.

## 6) Problemas comunes

- `No se pudo importar el archivo`: revisa que el formato sea `Moodle XML` y que el archivo no este truncado.
- `No aparecen preguntas`: confirma que importaste en la categoria correcta del curso.
- `No se crea el cuestionario automaticamente`: comportamiento esperado; el XML importa preguntas, no actividades completas.
- `No aparece el curso completo con secciones y actividades`: comportamiento esperado; para eso se requiere `.mbz`.

## 7) Recomendacion de operacion

Para mantener trazabilidad, usa siempre el mismo par de archivos con igual timestamp:

- `moodle_course_<slug>_<timestamp>.xml`
- `moodle_quiz_<slug>_<timestamp>.xml`

Asi evitas mezclar bancos de preguntas de ejecuciones distintas.

## 8) Roadmap para importacion de curso completo

Si se quiere restaurar automaticamente TODO el curso (secciones, recursos,
actividades y evaluacion), se recomienda avanzar por fases.

### Fase 1: Modelo de publicacion Moodle (MVP tecnico)

Objetivo: construir una representacion intermedia estable antes de generar
formatos finales.

Entregables:

- Esquema interno `moodle_publish_payload` (JSON) con:
  - curso (nombre corto/largo, formato, resumen),
  - secciones por periodo/ADA,
  - recursos (Pagina/Libro/URL/Archivo),
  - actividades (Tarea/Cuestionario),
  - categorias de preguntas y relaciones con quiz.
- Validaciones de consistencia (ids, orden, referencias cruzadas, campos minimos).

### Fase 2A: Provision automatica por API (si existe acceso)

Objetivo: crear el curso completo consumiendo Web Services de Moodle, sin
generar `.mbz` al inicio.

Entregables:

- Cliente `moodle_api_client.py` (token + endpoint REST).
- Comandos de provision:
  - crear curso,
  - crear secciones,
  - crear recursos por seccion,
  - crear actividades (tarea/quiz),
  - importar banco de preguntas existente,
  - poblar quiz con preguntas por categoria.
- Modo idempotente (reintentos seguros y actualizacion sin duplicados).

Ventajas:

- Menor complejidad inicial que `.mbz`.
- Mejor trazabilidad y logs por paso.
- Facil rollback en entorno de pruebas.

### Fase 2B: Provision sin API (camino para tu escenario)

Objetivo: acelerar la carga del curso completo sin depender de Web Services.

Entregables:

- Plantilla operativa de montaje en Moodle por ADA (secciones, recursos y actividades).
- Paquete de apoyo para edicion manual:
  - textos listos para `Pagina/Libro`,
  - instrucciones de `Tarea`,
  - matriz de mapeo `ADA -> recurso/actividad`.
- Checklist de publicacion para evitar omisiones.

Implementacion sugerida en este repositorio:

- Exportar desde el JSON un `manual_build_pack` en `data/output/` con:
  - `outline_curso.json` (estructura de secciones),
  - `adas/<ada_slug>/contenido.html` (lecturas/sesiones/presentacion),
  - `adas/<ada_slug>/entregable.txt`.

Esto no crea actividades automaticamente, pero reduce mucho el trabajo manual y
estandariza la carga del curso.

### Fase 3: Exportador `.mbz` (restauracion nativa completa)

Objetivo: empaquetar todo para restauracion nativa de Moodle en una sola accion.

Entregables:

- Generador de estructura de backup compatible con la version objetivo de Moodle.
- Serializacion de metadata de curso, secciones, modulos, contextos y archivos.
- Empaquetado final en `.mbz` con validacion previa de integridad.

Consideraciones:

- Alta sensibilidad a version de Moodle y plugins instalados.
- Mayor esfuerzo de mantenimiento que el camino API.

### Fase 4: QA funcional y operativa

Objetivo: asegurar que la restauracion/provision sea estable en ambientes reales.

Checklist minimo:

- Curso visible con secciones y orden correcto.
- Recursos renderizados (texto, lecturas, presentaciones).
- Tareas con instrucciones y fechas coherentes.
- Quiz con banco, barajado y calificacion correctos.
- Libro de calificaciones y ponderaciones esperadas.
- Prueba con rol docente y rol estudiante.

## 9) Estimacion de esfuerzo (orientativa)

- Fase 1: 2 a 4 dias.
- Fase 2A (con API): 1 a 2 semanas.
- Fase 2B (sin API): 3 a 6 dias.
- Fase 3: 2 a 4 semanas.
- Fase 4: 3 a 5 dias (por entorno).

Duracion total aproximada:

- Camino sin API (Fase 1 + Fase 2B + Fase 4): 2 a 3 semanas.
- Camino API primero (Fase 1 + Fase 2A + Fase 4): 2 a 3 semanas.
- Incluyendo exportador `.mbz`: 4 a 7 semanas.

## 10) Siguiente paso recomendado

Si no tienes acceso al API, implementar primero la Fase 1 + Fase 2B, manteniendo
los XML actuales como respaldo. Con eso se logra una importacion operativa del
curso completo (asistida) antes de invertir en la complejidad de `.mbz`.

Si en el futuro habilitan API, se puede migrar a Fase 2A sin rehacer el modelo
de datos de Fase 1.
