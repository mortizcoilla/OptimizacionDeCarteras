"""
scripts/figures_paper.py
========================

Genera las figuras PNG del paper a partir de los resultados del backtest
(data/processed/strategies.json + metrics.json + coverage.json + IPSA prices).

Salidas en docs/figures/*.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

PROJECT_ROOT = Path(r"C:\Workspace\Optimizacion_de_Carteras\OptimizacionDeCarteras")
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR = PROJECT_ROOT / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Paleta turquoise/grey/navy (igual a la web)
COL_INK = "#081630"
COL_TEAL = "#3B878C"
COL_TEAL_DEEP = "#125358"
COL_TEAL_SOFT = "#D9E7E8"
COL_GREY = "#C2C3C5"
COL_PAPER = "#EBEBED"
COL_PAPER_DEEP = "#DCDDDF"
COL_LOSS = "#A04545"
COL_LOSS_SOFT = "#F0DCDA"

STRATEGY_COLORS = {
    "E1_EqualWeight": "#3B878C",
    "E2_CapWeighted": "#125358",
    "E3_MinVariance": "#081630",
    "E4_MaxSharpe": "#A04545",
    "E5_RiskParity": "#C2C3C5",
    "E6_MaxDiversification": "#5C8A6E",
}

STRATEGY_LABELS = {
    "E1_EqualWeight": "1/N",
    "E2_CapWeighted": "Cap-weighted (IPSA)",
    "E3_MinVariance": "Min-varianza",
    "E4_MaxSharpe": "Max-Sharpe",
    "E5_RiskParity": "Risk-parity (ERC)",
    "E6_MaxDiversification": "Max-diversificación",
}

# Cargar datos
strategies = json.loads((DATA_DIR / "strategies.json").read_text(encoding="utf-8"))
metrics = json.loads((DATA_DIR / "metrics.json").read_text(encoding="utf-8"))
regime_returns = metrics.get("regime_returns", {})

# Setup matplotlib
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

# ---------------------------------------------------------------------------
# Fig 1 — Equity curves de las 6 estrategias
# ---------------------------------------------------------------------------

def fig_equity_curves():
    fig, ax = plt.subplots(figsize=(10, 5))
    dates = None
    for key, data in strategies.items():
        e = np.array([np.nan if v is None else v for v in data["equity_base100"]])
        d = pd.to_datetime(data["dates"])
        if dates is None:
            dates = d
        valid = ~np.isnan(e)
        ax.plot(d[valid], e[valid], label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], linewidth=1.8, alpha=0.95)
    ax.set_title("Equity curves de las 6 estrategias (IPSA, 2010-2024)\nBase 100 al 2010-01-04 · Rebalanceo mensual · Costos 10 bps", pad=14)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Equity (base 100)")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9, ncol=2)
    ax.axhline(100, color=COL_GREY, linewidth=0.5, linestyle="--", alpha=0.5)
    # Anotar crisis 2019-2021
    ax.axvspan(pd.Timestamp("2019-10-01"), pd.Timestamp("2021-12-31"), alpha=0.10, color=COL_LOSS, label="_nolegend_")
    ax.text(pd.Timestamp("2020-10-15"), 60, "Estallido social + COVID\n(2019-2021)", ha="center", fontsize=8, color=COL_LOSS, style="italic")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_equity_curves.png", dpi=200)
    plt.close(fig)
    print("OK fig1_equity_curves.png")

# ---------------------------------------------------------------------------
# Fig 2 — Drawdown de las 6 estrategias
# ---------------------------------------------------------------------------

def fig_drawdowns():
    fig, ax = plt.subplots(figsize=(10, 5))
    for key, data in strategies.items():
        e = np.array([np.nan if v is None else v for v in data["equity_base100"]])
        d = pd.to_datetime(data["dates"])
        # Drawdown
        dd = np.full(len(e), np.nan)
        peak = np.nan
        for i in range(len(e)):
            if not np.isnan(e[i]):
                if np.isnan(peak) or e[i] > peak:
                    peak = e[i]
                if peak > 0:
                    dd[i] = (e[i] - peak) / peak
        valid = ~np.isnan(dd)
        ax.fill_between(d[valid], dd[valid], 0, alpha=0.25, color=STRATEGY_COLORS[key])
        ax.plot(d[valid], dd[valid], color=STRATEGY_COLORS[key], linewidth=1.2, label=STRATEGY_LABELS[key], alpha=0.9)
    ax.set_title("Drawdown de las 6 estrategias (IPSA, 2010-2024)\nCaída desde el peak acumulado", pad=14)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
    ax.legend(loc="lower left", frameon=True, framealpha=0.9, fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_drawdowns.png", dpi=200)
    plt.close(fig)
    print("OK fig2_drawdowns.png")

# ---------------------------------------------------------------------------
# Fig 3 — Rolling Sharpe 12m
# ---------------------------------------------------------------------------

def fig_rolling_sharpe():
    fig, ax = plt.subplots(figsize=(10, 5))
    for key, data in strategies.items():
        r = np.array([np.nan if v is None else v for v in data["daily_returns"]])
        d = pd.to_datetime(data["dates"])
        rs = np.full(len(r), np.nan)
        for i in range(252, len(r)):
            win = r[i-252:i]
            win = win[~np.isnan(win)]
            if len(win) < 200:
                continue
            mean_r = win.mean() * 252
            vol = win.std(ddof=1) * np.sqrt(252)
            rs[i] = (mean_r - 0.04) / vol if vol > 0 else 0
        valid = ~np.isnan(rs)
        ax.plot(d[valid], rs[valid], label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], linewidth=1.4, alpha=0.9)
    ax.axhline(0, color=COL_GREY, linewidth=0.7, linestyle="--", alpha=0.6)
    ax.set_title("Rolling Sharpe 12 meses (252 días)\nMedia anualizada sobre ventana móvil", pad=14)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Sharpe rolling")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_rolling_sharpe.png", dpi=200)
    plt.close(fig)
    print("OK fig3_rolling_sharpe.png")

# ---------------------------------------------------------------------------
# Fig 4 — Retorno por régimen
# ---------------------------------------------------------------------------

def fig_regime_returns():
    fig, ax = plt.subplots(figsize=(10, 5))
    regimes_order = ["2010-2013", "2014-2018", "2019-2021", "2022-2024"]
    n_regimes = len(regimes_order)
    n_strat = len(STRATEGY_LABELS)
    width = 0.13
    x = np.arange(n_regimes)
    for i, key in enumerate(STRATEGY_LABELS):
        vals = []
        for r_name in regimes_order:
            v = next((rr["ann_return"] for rr in regime_returns.get(key, []) if rr["regime"] == r_name), 0)
            vals.append(v)
        bars = ax.bar(x + (i - n_strat/2) * width + width/2, [v * 100 for v in vals], width,
                      label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], edgecolor="white", linewidth=0.5)
    ax.axhline(0, color=COL_GREY, linewidth=0.7, alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(["2010-2013\n(post-subprime)", "2014-2018\n(reforma trib.)", "2019-2021\n(estallido+COVID)", "2022-2024\n(normalización)"], fontsize=9)
    ax.set_title("Retorno anualizado por régimen y estrategia", pad=14)
    ax.set_ylabel("Retorno anual (%)")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_regime_returns.png", dpi=200)
    plt.close(fig)
    print("OK fig4_regime_returns.png")

# ---------------------------------------------------------------------------
# Fig 5 — Heatmap de correlaciones
# ---------------------------------------------------------------------------

def fig_correlation_heatmap():
    prices = pd.read_csv(DATA_DIR / "prices_clean.csv", index_col=0, parse_dates=True)
    rets = prices.pct_change().dropna()
    corr = rets.corr()
    # Clustering simple: ordenar por suma de correlación (proxy)
    order = list(corr.sum().sort_values().index)
    corr_o = corr.loc[order, order]
    fig, ax = plt.subplots(figsize=(10, 9))
    cmap = LinearSegmentedColormap.from_list("teal_red", [COL_TEAL, "#FFFDFC", COL_LOSS])
    im = ax.imshow(corr_o.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    labels = [t.replace(".SN", "") for t in order]
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=7, family="monospace")
    ax.set_yticklabels(labels, fontsize=7, family="monospace")
    ax.set_title("Matriz de correlaciones de los 30 activos del IPSA\nRetornos diarios 2010-2024 · Ordenada por clustering", pad=14)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Correlación de Pearson", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_correlation_heatmap.png", dpi=200)
    plt.close(fig)
    print("OK fig5_correlation_heatmap.png")

# ---------------------------------------------------------------------------
# Fig 6 — Treemap de capitalización
# ---------------------------------------------------------------------------

def fig_treemap():
    universe = pd.read_csv(PROJECT_ROOT / "src" / "assets" / "data" / "ipsa.csv", index_col=0)
    # Filtrar los que tienen capitalización
    df = universe[universe["Capitalización de mercado"] > 0].copy()
    # Jerarquía: sector → ticker
    sectors = df.groupby("Sector")["Capitalización de mercado"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 7))
    x0, y0 = 0, 0
    W, H = 100, 100
    total_cap = df["Capitalización de mercado"].sum()
    cur_y = 0
    palette = [COL_TEAL, COL_TEAL_DEEP, COL_INK, COL_LOSS, COL_TEAL_SOFT, COL_PAPER_DEEP, "#5C8A6E", "#C66638"]
    for s_idx, (sector, cap) in enumerate(sectors.items()):
        h = (cap / total_cap) * H
        tickers = df[df["Sector"] == sector].sort_values("Capitalización de mercado", ascending=False)
        sector_total = tickers["Capitalización de mercado"].sum()
        cur_x = 0
        for t_idx, (_, row) in enumerate(tickers.iterrows()):
            w = (row["Capitalización de mercado"] / cap) * W
            color = palette[s_idx % len(palette)]
            ax.add_patch(Rectangle((cur_x, cur_y), w, h, facecolor=color, edgecolor="white", linewidth=1.5, alpha=0.85))
            if w > 6 and h > 4:
                ax.text(cur_x + w/2, cur_y + h/2, row["Ticker"].replace(".SN", ""), ha="center", va="center", fontsize=8, color="white", family="monospace", weight="bold")
            cur_x += w
        # Label del sector
        if h > 4:
            ax.text(0.5, cur_y + h - 1.5, sector, ha="left", va="top", fontsize=9, color=COL_INK, weight="bold")
        cur_y += h
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title("Composición del IPSA por sector y emisor\nTamaño = capitalización bursátil (CLP)", pad=14)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_treemap.png", dpi=200)
    plt.close(fig)
    print("OK fig6_treemap.png")

# ---------------------------------------------------------------------------
# Fig 7 — Tabla visual de métricas (heatmap)
# ---------------------------------------------------------------------------

def fig_metrics_heatmap():
    metrics_clean = {k: v for k, v in metrics.items() if k != "regime_returns"}
    cols = ["ann_return", "ann_volatility", "sharpe", "sortino", "max_drawdown", "calmar", "pct_positive_months"]
    col_labels = ["Retorno", "Volatilidad", "Sharpe", "Sortino", "Max DD", "Calmar", "% +"]
    keys = list(STRATEGY_LABELS.keys())
    M = np.zeros((len(keys), len(cols)))
    for i, k in enumerate(keys):
        for j, c in enumerate(cols):
            M[i, j] = metrics_clean[k][c]
    # Normalizar cada columna entre 0 y 1 (Max DD se invierte porque más negativo es peor)
    M_norm = M.copy()
    for j in range(len(cols)):
        if cols[j] == "max_drawdown":
            M_norm[:, j] = (M[:, j] - M[:, j].min()) / (M[:, j].max() - M[:, j].min() + 1e-9)
        else:
            M_norm[:, j] = (M[:, j] - M[:, j].min()) / (M[:, j].max() - M[:, j].min() + 1e-9)
    # Heatmap con anotaciones
    fig, ax = plt.subplots(figsize=(11, 5))
    cmap = LinearSegmentedColormap.from_list("teal_red", [COL_LOSS_SOFT, "#FFFDFC", COL_TEAL_SOFT])
    im = ax.imshow(M_norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(col_labels, fontsize=10, rotation=0)
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([STRATEGY_LABELS[k] for k in keys], fontsize=10)
    # Anotar valores
    for i in range(len(keys)):
        for j in range(len(cols)):
            val = M[i, j]
            if cols[j] == "ann_return" or cols[j] == "ann_volatility" or cols[j] == "max_drawdown" or cols[j] == "pct_positive_months":
                txt = f"{val*100:+.1f}%" if cols[j] != "max_drawdown" else f"{val*100:.1f}%"
            else:
                txt = f"{val:.2f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=9,
                    color=COL_INK if 0.2 < M_norm[i, j] < 0.8 else COL_INK, weight="bold")
    ax.set_title("Tabla de métricas (heatmap normalizado por columna)\nTeal = mejor · Rojo = peor (en cada métrica)", pad=14)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig7_metrics_heatmap.png", dpi=200)
    plt.close(fig)
    print("OK fig7_metrics_heatmap.png")

# ---------------------------------------------------------------------------
# Fig 8 — Distribución de retornos mensuales (violin)
# ---------------------------------------------------------------------------

def fig_violin():
    fig, ax = plt.subplots(figsize=(10, 5))
    keys = list(STRATEGY_LABELS.keys())
    data_by_strat = []
    labels = []
    colors = []
    for key in keys:
        r = np.array([np.nan if v is None else v for v in strategies[key]["daily_returns"]])
        # Calcular retornos mensuales
        monthly = []
        cur_start = None
        for i, val in enumerate(r):
            d = pd.to_datetime(strategies[key]["dates"][i])
            if cur_start is None or d.month != cur_start.month:
                if cur_start is not None:
                    monthly.append(cum)
                cur_start = d
                cum = 1.0
            if not np.isnan(val):
                cum *= 1 + val
        if cur_start is not None:
            monthly.append(cum)
        monthly_ret = [m - 1 for m in monthly]
        data_by_strat.append(monthly_ret)
        labels.append(STRATEGY_LABELS[key])
        colors.append(STRATEGY_COLORS[key])
    parts = ax.violinplot(data_by_strat, positions=range(len(keys)), showmedians=True, widths=0.7)
    for pc, color in zip(parts["bodies"], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.6)
    for partname in ("cbars", "cmins", "cmaxes", "cmedians"):
        if partname in parts:
            parts[partname].set_edgecolor(COL_INK)
            parts[partname].set_linewidth(1)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.axhline(0, color=COL_GREY, linewidth=0.7, linestyle="--", alpha=0.6)
    ax.set_title("Distribución de retornos mensuales por estrategia\nViolín: KDE · Línea central: mediana", pad=14)
    ax.set_ylabel("Retorno mensual")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig8_violin_monthly.png", dpi=200)
    plt.close(fig)
    print("OK fig8_violin_monthly.png")

# ---------------------------------------------------------------------------
# Ejecutar todas
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[figures] Generando figuras en {FIG_DIR}...")
    fig_equity_curves()
    fig_drawdowns()
    fig_rolling_sharpe()
    fig_regime_returns()
    fig_correlation_heatmap()
    fig_treemap()
    fig_metrics_heatmap()
    fig_violin()
    print(f"[figures] Listo. {len(list(FIG_DIR.glob('*.png')))} figuras en {FIG_DIR}/")
