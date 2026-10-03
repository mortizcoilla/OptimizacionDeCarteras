# Decisiones de diseño visual

> Documento de referencia. Define paleta, semántica cromática, sistema de componentes editoriales, set de gráficos disponibles y decisiones tomadas. Estas decisiones alimentan el paper 1 (backtest) y su derivado.
>
> **Revisión 2026-07-27 (noche):** se incorpora el patrón editorial del Attention Residuals interactive explainer (Moonshot AI, arXiv:2603.15031). Mantenemos la paleta fría turquoise/grey/navy; adoptamos el sistema de paneles, sticky nav, stat cards, result notes, reveals on beat y mono en metadata/captions.

---

## 1. Paleta institucional

5 colores base, todos de la imagen de referencia entregada por Miguel ("turquoise grey navy palette", coolors.co). Paleta **monocromática-azul** con un solo acento (teal medio) y dos grises neutros.

| Variable CSS | Hex | Nombre | Rol semántico |
|---|---|---|---|
| `--ink` | `#081630` | Navy profundo | Texto principal, títulos, números destacados, fondo oscuro opcional |
| `--teal-deep` | `#125358` | Teal oscuro | Acento secundario, líneas de referencia, ejes, series secundarias |
| `--teal` | `#3B878C` | Teal medio | **Color de datos primario.** Series principales, áreas, líneas primarias |
| `--grey` | `#C2C3C5` | Gris medio | Cuadrículas, separadores, series contextuales, ejes secundarios |
| `--paper` | `#EBEBED` | Gris claro | Fondo de página, fondo de charts en blanco |

### 1.1 Color funcional (decisión abierta a revisar)

La paleta no tiene color para "pérdida/negativo". Para un paper cuantitativo eso es un problema: si una serie cae 20% y la otra sube 20%, no pueden ser ambas del mismo teal.

**Decisión tomada por defecto:** agregar **un solo color funcional** para pérdidas:

| Variable CSS | Hex | Nombre | Uso |
|---|---|---|---|
| `--loss` | `#A04545` | Rojo apagado | Pérdida, drawdown, valor negativo, retorno < 0 |

- **Ganancias / valores positivos:** se renderizan con `--teal` (color primario de la paleta).
- **Pérdidas / valores negativos:** se renderizan con `--loss`.
- **No se agrega verde funcional** para mantener la paleta monocromática-azul. Si Miguel prefiere verde para ganancias y rojo para pérdidas (convención más estándar), se cambia.

> **Pendiente de confirmación:** ¿mantener este esquema (ganancia=teal, pérdida=rojo) o usar convención clásica (verde/rojo)? Si se decide monocromático puro, se quita `--loss` y se distingue por otro medio (ej. saturación, opacidad, o series separadas en paneles).

### 1.2 Tono de fondo (decisión a discutir)

La paleta actual propone `--paper = #EBEBED` (gris muy claro, casi blanco). El explainer de Moonshot usa `#F4F0E8` (cream cálido) que da una sensación más "paper" / editorial. **Decisión por defecto:** mantener `--paper = #EBEBED` para coherencia con la paleta fría. Si Miguel prefiere un fondo tipo "paper impreso" (más cálido, beige), se puede cambiar a `#F2F0EC` sin salirnos de la paleta fría.

---

## 2. Tipografía

- **Familias:**
  - **Sans (body, headings):** Inter (vía Google Fonts), fallback `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.
  - **Mono (metadata, captions, axis, code):** JetBrains Mono o IBM Plex Mono (vía Google Fonts), fallback `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.
- **Escala:**
  - **h1 (título del paper):** `clamp(28px, 3.4vw, 44px)`, weight 800, line-height 1.14, letter-spacing -0.015em, color `--ink`.
  - **h2 (sección):** `clamp(20px, 2.2vw, 28px)`, weight 800, line-height 1.22, color `--ink`.
  - **h3 (subsección):** 16-18 px, weight 700, color `--ink`.
  - **Body:** 15-17 px, weight 400, line-height 1.62, color `--ink`.
  - **Kicker / eyebrow:** 12 px, mono, letter-spacing 0.14em, uppercase, color `--teal`.
  - **Stat value:** `clamp(22px, 2.4vw, 30px)`, weight 800, color `--teal`.
  - **Caption / metadata / axis:** 12-13 px, mono, color `--teal-deep` o `--grey`.
  - **Number destacado (paper hero, stat grande):** 48-72 px, weight 800, tabular-nums, color `--ink`.
