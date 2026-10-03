# Paper 2 derivado — Esbozo: Risk Parity en mercados concentrados, el caso del IPSA

> Esbozo de 1-2 páginas. Paper derivado del paper 1. Comparte la tubería de datos y la metodología base; profundiza sólo en la comparación risk parity vs cap-weighted. Se publica después del paper 1.

---

## 1. Título tentativo

> **Risk Parity en mercados concentrados: por qué la "diversificación verdadera" no funciona como en EE.UU. cuando el top-5 pesa 30%**

Variante más corta:
- "Risk Parity en el IPSA: una promesa que la concentración local no deja cumplir"

---

## 2. Hipótesis central

> La propuesta de Qian (2005) — risk parity como portafolio que iguala la contribución al riesgo de cada activo, independientemente de su capitalización — funciona en mercados líquidos y diversificados (S&P 500) porque ningún activo individual domina el riesgo. **En el IPSA, donde las 5 acciones más grandes representan ~30% del peso y ~40-50% de la varianza del índice, risk parity se ve forzado a sobreponderar papeles de baja capitalización que no tienen el float ni la liquidez para sostener esa asignación.** El resultado: risk parity en el IPSA no entrega los beneficios documentados en la literatura de EE.UU., y en algunos subperíodos (crisis de liquidez 2019-2020) sub-performa al cap-weighted.

**Hipótesis formal:** el spread de Sharpe entre risk-parity y cap-weighted en el IPSA 2010-2024 es **negativo o no significativo**, en contraste con la literatura de EE.UU. donde el spread es positivo y robusto.

---

## 3. Estructura del paper (5 secciones)

### 3.1. Introducción (1-2 páginas)
- Recordatorio del paper 1: risk parity quedó en la mitad de la tabla.
- La pregunta: ¿es un artefacto del período, o un problema estructural del IPSA?
- La intuición: si el benchmark es muy concentrado, "diversificar el riesgo" implica alejarse mucho del benchmark, lo que introduce tracking error grande y costos de transacción altos.

### 3.2. Marco teórico (1-2 páginas)
- Qian (2005) — definición formal de ERC (Equal Risk Contribution).
- Roncalli (2013) — extensión y variantes.
- Spinu (2013) — optimización directa de ERC.
- Maillard, Roncalli & Teïletche (2010) — propiedades teóricas.
- Por qué la concentración del benchmark importa: intuición + cita a BCCh sobre estructura del IPSA.

### 3.3. Datos y metodología (1-2 páginas)
- Mismos datos que el paper 1 (consistencia).
- Definición operativa de ERC.
- Medición de la concentración del benchmark:
  - Herfindahl-Hirschman Index (HHI) sobre pesos.
  - HHI sobre contribuciones al riesgo.
  - Top-5 weight y top-5 risk contribution (evolución temporal).
- Comparación IPSA vs S&P 500, MSCI World, etc. (referencia, no central).
- Métricas específicas para este paper:
  - Tracking error vs cap-weighted.
  - Turnover adicional sobre cap-weighted.
  - Sharpe del spread (RP − CW).
  - Maximum active weight (cuánto se aleja del benchmark).

### 3.4. Resultados (3-4 páginas)
- 4.1 Concentración del IPSA vs benchmarks internacionales (1 figura + tabla).
- 4.2 Pesos de risk parity vs cap-weighted (treemap lado a lado + streamgraph de evolución).
- 4.3 Contribución al riesgo por activo en cada portafolio (stacked bar + waterfall).
- 4.4 Desempeño ajustado por tracking error (scatter Sharpe vs tracking error).
- 4.5 Estabilidad temporal (rolling Sharpe, rolling turnover, rolling max active weight).
- 4.6 Sensibilidad al umbral de "liquidez mínima" (¿qué pasa si se obliga a no tener más del 10% en un activo?).

### 3.5. Discusión y conclusiones (1-2 páginas)
- Confirmación o rechazo de la hipótesis.
- Implicaciones para mercados emergentes: ¿hay un umbral de concentración bajo el cual risk parity deja de funcionar?
- Recomendación: en mercados con HHI > X, evaluar variants constreñidas (constrained risk parity con cap al peso máximo).
- Trabajo futuro: aplicar a otros índices LATAM (Bovespa, Merval, MexBol) para validar la generalización.

---

## 4. Figuras del paper (5-7)

| # | Figura | Tipo gráfico | Rol |
|---|---|---|---|
| F1 | Tabla comparativa de concentración: IPSA vs S&P 500 vs MSCI World | Tabla | Contexto |
| F2 | HHI del IPSA en el tiempo | Línea | Evolución estructural |
| F3 | Treemaps lado a lado: cap-weighted vs ERC | Treemap | Reorganización |
| F4 | Streamgraph de pesos ERC en el tiempo | Streamgraph | Drift |
| F5 | Contribución al riesgo por activo (stacked bar) | Barras apiladas | Verificación del ERC |
| F6 | Scatter Sharpe vs tracking error | Dispersión | Eficiencia ajustada |
| F7 | Rolling Sharpe: ERC vs CW vs 1/N | Línea | Comparación temporal |

---

## 5. Conexión con el paper 1

- **Reutiliza:** la tubería de descarga de precios, la limpieza de datos, las funciones de cálculo de retorno y volatilidad, la estructura de ventanas rolling.
- **Reutiliza:** el bloque de "metodología base" como referencia cruzada (en vez de repetir).
- **Reutiliza:** la paleta y el formato HTML estático.
- **Aporta nuevo:** la metodología de cálculo de pesos ERC, las métricas de concentración, el análisis de tracking error.
- **No repite:** las preguntas de investigación sobre jerarquía general de estrategias, el análisis por régimen macroeconómico completo, la comparación con maximum diversification.

---

## 6. Estimación de esfuerzo

- Reutilización: ~60% del paper 1.
- Trabajo nuevo: ~40% (cálculo ERC, métricas de concentración, comparativa internacional).
- Tiempo estimado: 1/3 a 1/2 del tiempo del paper 1.

---

## 7. Decisiones pendientes

- [ ] ¿Confirmar que el derivado es risk parity (no robust optimization)?
- [ ] ¿Comparar también con variants constreñidas (capped ERC)?
- [ ] ¿Incluir la comparativa con otros índices LATAM o dejarla para un tercer paper?
- [ ] ¿Se publica como paper independiente o como extensión del paper 1 (mismo título con "— Parte II")?
