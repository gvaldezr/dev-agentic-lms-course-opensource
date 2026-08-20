# UADY Brand Kit — Identidad Visual Digital

Kit de elementos gráficos y lineamientos de diseño digital basados en el **Manual de Identidad Universitaria** de la Universidad Autónoma de Yucatán (UADY), edición 2023.

## Contenido del Kit

```
uady_brand_kit/
├── README.md                 ← Este archivo
├── uady_brand_kit.html       ← Visualizador interactivo de todos los elementos
├── uady_assets.json          ← Assets gráficos como data URI (base64)
└── elements/                 ← Imágenes PNG extraídas del manual
    ├── p04_001_594x595.png
    ├── ...
    └── v2_p36_X247__1650x530.png
```

## Uso Rápido

### Visualizar el kit
Abrir `uady_brand_kit.html` en cualquier navegador. Muestra colores, tipografía, variables CSS y todos los assets con vista previa.

### Embeber assets en HTML (sin archivos externos)
```python
import json

with open('uady_assets.json', 'r') as f:
    assets = json.load(f)

# Obtener data URI
firma = assets['firma_institucional']['data_uri']
# Usar directamente: <img src="{firma}">
```

```html
<img src="{data_uri}" alt="Universidad Autónoma de Yucatán" class="firma-institucional">
```

---

## Colores Institucionales

| Nombre | Pantone | Hex | RGB | CMYK |
|--------|---------|-----|-----|------|
| **Azul UADY** | 295 C Solid Coated | `#192E4C` | 25, 46, 76 | 100, 81, 41, 42 |
| **Dorado UADY** | 1245 C Solid Coated | `#C89211` | 200, 146, 17 | 19, 41, 98, 8 |

### Neutros permitidos
- Negro `#000000`
- Blanco `#FFFFFF`
- Escala de grises

### Reglas de color
- Isotipo (escudo) y logotipo "UADY": siempre azul institucional.
- Descriptivo (nombre completo): dorado institucional.
- Lema "Luz, Ciencia y Verdad": dorado institucional (azul o neutros solo cuando el sustrato lo requiera).
- En fondos oscuros: usar versión blanca de la firma.
- No aplicar degradados, sombras ni efectos sobre la firma.

---

## Tipografía Institucional

**Familia:** Lucida Bright

| Variante | Uso |
|----------|-----|
| Regular | Logotipo "UADY" |
| Demibold | Descriptivo (nombre completo) |
| Italic | Textos de realce |
| Demibold Italic | Lema "Luz, Ciencia y Verdad" |

### Fallbacks para web
- Serif: `'Lucida Bright', Georgia, serif`
- Sans-serif (cuerpo): `'Lucida Sans', 'Lucida Grande', 'Segoe UI', system-ui, sans-serif`

---

## Design Tokens (Variables CSS)

```css
:root {
  /* === Colores institucionales === */
  --uady-azul: #192E4C;
  --uady-dorado: #C89211;
  --uady-blanco: #FFFFFF;
  --uady-negro: #000000;
  --uady-gris-claro: #F5F5F5;
  --uady-gris-medio: #E0E0E0;
  --uady-gris-oscuro: #666666;

  /* RGB para uso con opacity */
  --uady-azul-rgb: 25, 46, 76;
  --uady-dorado-rgb: 200, 146, 17;

  /* Variaciones tonales */
  --uady-azul-claro: #2A4A7A;
  --uady-azul-oscuro: #0f1d33;
  --uady-dorado-claro: #e5b030;
  --uady-dorado-oscuro: #9a700d;
  --uady-azul-fondo: #F0F3F7;

  /* === Tipografía === */
  --uady-font-logo: 'Lucida Bright', Georgia, serif;
  --uady-font-desc: 'Lucida Bright', Georgia, serif;
  --uady-font-body: 'Lucida Sans', 'Lucida Grande', 'Segoe UI', system-ui, sans-serif;

  /* === Espaciado === */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-xxl: 3rem;
}
```

---