- **Figuras:** título 14-16 px, leyenda 10-11 px, axis labels 10-11 px mono.
- **Fórmulas:** KaTeX render (CDN), tamaño 16-20 px.

> **Pendiente de confirmación:** confirmar Inter como sans (default) o cambiar a IBM Plex Sans. Default: **Inter**.

---

## 3. Sistema de componentes editoriales

> Adoptamos el patrón de "interactive research explainer" del paper de Moonshot AI. Cada componente se mapea a una sección del paper.

### 3.1 Header (hero del paper)

```html
<header class="paperhead">
  <p class="kicker">Working paper</p>
  <h1>Título del paper aquí</h1>
  <p class="subtitle">Subtítulo descriptivo</p>
  <p class="meta">Miguel Ortiz C. · Julio 2026 · <a href="...">arXiv link</a> · <a href="...">GitHub</a></p>
</header>
```

- Fondo `--paper` con grilla sutil de 24px (mismo patrón del explainer).
- Kicker mono en uppercase con color `--teal`.
- h1 grande, weight 800, max-width 22ch.
- Metadata en mono con links en `--teal-deep`.

### 3.2 Sticky nav (secciones numeradas)

```html
<nav id="topnav">
  <a href="#sec0">Overview</a>
  <a href="#sec1">1 · Introducción</a>
  <a href="#sec2">2 · Marco teórico</a>
  <a href="#sec3">3 · Datos y metodología</a>
  <a href="#sec4">4 · Resultados</a>
  <a href="#sec5">5 · Discusión</a>
  <a href="#sec6">6 · Conclusiones</a>
  <a href="#sec7">7 · Apéndice</a>
</nav>
```

- Sticky top, fondo `--paper` con 96% opacidad, border-bottom 1px `--grey`.
- Links en mono, padding pill, hover bg `--paper-deep`.
- **No incluye** selector de velocidad global (decidido no usar — el scroll es suficiente).

### 3.3 Panel (sección del paper)

```html
<section class="panel">
  <h2>Título de la sección</h2>
  <p class="lede">Párrafo introductorio (max-width 75ch)</p>
  <!-- contenido -->
</section>
```

- Fondo `--paper` (más claro que el fondo de la página).
- Border 1px `--grey`, radius 16px, shadow `0 1px 2px rgba(8,22,48,.05), 0 8px 24px rgba(8,22,48,.06)`.
- Padding generoso (clamp 18px, 3vw, 34px).

### 3.4 Cards 3 columnas (overview / hallazgos)

```html
<article class="minicard">
  <p class="tag tag-teal">Hallazgo</p>
  <h3>Título del hallazgo</h3>
  <p>Descripción breve.</p>
</article>
```

- Grid 3 columnas en desktop, 1 columna en mobile (≤900px).
- Border, radius 14px, fondo `--paper` (mismo que panel, sutil diferenciación).
- Tags: `.tag-teal`, `.tag-ink`, `.tag-loss`, `.tag-grey` — fondo soft del color, border 1px del color, texto en mono 11px uppercase.

### 3.5 Stat cards (métricas principales)

```html
<article class="statcard">
  <p class="statval">1.27</p>
  <p class="statdesc">Sharpe ratio del portafolio max-Sharpe, 2010-2024</p>
</article>
```

- Grid 4 columnas en desktop, 2 columnas en mobile.
- Border, radius 14px, fondo `--paper`.
- **statval:** weight 800, `clamp(22px, 2.4vw, 30px)`, color `--teal`.
- **statdesc:** 13 px, color `--ink`.

### 3.6 Fórmula band

```html
<div class="formulaband">
  <p class="tex" data-tex="Sharpe = \frac{R_p - R_f}{\sigma_p}">…</p>
  <p class="support">Ratio de Sharpe: retorno excedente por unidad de volatilidad total.</p>
</div>
```

