# SPA · Planeación Didáctica (UADY)

Aplicación de una sola página (HTML/CSS/JS, sin build ni dependencias) que carga un
archivo `course_structure.json` y lo renderiza con el formato institucional de la
plantilla **"Planeación Didáctica – Curso Regular"** de la Universidad Autónoma de
Yucatán.

## Cómo usarla

Para que la SPA **liste automáticamente** los `.json` disponibles en `data/output/`,
sírvela con un servidor estático desde la raíz del repo:

```bash
python -m http.server 8000
```

Luego abre: <http://localhost:8000/spa/>

- El selector **Archivo** se llena con los `.json` encontrados en `data/output/`.
  Si solo hay uno, se carga automáticamente.
- También puedes usar **Seleccionar archivo** para subir cualquier `.json` a mano
  (funciona incluso abriendo el HTML directamente con `file://`).
- **Exportar PDF** abre el diálogo de impresión del navegador (Guardar como PDF),
  con estilos optimizados para impresión.

## Mapeo JSON → plantilla

| Sección de la plantilla | Origen en el JSON |
|---|---|
| 1. Datos generales | `planeacion_operativa.reglas` (horas, sesiones, semanas). Modalidad, créditos, HCP/HEI/HPF, semestre y requisitos son **editables**. |
| 2. Intencionalidad | **Editable** (no está en el JSON). Se muestran `conceptos_clave_openalex` como apoyo. |
| 3. Competencia de la asignatura | `competencia_curso` |
| 4. Acreditación | ADAs (`estructura_curso_adas.periodos[].adas[]`) + producto integrador. Fechas y puntajes son **editables**. |
| 5. Secuencia didáctica y guion | Por unidad: ADAs (objetivo, contenidos, estrategias, evidencias, instrumento, referencias APA) y guion **sesión por sesión** con INICIO/DESARROLLO/CIERRE y minutos. |
| 6. Evaluación de producto | `fase_proyecto_integrador.ada_integradora_producto` de cada periodo. |

## Campos editables

Los campos que la plantilla exige pero que el JSON no contiene (modalidad, créditos,
fechas, puntajes, competencias de unidad, datos del docente, etc.) se muestran como
campos editables con fondo crema. **Las ediciones se guardan en `localStorage`** del
navegador, asociadas al nombre del archivo cargado, y persisten al recargar.

## Estructura

```
spa/
├── index.html        # SPA completa (todo en un archivo)
├── assets/
│   ├── logo1.png     # Banner de encabezado UADY (extraído del .docx)
│   └── logo2.png     # Línea decorativa de pie (extraída del .docx)
└── README.md
```
