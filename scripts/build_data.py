"""
scripts/build_data.py
=====================

Descarga precios diarios ajustados del IPSA 2010-2024 desde Yahoo Finance,
los limpia, y genera `js/data.js` con los datos embebidos para el paper 1
(Backtest de estrategias de construcción de portafolios en el IPSA 2010-2024).

Uso
---
    python scripts/build_data.py

Requisitos
----------
    pip install yfinance pandas

Salidas
-------
    js/data.js                         — datos embebidos (namespace window.OC)
    data/processed/coverage.json       — reporte de cobertura por ticker
    data/processed/prices_clean.csv    — copia local de la matriz limpia (auditoría)

No editar `js/data.js` a mano. Regenerar con este script.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Forzar UTF-8 en stdout/stderr (Windows defaults a cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IPSA_CSV = PROJECT_ROOT / "src" / "assets" / "data" / "ipsa.csv"
DATA_JS = PROJECT_ROOT / "js" / "data.js"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

START_DATE = "2010-01-01"
END_DATE = "2024-12-31"
INTERVAL = "1d"
FFILL_LIMIT = 5  # días
MIN_NONNAN_RATIO = 0.5  # al menos 50% de tickers con dato para conservar la fila


# ---------------------------------------------------------------------------
# Pasos
# ---------------------------------------------------------------------------

def load_ipsa_universe() -> list[dict[str, Any]]:
    """Carga la composición del IPSA desde el CSV ya descargado por scripts/ipsa.py."""
    df = pd.read_csv(IPSA_CSV, index_col=0)
    universe: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        cap_raw = row.get("Capitalización de mercado", 0)
        try:
            cap_val = float(cap_raw) if cap_raw not in (None, "", "No disponible") else 0.0
        except (TypeError, ValueError):
            cap_val = 0.0
        universe.append({
            "ticker": str(row["Ticker"]).strip(),
            "nombre": str(row.get("Nombre completo", "")).strip(),
            "sector": str(row.get("Sector", "")).strip(),
            "industria": str(row.get("Industria", "")).strip(),
            "capitalizacion": cap_val,
        })
    return universe


def download_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Descarga precios ajustados para los tickers dados vía yfinance."""
    print(f"[build_data] Descargando {len(tickers)} tickers, {start} → {end}, intervalo {INTERVAL}…")
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval=INTERVAL,
        auto_adjust=False,   # queremos columna 'Adj Close' explícita
        progress=True,
        threads=True,
    )
    if data.empty:
        raise RuntimeError("yfinance devolvió un DataFrame vacío. Revisar conexión o tickers.")
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.get_level_values(0):
            prices = data["Adj Close"].copy()
        elif "Close" in data.columns.get_level_values(0):
            print("[build_data] Aviso: 'Adj Close' no presente, usando 'Close'.")
            prices = data["Close"].copy()
        else:
            raise RuntimeError(f"No se encontró 'Adj Close' ni 'Close'. Columnas: {data.columns.get_level_values(0).unique()}")
    else:
        # yfinance devuelve columnas planas cuando hay un solo ticker
        if "Adj Close" in data.columns:
            prices = data[["Adj Close"]].copy()
            prices.columns = tickers
        else:
            prices = data[["Close"]].copy()
            prices.columns = tickers
    prices.sort_index(inplace=True)
    return prices