- Border 1px `--grey`, border-left 4px `--teal`, fondo `--paper`, radius 12px.
- Fórmula renderizada con KaTeX (CDN, 0.16.x).
- support: 14 px, color `--teal-deep` o `--grey`.

### 3.7 Result note (panel destacado)

```html
<aside class="resultnote">
  <p><strong>Hallazgo 1.</strong> La estrategia 1/N no es subóptima en el IPSA 2010-2024.</p>
  <p>En el período completo, el portafolio equal-weight entrega un Sharpe de 0.78, comparado con 0.71 del portafolio max-Sharpe estimado con rolling window.</p>
</aside>
```

- Border 1px `--teal`, border-left 4px `--teal`, fondo `--teal-soft` (un teal al 12% de opacidad, lo agregamos como variable), radius 12px.
- Padding 14px 18px.
- Para hallazgos negativos o limitaciones, fondo `--loss-soft` (rojo al 12%).

### 3.8 Caption mono (sobre las figuras)

```html
<p class="caption">F4 — Rolling Sharpe 12-meses por estrategia. La jerarquía es estable en el primer quinquenio y se inverte después de 2019.</p>
```

- Mono 12.8px, line-height 1.55, color `--ink`.
- Fondo `--paper-deep`, border-left 3px `--teal`, radius 8px, padding 9px 12px.
- `min-height: 2.6em` para que la altura no salte cuando cambia el texto (en el caso de captions dinámicos en reveals on beat).

### 3.9 Tabla de métricas (benchmark-style)

```html
<table class="bench">
  <caption>Tabla 1 — Métricas de las 6 estrategias, 2010-2024</caption>
  <thead>
    <tr><th>Estrategia</th><th>Retorno</th><th>Vol</th><th>Sharpe</th><th>Max DD</th></tr>
  </thead>
  <tbody>
    <tr><td>Equal-weight</td><td class="up">9.8%</td><td>15.2%</td><td class="up">0.78</td><td>-32%</td></tr>
    <!-- ... -->
  </tbody>
</table>
```

- Border-collapse, width 100%, min-width 460px, font-size 13.5px.
- Caption arriba a la izquierda, mono 12px, color `--grey`.
- Header: mono 11.5px, uppercase, color `--grey`, fondo `--paper`.
- Celdas con clase `.up` (color `--teal-deep`, weight 700), `.loss` (color `--loss`), `.tie` (color `--grey`).
- Wrapper `.tablewrap` con `overflow-x: auto` y border 1px `--grey`, radius 12px.

### 3.10 Reveal on beat (IntersectionObserver)

Para figuras complejas (treemap, chord diagram, ridgeline), se renderizan por capas que aparecen progresivamente cuando la figura entra al viewport. Patrón de implementación:

```js
// En main.js
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Activar reveal de la figura
      entry.target.classList.add('revealed');
    }
  });
}, { threshold: 0.3 });

document.querySelectorAll('.revealable').forEach(el => observer.observe(el));
```

CSS:
```css
.revealable { opacity: 0; transform: translateY(8px); transition: opacity .5s ease, transform .5s ease; }
.revealable.revealed { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  .revealable { transition: none; transform: none; }
}
```

Para figuras con múltiples sub-pasos (ej. chord diagram con 5 capas que se van dibujando), se usa una función `reveal(figureId, beatIndex)` que activa cada sub-capa con un delay. **No** se usa Play/Pause/Step/Reset por sección (decisión tomada: el scroll es suficiente).

### 3.11 Footer

```html
<footer>
  <p><strong>Miguel Ortiz C.</strong></p>
  <p>Contacto: <a href="https://linkedin.com/in/mortizcoilla">LinkedIn</a> · <a href="mailto:mortizcoilla@gmail.com">Email</a> · <a href="https://wa.me/56933293943">WhatsApp</a></p>
  <p>Repo: <a href="...">GitHub</a> · Licencia: MIT</p>
</footer>
```

- Border-top 1px `--grey`, fondo `--paper-deep`.
- Mono 13.5px, color `--grey`.
- **Sin** los 3 botones SVG (de la regla de autor), o con ellos si se prefiere consistencia con los monitores. Decisión por defecto: **botones SVG inline** con los mismos iconos que el monitor financiero (consistencia cross-project).

