# Paper 1 — Propuesta: Backtest de estrategias de construcción de portafolios en el IPSA (2010-2024)

> Documento de propuesta. 2-3 páginas. No es el paper, es el brief que define alcance, estructura, figuras, citas y supuestos antes de escribir. Se revisa y ajusta antes de partir a implementación.

---

## 1. Título tentativo

> **Estrategias de construcción de portafolios en un mercado concentrado: backtest de 14 años sobre el IPSA (2010-2024)**

Variantes más cortas si se quiere menos barroco:
- "Backtest comparativo de estrategias de portafolio en el IPSA, 2010-2024"
- "Rendimiento, riesgo y composición: 14 años de construcción de portafolios en el IPSA"

---

## 2. Abstract (borrador, ~150 palabras)

> Se comparan seis estrategias de construcción de portafolios —equal-weight, cap-weighted (IPSA), minimum-variance, maximum-Sharpe, risk-parity (ERC) y maximum-diversification— sobre el universo accionario chileno del IPSA entre 2010 y 2024. El backtest emplea ventanas de estimación rolling de 252 días, rebalanceo mensual y supuestos explícitos de costos de transacción. Se reportan métricas de retorno-riesgo (Sharpe, Sortino, Calmar, max drawdown, time-under-water, turnover) y se analiza la estabilidad temporal de la jerarquía de estrategias. Los resultados muestran que (i) las estrategias naive igualan o superan a las optimizadas en el período completo, (ii) la jerarquía es inestable y rota con el régimen, y (iii) la concentración del benchmark chileno (top-5 ≈ 30% del peso) condiciona severamente el desempeño de risk-parity. Se discute la implicancia para inversionista retail e institucional en mercados emergentes concentrados.

---

## 3. Preguntas de investigación

1. **¿Qué estrategia de construcción de portafolios entrega el mejor ratio retorno-riesgo ajustado por drawdown en el IPSA 2010-2024?**
2. **¿La jerarquía de estrategias es estable a lo largo del tiempo, o cambia con el régimen de mercado (pre-2014 estable, 2014-2019 moderado, 2019-2021 crisis, 2022-2024 post-crisis)?**
3. **¿Cómo afecta la concentración del benchmark chileno (top-5 ≈ 30% del peso) al desempeño relativo de risk-parity frente a cap-weighted?**
4. **¿Qué tan robustos son los resultados a cambios en la ventana de estimación y a la inclusión de costos de transacción?**

---

## 4. Estructura del paper

### 4.1. Resumen (1 página, sin figura)
### 4.2. Introducción (2-3 páginas)
- Motivación: la construcción de portafolios en mercados emergentes concentrados.
- Vacío: la literatura de comparación de estrategias se concentra en EE.UU. y Europa; Chile es caso de estudio interesante por la concentración del benchmark y la alta proporción de commodities.
- Preguntas de investigación.
- Aporte: evidencia local rigurosa con datos públicos.

### 4.3. Marco teórico (2-3 páginas)
- Markowitz (1952) — frontera eficiente.
- Sharpe (1964) — ratio de retorno-riesgo.
- Choueifaty & Coignard (2008) — maximum diversification ratio.
- Qian (2005) — risk parity / equal risk contribution.
- Michaud (1989) y Ledoit-Wolf (2003) — robustez.
- Literatura local: documentos de trabajo BCCh sobre estructura del IPSA.

### 4.4. Datos y metodología (2-3 páginas)
- Universo: 30 acciones del IPSA, datos diarios 2010-01-01 a 2024-12-31.
- Fuente: Yahoo Finance vía `yfinance` (precios ajustados por dividendos y splits).
- Validación cruzada:对比 con cartola oficial de la Bolsa de Santiago.
- Ventana de estimación rolling: 252 días.
- Frecuencia de rebalanceo: mensual.
- Costos de transacción: 10 bps por rebalanceo (assumption declarado).
- Métricas evaluadas (ver §6).
- Subperíodos para análisis de régimen:
  - 2010-2013: post-subprime, commodities altos.
  - 2014-2018: reforma tributaria 2014, desaceleración.
  - 2019-2021: estallido social oct-2019, COVID 2020.
  - 2022-2024: guerra, ciclo de alza TPM, normalización.

