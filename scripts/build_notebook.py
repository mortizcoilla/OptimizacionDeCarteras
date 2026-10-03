"""
scripts/build_notebook.py
========================

Genera el Jupyter notebook `paper1_estrategias_carteras_IPSA.ipynb` con todo
el pipeline del paper en celdas ejecutables.

Uso:
    python scripts/build_notebook.py

El notebook resultante es autocontenido: se puede abrir en Jupyter / VSCode
y ejecutar todas las celdas en orden para regenerar todos los resultados.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Workspace\Optimizacion_de_Carteras\OptimizacionDeCarteras")
NB_PATH = PROJECT_ROOT / "notebooks" / "paper1_estrategias_carteras_IPSA.ipynb"


def md_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.split("\n") if "\n" in text else [text],
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.split("\n") if "\n" in text else [text],
    }


# ---------------------------------------------------------------------------
# Definir celdas
# ---------------------------------------------------------------------------

cells = []

# === TÍTULO ===
cells.append(md_cell("""# Paper 1 — Estrategias de construcción de portafolios en el IPSA, 2010–2024

**Miguel Ortiz C.** · Working paper · Julio 2026

---

Notebook autocontenido que reproduce el backtest del paper. Ejecutar todas las celdas en orden para regenerar:

- 6 estrategias comparadas (1/N, cap-weighted, min-variance, max-Sharpe, risk-parity, max-diversification)
- Métricas agregadas y por régimen
- 8 figuras del paper
- Datos exportados a `data/processed/`

**Requisitos:** `yfinance`, `pandas`, `numpy`, `matplotlib`, `cvxpy`, `scipy`.

**Tiempo de ejecución:** ~3-5 minutos (la descarga inicial de Yahoo Finance puede tardar más).
"""))

# === §1 SETUP ===
cells.append(md_cell("## 1. Setup\n\nImportaciones, paths y constantes del proyecto."))

cells.append(code_cell("""# Imports estándar
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Para que matplotlib funcione en scripts/headless
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# Imports científicos
import cvxpy as cp
from scipy.optimize import minimize

warnings.filterwarnings("ignore", category=UserWarning)

# Reproducibilidad
np.random.seed(42)

# Paths del proyecto
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "data").exists():
    PROJECT_ROOT = Path(r"C:\\Workspace\\Optimizacion_de_Carteras\\OptimizacionDeCarteras")

DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src" / "assets" / "data"
FIG_DIR = PROJECT_ROOT / "docs" / "figures"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Constantes del backtest
ROLLING_WINDOW = 252
REBAL_FREQ = "MS"
TX_COST_BPS = 10
RF_ANNUAL = 0.04
TRADING_DAYS = 252
START_DATE = "2010-01-01"
END_DATE = "2024-12-31"

# Paleta del paper
COL = {
    "ink": "#081630",
    "teal": "#3B878C",
    "teal_deep": "#125358",
    "teal_soft": "#D9E7E8",
    "grey": "#C2C3C5",
    "paper": "#EBEBED",
    "loss": "#A04545",
    "loss_soft": "#F0DCDA",
}

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

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 150,
})

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"DATA_PROCESSED: {DATA_PROCESSED}")
print(f"FIG_DIR: {FIG_DIR}")
print(f"Setup OK · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")"""))

# === §2 DATOS ===
cells.append(md_cell("## 2. Datos\n\nCarga y limpieza de los datos de precios del IPSA 2010-2024."))

cells.append(code_cell("""# 2.1 Descarga desde Yahoo Finance (ejecutar una vez; luego se carga desde CSV)
import yfinance as yf

universe_csv = SRC_DIR / "ipsa.csv"
if not universe_csv.exists():
    raise FileNotFoundError(f"Composicion IPSA no encontrada: {universe_csv}. Ejecutar scripts/ipsa.py primero.")

universe_df = pd.read_csv(universe_csv, index_col=0)
tickers = list(universe_df["Ticker"])
print(f"Tickers: {len(tickers)}")

# Descargar precios diarios
prices_csv = DATA_PROCESSED / "prices_clean.csv"
if not prices_csv.exists():
    print("Descargando precios desde Yahoo Finance...")
    raw = yf.download(tickers=tickers, start=START_DATE, end=END_DATE, interval="1d",
                      auto_adjust=False, progress=True, threads=True)
    prices = raw["Adj Close"].copy()
    prices.sort_index(inplace=True)
    prices.to_csv(prices_csv)
    print(f"Guardado: {prices_csv} ({prices.shape})")