---

## 4. Set de gráficos disponibles

> Catálogo de tipos de gráficos D3 que se pueden usar en el paper 1 y derivados. No es obligatorio usar todos. Cada uno se justifica con un rol analítico concreto.

### 4.1 Gráficos convencionales (uso permitido)

- **Línea** — series temporales (equity curves, rolling Sharpe, drawdowns).
- **Barras (vertical y horizontal)** — métricas, rankings, contribuciones.
- **Área apilada** — composición acumulada.
- **Dispersión (scatter)** — relación entre dos variables (ej. retorno vs vol de portafolios).
- **Tabla HTML con clases CSS** — comparación de métricas (es la "figura 1" de cualquier paper cuantitativo).

### 4.2 Gráficos no convencionales (recomendados para el paper)

| Tipo | Rol analítico | Dificultad D3 | Uso propuesto |
|---|---|---|---|
| **Heatmap** | Matriz de correlaciones entre activos, ordenada por clustering jerárquico | Media | F10 — diversificación |
| **Treemap jerárquico** | Composición de un portafolio (sector → industria → activo), tamaño = peso | Media-alta | F5 — comparación cap-weighted vs óptimo |
| **Ridgeline (joyplot)** | Distribuciones de retornos apiladas por régimen (pre-2014, 2014-2019, crisis 2019-2021, post-2022) | Alta | F9 — comportamiento bajo regímenes |
| **Violin plot** | Distribución de retornos mensuales por estrategia | Media | F9 alt — complementa al ridgeline |
| **Radar / Spider** | Perfil multidimensional por estrategia (8 dimensiones) | Media | F6 — comparación de perfiles |
| **Waterfall** | Contribución por activo al retorno total del portafolio ganador | Media | F7 — atribución de performance |
| **Bump chart** | Ranking de estrategias a lo largo del tiempo (rolling) | Media | F8 — estabilidad temporal del ranking |
| **Streamgraph** | Evolución de pesos del portafolio a lo largo del backtest (rebalanceo mensual) | Alta | F5 alt — drift estructural |
| **Chord diagram** | Correlaciones top-10 activos (alternativa elegante al heatmap) | Alta | F10 alt — limitada a subconjunto |
| **Parallel coordinates** | Trade-offs multivariados (todos los activos cruzando ejes retorno, vol, drawdown, beta) | Alta | F4 alt — outliers visuales |
| **Box plot** | Distribución por estrategia (cuartiles, outliers) | Baja-media | F9 alt — más simple que violin |

### 4.3 Gráficos que NO se usaron y por qué

- **Gauge / velocímetro semicircular:** frágil geométricamente, se rompe con cambios de tamaño. Es del formato monitor; acá no aplica.
- **Waffle chart:** visualmente simpático pero pierde precisión. No comunica análisis serio.
- **Bullet chart:** útil para KPIs con targets, pero no hay targets claros en un paper cuantitativo.
- **Pictogramas:** decorativos, no analíticos.

### 4.4 Animación de gráficos

- **Reveal on beat** (IntersectionObserver): figuras complejas se dibujan por capas al entrar al viewport.
- **No** usamos Play/Pause/Step/Reset por sección (el scroll natural es suficiente en un paper).
- **`prefers-reduced-motion` respetado**: si el usuario lo tiene activo, las figuras se renderizan completas sin animación.
- **Transiciones cortas** (200-500ms) para que el scroll se sienta fluido, no cinematográfico.

---

## 5. Convenciones de estilo

### 5.1 CSS

- Variables CSS en `:root` (no SCSS, no Tailwind, no preprocesador).
- Convención BEM-like: `.paperhead`, `.panel`, `.minicard`, `.statcard`, `.formulaband`, `.resultnote`, `.caption`, `.bench`, `.revealable`.
- Componentes reutilizables y no acoplados al paper específico (la idea es que la plantilla sirva para paper 1, paper 2 derivado, y futuros).

### 5.2 Datos embebidos

- Todos los datos van en `js/data.js` como constantes con namespace (`window.OC.<sección>`).
- Los CSVs del pipeline Python se pre-procesan y se exportan a JSON embebido. No hay fetches.
- Formato: arrays de objetos con claves explícitas y documentadas en JSDoc.