### 4.5. Resultados (4-5 páginas)
- 5.1 Desempeño en el período completo (tabla de métricas, equity curves, drawdown chart).
- 5.2 Estabilidad temporal de la jerarquía (rolling Sharpe, bump chart de ranking).
- 5.3 Composición de los portafolios (treemaps lado a lado, streamgraph de pesos).
- 5.4 Perfiles multidimensionales (radar).
- 5.5 Distribución de retornos por estrategia (violin/box).
- 5.6 Contribución al retorno (waterfall).
- 5.7 Sensibilidad a la ventana de estimación y costos (apéndice, no central).

### 4.6. Discusión (2-3 páginas)
- Por qué las estrategias naive no son "subóptimas" en mercados concentrados.
- La ilusión de optimalidad de Markowitz en muestras pequeñas.
- La concentración del IPSA como ventaja del cap-weighted (no se puede diversificar lo que no existe).
- Implicaciones para el inversionista retail chileno.
- Implicaciones para AFPs y administradoras (que suelen usar variants de cap-weighted).

### 4.7. Conclusiones (1 página)
- 3-5 hallazgos principales.
- 3-5 limitaciones declaradas.
- Trabajo futuro: extensión con Black-Litterman (paper 2 derivado), expansión del universo a bonos y dólar.

### 4.8. Apéndice
- A: fórmulas exactas de cada estrategia, parámetros.
- B: sensibilidad (ventana 126 / 504 días, costos 0% / 30 bps).
- C: lista completa de activos con fechas de entrada/salida del IPSA.

---

## 5. Universo de estrategias a comparar

| # | Estrategia | Descripción | Referencia principal |
|---|---|---|---|
| E1 | **Equal-weight (1/N)** | Mismo peso a todos los activos | DeMiguel, Garlappi & Uppal (2009) |
| E2 | **Cap-weighted (IPSA)** | Pesos según capitalización bursátil | Benchmark natural |
| E3 | **Minimum variance** | Minimiza σ² del portafolio | Markowitz (1952) |
| E4 | **Maximum Sharpe (tangente)** | Maximiza (μ − rf)/σ | Markowitz (1952) |
| E5 | **Risk parity (ERC)** | Igual contribución al riesgo | Qian (2005) |
| E6 | **Maximum diversification** | Maximiza diversification ratio | Choueifaty & Coignard (2008) |

> **Opcional (no priorizado):** E7 = Black-Litterman con equilibrio de mercado + views nulas (degradaría a E2). Si se incluye, se discute en el paper 2 derivado.

---

## 6. Métricas a reportar

| Métrica | Fórmula conceptual | Lectura |
|---|---|---|
| Retorno anualizado | media geométrica diaria × 252 | Ganancia esperada por año |
| Volatilidad anualizada | σ diaria × √252 | Dispersión del retorno |
| Sharpe ratio | (R − rf) / σ | Retorno-riesgo total |
| Sortino ratio | (R − rf) / σ_downside | Retorno-riesgo de pérdida |
| Maximum drawdown | max caída peak-to-trough | Peor pérdida acumulada |
| Calmar ratio | R anualizado / |max DD| | Retorno por unidad de drawdown |
| Time under water (días) | Tiempo para recuperar el peak | Resiliencia |
| % meses positivos | count(retorno_mensual > 0) / total | Consistencia |
| Turnover anualizado | suma(|Δw|) / 2 / 12 | Costo de rebalancear |

---

## 7. Figuras del paper (10 principales + 3 complementarias)

### 7.1 Principales

| # | Figura | Tipo gráfico | Rol analítico |
|---|---|---|---|
| F1 | Tabla-resumen de métricas por estrategia | Tabla HTML | "Hechos" del paper |
| F2 | Equity curves (base 100, 2010-2024) | Línea (6 series) | Trayectoria comparada |
| F3 | Drawdown chart superpuesto | Área (6 series, α 0.4) | Resiliencia visual |
| F4 | Rolling Sharpe 12-meses | Línea (6 series) | Estabilidad temporal |
| F5 | Treemaps lado a lado (cap-weighted vs max-Sharpe final) | Treemap | Reorganización estructural |
| F6 | Radar de perfiles (8 dimensiones) | Radar/Polar | Trade-offs multidimensionales |
| F7 | Waterfall de contribución al retorno del ganador | Waterfall | Atribución |
| F8 | Bump chart de ranking de Sharpe rolling | Bump chart | Cambios de jerarquía |
| F9 | Ridgeline de retornos mensuales por estrategia | Ridgeline | Distribuciones comparadas |
| F10 | Heatmap de correlaciones (al cierre del período) | Heatmap ordenado | Diversificación |