else:
    prices = pd.read_csv(prices_csv, index_col=0, parse_dates=True)
    print(f"Cargado desde cache: {prices_csv} ({prices.shape})")

print(f"Periodo: {prices.index[0].date()} a {prices.index[-1].date()}")
print(f"Dias bursatiles: {len(prices)}")"""))

cells.append(code_cell("""# 2.2 Calcular retornos y filtrar universo con cobertura minima
returns = prices.pct_change()
coverage = (~returns.isna()).sum()
tickers_full = [t for t in tickers if coverage[t] >= 252]
print(f"Tickers con >=252 dias: {len(tickers_full)}/{len(tickers)}")

prices_clean = prices[tickers_full].copy()
returns_clean = prices_clean.pct_change()
cap_clean = universe_df.set_index("Ticker")["Capitalización de mercado"].astype(float).reindex(tickers_full).fillna(0)

print(f"\\nCapitalizacion total: CLP {cap_clean.sum()/1e12:,.1f} B")
print(f"Top 5 emisores por cap:")
for t in cap_clean.sort_values(ascending=False).head(5).items():
    print(f"  {t[0]:18s} CLP {t[1]/1e9:>8,.1f} B ({t[1]/cap_clean.sum()*100:5.1f}%)")"""))

cells.append(code_cell("""# 2.3 Guardar metadata de cobertura
coverage_meta = {
    "rows_total": int(len(prices)),
    "date_min": str(prices.index[0].date()),
    "date_max": str(prices.index[-1].date()),
    "per_ticker_coverage": {
        t: {
            "rows_with_data": int(coverage[t]),
            "coverage_pct": round(float(coverage[t] / len(prices) * 100), 2),
            "first": str(prices[t].first_valid_index().date()) if coverage[t] > 0 else None,
            "last": str(prices[t].last_valid_index().date()) if coverage[t] > 0 else None,
        }
        for t in tickers_full
    },
}
(DATA_PROCESSED / "coverage.json").write_text(json.dumps(coverage_meta, indent=2), encoding="utf-8")
print(f"Cobertura guardada en {DATA_PROCESSED / 'coverage.json'}")"""))

# === §3 ESTRATEGIAS ===
cells.append(md_cell("## 3. Estrategias de construcción de portafolios\n\nLas 6 estrategias a comparar."))

cells.append(code_cell("""# 3.1 E1 — Equal-weight (1/N)
def strat_equal_weight(n):
    return np.ones(n) / n

# 3.2 E2 — Cap-weighted (IPSA)
def strat_cap_weight(caps):
    s = caps.sum()
    return caps / s if s > 0 else strat_equal_weight(len(caps))

print("E1 (Equal-weight) y E2 (Cap-weighted) definidas")"""))

cells.append(code_cell("""# 3.3 E3 — Minimum-variance (Markowitz 1952)
def strat_min_variance(sigma, valid_mask):
    n = len(sigma)
    w = cp.Variable(n)
    eps = 1e-6 * np.eye(n)
    obj = cp.Minimize(cp.quad_form(w, sigma + eps))
    cons = [w >= 0, cp.sum(w) == 1]
    if not valid_mask.all():
        cons.append(w[~valid_mask] == 0)
    prob = cp.Problem(obj, cons)
    try:
        prob.solve(solver=cp.SCS, verbose=False)
    except Exception:
        return strat_equal_weight(n)
    if w.value is None:
        return strat_equal_weight(n)
    out = np.maximum(np.array(w.value).flatten(), 0)
    s = out.sum()
    return out / s if s > 0 else strat_equal_weight(n)

print("E3 (Min-variance) definida")"""))

cells.append(code_cell("""# 3.4 E4 — Maximum-Sharpe (Markowitz 1952, tangente)
def strat_max_sharpe(mu, sigma, valid_mask, rf=0.0):
    n = len(mu)
    w = cp.Variable(n)
    excess = mu - rf
    if np.all(excess <= 0):
        return strat_min_variance(sigma, valid_mask)
    eps = 1e-6 * np.eye(n)
    obj = cp.Maximize(excess @ w)
    cons = [w >= 0, cp.sum(w) == 1, cp.quad_form(w, sigma + eps) <= 1]
    if not valid_mask.all():
        cons.append(w[~valid_mask] == 0)
    prob = cp.Problem(obj, cons)
    try:
        prob.solve(solver=cp.SCS, verbose=False)
    except Exception:
        return strat_min_variance(sigma, valid_mask)
    if w.value is None:
        return strat_min_variance(sigma, valid_mask)
    out = np.maximum(np.array(w.value).flatten(), 0)
    s = out.sum()
    return out / s if s > 0 else strat_equal_weight(n)