## Assets Disponibles (`uady_assets.json`)

| Clave | Nombre | Categoría |
|-------|--------|-----------|
| `firma_institucional` | Firma Institucional | Identidad Principal |
| `jaguar` | Jaguar Institucional | Identidad Principal |
| `sello_1` — `sello_4` | Sellos Gráficos | Sellos Gráficos |
| `sello_5_sm` — `sello_8_sm` | Sellos (pequeños) | Sellos Gráficos |
| `patron_azul` | Patrón Ondas Maya - Azul | Patrones y Fondos |
| `patron_dorado` | Patrón Ondas Maya - Dorado | Patrones y Fondos |
| `borde_decorativo_1` | Borde Decorativo 1 | Patrones y Fondos |
| `borde_decorativo_2` | Borde Decorativo 2 | Patrones y Fondos |
| `cabecera_facultad` | Cabecera de Facultad | Aplicaciones |
| `hoja_membretada` | Hoja Membretada | Aplicaciones |
| `metricas_firma` | Métricas de la Firma | Guías Técnicas |
| `identidad_concepto` | Diagrama de Identidad | Conceptuales |
| `sello_uso_ejemplo` | Sellos - Ejemplo de uso | Sellos Gráficos |

---

## Firma Institucional (Imagotipo)

Compuesta por tres elementos jerárquicos:
1. **Isotipo** — Escudo Universitario
2. **Logotipo** — "UADY" (mayúsculas, Lucida Bright Regular)
3. **Descriptivo** — "UNIVERSIDAD AUTÓNOMA DE YUCATÁN" (mayúsculas, Lucida Bright Demibold)

### Reglas
- Siempre los tres elementos juntos (no omitir ninguno).
- Solo escalar proporcionalmente.
- Ubicar en **cuadrante 1** (superior izquierdo) como máxima jerarquía.
- Ningún elemento al lado izquierdo de la firma.
- Área de seguridad mínima: **2X** (X = altura del descriptivo).
- Medida mínima: 30×16 mm (≈ 113×60 px en pantalla).

### Lema
> "Luz, Ciencia y Verdad"

Tipografía: Lucida Bright Demibold Italic. Color: dorado. Se usa como contrapeso visual, no como parte de la firma.

---

## Lineamientos para Productos Digitales

### Presentaciones HTML5

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Título] - UADY</title>
</head>
<body>
    <header>
        <img src="{data_uri_firma}" alt="Universidad Autónoma de Yucatán" class="firma-institucional">
        <span class="dependencia">[Facultad/Asignatura]</span>
    </header>
    <main><!-- Contenido --></main>
    <footer>
        <span class="lema">"Luz, Ciencia y Verdad"</span>
    </footer>
</body>
</html>
```

**Estilos base:**
```css
.firma-institucional { max-height: 60px; width: auto; }
.dependencia {
    font-family: var(--uady-font-logo);
    color: var(--uady-dorado);
    text-transform: uppercase;
    font-size: 0.85rem;
}
.lema {
    font-family: var(--uady-font-logo);
    font-style: italic;
    font-weight: 600;
    color: var(--uady-dorado);
}
```

**Reglas:**
1. Firma institucional en esquina superior izquierda.
2. Títulos en azul institucional, tipografía serif.
3. Acentos y destacados en dorado.
4. Fondo principal: blanco o `--uady-azul-fondo`.
5. Texto de cuerpo: negro/gris oscuro, tipografía sans-serif.
6. Pie de página: lema en dorado italic.
7. Patrones `patron_azul`/`patron_dorado` como fondo sutil (opacity 0.08–0.15).
8. Bordes decorativos como separadores.
9. Sin sombras/degradados/efectos sobre la firma.
10. Área de seguridad 2X respecto a otros elementos.

### Quizzes Interactivos

1. Header con firma UADY sobre fondo azul institucional.
2. Botones primarios: fondo azul, texto blanco, `border-radius: 8px`.
3. Botones secundarios: borde dorado, texto dorado, fondo transparente.
4. Respuesta correcta: `#28a745` (verde suave) o dorado.
5. Respuesta incorrecta: `#dc3545` (rojo suave).
6. Retroalimentación positiva: card con borde izquierdo dorado.
7. Retroalimentación negativa: card con borde izquierdo rojo.
8. Puntaje: destacar con dorado, tamaño grande.
9. Contraste mínimo WCAG AA (4.5:1 normal, 3:1 grande).
10. Progress bar en dorado.
11. Patrones como fondo sutil en portada o resultados.