### 5.3 Idioma

- UI, código, comentarios y paper en **español** (es-CL).
- Términos técnicos en inglés cuando son estándar (Sharpe ratio, drawdown, rebalanceo, backtest, etc.).
- Fórmulas matemáticas: en notación LaTeX estándar (KaTeX las renderiza).

---

## 6. Formato del entregable (NO es un monitor)

### 6.1 Lo que NO va (vs. formato monitor)

- ❌ Portada con scorecard de un índice compuesto.
- ❌ Filtros globales con factores multiplicativos.
- ❌ Drawer mobile / sidebar fija.
- ❌ Capas analíticas "derivadas" (perfiles/segmentos/panel).
- ❌ 5 niveles de color para un score.
- ❌ "Dato macro · no ajustable" como badge.
- ❌ Controles Play/Pause/Step/Reset por sección (explicador interactivo de ML; acá no aplica).

### 6.2 Lo que SÍ va (rescatado del monitor)

- ✅ Profundidad analítica comparable a un paper serio.
- ✅ Cita de fuentes primarias por cada cifra/afirmación.
- ✅ Metodología explícita y reproducible.
- ✅ Limitaciones declaradas.
- ✅ README documentado.
- ✅ JSDoc en español, IIFE con namespace, `try/catch` por módulo.
- ✅ Bloque de autor con 3 botones (LinkedIn/Email/WhatsApp), **sin títulos académicos**.

### 6.3 Lo nuevo (del interactive research explainer)

- ✅ Sistema de paneles editoriales con shadow.
- ✅ Sticky nav numerada con secciones.
- ✅ Stat cards para métricas principales.
- ✅ Result notes en panel destacado.
- ✅ Captions en mono sobre `--paper-deep`.
- ✅ Fórmulas KaTeX con bandas de color.
- ✅ Reveal on beat con IntersectionObserver.
- ✅ Tabla de benchmarks con header mono y celdas coloreadas.
- ✅ Mini cards con tags de color en overview.
- ✅ Header editorial con kicker + h1 + meta mono.

### 6.4 Formato concreto

- **Paper:** documento markdown/HTML con estructura IMRyD (ver propuesta del paper 1).
- **Complemento HTML estático:** `index.html` + `css/styles.css` + `js/{data,core,modules,main}.js`, vanilla JS + D3.js v7 vía CDN, sin build step, sin `npm install`. Las figuras del paper viven como SVG interactivos en este complemento.
- **Datos descargables:** CSV/JSON en `/data/` del repo, accesibles desde el HTML.
- **No hay** navegación por sidebar ni portada de "índice compuesto". El HTML es un **lector de paper con figuras embebidas**, no un dashboard.

---

## 7. Decisiones tomadas (resumen)

| # | Decisión | Default | Pendiente |
|---|---|---|---|
| 1 | Paleta | 5 colores turquoise/grey/navy de la imagen | — |
| 2 | Color funcional de pérdida | `#A04545` rojo apagado | ¿Sí / monocromático puro? |
| 3 | Color de ganancia | `--teal` (mismo que series primarias) | ¿Verde funcional en su lugar? |
| 4 | Fondo | `--paper = #EBEBED` (frío) | ¿Beige cálido tipo paper impreso? |
| 5 | Tipografía | Inter (sans) + JetBrains Mono (mono) | — |
| 6 | KaTeX para fórmulas | Sí, CDN 0.16.x | — |
| 7 | Set de gráficos | 11 tipos no convencionales habilitados | — |
| 8 | Animación de figuras | Reveal on beat con IntersectionObserver | — |
| 9 | Idioma | es-CL | — |
| 10 | Formato del entregable | Paper + complemento HTML estático | — |
| 11 | Stack del HTML | Vanilla JS + D3 v7, sin build | — |
| 12 | Convención de datos | Embebidos en `data.js`, no fetches | — |
| 13 | Bloque de autor | 3 botones SVG sin títulos | — |
| 14 | Sticky nav | Numerada, sin selector de velocidad | — |
| 15 | Patrón editorial | Adoptado del explainer Moonshot AI | — |