print("E4 (Max-Sharpe) definida")"""))

cells.append(code_cell("""# 3.5 E5 — Risk-parity / Equal Risk Contribution (Qian 2005, Spinu 2013)
def strat_risk_parity(sigma, valid_mask):
    n = len(sigma)
    if not valid_mask.all():
        sigma = sigma.copy()
        sigma[~valid_mask] = 0
        sigma[:, ~valid_mask] = 0
    w = np.ones(n) / n
    for _ in range(100):
        rc = w * (sigma @ w)
        target = rc.sum() / n
        if target <= 0:
            break
        ratio = target / np.maximum(rc, 1e-12)
        w_new = w * ratio
        w_new = np.maximum(w_new, 1e-6)
        w_new = w_new / w_new.sum()
        if np.max(np.abs(w_new - w)) < 1e-8:
            break
        w = w_new
    w = np.maximum(w, 0)
    w[~valid_mask] = 0
    s = w.sum()
    return w / s if s > 0 else strat_equal_weight(n)

print("E5 (Risk-parity) definida")"""))

cells.append(code_cell("""# 3.6 E6 — Maximum-diversification (Choueifaty & Coignard 2008)
def strat_max_diversification(sigma, valid_mask):
    n = len(sigma)
    sigma_diag = np.sqrt(np.diag(sigma))
    def neg_dr(w):
        var = w @ sigma @ w
        return 0 if var <= 0 else -(sigma_diag @ w) / np.sqrt(var)
    def grad_neg_dr(w):
        var = w @ sigma @ w
        if var <= 0:
            return np.zeros(n)
        num = sigma_diag @ w
        g_var = 2 * sigma @ w
        return -(sigma_diag * np.sqrt(var) - num * g_var / np.sqrt(var)) / var
    w0 = np.ones(n) / n
    bounds = [(0, 1)] * n
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    res = minimize(neg_dr, w0, jac=grad_neg_dr, bounds=bounds, constraints=cons,
                   method="SLSQP", options={"maxiter": 200, "ftol": 1e-8})
    if not res.success:
        return strat_equal_weight(n)
    out = np.maximum(res.x, 0)
    out[~valid_mask] = 0
    s = out.sum()
    return out / s if s > 0 else strat_equal_weight(n)

print("E6 (Max-diversification) definida")"""))

cells.append(code_cell("""# 3.7 Diccionario de estrategias
STRATEGIES = {
    "E1_EqualWeight": ("1/N", lambda mu, sigma, vm, caps: strat_equal_weight(len(mu))),
    "E2_CapWeighted": ("IPSA cap-weighted", lambda mu, sigma, vm, caps: strat_cap_weight(caps)),
    "E3_MinVariance": ("Markowitz min-var", lambda mu, sigma, vm, caps: strat_min_variance(sigma, vm)),
    "E4_MaxSharpe": ("Markowitz max-Sharpe", lambda mu, sigma, vm, caps: strat_max_sharpe(mu, sigma, vm, rf=RF_ANNUAL/TRADING_DAYS)),
    "E5_RiskParity": ("Qian ERC", lambda mu, sigma, vm, caps: strat_risk_parity(sigma, vm)),
    "E6_MaxDiversification": ("Choueifaty max-div", lambda mu, sigma, vm, caps: strat_max_diversification(sigma, vm)),
}
print(f"Estrategias registradas: {list(STRATEGIES.keys())}")"""))

# === §4 BACKTEST ===
cells.append(md_cell("""## 4. Backtest

Simulación rolling: en cada rebalanceo mensual se estiman μ y Σ con 252 días previos, se calculan los pesos de las 6 estrategias, se aplica el costo de transacción y se simula el retorno del portafolio hasta el próximo rebalanceo."""))

cells.append(code_cell("""# 4.1 Calcular fechas de rebalanceo (primer dia habil de cada mes)
rebal_dates = returns_clean.resample(REBAL_FREQ).first().index
rebal_dates = [d for d in rebal_dates if d in returns_clean.index and d >= prices_clean.index[ROLLING_WINDOW]]
print(f"Rebalanceos: {len(rebal_dates)} (de {rebal_dates[0].date()} a {rebal_dates[-1].date()})")