### 7.2 Complementarias (apéndice o notas)

| # | Figura | Tipo gráfico | Rol |
|---|---|---|---|
| C1 | Rolling vol por estrategia | Línea | Complemento de F4 |
| C2 | Matriz de transición (% meses que cada estrategia fue la mejor) | Heatmap pequeño | Resumen de F8 |
| C3 | Streamgraph de pesos del portafolio max-Sharpe en el tiempo | Streamgraph | Drift del portafolio |

---

## 8. Datos y fuentes (citas explícitas)

### 8.1 Datos primarios

| Dato | Fuente | URL/Referencia | Cita sugerida |
|---|---|---|---|
| Precios diarios IPSA 2010-2024 | Yahoo Finance | `yfinance` API, descarga documentada con timestamp | "precios ajustados por dividendos y splits, vía `yfinance`, descargados el [FECHA]" |
| Composición actual del IPSA | Bolsa de Santiago | [cartola oficial](https://www.bolsadesantiago.com/) | "Bolsa de Santiago, cartola oficial del IPSA" |
| Validación cruzada precios | Bolsa de Santiago / RiskAmerica | Series oficiales | Comparación in-line en §4 |
| TPM diaria | Banco Central de Chile | [si3.bcentral.cl](https://si3.bcentral.cl/) | "BCCh, base de datos estadísticos" |
| IPC mensual | INE | [ine.cl](https://www.ine.cl/) | "INE, Índice de Precios al Consumidor" |
| Tipo de cambio USD/CLP | BCCh | si3.bcentral.cl | "BCCh, dólar observado" |
| Precio del cobre | Cochilco | [cochilco.cl](https://www.cochilco.cl/) | "Cochilco, precio promedio mensual del cobre" |
| IPoM por trimestre | BCCh | [bcentral.cl/publicaciones](https://www.bcentral.cl/publicaciones) | Cita explícita: "BCCh, IPoM [mes] [año]" |
| Crisis 2014 (reforma tributaria) | BCCh IPoM sep-2014 | — | "BCCh, IPoM sep-2014" |
| Estallido social 2019 | BCCh IPoM dic-2019 | — | "BCCh, IPoM dic-2019" |
| COVID 2020 | BCCh IPoM mar-2020, jun-2020 | — | "BCCh, IPoM [trimestre] 2020" |
| Guerra 2022 / ciclo TPM | BCCh IPoM 2022 | — | "BCCh, IPoM 2022 (varios trimestres)" |
| Bonos BCP/BCU (referencia) | BCCh | si3.bcentral.cl | "BCCh, curva de rendimientos" |

### 8.2 Literatura académica citada

- Markowitz, H. (1952). *Portfolio Selection*. Journal of Finance, 7(1), 77-91.
- Sharpe, W. F. (1964). *Capital Asset Prices: A Theory of Market Equilibrium*. Journal of Finance, 19(3), 425-442.
- Black, F. & Litterman, R. (1992). *Asset Allocation: Combining Investor Views with Market Equilibrium*. Goldman Sachs Fixed Income Research.
- Ledoit, O. & Wolf, M. (2003). *Improved Estimation of the Covariance Matrix of Stock Returns Based on Shrinkage*. Journal of Portfolio Management, 29(4).
- Michaud, R. (1989). *The Markowitz Optimization Enigma: Is 'Optimized' Optimal?*. Financial Analysts Journal, 45(1).
- Qian, E. (2005). *Risk Parity Portfolios: Efficient Portfolios Through True Diversification*. PanAgora Asset Management.
- Choueifaty, Y. & Coignard, Y. (2008). *Toward Maximum Diversification*. Journal of Portfolio Management, 35(1).
- DeMiguel, V., Garlappi, L. & Uppal, R. (2009). *Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?*. Review of Financial Studies, 22(5).
- Rockafellar, R. & Uryasev, S. (2000). *Optimization of Conditional Value-at-Risk*. Journal of Risk, 2(3).
- Ang, A. & Chen, J. (2002). *Asymmetric Correlations of Equity Portfolios*. Journal of Financial Economics, 63(3).
- Longin, F. & Solnik, B. (2001). *Extreme Correlation of International Equity Markets*. Journal of Finance, 56(2).
- BCCh, varios. *Documentos de Trabajo* sobre estructura del mercado accionario chileno.

### 8.3 Literatura local / institucional

- ABIF (Asociación de Bancos e Instituciones Financieras), informes anuales de gestión.
- CMF, informes de deuda y participación accionaria.
- USS-Equifax, informes de deuda morosa (referencia comparativa, no central).
- Estudios de la Facultad de Economía y Negocios de la Universidad de Chile sobre el IPSA.

---

## 9. Supuestos y limitaciones declaradas

1. **Universo concentrado:** el IPSA tiene 30 acciones; las optimizaciones tienen alta sensibilidad a los inputs (problema conocido de Michaud).
2. **Sesgo de supervivencia:** se usan sólo las acciones actualmente en el IPSA, lo que puede sobreestimar el desempeño de las estrategias que sobreviven.
3. **Costos de transacción:** assumption de 10 bps por rebalanceo, no modelamos spreads ni impacto.
4. **Estimación de retornos esperados:** se usa media histórica rolling; el paper reconoce que esto es el talón de Aquiles de Markowitz y se discute en §6.
5. **No se considera apalancamiento ni short-selling:** los portafolios son long-only.
6. **No se incluyen costos fiscales ni de custodia.**
7. **Backtest ≠ predicción:** el desempeño pasado no garantiza resultados futuros; se declara explícitamente.
8. **Tamaño muestral:** 14 años × 252 días ≈ 3.528 observaciones, suficiente para métricas estándar pero insuficiente para eventos extremos robustos.

---

## 10. Decisiones de implementación (resumen, ver `00_PALETA_Y_DECISIONES_VISUALES.md`)

| # | Decisión | Default |
|---|---|---|
| 1 | Stack del HTML | Vanilla JS + D3 v7, sin build, sin `npm install` |
| 2 | Datos embebidos en `js/data.js` | Sí, no fetches |
| 3 | Convención de idioma | es-CL, paper en español |
| 4 | Paleta | turquoise/grey/navy (5 colores) + rojo apagado funcional para pérdidas |
| 5 | Tipografía | Inter vía Google Fonts |
| 6 | Bloque de autor | 3 botones (LinkedIn/Email/WhatsApp), sin títulos académicos |
| 7 | Figuras no convencionales | 11 tipos habilitados (ver doc de decisiones) |
| 8 | Formato | Paper markdown + HTML estático como "supplementary" interactivo |

---

## 11. Próximos pasos (propuestos)

Una vez aprobada esta propuesta:

1. **Crear estructura de archivos** del proyecto nuevo (sin tocar el código actual hasta validar).
2. **Implementar el pipeline Python** que descarga precios del IPSA y exporta a JSON embebido en `data.js`.
3. **Calcular las 6 estrategias** sobre los 14 años con ventana rolling.
4. **Escribir el paper** con las figuras pre-calculadas.
5. **Construir el HTML estático** con las figuras como SVG interactivos.
6. **Revisar citas y referencias** una por una.
7. **Releer el paper entero** con ojos de "alguien que lo va a citar" — verificar cada afirmación tiene fuente.

---

## 12. Decisiones pendientes de Miguel

- [ ] ¿Título del paper? (3 variantes propuestas en §1)
- [ ] ¿Convención de color para ganancia/pérdida? (teal/rojo vs verde/rojo vs monocromático)
- [ ] ¿Mantener el paper 2 derivado = risk parity, o cambiar a robust optimization?
- [ ] ¿Período 2010-2024 completo, o recortar (ej. 2014-2024 post-reforma tributaria)?
- [ ] ¿Se incluye E7 (Black-Litterman) en este paper o se deja para el derivado?
- [ ] ¿El paper se publica en español, en inglés, o bilingüe?
