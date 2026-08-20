---
inclusion: auto
---

# Identidad Visual UADY — Lineamientos de Diseño

Este documento establece las reglas de identidad visual de la Universidad Autónoma de Yucatán (UADY) que deben seguirse al generar cualquier producto digital (presentaciones HTML, quizzes, páginas web, documentos).

## Colores Institucionales

| Nombre | Pantone | Hex | RGB | CMYK |
|--------|---------|-----|-----|------|
| Azul UADY | 295 C Solid Coated | `#192E4C` | R:25, G:46, B:76 | C:100%, M:81%, Y:41%, K:42% |
| Dorado UADY | 1245 C Solid Coated | `#C89211` | R:200, G:146, B:17 | C:19%, M:41%, Y:98%, K:8% |

### Colores neutros permitidos
- Negro `#000000`
- Blanco `#FFFFFF`
- Escala de grises

### Reglas de color
- El isotipo (escudo) y logotipo ("UADY") usan siempre el azul institucional.
- El descriptivo (nombre completo) usa el dorado institucional.
- El lema "Luz, Ciencia y Verdad" usa el dorado institucional; solo se permite azul o neutros cuando el sustrato o sistema de impresión lo requiera.
- Las firmas pueden aplicarse a una tinta siempre que sea en color institucional o neutro.
- En fondos oscuros, usar la versión blanca de la firma.

## Tipografía Institucional

**Familia:** Lucida Bright

| Variante | Uso principal |
|----------|--------------|
| Lucida Bright Regular | Logotipo "UADY" |
| Lucida Bright Demibold | Descriptivo (nombre completo de la universidad) |
| Lucida Bright Italic | Textos de realce dentro de cajas de texto |
| Lucida Bright Demibold Italic | Lema "Luz, Ciencia y Verdad"; textos de gran importancia |

### Reglas tipográficas
- La tipografía institucional siempre se escala proporcionalmente.
- La tipografía institucional puede ser reemplazada por otras fuentes dentro del cuerpo de texto de documentos y aplicaciones.
- No se usan minúsculas ni cursivas en los elementos del imagotipo.
- El tamaño mínimo del lema es 5 puntos.

### Tipografía sugerida para cuerpos de texto digitales
Cuando Lucida Bright no esté disponible en web, usar:
- Primaria: `Georgia, serif` (similar serif clásico)
- Alternativa: sistema serif disponible

## Firma Institucional (Imagotipo)

Compuesta por tres elementos en orden jerárquico:
1. **Isotipo** — Escudo Universitario
2. **Logotipo** — Palabra "UADY" (siempre mayúsculas, Lucida Bright Regular)
3. **Descriptivo** — "UNIVERSIDAD AUTÓNOMA DE YUCATÁN" (mayúsculas, Lucida Bright Demibold, alineado a la derecha)

### Reglas de la firma
- Siempre contiene los tres elementos; no se omite ninguno.
- El orden y ubicación no se modifican.
- Solo se escala proporcionalmente, nunca elementos por separado.
- No se aplican: contornos, sombras, degradados, biselados, brillos o efectos.
- No se encasilla en recuadros limitados ni sobre fondos complejos.
- La firma institucional se ubica en el **cuadrante 1** (superior izquierdo) como elemento de mayor jerarquía.
- Ningún elemento se coloca al lado izquierdo de la firma.

## Lema

> "Luz, Ciencia y Verdad"

- Tipografía: Lucida Bright Demibold Italic
- Color: Dorado institucional (primario)
- Se usa como contrapeso visual de la firma, no como parte de ella.
- No se altera su interletraje.

## Firma Secundaria

Alternativa vertical: isotipo + logotipo + lema.
- Puede usarse sin la firma institucional siempre que se acompañe del nombre "UNIVERSIDAD AUTÓNOMA DE YUCATÁN".

## Gráfico de Acompañamiento (2023)

Inspirado en los arcos del Centro Cultural Universitario.
- Se usa como textura visual decorativa.
- No debe invadir el área de seguridad de la firma institucional.
- Puede usarse en versión dorada, azul o combinación.
- No debe dañar la legibilidad de elementos escritos y gráficos.

## Jerarquía y Composición

- Lectura occidental: izquierda → derecha, arriba → abajo.
- Cuadrante 1 (superior izquierdo): firma institucional.
- Los logotipos oficiales de dependencias sirven como contrapeso visual (nunca en cuadrante 1).
- En presentaciones y portadas se puede usar la firma en cuadrantes 2 o 5 si no hay elementos previos.

## Área de Seguridad

- Mínimo **2X** de separación respecto a cualquier otro elemento gráfico (donde X = altura del descriptivo).
- No puede haber elementos gráficos detrás o sobre las firmas.

## Medidas Mínimas

| Elemento | Medida mínima |
|----------|--------------|
| Firma institucional | 30 × 16 mm |
| Firma secundaria | 19 × 23 mm |
| Isotipo (escudo) | 10 × 16 mm |

## Aplicaciones Digitales

### Presentaciones
- Firma institucional en cuadrante 1.
- Fondo claro u oscuro (con firma en color adecuado).
- Logotipo oficial de dependencia como contrapeso.

### Redes Sociales — Dimensiones
| Red | Foto perfil | Foto portada |
|-----|-------------|--------------|
| Facebook | 170×170 px | 820×312 px |
| Instagram | 320×320 px | — |
| Twitter/X | 400×400 px | 1500×500 px |
| YouTube | 800×800 px | 2560×1440 px |
| TikTok/Stories | — | 1080×1920 px (9:16) |

### Publicaciones
- Formato cuadrado: 1200×1200 px
- La firma institucional debe ser legible con contraste en todas las publicaciones.

### Portal Web
- Diseño responsivo obligatorio.
- La firma corporativa debe direccionar a www.uady.mx.
- URLs amigables/semánticas.
- Contenidos en formato texto para motores de búsqueda y traducción.

## Elementos Prohibidos

- Gráficos "Arcos" e "Integración" (triángulos) — derogados, no usar.
- Efectos de sombra, brillo, biselado, degradados en firmas.
- Rotación de letras o componentes del logotipo.
- Uso del isotipo como logotipo oficial de dependencia.
- Publicar contenido comercial ajeno a la UADY.

## Valores Institucionales (para tono de contenidos)

Responsabilidad, Respeto, Equidad, Justicia, Honestidad, Honradez, Humildad, Empatía, Perseverancia, Compromiso, Ética.

## Brand Kit del Proyecto

El proyecto cuenta con un Brand Kit completo en `uady_brand_kit/`:
- **`uady_brand_kit.html`** — Visualizador interactivo de todos los elementos gráficos
- **`uady_assets.json`** — Assets gráficos embebidos como data URI (base64), listos para usar en productos HTML sin dependencias externas
- **`uady_brand_kit/elements/`** — Imágenes PNG extraídas del manual de identidad

Los assets incluyen: firma institucional, jaguar, sellos gráficos, patrones decorativos (ondas maya), bordes, y ejemplos de aplicación.

Para detalles de implementación CSS y uso de assets, consultar el steering `diseno-productos-digitales-uady.md` (se activa automáticamente al editar archivos HTML).

## Misión

La Universidad Autónoma de Yucatán es una institución pública de educación media superior y superior que promueve oportunidades de aprendizaje para todas y todos, a través de una educación humanista, pertinente y de calidad.

## Visión 2030

Universidad internacional, vinculada estratégicamente a lo local, con amplio reconocimiento por su relevancia y trascendencia social.