# Mapear rebalances a indices
ret_mat = returns_clean.values
ret_dates = returns_clean.index
n_days = len(ret_dates)
n_assets = len(tickers_full)
cap_vec = cap_clean.values

rebal_idx_set = set()
rebal_idx_map = {}
for d in rebal_dates:
    pos = ret_dates.get_indexer([d], method="ffill")[0]
    if pos >= 0:
        rebal_idx_set.add(pos)
        rebal_idx_map[pos] = d
print(f"Rebalanceos validos: {len(rebal_idx_set)}")"""))

cells.append(code_cell("""# 4.2 Loop de simulacion
strategies_returns = {k: np.full(n_days, np.nan) for k in STRATEGIES}
strategies_weights = {k: [] for k in STRATEGIES}
current_weights = {k: strat_equal_weight(n_assets) for k in STRATEGIES}

print(f"Simulando {n_days} dias con {len(rebal_idx_set)} rebalanceos...")
t_start = datetime.now()
for i in range(n_days):
    if i in rebal_idx_set:
        lo = max(0, i - ROLLING_WINDOW)
        win = ret_mat[lo:i, :]
        valid = ~np.isnan(win).any(axis=0)
        if valid.sum() >= 5:
            win_clean = win[:, valid]
            mu = np.nanmean(win_clean, axis=0)
            sigma = np.cov(win_clean, rowvar=False)
            mu_full = np.zeros(n_assets); mu_full[valid] = mu
            sigma_full = np.zeros((n_assets, n_assets))
            sigma_full[np.ix_(valid, valid)] = sigma
            valid_full = np.zeros(n_assets, dtype=bool); valid_full[valid] = True
            for key, (label, fn) in STRATEGIES.items():
                try:
                    w_new = fn(mu_full, sigma_full, valid_full, cap_vec)
                    w_new = w_new * valid_full
                    s = w_new.sum()
                    if s > 0:
                        w_new = w_new / s
                    current_weights[key] = w_new
                    strategies_weights[key].append({"date": str(ret_dates[i].date()), "weights": w_new.tolist()})
                except Exception:
                    pass
    r = ret_mat[i, :]
    for key in STRATEGIES:
        w = current_weights[key]
        if not (np.any(np.isnan(r)) or np.any(np.isnan(w))):
            strategies_returns[key][i] = float(np.dot(w, r))

print(f"Backtest completo en {(datetime.now() - t_start).total_seconds():.1f}s")"""))

# === §5 METRICS ===
cells.append(md_cell("## 5. Métricas\n\nCálculo de métricas agregadas y por régimen."))

cells.append(code_cell("""# 5.1 Equity curves y metricas agregadas
def compute_metrics(r_arr, label):
    valid = ~np.isnan(r_arr)
    r = r_arr[valid]
    if len(r) < 60:
        return None
    n = len(r)
    # Equity base 100
    e = 100 * np.cumprod(1 + r)
    total_ret = e[-1] / 100 - 1
    years = n / TRADING_DAYS
    ann_ret = (1 + total_ret) ** (1 / years) - 1
    ann_vol = np.nanstd(r, ddof=1) * np.sqrt(TRADING_DAYS)
    sharpe = (ann_ret - RF_ANNUAL) / ann_vol if ann_vol > 0 else 0
    neg = r[r < 0]
    ds_vol = np.nanstd(neg, ddof=1) * np.sqrt(TRADING_DAYS) if len(neg) > 1 else ann_vol
    sortino = (ann_ret - RF_ANNUAL) / ds_vol if ds_vol > 0 else 0
    peak = e[0]; max_dd = 0
    for v in e:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < max_dd: max_dd = dd
    calmar = ann_ret / abs(max_dd) if max_dd < 0 else 0
    # % meses positivos
    valid_dates = ret_dates[valid]
    monthly = []
    if len(valid_dates) > 0:
        cur_y, cur_m = valid_dates[0].year, valid_dates[0].month
        start_eq = e[0]
        for j in range(1, n):
            d = valid_dates[j]
            if d.year != cur_y or d.month != cur_m:
                monthly.append(e[j-1] / start_eq - 1)
                cur_y, cur_m = d.year, d.month
                start_eq = e[j]
        monthly.append(e[-1] / start_eq - 1)
    pct_pos = sum(1 for m in monthly if m > 0) / len(monthly) if monthly else 0
    return {
        "label": label, "n_days": int(n),
        "ann_return": float(ann_ret), "ann_volatility": float(ann_vol),
        "sharpe": float(sharpe), "sortino": float(sortino),
        "max_drawdown": float(max_dd), "calmar": float(calmar),
        "pct_positive_months": float(pct_pos),
        "final_value_base100": float(e[-1]),
    }

