/**
 * js/main.js
 *
 * Orquestador del paper. Se ejecuta después de data.js, analytics.js, figures.js.
 * Responsabilidades:
 *   1. Reveal on scroll (fade-in).
 *   2. Active state en la sticky nav.
 *   3. Tablas derivadas desde META.
 *   4. Render de las figuras D3 y tablas analíticas.
 *
 * @namespace OC.main
 * @author Miguel Ortiz C.
 * @license MIT
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || !window.OC) {
    console.error('[OC.main] window.OC no está disponible.');
    return;
  }

  const META = window.OC.META;
  const UNIVERSE = window.OC.IPSA_UNIVERSE;
  const PRICES = window.OC.PRICES;
  const COVERAGE = (META && META.coverage) || {};

  // -------------------------------------------------------------------------
  // 1. Reveal on scroll
  // -------------------------------------------------------------------------

  function initReveals() {
    const items = document.querySelectorAll('.revealable');
    if (!('IntersectionObserver' in window) || items.length === 0) {
      items.forEach(function (el) { el.classList.add('revealed'); });
      return;
    }
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -10% 0px' });
    items.forEach(function (el) { observer.observe(el); });
  }

  // -------------------------------------------------------------------------
  // 2. Active state en sticky nav
  // -------------------------------------------------------------------------

  function initNavActive() {
    const navLinks = document.querySelectorAll('#topnav .navrow a');
    if (navLinks.length === 0) return;
    const sections = Array.from(navLinks)
      .map(function (a) {
        const id = a.getAttribute('href');
        if (!id || !id.startsWith('#')) return null;
        const el = document.querySelector(id);
        return el ? { id: id, el: el, link: a } : null;
      })
      .filter(Boolean);
    if (sections.length === 0) return;
    function setActive(activeId) {
      sections.forEach(function (s) {
        if (s.id === activeId) s.link.classList.add('is-active');
        else s.link.classList.remove('is-active');
      });
    }
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(function (entries) {
        let best = null;
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            if (!best || entry.intersectionRatio > best.intersectionRatio) best = entry;
          }
        });
        if (best) setActive('#' + best.target.id);
      }, { rootMargin: '-30% 0px -60% 0px', threshold: [0, 0.1, 0.3, 0.5] });
      sections.forEach(function (s) { observer.observe(s.el); });
    }
  }

  // -------------------------------------------------------------------------
  // 3. Tablas estáticas (cobertura, header stats)
  // -------------------------------------------------------------------------

  function renderCoverageTable() {
    const tbody = document.querySelector('#coverage-table tbody');
    if (!tbody || !COVERAGE.per_ticker_coverage) return;
    const entries = Object.entries(COVERAGE.per_ticker_coverage)
      .map(function (kv) { return { ticker: kv[0], info: kv[1] }; })
      .filter(function (e) { return e.info.first && e.info.last; })
      .sort(function (a, b) { return a.info.coverage_pct - b.info.coverage_pct; })
      .slice(0, 8);
    if (entries.length === 0) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--grey); font-family: var(--font-mono); padding: 20px;">Sin datos de cobertura.</td></tr>'; return; }
    const maxCov = Math.max.apply(null, entries.map(function (e) { return e.info.coverage_pct; }));
    const minCov = Math.min.apply(null, entries.map(function (e) { return e.info.coverage_pct; }));
    tbody.innerHTML = entries.map(function (e) {
      const cls = e.info.coverage_pct === minCov ? 'loss' : (e.info.coverage_pct === maxCov ? 'up' : '');
      return '<tr>'
        + '<td><code>' + e.ticker + '</code></td>'
        + '<td class="' + cls + '">' + e.info.coverage_pct.toFixed(1) + '%</td>'
        + '<td>' + e.info.rows_with_data.toLocaleString('es-CL') + '</td>'
        + '<td>' + e.info.first + '</td>'
        + '<td>' + e.info.last + '</td>'
        + '</tr>';
    }).join('');
  }

  function renderMetaStats() {
    const elDays = document.querySelector('#stat-period-days');
    if (elDays && COVERAGE.rows_total) elDays.textContent = COVERAGE.rows_total.toLocaleString('es-CL');
    const elUniv = document.querySelector('#stat-universe');
    if (elUniv && UNIVERSE.length) elUniv.textContent = String(UNIVERSE.length);
    const elYears = document.querySelector('#stat-years');
    if (elYears && COVERAGE.date_min && COVERAGE.date_max) {
      const d0 = new Date(COVERAGE.date_min);
      const d1 = new Date(COVERAGE.date_max);
      const years = (d1 - d0) / (365.25 * 24 * 3600 * 1000);
      elYears.textContent = years.toFixed(1);
    }
  }

  // -------------------------------------------------------------------------
  // 4. Render de figuras y tablas analíticas
  // -------------------------------------------------------------------------

  function renderAnalytics() {
    if (!window.OC.analytics || !window.OC.figures) {
      console.warn('[OC.main] analytics o figures no disponibles.');
      return;
    }
    try {
      // Calcular todo
      const equity = window.OC.analytics.capWeightedEquity();
      const summary = window.OC.analytics.ipsaSummary();
      const metrics = window.OC.analytics.metricsForAll();
      const regimes = window.OC.analytics.regimeReturns();
      const monthly = window.OC.analytics.monthlyReturnsDistribution();
      const tickers = UNIVERSE.map(function (u) { return u.ticker; });

      // Stat cards IPSA
      window.OC.figures.ipsaStatCard('#ipsa-stats', summary);

      // Figuras D3
      window.OC.figures.equityAndDrawdown('#fig-equity', equity, { height: 320 });
      window.OC.figures.treemap('#fig-treemap', window.OC.analytics.treemapData());
      window.OC.figures.monthlyReturnsViolin('#fig-violin', monthly);
      window.OC.figures.rollingVol('#fig-vol', 'COPEC.SN');
      window.OC.figures.correlationHeatmap('#fig-heatmap', tickers);

      // Tablas
      window.OC.figures.metricsTable('#metrics-per-asset-table tbody', metrics);
      window.OC.figures.regimeTable('#regime-table tbody', regimes);

      // Re-bind reveals (las stat cards se crearon dinámicamente)
      const newRevealables = document.querySelectorAll('.statcard.revealable:not(.revealed)');
      if (newRevealables.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add('revealed');
              observer.unobserve(entry.target);
            }
          });
        }, { threshold: 0.15 });
        newRevealables.forEach(function (el) { observer.observe(el); });
      }
    } catch (e) {
      console.error('[OC.main] renderAnalytics:', e);
    }
  }

  // -------------------------------------------------------------------------
  // 4b. Renderizar fórmulas KaTeX desde data-tex
  // -------------------------------------------------------------------------

  function renderFormulas() {
    if (typeof katex === 'undefined') {
      // KaTeX no cargó (CDN caído o bloqueado). Dejar el texto plano.
      return;
    }
    const formulas = document.querySelectorAll('.tex[data-tex]');
    formulas.forEach(function (el) {
      try {
        const tex = el.getAttribute('data-tex');
        katex.render(tex, el, { displayMode: true, throwOnError: false });
      } catch (e) {
        console.warn('[OC.main] katex:', e);
      }
    });
  }

  // -------------------------------------------------------------------------
  // 5. Init
  // -------------------------------------------------------------------------

  function init() {
    try { renderFormulas(); } catch (e) { console.warn('[OC.main] formulas:', e); }
    try { initReveals(); } catch (e) { console.warn('[OC.main] reveals:', e); }
    try { initNavActive(); } catch (e) { console.warn('[OC.main] nav:', e); }
    try { renderMetaStats(); } catch (e) { console.warn('[OC.main] meta:', e); }
    try { renderCoverageTable(); } catch (e) { console.warn('[OC.main] coverage:', e); }
    try { renderAnalytics(); } catch (e) { console.warn('[OC.main] analytics:', e); }

    window.OC.main = Object.freeze({
      META: META,
      universeSize: UNIVERSE.length,
      priceRows: PRICES.length,
      coverage: COVERAGE,
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
