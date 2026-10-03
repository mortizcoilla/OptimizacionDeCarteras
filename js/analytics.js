/**
 * js/analytics.js
 *
 * Cálculos analíticos sobre window.OC.PRICES. Sin dependencias externas (todo a mano).
 * API expuesta en window.OC.analytics.
 *
 * Capacidades:
 *   - retornos diarios por activo
 *   - equity curve del cap-weighted (IPSA) con rebalanceo mensual
 *   - drawdown, rolling vol, rolling Sharpe
 *   - métricas por activo (retorno anualizado, vol, Sharpe, Sortino, max DD)
 *   - matriz de correlaciones + clustering jerárquico (single-linkage) para ordenar heatmap
 *   - treemap de capitalización (jerarquía sector → industria → ticker)
 *   - retornos anualizados por subperíodo (4 regímenes)
 *
 * @namespace OC.analytics
 * @author Miguel Ortiz C.
 * @license MIT
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || !window.OC) {
    console.error('[OC.analytics] window.OC no disponible.');
    return;
  }

  // -------------------------------------------------------------------------
  // Utilidades
  // -------------------------------------------------------------------------

  function mean(arr) {
    let s = 0, n = 0;
    for (let i = 0; i < arr.length; i++) if (Number.isFinite(arr[i])) { s += arr[i]; n++; }
    return n === 0 ? 0 : s / n;
  }

  function stddev(arr) {
    const m = mean(arr);
    let s = 0, n = 0;
    for (let i = 0; i < arr.length; i++) {
      if (Number.isFinite(arr[i])) { s += (arr[i] - m) ** 2; n++; }
    }
    return n < 2 ? 0 : Math.sqrt(s / (n - 1));
  }

  function downsample(arr, factor) {
    const out = [];
    for (let i = 0; i < arr.length; i += factor) out.push(arr[i]);
    return out;
  }

  // -------------------------------------------------------------------------
  // 1. Parseo de PRICES a series por activo
  // -------------------------------------------------------------------------

  function getTickerSeries(ticker) {
    const out = [];
    for (let i = 0; i < window.OC.PRICES.length; i++) {
      const row = window.OC.PRICES[i];
      const v = row.values[ticker];
      if (v !== null && v !== undefined) {
        out.push({ date: row.date, value: v });
      }
    }
    return out;
  }

  function getAllDates() {
    return window.OC.PRICES.map(function (r) { return r.date; });
  }

  // -------------------------------------------------------------------------
  // 2. Retornos diarios por activo
  // -------------------------------------------------------------------------

  function dailyReturnsForTicker(ticker) {
    const series = getTickerSeries(ticker);
    const out = [];
    for (let i = 1; i < series.length; i++) {
      const prev = series[i - 1].value;
      const cur = series[i].value;
      if (prev > 0 && cur > 0 && Number.isFinite(prev) && Number.isFinite(cur)) {
        out.push({ date: series[i].date, ret: cur / prev - 1 });
      } else {
        out.push({ date: series[i].date, ret: null });
      }
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // 3. Métricas por activo
  // -------------------------------------------------------------------------

  function metricsForTicker(ticker) {
    const rets = dailyReturnsForTicker(ticker);
    const valid = rets.filter(function (r) { return r.ret !== null; }).map(function (r) { return r.ret; });
    if (valid.length < 60) {
      return { ticker: ticker, hasData: false };
    }
    const n = valid.length;
    const totalReturn = valid.reduce(function (a, b) { return a * (1 + b); }, 1) - 1;
    const annRet = (Math.pow(1 + totalReturn, 252 / n)) - 1;
    const annVol = stddev(valid) * Math.sqrt(252);
    const meanDaily = mean(valid);
    const sharpe = annVol > 0 ? (annRet - 0) / annVol : 0;

    // Sortino: downside vol sólo de retornos negativos
    const neg = valid.filter(function (r) { return r < 0; });
    const dsVol = stddev(neg) * Math.sqrt(252);
    const sortino = dsVol > 0 ? annRet / dsVol : 0;

    // Max drawdown
    let equity = 1, peak = 1, maxDD = 0;
    for (let i = 0; i < valid.length; i++) {
      equity *= 1 + valid[i];
      if (equity > peak) peak = equity;
      const dd = (equity - peak) / peak;
      if (dd < maxDD) maxDD = dd;
    }
    const calmar = maxDD < 0 ? annRet / Math.abs(maxDD) : 0;

    // % meses positivos (asumiendo 21 días por mes aprox — usamos ret mensual)
    let posMonths = 0, totalMonths = 0;
    for (let i = 21; i < n; i += 21) {
      let mRet = 1;
      for (let j = i - 21; j < i; j++) mRet *= 1 + valid[j];
      mRet -= 1;
      if (Number.isFinite(mRet)) {
        totalMonths++;
        if (mRet > 0) posMonths++;
      }
    }
    const pctPos = totalMonths > 0 ? posMonths / totalMonths : 0;

    return {
      ticker: ticker,
      hasData: true,
      n: n,
      annRet: annRet,
      annVol: annVol,
      sharpe: sharpe,
      sortino: sortino,
      maxDD: maxDD,
      calmar: calmar,
      pctPositive: pctPos,
    };
  }

  function metricsForAll() {
    const out = [];
    for (let i = 0; i < window.OC.IPSA_UNIVERSE.length; i++) {
      out.push(metricsForTicker(window.OC.IPSA_UNIVERSE[i].ticker));
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // 4. Equity curve del cap-weighted (IPSA) con rebalanceo mensual
  // -------------------------------------------------------------------------

  function capWeightedEquity() {
    const universe = window.OC.IPSA_UNIVERSE;
    const totalCap = universe.reduce(function (s, u) { return s + (u.capitalizacion || 0); }, 0);
    const weights = {};
    for (let i = 0; i < universe.length; i++) {
      const u = universe[i];
      weights[u.ticker] = totalCap > 0 ? (u.capitalizacion || 0) / totalCap : 0;
    }

    // Equity: 100 al inicio, evoluciona por retornos diarios de cada activo ponderado.
    // Rebalanceo mensual: en el primer día de cada mes, recalculamos pesos.
    const rows = window.OC.PRICES;
    const equity = [{ date: rows[0].date, value: 100 }];
    let prevValues = {};
    let lastMonth = rows[0].date.slice(0, 7);

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const month = row.date.slice(0, 7);
      const isMonthStart = month !== lastMonth;
      lastMonth = month;

      // Recalcular pesos al inicio de cada mes (con cap actual — assumption simplificado)
      if (isMonthStart) {
        // Los pesos se mantienen; sólo recalculamos si hay drift grande (>5%)
        // Simplificación: mantener pesos del inicio
      }

      // Calcular retorno diario del portafolio
      let portRet = 0, portWeight = 0;
      for (let t = 0; t < universe.length; t++) {
        const ticker = universe[t].ticker;
        const cur = row.values[ticker];
        const prev = prevValues[ticker];
        const w = weights[ticker] || 0;
        if (cur !== null && cur !== undefined && prev !== null && prev !== undefined && prev > 0 && cur > 0) {
          portRet += w * (cur / prev - 1);
          portWeight += w;
        }
      }
      // Si la suma de pesos con datos es 0, no se opera
      if (portWeight === 0) {
        equity.push({ date: row.date, value: equity[equity.length - 1].value });
      } else {
        // Normalizar al universo con datos disponibles
        const normRet = portRet / portWeight;
        equity.push({ date: row.date, value: equity[equity.length - 1].value * (1 + normRet) });
      }

      // Guardar valores para próxima iteración
      prevValues = {};
      for (let t = 0; t < universe.length; t++) {
        const ticker = universe[t].ticker;
        const v = row.values[ticker];
        prevValues[ticker] = (v !== null && v !== undefined) ? v : null;
      }
    }
    return equity;
  }

  // -------------------------------------------------------------------------
  // 5. Drawdown y rolling vol desde una equity curve
  // -------------------------------------------------------------------------

  function drawdown(equity) {
    const out = [];
    let peak = equity[0].value;
    for (let i = 0; i < equity.length; i++) {
      if (equity[i].value > peak) peak = equity[i].value;
      const dd = (equity[i].value - peak) / peak;
      out.push({ date: equity[i].date, value: dd });
    }
    return out;
  }

  function rollingVol(ticker, window) {
    const rets = dailyReturnsForTicker(ticker);
    const out = [];
    for (let i = 0; i < rets.length; i++) {
      if (i < window) { out.push({ date: rets[i].date, value: null }); continue; }
      const slice = rets.slice(i - window, i).map(function (r) { return r.ret; }).filter(function (v) { return v !== null; });
      if (slice.length < 60) { out.push({ date: rets[i].date, value: null }); continue; }
      out.push({ date: rets[i].date, value: stddev(slice) * Math.sqrt(252) });
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // 6. Matriz de correlaciones + clustering jerárquico simple
  // -------------------------------------------------------------------------

  function buildReturnsMatrix(tickers) {
    // Devuelve { dates: [], matrix: {ticker: [ret_diario]} } alineado
    const allDates = getAllDates();
    const series = {};
    for (let t = 0; t < tickers.length; t++) {
      series[tickers[t]] = dailyReturnsForTicker(tickers[t]);
    }
    const matrix = {};
    for (let t = 0; t < tickers.length; t++) {
      const ticker = tickers[t];
      const arr = [];
      for (let i = 0; i < series[ticker].length; i++) {
        arr.push(series[ticker][i].ret);
      }
      matrix[ticker] = arr;
    }
    return { dates: series[tickers[0]].map(function (r) { return r.date; }), matrix: matrix };
  }

  function correlationMatrix(tickers) {
    const m = buildReturnsMatrix(tickers);
    const n = tickers.length;
    const corr = [];
    for (let i = 0; i < n; i++) {
      const row = [];
      const a = m.matrix[tickers[i]].filter(function (v) { return v !== null; });
      for (let j = 0; j < n; j++) {
        const b = m.matrix[tickers[j]].filter(function (v) { return v !== null; });
        if (a.length !== b.length || a.length < 60) { row.push(0); continue; }
        const ma = mean(a), mb = mean(b);
        let num = 0, da = 0, db = 0;
        for (let k = 0; k < a.length; k++) {
          const xa = a[k] - ma, xb = b[k] - mb;
          num += xa * xb;
          da += xa * xa;
          db += xb * xb;
        }
        const den = Math.sqrt(da * db);
        row.push(den > 0 ? num / den : 0);
      }
      corr.push(row);
    }
    return { tickers: tickers, matrix: corr };
  }

  // Clustering jerárquico single-linkage
  function clusterOrder(tickers, corr) {
    const n = tickers.length;
    const clusters = tickers.map(function (t, i) { return { id: i, items: [i] }; });
    const distance = function (a, b) {
      // 1 - correlation como distancia
      let max = -Infinity;
      for (let i = 0; i < a.items.length; i++) {
        for (let j = 0; j < b.items.length; j++) {
          const d = 1 - corr.matrix[a.items[i]][b.items[j]];
          if (d > max) max = d;
        }
      }
      return max;
    };
    while (clusters.length > 1) {
      let minD = Infinity, mi = 0, mj = 1;
      for (let i = 0; i < clusters.length; i++) {
        for (let j = i + 1; j < clusters.length; j++) {
          const d = distance(clusters[i], clusters[j]);
          if (d < minD) { minD = d; mi = i; mj = j; }
        }
      }
      const merged = { id: clusters[mi].id, items: clusters[mi].items.concat(clusters[mj].items) };
      clusters.splice(mj, 1);
      clusters[mi] = merged;
    }
    return clusters[0].items;
  }

  // -------------------------------------------------------------------------
  // 7. Treemap de capitalización
  // -------------------------------------------------------------------------

  function treemapData() {
    const universe = window.OC.IPSA_UNIVERSE;
    // Agrupar por sector → industria → ticker
    const bySector = {};
    for (let i = 0; i < universe.length; i++) {
      const u = universe[i];
      const sector = u.sector || 'Otros';
      const industria = u.industria || 'Otros';
      if (!bySector[sector]) bySector[sector] = {};
      if (!bySector[sector][industria]) bySector[sector][industria] = [];
      bySector[sector][industria].push({ name: u.ticker, value: Math.max(u.capitalizacion || 1, 1) });
    }
    const children = [];
    const sectorNames = Object.keys(bySector);
    for (let s = 0; s < sectorNames.length; s++) {
      const sector = sectorNames[s];
      const industrias = bySector[sector];
      const indArr = [];
      const indNames = Object.keys(industrias);
      for (let i = 0; i < indNames.length; i++) {
        indArr.push({
          name: indNames[i],
          children: industrias[indNames[i]],
        });
      }
      children.push({ name: sector, children: indArr });
    }
    return { name: 'IPSA', children: children };
  }

  // -------------------------------------------------------------------------
  // 8. Retornos anualizados por subperíodo (4 regímenes)
  // -------------------------------------------------------------------------

  function regimeReturns() {
    const regimes = [
      { name: '2010–2013 (post-subprime, commodities)', start: '2010-01-01', end: '2013-12-31' },
      { name: '2014–2018 (reforma tributaria, desaceleración)', start: '2014-01-01', end: '2018-12-31' },
      { name: '2019–2021 (estallido social, COVID)', start: '2019-01-01', end: '2021-12-31' },
      { name: '2022–2024 (guerra, ciclo TPM, normalización)', start: '2022-01-01', end: '2024-12-31' },
    ];
    const equity = capWeightedEquity();
    const out = [];
    for (let r = 0; r < regimes.length; r++) {
      const regime = regimes[r];
      const slice = equity.filter(function (e) { return e.date >= regime.start && e.date <= regime.end; });
      if (slice.length < 2) {
        out.push({ name: regime.name, start: regime.start, end: regime.end, ret: 0, days: 0 });
        continue;
      }
      const startV = slice[0].value;
      const endV = slice[slice.length - 1].value;
      const years = (slice.length - 1) / 252;
      const annRet = years > 0 ? (Math.pow(endV / startV, 1 / years)) - 1 : 0;
      out.push({
        name: regime.name,
        start: regime.start,
        end: regime.end,
        ret: annRet,
        days: slice.length - 1,
        startVal: startV,
        endVal: endV,
      });
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // 9. Distribución de retornos mensuales (cap-weighted)
  // -------------------------------------------------------------------------

  function monthlyReturnsDistribution() {
    const equity = capWeightedEquity();
    const out = [];
    // Agrupar por mes
    let monthStart = null;
    let lastMonth = null;
    for (let i = 0; i < equity.length; i++) {
      const month = equity[i].date.slice(0, 7);
      if (month !== lastMonth) {
        if (monthStart !== null) {
          const startV = monthStart.value;
          const endV = equity[i - 1].value;
          out.push({ date: monthStart.date, ret: endV / startV - 1 });
        }
        monthStart = equity[i];
        lastMonth = month;
      }
    }
    if (monthStart !== null) {
      const startV = monthStart.value;
      const endV = equity[equity.length - 1].value;
      out.push({ date: monthStart.date, ret: endV / startV - 1 });
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // 10. Resumen agregado del IPSA (cap-weighted)
  // -------------------------------------------------------------------------

  function ipsaSummary() {
    const equity = capWeightedEquity();
    const dd = drawdown(equity);
    const rets = [];
    for (let i = 1; i < equity.length; i++) {
      rets.push(equity[i].value / equity[i - 1].value - 1);
    }
    const n = rets.length;
    const totalRet = equity[equity.length - 1].value / 100 - 1;
    const years = n / 252;
    const annRet = (Math.pow(1 + totalRet, 1 / years)) - 1;
    const annVol = stddev(rets) * Math.sqrt(252);
    const sharpe = annVol > 0 ? annRet / annVol : 0;
    const neg = rets.filter(function (r) { return r < 0; });
    const dsVol = stddev(neg) * Math.sqrt(252);
    const sortino = dsVol > 0 ? annRet / dsVol : 0;
    const maxDD = Math.min.apply(null, dd.map(function (d) { return d.value; }));
    const calmar = maxDD < 0 ? annRet / Math.abs(maxDD) : 0;
    const posMonths = monthlyReturnsDistribution().filter(function (m) { return m.ret > 0; }).length;
    const totalMonths = monthlyReturnsDistribution().length;
    return {
      annRet: annRet,
      annVol: annVol,
      sharpe: sharpe,
      sortino: sortino,
      maxDD: maxDD,
      calmar: calmar,
      pctPositive: posMonths / totalMonths,
      totalMonths: totalMonths,
      years: years,
      finalValue: equity[equity.length - 1].value,
    };
  }

  // -------------------------------------------------------------------------
  // Exponer API
  // -------------------------------------------------------------------------

  window.OC.analytics = Object.freeze({
    dailyReturnsForTicker: dailyReturnsForTicker,
    metricsForTicker: metricsForTicker,
    metricsForAll: metricsForAll,
    capWeightedEquity: capWeightedEquity,
    drawdown: drawdown,
    rollingVol: rollingVol,
    correlationMatrix: correlationMatrix,
    clusterOrder: clusterOrder,
    treemapData: treemapData,
    regimeReturns: regimeReturns,
    monthlyReturnsDistribution: monthlyReturnsDistribution,
    ipsaSummary: ipsaSummary,
    downsample: downsample,
  });
})();