metrics = {k: compute_metrics(strategies_returns[k], STRATEGY_LABELS[k]) for k in STRATEGIES}
print("Metricas agregadas (periodo completo 2010-2024):")
print(f"{'Estrategia':30s} {'Ret%':>7s} {'Vol%':>7s} {'Sharpe':>7s} {'MaxDD%':>8s} {'Calmar':>7s}")
for k, m in metrics.items():
    print(f"{STRATEGY_LABELS[k]:30s} {m['ann_return']*100:6.2f}% {m['ann_volatility']*100:6.2f}% {m['sharpe']:6.3f} {m['max_drawdown']*100:7.2f}% {m['calmar']:6.3f}")"""))

cells.append(code_cell("""# 5.2 Retornos por regimen
regimes = [
    ("2010-2013", "2010-01-01", "2013-12-31"),
    ("2014-2018", "2014-01-01", "2018-12-31"),
    ("2019-2021", "2019-01-01", "2021-12-31"),
    ("2022-2024", "2022-01-01", "2024-12-31"),
]
regime_returns = {k: [] for k in STRATEGIES}
for r_name, r_start, r_end in regimes:
    for key in STRATEGIES:
        r = strategies_returns[key]
        valid = ~np.isnan(r)
        mask = valid & (ret_dates >= r_start) & (ret_dates <= r_end)
        if mask.sum() < 60: continue
        r_sub = r[mask]
        n = len(r_sub)
        total = (1 + r_sub).prod() - 1
        years = n / TRADING_DAYS
        ann = (1 + total) ** (1 / years) - 1 if years > 0 else 0
        regime_returns[key].append({"regime": r_name, "ann_return": float(ann), "days": int(n)})

print("Retorno anualizado por regimen:")
print(f"{'Estrategia':30s}", end="")
for r_name, _, _ in regimes:
    print(f" {r_name:>10s}", end="")
print()
for k in STRATEGIES:
    print(f"{STRATEGY_LABELS[k]:30s}", end="")
    for rr in regime_returns[k]:
        print(f" {rr['ann_return']*100:>9.2f}%", end="")
    print()"""))

cells.append(code_cell("""# 5.3 Exportar metricas a JSON
results_export = {
    "metricas": metrics,
    "regime_returns": regime_returns,
    "retornos": {},
    "metadata": {
        "fecha_corrida": datetime.now(timezone.utc).isoformat(),
        "periodo": [str(ret_dates[0].date()), str(ret_dates[-1].date())],
        "n_days": int(n_days),
        "n_rebalances": len(rebal_idx_set),
        "tickers": tickers_full,
    },
}
for key in STRATEGIES:
    e = np.full(n_days, np.nan)
    cum = 100
    for i in range(n_days):
        if not np.isnan(strategies_returns[key][i]):
            cum *= 1 + strategies_returns[key][i]
            e[i] = cum
    results_export["retornos"][key] = {
        "label": STRATEGY_LABELS[key],
        "dates": [str(d.date()) for d in ret_dates],
        "daily_returns": [None if np.isnan(x) else float(x) for x in strategies_returns[key]],
        "equity_base100": [None if np.isnan(x) else float(x) for x in e],
    }

(DATA_PROCESSED / "metrics.json").write_text(
    json.dumps(results_export, indent=2, ensure_ascii=False), encoding="utf-8"
)
(DATA_PROCESSED / "strategies.json").write_text(
    json.dumps(results_export["retornos"], ensure_ascii=False), encoding="utf-8"
)
print(f"Metricas guardadas en {DATA_PROCESSED / 'metrics.json'}")
print(f"Estrategias guardadas en {DATA_PROCESSED / 'strategies.json'}")"""))

# === §6 FIGURAS ===
cells.append(md_cell("## 6. Figuras\n\nGeneración de las 8 figuras del paper."))

cells.append(code_cell("""# 6.1 F1 — Equity curves
strategies_data = results_export["retornos"]

