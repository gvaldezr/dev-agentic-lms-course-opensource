---
inclusion: fileMatch
fileMatchPattern: "**/*.html,**/presentacion*,**/quiz*,**/spa/**"
---

# Diseño de Productos Digitales UADY

Lineamientos específicos para la generación de presentaciones HTML5, quizzes interactivos y páginas web del proyecto LMS.

## Brand Kit de Referencia

El proyecto incluye un Brand Kit completo en `uady_brand_kit/` con:
- `uady_brand_kit.html` — Guía visual interactiva con todos los elementos de identidad
- `uady_assets.json` — Assets gráficos en formato data URI (base64) listos para embeber en HTML
- `uady_brand_kit/elements/` — Imágenes PNG extraídas del manual de identidad

### Assets disponibles en `uady_assets.json`

| Clave | Nombre | Categoría | Uso |
|-------|--------|-----------|-----|
| `firma_institucional` | Firma Institucional | Identidad Principal | Logo completo (Escudo + UADY + Descriptivo) |
| `jaguar` | Jaguar Institucional | Identidad Principal | Mascota deportiva |
| `sello_1` a `sello_4` | Sellos Gráficos | Sellos Gráficos | Identificadores visuales grandes |
| `sello_5_sm` a `sello_8_sm` | Sellos pequeños | Sellos Gráficos | Versiones reducidas |
| `patron_azul` | Patrón Ondas Maya - Azul | Patrones y Fondos | Textura decorativa azul |
| `patron_dorado` | Patrón Ondas Maya - Dorado | Patrones y Fondos | Textura decorativa dorada |
| `borde_decorativo_1` | Borde Decorativo 1 | Patrones y Fondos | Líneas decorativas |
| `borde_decorativo_2` | Borde Decorativo 2 | Patrones y Fondos | Líneas decorativas |
| `cabecera_facultad` | Cabecera de Facultad | Aplicaciones | Ejemplo de header |
| `hoja_membretada` | Hoja Membretada | Aplicaciones | Ejemplo de membrete |
| `metricas_firma` | Métricas de la Firma | Guías Técnicas | Proporciones del logo |
| `identidad_concepto` | Diagrama de Identidad | Elementos Conceptuales | Esquema conceptual |
| `sello_uso_ejemplo` | Sellos - Ejemplo de uso | Sellos Gráficos | Ejemplo aplicado |

### Cómo usar los assets en HTML

Para embeber un asset del Brand Kit directamente en un producto HTML:

```python
import json

with open('uady_brand_kit/uady_assets.json', 'r') as f:
    assets = json.load(f)

# Obtener data URI de la firma institucional
firma_uri = assets['firma_institucional']['data_uri']
# Usar en un <img src="...">
```

```html
<!-- Ejemplo: embeber firma directamente desde data URI -->
<img src="{data_uri_de_firma_institucional}" 
     alt="Universidad Autónoma de Yucatán" 
     class="firma-institucional">
```

### Logos adicionales (carpeta spa/assets/)
- `spa/assets/logo1.png` — Firma institucional horizontal (879×246 px)
- `spa/assets/logo2.png` — Variante horizontal amplia (1700×284 px)

## Paleta CSS (Design Tokens)

Usar estas variables CSS en todos los productos digitales (alineadas con el Brand Kit):

```css
:root {
  /* === Colores institucionales UADY === */
  --uady-azul: #192E4C;
  --uady-dorado: #C89211;
  
  /* Neutros */
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
  --font-institucional: var(--uady-font-logo);
  --font-cuerpo: var(--uady-font-body);
  
  /* === Espaciado === */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-xxl: 3rem;
}
```

## Estructura de Presentaciones HTML5

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Título de la presentación] - UADY</title>
    <!-- Variables CSS institucionales aquí -->
</head>
<body>
    <!-- Header: firma institucional en cuadrante 1 (superior izquierdo) -->
    <header>
        <img src="{data_uri_firma_institucional}" 
             alt="Universidad Autónoma de Yucatán"
             class="firma-institucional">
        <!-- Nombre de la dependencia/asignatura como contrapeso a la derecha -->
        <span class="dependencia">[Nombre de la Facultad/Asignatura]</span>
    </header>

    <!-- Contenido principal -->
    <main>
        <!-- Slides o secciones de contenido -->
    </main>

    <!-- Footer: lema como contrapeso visual -->
    <footer>
        <span class="lema">"Luz, Ciencia y Verdad"</span>
    </footer>
</body>
</html>
```

### Estilos base para presentaciones
```css
.firma-institucional {
    max-height: 60px;
    width: auto;
}

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