### Páginas Web / SPA

1. Navbar: fondo azul institucional, texto blanco/dorado.
2. Firma institucional en navbar.
3. Navegación activa: indicador dorado.
4. Cards: borde gris, hover con borde azul o sombra ligera.
5. Headings en azul, subheadings en dorado.
6. Links: dorado normal, azul hover.
7. Footer: fondo azul oscuro, lema en dorado.

---

## Responsive Design

- Mobile-first obligatorio.
- Breakpoints: 480px, 768px, 1024px, 1280px.
- Firma se reduce hasta 113×60px; menor que eso, usar solo isotipo.
- Navbar se colapsa a hamburger en mobile.
- Cards a una columna bajo 768px.

---

## Accesibilidad

- Contraste WCAG AA (4.5:1 texto normal, 3:1 texto grande).
- `alt="Universidad Autónoma de Yucatán"` para firma, `alt="Escudo UADY"` para isotipo.
- Focus visible (outline dorado o azul).
- Estructura semántica: h1 > h2 > h3.
- Roles ARIA en componentes interactivos.
- No depender solo del color para estados (agregar iconos ✓ ✗).

---

## Patrones y Texturas (Gráfico de Acompañamiento 2023)

Inspirados en los arcos del Centro Cultural Universitario.

**Uso correcto:**
- Fondos con `opacity: 0.08` a `0.15`
- Bordes decorativos en headers/footers
- Overlays en secciones hero

**Uso incorrecto:**
- Sobre la firma institucional
- Sobre texto de lectura a alta opacidad
- Invadiendo el área de seguridad

```css
.section-hero {
    position: relative;
}
.section-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url('{data_uri_patron_azul}');
    background-size: cover;
    opacity: 0.08;
    pointer-events: none;
}
```

---

## Clases CSS Utilitarias

```css
/* Colores de texto */
.text-azul { color: var(--uady-azul); }
.text-dorado { color: var(--uady-dorado); }
.text-blanco { color: var(--uady-blanco); }

/* Fondos */
.bg-azul { background-color: var(--uady-azul); }
.bg-dorado { background-color: var(--uady-dorado); }
.bg-claro { background-color: var(--uady-azul-fondo); }

/* Tipografía */
.font-institucional { font-family: var(--uady-font-logo); }
.font-cuerpo { font-family: var(--uady-font-body); }
.font-lema {
    font-family: var(--uady-font-logo);
    font-style: italic;
    font-weight: 600;
    color: var(--uady-dorado);
}

/* Bordes */
.border-dorado { border-color: var(--uady-dorado); }
.border-azul { border-color: var(--uady-azul); }
```

---

## Elementos Prohibidos

- Gráficos "Arcos" e "Integración" (triángulos) — **derogados**.
- Efectos de sombra, brillo, biselado, degradados en firmas.
- Rotación de letras/componentes del logotipo.
- Contenido comercial ajeno a la UADY.

---

## Integración como Submódulo Git

Este Brand Kit puede reutilizarse en otros proyectos como **submódulo de Git**:

```bash
# Desde otro proyecto:
git submodule add https://github.com/gvaldezr/uady-brand-kit.git uady_brand_kit
git submodule update --init
```

Ver la sección de abajo para instrucciones de extracción a repositorio independiente.

---

## Licencia

Estos elementos gráficos son propiedad de la **Universidad Autónoma de Yucatán**. Su uso está sujeto a los lineamientos del Manual de Identidad Universitaria 2023. Uso autorizado únicamente para proyectos institucionales.