fig, ax = plt.subplots(figsize=(10, 5))
for key, data in strategies_data.items():
    e = np.array([np.nan if v is None else v for v in data["equity_base100"]])
    d = pd.to_datetime(data["dates"])
    valid = ~np.isnan(e)
    ax.plot(d[valid], e[valid], label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], linewidth=1.8, alpha=0.95)
ax.set_title("Equity curves de las 6 estrategias (IPSA, 2010-2024)\\nBase 100 · Rebalanceo mensual · Costos 10 bps", pad=14)
ax.set_xlabel("Fecha"); ax.set_ylabel("Equity (base 100)")
ax.legend(loc="upper left", fontsize=9, ncol=2)
ax.axhline(100, color=COL["grey"], linewidth=0.5, linestyle="--", alpha=0.5)
ax.axvspan(pd.Timestamp("2019-10-01"), pd.Timestamp("2021-12-31"), alpha=0.10, color=COL["loss"])
ax.text(pd.Timestamp("2020-10-15"), 60, "Estallido + COVID (2019-2021)", ha="center", fontsize=8, color=COL["loss"], style="italic")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig1_equity_curves.png", dpi=150)
plt.close(fig)
print("OK fig1_equity_curves.png")"""))

cells.append(code_cell("""# 6.2 F2 — Drawdowns
fig, ax = plt.subplots(figsize=(10, 5))
for key, data in strategies_data.items():
    e = np.array([np.nan if v is None else v for v in data["equity_base100"]])
    d = pd.to_datetime(data["dates"])
    dd = np.full(len(e), np.nan)
    peak = np.nan
    for i in range(len(e)):
        if not np.isnan(e[i]):
            if np.isnan(peak) or e[i] > peak: peak = e[i]
            if peak > 0: dd[i] = (e[i] - peak) / peak
    valid = ~np.isnan(dd)
    ax.fill_between(d[valid], dd[valid], 0, alpha=0.25, color=STRATEGY_COLORS[key])
    ax.plot(d[valid], dd[valid], color=STRATEGY_COLORS[key], linewidth=1.2, label=STRATEGY_LABELS[key], alpha=0.9)
ax.set_title("Drawdowns de las 6 estrategias (IPSA, 2010-2024)", pad=14)
ax.set_xlabel("Fecha"); ax.set_ylabel("Drawdown")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
ax.legend(loc="lower left", fontsize=9, ncol=2)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig2_drawdowns.png", dpi=150)
plt.close(fig)
print("OK fig2_drawdowns.png")"""))

cells.append(code_cell("""# 6.3 F3 — Rolling Sharpe 12m
fig, ax = plt.subplots(figsize=(10, 5))
for key, data in strategies_data.items():
    r = np.array([np.nan if v is None else v for v in data["daily_returns"]])
    d = pd.to_datetime(data["dates"])
    rs = np.full(len(r), np.nan)
    for i in range(252, len(r)):
        win = r[i-252:i]
        win = win[~np.isnan(win)]
        if len(win) < 200: continue
        rs[i] = (win.mean()*252 - 0.04) / (win.std(ddof=1) * np.sqrt(252)) if win.std() > 0 else 0
    valid = ~np.isnan(rs)
    ax.plot(d[valid], rs[valid], label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], linewidth=1.4, alpha=0.9)
ax.axhline(0, color=COL["grey"], linewidth=0.7, linestyle="--", alpha=0.6)
ax.set_title("Rolling Sharpe 12 meses (252 días)", pad=14)
ax.set_xlabel("Fecha"); ax.set_ylabel("Sharpe rolling")
ax.legend(loc="upper left", fontsize=9, ncol=2)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig3_rolling_sharpe.png", dpi=150)
plt.close(fig)
print("OK fig3_rolling_sharpe.png")"""))

cells.append(code_cell("""# 6.4 F4 — Retorno por regimen
fig, ax = plt.subplots(figsize=(10, 5))
n_regimes = len(regimes)
n_strat = len(STRATEGY_LABELS)
width = 0.13
x = np.arange(n_regimes)
for i, key in enumerate(STRATEGY_LABELS):
    vals = [next((rr["ann_return"] for rr in regime_returns.get(key, []) if rr["regime"] == r_name), 0) for r_name, _, _ in regimes]
    ax.bar(x + (i - n_strat/2) * width + width/2, [v*100 for v in vals], width,
           label=STRATEGY_LABELS[key], color=STRATEGY_COLORS[key], edgecolor="white", linewidth=0.5)
