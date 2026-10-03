/**
 * js/figures.js
 *
 * Renderers D3.js v7 para las figuras del paper.
 * API expuesta en window.OC.figures.
 *
 * Cada función toma (selector CSS, datos, opciones) y renderiza un SVG inline
 * con interactividad mínima (hover, tooltip básico).
 *
 * @namespace OC.figures
 * @author Miguel Ortiz C.
 * @license MIT
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || !window.OC) {
    console.error('[OC.figures] window.OC no disponible.');
    return;
  }

  if (typeof d3 === 'undefined') {
    console.error('[OC.figures] D3 no disponible. ¿Cargaste el CDN?');
    return;
  }

  // Tokens de color desde CSS para que el SVG se vea consistente
  const COLORS = {
    ink: '#081630',
    teal: '#3B878C',
    tealDeep: '#125358',
    tealSoft: '#D9E7E8',
    grey: '#C2C3C5',
    paper: '#EBEBED',
    paperDeep: '#DCDDDF',
    loss: '#A04545',
    lossSoft: '#F0DCDA',
  };

  // Escala de color divergente para el heatmap (teal → blanco → loss)
  function divergingScale() {
    return d3.scaleDiverging()
      .domain([-1, 0, 1])
      .range([COLORS.teal, '#FFFDFC', COLORS.loss])
      .interpolator(d3.interpolateRgbBasis([COLORS.teal, '#FFFDFC', COLORS.loss]));
  }

  // -------------------------------------------------------------------------
  // F1 — Equity curve + drawdown combinado
  // -------------------------------------------------------------------------

  function equityAndDrawdown(selector, equity, options) {
    options = options || {};
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = '';

    const containerWidth = el.clientWidth || 900;
    const margin = { top: 16, right: 24, bottom: 36, left: 56 };
    const width = containerWidth - margin.left - margin.right;
    const height = (options.height || 280) - margin.top - margin.bottom;

    const svg = d3.select(el).append('svg')
      .attr('viewBox', `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
      .attr('preserveAspectRatio', 'xMinYMin meet')
      .style('width', '100%')
      .style('height', 'auto');

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const parseDate = d3.timeParse('%Y-%m-%d');
    const eqData = equity.map(function (d) { return { date: parseDate(d.date), value: d.value }; });
    const dd = window.OC.analytics.drawdown(equity);
    const ddData = dd.map(function (d) { return { date: parseDate(d.date), value: d.value }; });

    const x = d3.scaleTime().domain(d3.extent(eqData, function (d) { return d.date; })).range([0, width]);
    const yLeft = d3.scaleLinear().domain([d3.min(ddData, function (d) { return d.value; }) * 1.05, 1]).range([height, 0]);
    const yRight = d3.scaleLinear().domain([0, d3.max(eqData, function (d) { return d.value; }) * 1.05]).range([height, 0]);

    // Ejes
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%Y')))
      .selectAll('text').style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', COLORS.tealDeep);

    g.append('g')
      .call(d3.axisLeft(yLeft).ticks(5).tickFormat(d3.format('.0%')).tickSize(-width))
      .selectAll('text').style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', COLORS.tealDeep);
    g.selectAll('.tick line').attr('stroke', COLORS.grey).attr('stroke-opacity', 0.4);
    g.select('.domain').attr('stroke', COLORS.grey);

    // Drawdown area (rojo, debajo de 1)
    const ddArea = d3.area()
      .x(function (d) { return x(d.date); })
      .y0(yLeft(0))
      .y1(function (d) { return yLeft(d.value); })
      .curve(d3.curveMonotoneX);
    g.append('path')
      .datum(ddData)
      .attr('fill', COLORS.lossSoft)
      .attr('opacity', 0.7)
      .attr('d', ddArea);

    // Drawdown line (loss)
    const ddLine = d3.line()
      .x(function (d) { return x(d.date); })
      .y(function (d) { return yLeft(d.value); })
      .curve(d3.curveMonotoneX);
    g.append('path')
      .datum(ddData)
      .attr('fill', 'none')
      .attr('stroke', COLORS.loss)
      .attr('stroke-width', 1.2)
      .attr('opacity', 0.8)
      .attr('d', ddLine);

    // Equity line (teal)
    const eqLine = d3.line()
      .x(function (d) { return x(d.date); })
      .y(function (d) { return yRight(d.value); })
      .curve(d3.curveMonotoneX);
    g.append('path')
      .datum(eqData)
      .attr('fill', 'none')
      .attr('stroke', COLORS.teal)
      .attr('stroke-width', 2)
      .attr('d', eqLine);

    // Etiquetas
    g.append('text').attr('x', 8).attr('y', 12).attr('font-size', 11).attr('font-family', 'JetBrains Mono, monospace').attr('fill', COLORS.teal).text('Equity (base 100)');
    g.append('text').attr('x', 8).attr('y', 26).attr('font-size', 11).attr('font-family', 'JetBrains Mono, monospace').attr('fill', COLORS.loss).text('Drawdown');

    // Hover crosshair
    const focus = g.append('g').style('display', 'none');
    focus.append('line').attr('class', 'crosshair').attr('y1', 0).attr('y2', height).attr('stroke', COLORS.ink).attr('stroke-dasharray', '3 3').attr('stroke-width', 1);
    focus.append('circle').attr('class', 'dot-eq').attr('r', 4).attr('fill', COLORS.teal);
    focus.append('circle').attr('class', 'dot-dd').attr('r', 4).attr('fill', COLORS.loss);
    const tip = d3.select(el).append('div').style('position', 'absolute').style('background', COLORS.ink).style('color', '#FFFDFC')
      .style('padding', '6px 10px').style('border-radius', '4px').style('font-family', 'JetBrains Mono, monospace').style('font-size', '11px')
      .style('pointer-events', 'none').style('opacity', 0);

    const bisect = d3.bisector(function (d) { return d.date; }).left;
    svg.append('rect').attr('width', width).attr('height', height).attr('transform', `translate(${margin.left},${margin.top})`)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mouseover', function () { focus.style('display', null); tip.style('opacity', 1); })
      .on('mouseout', function () { focus.style('display', 'none'); tip.style('opacity', 0); })
      .on('mousemove', function (event) {
        const [mx] = d3.pointer(event, this);
        const x0 = x.invert(mx - margin.left);
        const i = bisect(eqData, x0, 1);
        const d0 = eqData[i - 1], d1 = eqData[i] || d0;
        const d = (x0 - d0.date) > (d1.date - x0) ? d1 : d0;
        const ddPoint = ddData[i - 1] || ddData[0];
        focus.select('.crosshair').attr('x1', x(d.date)).attr('x2', x(d.date));
        focus.select('.dot-eq').attr('cx', x(d.date)).attr('cy', yRight(d.value));
        focus.select('.dot-dd').attr('cx', x(d.date)).attr('cy', yLeft(ddPoint.value));
        const dateStr = d3.timeFormat('%Y-%m-%d')(d.date);
        tip.html(`<strong>${dateStr}</strong><br/>Equity: ${d.value.toFixed(2)}<br/>DD: ${(ddPoint.value * 100).toFixed(1)}%`)
          .style('left', (x(d.date) + margin.left + 12) + 'px')
          .style('top', (margin.top + 8) + 'px');
      });
  }

  // -------------------------------------------------------------------------
  // F2 — Rolling vol 252d
  // -------------------------------------------------------------------------

  function rollingVol(selector, ticker) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = '';
    const data = window.OC.analytics.rollingVol(ticker, 252)
      .filter(function (d) { return d.value !== null; })
      .map(function (d) { return { date: d3.timeParse('%Y-%m-%d')(d.date), value: d.value }; });

    const containerWidth = el.clientWidth || 900;
    const margin = { top: 16, right: 24, bottom: 36, left: 56 };
    const width = containerWidth - margin.left - margin.right;
    const height = 220 - margin.top - margin.bottom;

    const svg = d3.select(el).append('svg')
      .attr('viewBox', `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
      .attr('preserveAspectRatio', 'xMinYMin meet')
      .style('width', '100%').style('height', 'auto');

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleTime().domain(d3.extent(data, function (d) { return d.date; })).range([0, width]);
    const y = d3.scaleLinear().domain([0, d3.max(data, function (d) { return d.value; }) * 1.1]).range([height, 0]);

    g.append('g').attr('transform', `translate(0,${height})`).call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%Y')))
      .selectAll('text').style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', COLORS.tealDeep);
    g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(function (d) { return (d * 100).toFixed(0) + '%'; }))
      .selectAll('text').style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', COLORS.tealDeep);
    g.selectAll('.tick line').attr('stroke', COLORS.grey).attr('stroke-opacity', 0.4);
    g.select('.domain').attr('stroke', COLORS.grey);

    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', COLORS.teal)
      .attr('stroke-width', 1.6)
      .attr('d', d3.line().x(function (d) { return x(d.date); }).y(function (d) { return y(d.value); }).curve(d3.curveMonotoneX));

    g.append('text').attr('x', 8).attr('y', 12).attr('font-size', 11).attr('font-family', 'JetBrains Mono, monospace').attr('fill', COLORS.teal).text(`Vol anualizada rolling 252d · ${ticker}`);
  }

  // -------------------------------------------------------------------------
  // F3 — Distribución de retornos mensuales (violin custom)
  // -------------------------------------------------------------------------

  function monthlyReturnsViolin(selector, data) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = '';
    const values = data.map(function (d) { return d.ret; }).sort(function (a, b) { return a - b; });
    if (values.length < 2) return;

    // KDE manual
    const n = values.length;
    const min = values[0], max = values[n - 1];
    const bandwidth = (max - min) * 0.4;
    function kde(x) {
      let s = 0;
      for (let i = 0; i < n; i++) {
        const u = (x - values[i]) / bandwidth;
        s += Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
      }
      return s / (n * bandwidth);
    }
    const samples = 60;
    const pts = [];
    for (let i = 0; i < samples; i++) {
      const x = min + (max - min) * (i / (samples - 1));
      pts.push({ x: x, y: kde(x) });
    }
    const yMax = d3.max(pts, function (d) { return d.y; }) || 1;

    const containerWidth = el.clientWidth || 900;
    const margin = { top: 16, right: 24, bottom: 36, left: 56 };
    const width = containerWidth - margin.left - margin.right;
    const height = 220 - margin.top - margin.bottom;

    const svg = d3.select(el).append('svg')
      .attr('viewBox', `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
      .style('width', '100%').style('height', 'auto');

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain([min, max]).range([0, width]);
    const y = d3.scaleLinear().domain([0, yMax]).range([height, 0]);

    g.append('g').attr('transform', `translate(0,${height})`).call(d3.axisBottom(x).ticks(8).tickFormat(d3.format('.0%')))
      .selectAll('text').style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', COLORS.tealDeep);
    g.selectAll('.tick line').attr('stroke', COLORS.grey).attr('stroke-opacity', 0.4);
    g.select('.domain').attr('stroke', COLORS.grey);

    // Eje y invisible (sólo el violin importa)
    g.append('g').call(d3.axisLeft(y).ticks(3).tickFormat(function (d) { return ''; }));

    // Línea cero
    g.append('line')
      .attr('x1', x(0)).attr('x2', x(0))
      .attr('y1', 0).attr('y2', height)
      .attr('stroke', COLORS.grey).attr('stroke-dasharray', '4 3').attr('stroke-width', 1);

    // Violin (simétrico arriba/abajo)
    const halfWidth = 0.45; // % del eje y
    const violin = d3.area()
      .x(function (d) { return x(d.x); })
      .y0(function (d) { return y(d.y / yMax * (1 - halfWidth)); })
      .y1(function (d) { return y(d.y / yMax * (1 + halfWidth)); })
      .curve(d3.curveCatmullRom);
    g.append('path')
      .datum(pts)
      .attr('fill', COLORS.tealSoft)
      .attr('stroke', COLORS.teal)
      .attr('stroke-width', 1.5)
      .attr('d', violin);

    // Cuartiles como líneas horizontales
    const q = function (p) { return values[Math.floor(p * n)]; };
    [0.25, 0.5, 0.75].forEach(function (p) {
      const v = q(p);
      const widthAt = (yMax > 0 ? y(kde(v)) / yMax * (1 + halfWidth) - y(kde(v)) / yMax * (1 - halfWidth) : 0) * height;
      g.append('line')
        .attr('x1', x(v) - widthAt / 2).attr('x2', x(v) + widthAt / 2)
        .attr('y1', height / 2).attr('y2', height / 2)
        .attr('stroke', COLORS.ink).attr('stroke-width', 1.5);
    });

    g.append('text').attr('x', 8).attr('y', 12).attr('font-size', 11).attr('font-family', 'JetBrains Mono, monospace').attr('fill', COLORS.teal).text(`Distribución retornos mensuales · IPSA · n=${n}`);
  }

  // -------------------------------------------------------------------------
  // F4 — Heatmap de correlaciones con clustering
  // -------------------------------------------------------------------------

  function correlationHeatmap(selector, tickers) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = '';
    const corr = window.OC.analytics.correlationMatrix(tickers);
    const order = window.OC.analytics.clusterOrder(tickers, corr);
    const n = tickers.length;

    const size = 14;
    const containerWidth = el.clientWidth || 900;
    const margin = { top: 60, right: 16, bottom: 16, left: 60 };
    const width = Math.min(containerWidth, n * size + margin.left + margin.right) - margin.left - margin.right;
    const cellSize = width / n;
    const height = width;

    const svg = d3.select(el).append('svg')
      .attr('viewBox', `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
      .style('width', '100%').style('height', 'auto');

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
    const color = divergingScale();

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        const ii = order[i], jj = order[j];
        const v = corr.matrix[ii][jj];
        g.append('rect')
          .attr('x', i * cellSize)
          .attr('y', j * cellSize)
          .attr('width', cellSize)
          .attr('height', cellSize)
          .attr('fill', color(v))
          .attr('stroke', COLORS.paper)
          .attr('stroke-width', 0.5)
          .append('title')
          .text(`${tickers[ii]} × ${tickers[jj]}: ${v.toFixed(2)}`);
      }
    }

    // Labels en los ejes
    g.selectAll('.row-label')
      .data(order)
      .enter().append('text')
      .attr('x', -6).attr('y', function (d, i) { return i * cellSize + cellSize / 2 + 3; })
      .attr('text-anchor', 'end')
      .style('font-family', 'JetBrains Mono, monospace').style('font-size', '8px').style('fill', COLORS.tealDeep)
      .text(function (d) { return tickers[d].replace('.SN', ''); });

    g.selectAll('.col-label')
      .data(order)
      .enter().append('text')
      .attr('transform', function (d, i) { return `translate(${i * cellSize + cellSize / 2},-6) rotate(-45)`; })
      .attr('text-anchor', 'start')
      .style('font-family', 'JetBrains Mono, monospace').style('font-size', '8px').style('fill', COLORS.tealDeep)
      .text(function (d) { return tickers[d].replace('.SN', ''); });
  }

  // -------------------------------------------------------------------------
  // F5 — Treemap de capitalización
  // -------------------------------------------------------------------------

  function treemap(selector, data) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = '';

    const root = d3.hierarchy(data)
      .sum(function (d) { return d.value || 0; })
      .sort(function (a, b) { return b.value - a.value; });

    const containerWidth = el.clientWidth || 900;
    const height = 380;

    d3.treemap()
      .size([containerWidth, height])
      .paddingOuter(4)
      .paddingTop(20)
      .paddingInner(2)
      .round(true)(root);

    const svg = d3.select(el).append('svg')
      .attr('viewBox', `0 0 ${containerWidth} ${height}`)
      .style('width', '100%').style('height', 'auto');

    const colorScale = d3.scaleOrdinal()
      .domain(root.children ? root.children.map(function (d) { return d.data.name; }) : [])
      .range(d3.schemeTableau10.map(function (c, i) {
        // Tintar con teal/grey
        if (i === 0) return COLORS.teal;
        if (i === 1) return COLORS.tealDeep;
        return d3.interpolateLab(COLORS.grey, COLORS.ink)(i / 8);
      }));

    // Sectores
    svg.selectAll('.sector-rect')
      .data(root.children || [])
      .enter().append('rect')
      .attr('x', function (d) { return d.x0; })
      .attr('y', function (d) { return d.y0; })
      .attr('width', function (d) { return d.x1 - d.x0; })
      .attr('height', function (d) { return d.y1 - d.y0; })
      .attr('fill', function (d) { return colorScale(d.data.name); })
      .attr('opacity', 0.18);

    // Borders
    svg.selectAll('.sector-border')
      .data(root.children || [])
      .enter().append('rect')
      .attr('x', function (d) { return d.x0; })
      .attr('y', function (d) { return d.y0; })
      .attr('width', function (d) { return d.x1 - d.x0; })
      .attr('height', function (d) { return d.y1 - d.y0; })
      .attr('fill', 'none')
      .attr('stroke', function (d) { return colorScale(d.data.name); })
      .attr('stroke-width', 1.5);

    // Labels de sector
    svg.selectAll('.sector-label')
      .data(root.children || [])
      .enter().append('text')
      .attr('x', function (d) { return d.x0 + 6; })
      .attr('y', function (d) { return d.y0 + 14; })
      .style('font-family', 'JetBrains Mono, monospace').style('font-size', '11px').style('font-weight', '600')
      .style('fill', COLORS.ink)
      .text(function (d) { return d.data.name; });

    // Tickers (leaf nodes)
    svg.selectAll('.leaf')
      .data(root.leaves())
      .enter().append('g')
      .attr('class', 'leaf')
      .attr('transform', function (d) { return `translate(${d.x0},${d.y0})`; })
      .each(function (d) {
        const w = d.x1 - d.x0, h = d.y1 - d.y0;
        if (w < 30 || h < 16) return;
        const g = d3.select(this);
        g.append('rect')
          .attr('width', w).attr('height', h)
          .attr('fill', function () {
            const parent = d.parent;
            return colorScale(parent.parent ? parent.parent.data.name : parent.data.name);
          })
          .attr('opacity', 0.55)
          .attr('stroke', COLORS.paper)
          .attr('stroke-width', 1);
        g.append('text')
          .attr('x', 4).attr('y', 12)
          .style('font-family', 'JetBrains Mono, monospace').style('font-size', '10px').style('fill', '#FFFDFC')
          .style('font-weight', '600')
          .text(d.data.name.replace('.SN', ''));
      })
      .append('title')
      .text(function (d) {
        const sector = d.parent.parent ? d.parent.parent.data.name : d.parent.data.name;
        return `${sector} · ${d.data.name} · cap: ${(d.value / 1e9).toFixed(1)}B CLP`;
      });
  }

  // -------------------------------------------------------------------------
  // F6 — Tabla de métricas por activo
  // -------------------------------------------------------------------------

  function metricsTable(selector, metrics) {
    const el = document.querySelector(selector);
    if (!el) return;
    const valid = metrics.filter(function (m) { return m.hasData; });
    if (valid.length === 0) { el.innerHTML = '<tr><td colspan="8">Sin datos</td></tr>'; return; }
    // Calcular mejor/peor por columna numérica
    const cols = ['annRet', 'annVol', 'sharpe', 'sortino', 'calmar', 'pctPositive'];
    const colMax = {};
    const colMin = {};
    cols.forEach(function (c) {
      colMax[c] = Math.max.apply(null, valid.map(function (m) { return m[c]; }));
      colMin[c] = Math.min.apply(null, valid.map(function (m) { return m[c]; }));
    });
    colMax.maxDD = Math.max.apply(null, valid.map(function (m) { return m.maxDD; })); // menos negativo es mejor
    colMin.maxDD = Math.min.apply(null, valid.map(function (m) { return m.maxDD; })); // más negativo es peor

    // Ordenar por Sharpe descendente
    const sorted = valid.slice().sort(function (a, b) { return b.sharpe - a.sharpe; });

    const fmtPct = function (v) { return (v * 100).toFixed(1) + '%'; };
    const fmtNum = function (v) { return v.toFixed(2); };

    const rows = sorted.map(function (m) {
      const cls = function (val, col) {
        if (col === 'maxDD') {
          if (val === colMax.maxDD) return 'best';
          if (val === colMin.maxDD) return 'loss';
          return '';
        }
        if (val === colMax[col]) return 'best';
        if (val === colMin[col]) return 'loss';
        return '';
      };
      return '<tr>'
        + '<td><code>' + m.ticker.replace('.SN', '') + '</code></td>'
        + '<td class="' + cls(m.annRet, 'annRet') + '">' + fmtPct(m.annRet) + '</td>'
        + '<td class="' + cls(m.annVol, 'annVol') + '">' + fmtPct(m.annVol) + '</td>'
        + '<td class="' + cls(m.sharpe, 'sharpe') + '">' + fmtNum(m.sharpe) + '</td>'
        + '<td class="' + cls(m.sortino, 'sortino') + '">' + fmtNum(m.sortino) + '</td>'
        + '<td class="' + cls(m.maxDD, 'maxDD') + '">' + fmtPct(m.maxDD) + '</td>'
        + '<td class="' + cls(m.calmar, 'calmar') + '">' + fmtNum(m.calmar) + '</td>'
        + '<td class="' + cls(m.pctPositive, 'pctPositive') + '">' + fmtPct(m.pctPositive) + '</td>'
        + '</tr>';
    }).join('');
    el.innerHTML = rows;
  }

  // -------------------------------------------------------------------------
  // F7 — Tabla de retornos por subperíodo
  // -------------------------------------------------------------------------

  function regimeTable(selector, regimes) {
    const el = document.querySelector(selector);
    if (!el) return;
    const maxRet = Math.max.apply(null, regimes.map(function (r) { return r.ret; }));
    const minRet = Math.min.apply(null, regimes.map(function (r) { return r.ret; }));
    const rows = regimes.map(function (r) {
      const cls = r.ret === maxRet ? 'best' : (r.ret === minRet ? 'loss' : '');
      return '<tr>'
        + '<td>' + r.name + '</td>'
        + '<td>' + r.days + ' días</td>'
        + '<td class="' + cls + '">' + (r.ret * 100).toFixed(1) + '%</td>'
        + '</tr>';
    }).join('');
    el.innerHTML = rows;
  }

  // -------------------------------------------------------------------------
  // F8 — Stat values del summary IPSA en el §4
  // -------------------------------------------------------------------------

  function ipsaStatCard(selector, summary) {
    const el = document.querySelector(selector);
    if (!el) return;
    const fmt = function (v, d) { return d === 0 ? '0%' : (v * 100).toFixed(1) + '%'; };
    const fmtN = function (v) { return v.toFixed(2); };
    const items = [
      { value: fmt(summary.annRet), desc: 'Retorno anualizado', cls: '' },
      { value: fmt(summary.annVol), desc: 'Volatilidad anualizada', cls: 'is-ink' },
      { value: fmtN(summary.sharpe), desc: 'Ratio de Sharpe', cls: '' },
      { value: fmt(summary.maxDD), desc: 'Maximum drawdown', cls: 'is-loss' },
      { value: fmtN(summary.calmar), desc: 'Ratio de Calmar', cls: '' },
      { value: fmt(summary.pctPositive), desc: 'Meses con retorno > 0', cls: '' },
    ];
    el.innerHTML = items.map(function (it) {
      return '<article class="statcard revealable">'
        + '<p class="statval ' + (it.cls || '') + '">' + it.value + '</p>'
        + '<p class="statdesc">' + it.desc + '</p>'
        + '<p class="statsource">IPSA cap-weighted · ' + summary.years.toFixed(1) + ' años</p>'
        + '</article>';
    }).join('');
  }

  // -------------------------------------------------------------------------
  // Exponer API
  // -------------------------------------------------------------------------

  window.OC.figures = Object.freeze({
    equityAndDrawdown: equityAndDrawdown,
    rollingVol: rollingVol,
    monthlyReturnsViolin: monthlyReturnsViolin,
    correlationHeatmap: correlationHeatmap,
    treemap: treemap,
    metricsTable: metricsTable,
    regimeTable: regimeTable,
    ipsaStatCard: ipsaStatCard,
  });
})();