def clean_prices(prices: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Limpia NaN, aplica ffill limitado, conserva filas con cobertura mínima. Devuelve también un reporte de cobertura."""
    n_before = int(prices.isna().sum().sum())
    prices = prices.ffill(limit=FFILL_LIMIT)
    rows_before = len(prices)
    prices = prices.dropna(thresh=int(len(prices.columns) * MIN_NONNAN_RATIO))
    rows_after = len(prices)
    n_after = int(prices.isna().sum().sum())
    coverage: dict[str, Any] = {
        "rows_total": rows_after,
        "rows_dropped_low_coverage": rows_before - rows_after,
        "date_min": str(prices.index.min().date()) if not prices.empty else None,
        "date_max": str(prices.index.max().date()) if not prices.empty else None,
        "na_filled": n_before - n_after,
        "ffill_limit_days": FFILL_LIMIT,
        "per_ticker_coverage": {},
    }
    for t in prices.columns:
        series = prices[t]
        n_valid = int(series.notna().sum())
        first_idx = series.first_valid_index()
        last_idx = series.last_valid_index()
        coverage["per_ticker_coverage"][t] = {
            "rows_with_data": n_valid,
            "coverage_pct": round(100.0 * n_valid / max(rows_after, 1), 2),
            "first": str(first_idx.date()) if first_idx is not None else None,
            "last": str(last_idx.date()) if last_idx is not None else None,
        }
    return prices, coverage


def to_dense_matrix(prices: pd.DataFrame) -> list[dict[str, Any]]:
    """Convierte DataFrame ancho a lista densa {date, values: {ticker: precio_o_null}}."""
    rows: list[dict[str, Any]] = []
    for date, row in prices.iterrows():
        values: dict[str, float | None] = {}
        for t, v in row.items():
            if pd.isna(v):
                values[t] = None
            else:
                values[t] = round(float(v), 4)
        rows.append({"date": date.strftime("%Y-%m-%d"), "values": values})
    return rows


def build_meta(universe: list[dict[str, Any]], coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": "Optimización de Carteras de Inversión",
        "paper": "Paper 1 — Backtest de estrategias en el IPSA 2010-2024",
        "version": "0.1.0",
        "buildDateUtc": datetime.now(timezone.utc).isoformat(),
        "dataSource": "Yahoo Finance via yfinance (Adj Close — precios ajustados por dividendos y splits)",
        "compositionSource": "Bolsa de Santiago / cartola oficial del IPSA",
        "scriptVersion": "scripts/build_data.py (rev. 2026-07-27)",
        "period": {
            "requested": {"start": START_DATE, "end": END_DATE},
            "actual": {"start": coverage["date_min"], "end": coverage["date_max"]},
            "tradingDays": coverage["rows_total"],
        },
        "universeSize": len(universe),
        "conventions": {
            "currency": "CLP nominal (sin ajuste por inflación)",
            "tickerFormat": "Yahoo Finance (.SN = Santiago Exchange)",
            "naPolicy": f"forward fill hasta {FFILL_LIMIT} días; filas con <{int(MIN_NONNAN_RATIO * 100)}% de cobertura eliminadas",
            "rebalanceFrequency": "monthly (definido en motor, no en datos)",
            "transactionCost": "10 bps por rebalanceo (assumption del paper, no en datos)",
        },
        "disclaimers": [
            "Backtest histórico. Desempeño pasado no garantiza resultados futuros.",
            "Sesgo de supervivencia: se usa la composición actual del IPSA. Activos que salieron del índice durante 2010-2024 no están representados.",
            "Costos de transacción asumidos, no modelados con spread ni impacto.",
            "No se considera apalancamiento, short-selling, costos fiscales ni de custodia.",
        ],
        "coverage": coverage,
    }


def write_data_js(meta: dict[str, Any], universe: list[dict[str, Any]], prices_dense: list[dict[str, Any]]) -> None:
    """Genera `js/data.js` con namespace window.OC. No editar a mano."""
    meta_json = json.dumps(meta, indent=2, ensure_ascii=False)
    universe_json = json.dumps(universe, indent=2, ensure_ascii=False)
    prices_json = json.dumps(prices_dense, ensure_ascii=False)
    n_days = f"{len(prices_dense):,}"

    # NOTA: este template NO es un f-string porque contiene llaves de JSDoc
    # que Python 3.14 no puede parsear dentro de f-strings. Concatenamos
    # las partes variables explícitamente.
    js = (
        "/**\n"
        " * js/data.js\n"
        " *\n"
        " * Datos embebidos del paper 1 — Backtest de estrategias en el IPSA 2010-2024.\n"
        " * Generado automáticamente por scripts/build_data.py. NO editar a mano.\n"
        " *\n"
        " * @namespace OC (Optimización de Carteras)\n"
        " * @author Miguel Ortiz C. <mortizcoilla@gmail.com>\n"
        " * @license MIT\n"
        " */\n"
        "(function () {\n"
        "  'use strict';\n"
        "\n"
        "  /**\n"
        "   * Metadata del dataset, fuentes, período, convenciones y disclaimers.\n"
        "   * @type {Object}\n"
        "   */\n"
        "  const META = " + meta_json + ";\n"
        "\n"
        "  /**\n"
        "   * Universo invertible: composición actual del IPSA con sector, industria\n"
        "   * y capitalización al momento de la descarga. Estructura inmutable.\n"
        "   * @type {Array<Object>}\n"
        "   */\n"
        "  const IPSA_UNIVERSE = " + universe_json + ";\n"
        "\n"
        "  /**\n"
        "   * Precios ajustados diarios (Adj Close). Matriz densa fecha × ticker.\n"
        "   * Cada entrada: { date: 'YYYY-MM-DD', values: { 'TICKER.SN': precio_clp | null, ... } }\n"
        "   * Valores `null` = sin dato después de la limpieza (no se debe operar en esa fecha).\n"
        "   * Total: " + n_days + " días bursátiles.\n"
        "   * @type {Array<Object>}\n"
        "   */\n"
        "  const PRICES = " + prices_json + ";\n"
        "\n"
        "  // Exponer namespace. META, IPSA_UNIVERSE y PRICES son inmutables (frozen);\n"
        "  // el namespace raíz es extensible para que los módulos analytics, figures y\n"
        "  // main puedan registrar sus APIs sin romper la carga incremental.\n"
        "  window.OC = {\n"
        "    META: Object.freeze(META),\n"
        "    IPSA_UNIVERSE: Object.freeze(IPSA_UNIVERSE.map(Object.freeze)),\n"
        "    PRICES: Object.freeze(PRICES.map(Object.freeze)),\n"
        "  };\n"
        "})();\n"
    )
    DATA_JS.parent.mkdir(parents=True, exist_ok=True)
    DATA_JS.write_text(js, encoding="utf-8")
    print(f"[build_data] Escrito " + str(DATA_JS) + " (" + f"{len(js):,}" + " bytes)")


def main() -> int:
    print(f"[build_data] Proyecto: {PROJECT_ROOT}")
    if not IPSA_CSV.exists():
        print(f"[build_data] ERROR: no se encuentra {IPSA_CSV}.", file=sys.stderr)
        return 1
    universe = load_ipsa_universe()
    tickers = [u["ticker"] for u in universe]
    print(f"[build_data] Universo: {len(tickers)} tickers cargados desde CSV.")

    raw = download_prices(tickers, START_DATE, END_DATE)
    cleaned, coverage = clean_prices(raw)
    if cleaned.empty:
        print("[build_data] ERROR: la matriz limpia quedó vacía. Revisar tickers o red.", file=sys.stderr)
        return 2
    print(f"[build_data] Días limpios: {coverage['rows_total']} "
          f"({coverage['date_min']} → {coverage['date_max']})")
    print(f"[build_data] Filas descartadas por baja cobertura: {coverage['rows_dropped_low_coverage']}")
    print(f"[build_data] NaN rellenados por ffill: {coverage['na_filled']}")

    dense = to_dense_matrix(cleaned)
    print(f"[build_data] Matriz densa: {len(dense):,} filas × {len(tickers)} tickers")

    meta = build_meta(universe, coverage)
    write_data_js(meta, universe, dense)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(DATA_DIR / "prices_clean.csv", index_label="date")
    (DATA_DIR / "coverage.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (DATA_DIR / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[build_data] Cobertura guardada en {DATA_DIR / 'coverage.json'}")
    print(f"[build_data] Meta guardada en {DATA_DIR / 'meta.json'}")
    print(f"[build_data] CSV limpio guardado en {DATA_DIR / 'prices_clean.csv'}")

    # Resumen de cobertura por ticker (top 5 peores)
    worst = sorted(
        coverage["per_ticker_coverage"].items(),
        key=lambda kv: kv[1]["coverage_pct"],
    )[:5]
    print("\n[build_data] Cobertura por ticker (5 con menor cobertura):")
    for t, info in worst:
        print(f"  {t:<14s} {info['coverage_pct']:>6.2f}%  "
              f"({info['rows_with_data']:>5d} días, {info['first']} → {info['last']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