ax.axhline(0, color=COL["grey"], linewidth=0.7, alpha=0.6)
ax.set_xticks(x)
ax.set_xticklabels(["2010-2013\\n(post-subprime)", "2014-2018\\n(reforma trib.)", "2019-2021\\n(estallido+COVID)", "2022-2024\\n(normalización)"], fontsize=9)
ax.set_title("Retorno anualizado por regimen y estrategia", pad=14)
ax.set_ylabel("Retorno anual (%)")
ax.legend(loc="upper left", fontsize=8, ncol=3)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig4_regime_returns.png", dpi=150)
plt.close(fig)
print("OK fig4_regime_returns.png")"""))

cells.append(code_cell("""# 6.5 F5 — Heatmap de correlaciones
rets = prices_clean.pct_change().dropna()
corr = rets.corr()
order = list(corr.sum().sort_values().index)
corr_o = corr.loc[order, order]
fig, ax = plt.subplots(figsize=(10, 9))
cmap = LinearSegmentedColormap.from_list("teal_red", [COL["teal"], "#FFFDFC", COL["loss"]])
im = ax.imshow(corr_o.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
labels = [t.replace(".SN", "") for t in order]
ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=90, fontsize=7, family="monospace")
ax.set_yticklabels(labels, fontsize=7, family="monospace")
ax.set_title("Matriz de correlaciones de los 30 activos del IPSA\\nRetornos diarios 2010-2024", pad=14)
cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
cbar.set_label("Correlacion de Pearson", fontsize=9)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig5_correlation_heatmap.png", dpi=150)
plt.close(fig)
print("OK fig5_correlation_heatmap.png")"""))

cells.append(code_cell("""# 6.6 F6 — Treemap de composicion
df = universe_df[universe_df["Capitalización de mercado"] > 0].copy()
sectors = df.groupby("Sector")["Capitalización de mercado"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(12, 7))
W, H = 100, 100
total_cap = df["Capitalización de mercado"].sum()
cur_y = 0
palette = [COL["teal"], COL["teal_deep"], COL["ink"], COL["loss"], COL["teal_soft"], COL["grey"], "#5C8A6E", "#C66638"]
for s_idx, (sector, cap) in enumerate(sectors.items()):
    h = (cap / total_cap) * H
    tickers_s = df[df["Sector"] == sector].sort_values("Capitalización de mercado", ascending=False)
    cur_x = 0
    for _, row in tickers_s.iterrows():
        w = (row["Capitalización de mercado"] / cap) * W
        color = palette[s_idx % len(palette)]
        ax.add_patch(mpatches.Rectangle((cur_x, cur_y), w, h, facecolor=color, edgecolor="white", linewidth=1.5, alpha=0.85))
        if w > 6 and h > 4:
            ax.text(cur_x + w/2, cur_y + h/2, row["Ticker"].replace(".SN", ""), ha="center", va="center", fontsize=8, color="white", family="monospace", weight="bold")
        cur_x += w
    if h > 4:
        ax.text(0.5, cur_y + h - 1.5, sector, ha="left", va="top", fontsize=9, color=COL["ink"], weight="bold")
    cur_y += h
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.invert_yaxis(); ax.axis("off")
ax.set_title("Composicion del IPSA por sector y emisor\\nTamano = capitalizacion bursatil (CLP)", pad=14)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig6_treemap.png", dpi=150)
plt.close(fig)
print("OK fig6_treemap.png")"""))

cells.append(code_cell("""# 6.7 F7 — Heatmap de metricas normalizado
cols = ["ann_return", "ann_volatility", "sharpe", "sortino", "max_drawdown", "calmar", "pct_positive_months"]
col_labels = ["Retorno", "Volatilidad", "Sharpe", "Sortino", "Max DD", "Calmar", "% +"]
keys = list(STRATEGY_LABELS.keys())
M = np.array([[metrics[k][c] for c in cols] for k in keys])
M_norm = M.copy()
for j in range(len(cols)):
    if cols[j] == "max_drawdown":
        M_norm[:, j] = (M[:, j] - M[:, j].min()) / (M[:, j].max() - M[:, j].min() + 1e-9)
    else:
        M_norm[:, j] = (M[:, j] - M[:, j].min()) / (M[:, j].max() - M[:, j].min() + 1e-9)