## Reglas para Presentaciones

1. **Encabezado**: firma institucional (escudo + "UADY" + descriptivo) en esquina superior izquierda — usar asset `firma_institucional` del Brand Kit.
2. **Títulos**: usar azul institucional (`--uady-azul`), tipografía serif.
3. **Acentos y destacados**: usar dorado institucional (`--uady-dorado`).
4. **Fondo principal**: blanco o gris muy claro (`--uady-azul-fondo`).
5. **Texto de cuerpo**: negro o gris oscuro sobre fondo claro, tipografía sans-serif.
6. **Pie de página**: lema "Luz, Ciencia y Verdad" en dorado, italic (Lucida Bright Demibold Italic).
7. **Patrones decorativos**: se pueden usar `patron_azul` o `patron_dorado` como fondo sutil con opacidad baja.
8. **Bordes**: usar `borde_decorativo_1` o `borde_decorativo_2` como separadores.
9. **No aplicar** sombras, degradados ni efectos sobre la firma institucional.
10. **Área de seguridad**: dejar al menos 2X de espacio libre alrededor de la firma (donde X = altura del descriptivo).

## Reglas para Quizzes Interactivos

1. **Header del quiz**: incluir firma UADY (`firma_institucional`) con fondo azul institucional.
2. **Botones de acción primaria**: fondo azul institucional, texto blanco, `border-radius: 8px`.
3. **Botones secundarios**: borde dorado, texto dorado, fondo transparente.
4. **Respuesta correcta**: borde/fondo `#28a745` (verde suave) o dorado institucional.
5. **Respuesta incorrecta**: borde/fondo `#dc3545` (rojo suave, no agresivo).
6. **Retroalimentación positiva**: card con borde izquierdo en dorado.
7. **Retroalimentación negativa**: card con borde izquierdo en rojo suave.
8. **Puntaje/calificación**: destacar con dorado, tamaño grande.
9. **Contraste mínimo**: WCAG AA (4.5:1 para texto normal, 3:1 para texto grande).
10. **Progress bar**: usar dorado para indicar avance.
11. **Patrones decorativos**: usar como fondo sutil en secciones de portada o resultados.

## Reglas para la SPA / Visualizador

1. Navbar con fondo azul institucional (`--uady-azul`) y texto blanco/dorado.
2. Firma institucional en navbar (usar `logo1.png` o `logo2.png` de `spa/assets/`).
3. Tabs o navegación con indicador activo en dorado (`--uady-dorado`).
4. Cards con borde sutil en gris medio, hover con borde azul o sombra ligera.
5. Headings principales en azul institucional, subheadings en dorado.
6. Links: color dorado en estado normal, azul en hover.
7. Mantener consistencia con la paleta institucional en toda la interfaz.
8. Footer con fondo azul oscuro y lema en dorado.

## Responsive Design

- Mobile-first obligatorio.
- Breakpoints sugeridos: 480px, 768px, 1024px, 1280px.
- La firma institucional se puede reducir hasta su medida mínima (30×16mm ≈ 113×60px en pantalla); si no cabe, usar solo el isotipo (escudo).
- En mobile, la navbar se colapsa a hamburger con firma reducida.
- Cards pasan a una columna en pantallas menores a 768px.

## Accesibilidad

- Contraste mínimo WCAG AA (4.5:1 texto normal, 3:1 texto grande).
- Textos alternativos en imágenes: `alt="Universidad Autónoma de Yucatán"` para la firma, `alt="Escudo UADY"` para el isotipo.
- Focus visible en elementos interactivos (outline en dorado o azul).
- Estructura semántica con headings jerárquicos (h1 > h2 > h3).
- Roles ARIA donde sea necesario para componentes interactivos (tabs, quizzes).
- No depender solo del color para comunicar estados (agregar iconos ✓ ✗).

## Gráfico de Acompañamiento (Arcos 2023) y Patrones

Los assets `patron_azul` y `patron_dorado` del Brand Kit representan la textura visual inspirada en los arcos del Centro Cultural Universitario.

### Uso correcto:
- Secciones de portada o separadores como fondo con `opacity: 0.1` a `0.15`.
- Bordes decorativos en headers o footers.
- Overlays sutiles en secciones hero.

### Uso incorrecto:
- Nunca sobre la firma institucional.
- Nunca sobre texto de lectura a opacidad alta.
- No debe invadir el área de seguridad de la firma.

```css
/* Ejemplo: patrón como fondo sutil */
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

## Clases CSS utilitarias recomendadas

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