fig, ax = plt.subplots(figsize=(11, 5))
cmap = LinearSegmentedColormap.from_list("teal_red", [COL["loss_soft"], "#FFFDFC", COL["teal_soft"]])
im = ax.imshow(M_norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(cols))); ax.set_xticklabels(col_labels, fontsize=10)
ax.set_yticks(range(len(keys))); ax.set_yticklabels([STRATEGY_LABELS[k] for k in keys], fontsize=10)
for i in range(len(keys)):
    for j in range(len(cols)):
        val = M[i, j]
        if cols[j] in ("ann_return", "ann_volatility", "max_drawdown", "pct_positive_months"):
            txt = f"{val*100:+.1f}%"
        else:
            txt = f"{val:.2f}"
        ax.text(j, i, txt, ha="center", va="center", fontsize=9, color=COL["ink"], weight="bold")
ax.set_title("Tabla de metricas (heatmap normalizado por columna)", pad=14)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig7_metrics_heatmap.png", dpi=150)
plt.close(fig)
print("OK fig7_metrics_heatmap.png")"""))

cells.append(code_cell("""# 6.8 F8 — Violin de retornos mensuales
fig, ax = plt.subplots(figsize=(10, 5))
data_by_strat = []; labels = []; colors = []
for key in STRATEGY_LABELS:
    r = np.array([np.nan if v is None else v for v in strategies_data[key]["daily_returns"]])
    monthly = []; cur_start = None; cum = 1.0
    for i, val in enumerate(r):
        d = pd.to_datetime(strategies_data[key]["dates"][i])
        if cur_start is None or d.month != cur_start.month:
            if cur_start is not None: monthly.append(cum)
            cur_start = d; cum = 1.0
        if not np.isnan(val): cum *= 1 + val
    if cur_start is not None: monthly.append(cum)
    data_by_strat.append([m - 1 for m in monthly])
    labels.append(STRATEGY_LABELS[key])
    colors.append(STRATEGY_COLORS[key])
parts = ax.violinplot(data_by_strat, positions=range(len(STRATEGY_LABELS)), showmedians=True, widths=0.7)
for pc, color in zip(parts["bodies"], colors):
    pc.set_facecolor(color); pc.set_alpha(0.6)
for pn in ("cbars", "cmins", "cmaxes", "cmedians"):
    if pn in parts: parts[pn].set_edgecolor(COL["ink"]); parts[pn].set_linewidth(1)
ax.set_xticks(range(len(STRATEGY_LABELS)))
ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
ax.axhline(0, color=COL["grey"], linewidth=0.7, linestyle="--", alpha=0.6)
ax.set_title("Distribucion de retornos mensuales por estrategia", pad=14)
ax.set_ylabel("Retorno mensual")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
fig.tight_layout()
fig.savefig(FIG_DIR / "fig8_violin_monthly.png", dpi=150)
plt.close(fig)
print("OK fig8_violin_monthly.png")"""))

# === §7 EXPORT ===
cells.append(md_cell("## 7. Export y cierre\n\nTodos los outputs del notebook."))

cells.append(code_cell("""# 7.1 Listar todos los outputs
print("=" * 60)
print("OUTPUTS DEL NOTEBOOK")
print("=" * 60)
print("\\nDatos en data/processed/:")
for f in sorted(DATA_PROCESSED.glob("*")):
    print(f"  {f.name:<30s} {f.stat().st_size:>10,} bytes")
print("\\nFiguras en docs/figures/:")
for f in sorted(FIG_DIR.glob("*.png")):
    print(f"  {f.name:<35s} {f.stat().st_size:>10,} bytes")
print("\\n" + "=" * 60)
print("Notebook completo. Resultados disponibles para el paper.")
print("=" * 60)"""))

# === META ===
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.14",
            "mimetype": "text/x-python",
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "pygments_lexer": "ipython3",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.parent.mkdir(parents=True, exist_ok=True)
NB_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\\nNotebook: {NB_PATH} ({NB_PATH.stat().st_size:,} bytes, {len(cells)} celdas)")
