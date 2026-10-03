"""
scripts/run_backtest.py
=======================

Backtest mensual de las 6 estrategias de construcción de portafolios sobre el
IPSA, 2010-2024. Ventana rolling 252d, rebalanceo mensual, 10 bps de costo.

Estrategias:
  E1 — Equal-weight (1/N)
  E2 — Cap-weighted (IPSA)
  E3 — Minimum-variance (Markowitz 1952)
  E4 — Maximum-Sharpe (tangente, Markowitz 1952)
  E5 — Risk-parity / Equal Risk Contribution (Qian 2005)
  E6 — Maximum-diversification (Choueifaty & Coignard 2008)

Salidas:
  data/processed/strategies.json — retornos diarios y equity por estrategia
  data/processed/metrics.json — métricas agregadas
  data/processed/backtest_log.json — log de pesos en cada rebalanceo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.optimize import minimize

PROJECT_ROOT = Path(r"C:\Workspace\Optimizacion_de_Carteras\OptimizacionDeCarteras")
PRICES_CSV = PROJECT_ROOT / "data" / "processed" / "prices_clean.csv"
UNIVERSE_CSV = PROJECT_ROOT / "src" / "assets" / "data" / "ipsa.csv"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

ROLLING_WINDOW = 252
REBAL_FREQ = "MS"  # Month Start
TX_COST_BPS = 10
RF_ANNUAL = 0.04  # ~TPM promedio Chile 2010-2024 (referencial)
TRADING_DAYS = 252

# ---------------------------------------------------------------------------
# Cargar datos
# ---------------------------------------------------------------------------

prices = pd.read_csv(PRICES_CSV, index_col=0, parse_dates=True)
universe = pd.read_csv(UNIVERSE_CSV, index_col=0)
cap = universe.set_index("Ticker")["Capitalización de mercado"].astype(float)
returns = prices.pct_change()

# Sólo activos que tienen TODA la historia (365+ días al final)
TICKERS = [t for t in prices.columns if prices[t].notna().sum() >= 252]
print(f"[backtest] Tickers con historia completa (>=252d): {len(TICKERS)}/{len(prices.columns)}")
print(f"[backtest] Tickers: {TICKERS}")

prices_clean = prices[TICKERS].copy()
returns_clean = prices_clean.pct_change()
cap_clean = cap.reindex(TICKERS).fillna(0)

# Fechas de rebalanceo: primer día hábil de cada mes
rebal_dates = returns_clean.resample(REBAL_FREQ).first().index
rebal_dates = [d for d in rebal_dates if d in returns_clean.index and d >= prices_clean.index[ROLLING_WINDOW]]
print(f"[backtest] Rebalanceos: {len(rebal_dates)} ({rebal_dates[0].date()} -> {rebal_dates[-1].date()})")

# ---------------------------------------------------------------------------
# Estrategias
# ---------------------------------------------------------------------------

def strat_equal_weight(n):
    return np.ones(n) / n

def strat_cap_weight(caps):
    s = caps.sum()
    if s <= 0:
        return strat_equal_weight(len(caps))
    return caps / s

def strat_min_variance(sigma, valid_mask):
    """Markowitz min-var con long-only y suma=1."""
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

def strat_max_sharpe(mu, sigma, valid_mask, rf=0.0):
    """Max Sharpe con transformación a QP: max (mu-rf)^T w s.a. w^T Sigma w <= 1, suma=1, long-only."""
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

def strat_risk_parity(sigma, valid_mask):
    """Equal Risk Contribution via iteración de Spinu (2013)."""
    n = len(sigma)
    if not valid_mask.all():
        sigma = sigma.copy()
        sigma[~valid_mask] = 0
        sigma[:, ~valid_mask] = 0
    # Inicialización 1/n
    w = np.ones(n) / n
    for _ in range(100):
        # RC_i = w_i * (sigma @ w)_i
        rc = w * (sigma @ w)
        # Buscamos w tal que RC_i sea igual para todo i
        # Iteración: w_i_new = w_i * (target / rc_i)
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
    # Forzar long-only y renormalizar
    w = np.maximum(w, 0)
    w[~valid_mask] = 0
    s = w.sum()
    return w / s if s > 0 else strat_equal_weight(n)

def strat_max_diversification(sigma, valid_mask):
    """Maximiza diversification ratio: (w^T sigma_diag) / sqrt(w^T Sigma w)."""
    n = len(sigma)
    sigma_diag = np.sqrt(np.diag(sigma))

    def neg_dr(w):
        var = w @ sigma @ w
        if var <= 0:
            return 0
        return -(sigma_diag @ w) / np.sqrt(var)

    def grad_neg_dr(w):
        var = w @ sigma @ w
        if var <= 0:
            return np.zeros(n)
        num = sigma_diag @ w
        g_var = 2 * sigma @ w
        return -(sigma_diag * np.sqrt(var) - num * g_var / np.sqrt(var)) / var

    w0 = np.ones(n) / n
    bounds = [(0, 1) for _ in range(n)]
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    res = minimize(neg_dr, w0, jac=grad_neg_dr, bounds=bounds, constraints=cons, method="SLSQP",
                   options={"maxiter": 200, "ftol": 1e-8})
    if not res.success:
        return strat_equal_weight(n)
    out = np.maximum(res.x, 0)
    out[~valid_mask] = 0
    s = out.sum()
    return out / s if s > 0 else strat_equal_weight(n)

STRATEGIES = {
    "E1_EqualWeight": ("1/N", lambda mu, sigma, vm, caps: strat_equal_weight(len(mu))),
    "E2_CapWeighted": ("IPSA cap-weighted", lambda mu, sigma, vm, caps: strat_cap_weight(caps)),
    "E3_MinVariance": ("Markowitz min-var", lambda mu, sigma, vm, caps: strat_min_variance(sigma, vm)),
    "E4_MaxSharpe": ("Markowitz max-Sharpe", lambda mu, sigma, vm, caps: strat_max_sharpe(mu, sigma, vm, rf=RF_ANNUAL/TRADING_DAYS)),
    "E5_RiskParity": ("Qian ERC", lambda mu, sigma, vm, caps: strat_risk_parity(sigma, vm)),
    "E6_MaxDiversification": ("Choueifaty max-div", lambda mu, sigma, vm, caps: strat_max_diversification(sigma, vm)),
}

# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------

# Matriz de retornos (numpy para velocidad)
ret_mat = returns_clean.values  # (T, N)
ret_dates = returns_clean.index
n_days = len(ret_dates)
n_assets = len(TICKERS)
cap_vec = cap_clean.values

# Estado: pesos actuales por estrategia
current_weights = {k: strat_equal_weight(n_assets) for k in STRATEGIES}

# Resultado: retornos diarios por estrategia + pesos en cada rebalanceo
strategies_returns = {k: np.full(n_days, np.nan) for k in STRATEGIES}
strategies_weights = {k: [] for k in STRATEGIES}
rebal_log = []

# Mapear índice del rebalanceo
rebal_idx_set = set()
rebal_idx_map = {}
for d in rebal_dates:
    # El rebalanceo ocurre al cierre de la fecha d; los retornos de d se aplican con los pesos nuevos
    pos = ret_dates.get_indexer([d], method="ffill")[0]
    if pos >= 0:
        rebal_idx_set.add(pos)
        rebal_idx_map[pos] = d

print(f"[backtest] Simulando {n_days} días con {len(rebal_idx_set)} rebalanceos...")
print(f"[backtest] Esto puede tardar 1-3 minutos...")

for i in range(n_days):
    # Verificar si hoy es rebalanceo
    if i in rebal_idx_set:
        # Estimar μ y Σ con ventana 252d hacia atrás
        lo = max(0, i - ROLLING_WINDOW)
        win = ret_mat[lo:i, :]
        # Sólo usar activos con datos en la ventana
        valid = ~np.isnan(win).any(axis=0)
        if valid.sum() < 5:
            # No hay suficientes datos, mantener pesos actuales
            pass
        else:
            win_clean = win[:, valid]
            mu = np.nanmean(win_clean, axis=0)
            sigma = np.cov(win_clean, rowvar=False)
            # Expandir mu y sigma al tamaño completo
            mu_full = np.zeros(n_assets); mu_full[valid] = mu
            sigma_full = np.zeros((n_assets, n_assets)); sigma_full[np.ix_(valid, valid)] = sigma
            valid_full = np.zeros(n_assets, dtype=bool); valid_full[valid] = True

            for key, (label, fn) in STRATEGIES.items():
                try:
                    w_new = fn(mu_full, sigma_full, valid_full, cap_vec)
                    # Asegurar que sólo invertimos en activos válidos
                    w_new = w_new * valid_full
                    s = w_new.sum()
                    if s > 0:
                        w_new = w_new / s
                    # Costos de transacción: turnover * bps
                    turnover = np.abs(w_new - current_weights[key]).sum() / 2
                    tx_cost = turnover * (TX_COST_BPS / 10000)
                    current_weights[key] = w_new
                    strategies_weights[key].append({"date": str(ret_dates[i].date()), "weights": w_new.tolist()})
                except Exception as e:
                    pass
            rebal_log.append({"date": str(ret_dates[i].date())})

    # Aplicar retorno del día a cada estrategia
    r = ret_mat[i, :]
    for key in STRATEGIES:
        w = current_weights[key]
        # Retorno del portafolio = w . r, restando costo (ya cargado en el rebalanceo)
        if np.any(np.isnan(r)) or np.any(np.isnan(w)):
            strategies_returns[key][i] = np.nan
        else:
            strategies_returns[key][i] = float(np.dot(w, r))

    if (i + 1) % 500 == 0:
        print(f"  día {i+1}/{n_days} ({ret_dates[i].date()})")

# ---------------------------------------------------------------------------
# Equity curves y métricas
# ---------------------------------------------------------------------------

results = {"retornos": {}, "metricas": {}, "metadata": {}}
results["metadata"] = {
    "fecha_corrida": pd.Timestamp.now().isoformat(),
    "periodo": [str(ret_dates[0].date()), str(ret_dates[-1].date())],
    "n_days": int(n_days),
    "n_rebalances": len(rebal_idx_set),
    "tickers": TICKERS,
    "rolling_window": ROLLING_WINDOW,
    "rebal_freq": REBAL_FREQ,
    "tx_cost_bps": TX_COST_BPS,
    "rf_annual": RF_ANNUAL,
}

# Equity base 100
for key, (label, _) in STRATEGIES.items():
    r = strategies_returns[key]
    valid_mask = ~np.isnan(r)
    r_valid = r[valid_mask]
    equity = np.empty(len(r))
    equity[:] = np.nan
    equity[valid_mask] = 100 * np.cumprod(1 + r_valid)
    results["retornos"][key] = {
        "label": label,
        "dates": [str(d.date()) for d in ret_dates],
        "daily_returns": [None if np.isnan(x) else float(x) for x in r],
        "equity_base100": [None if np.isnan(x) else float(x) for x in equity],
    }

# Métricas
def compute_metrics(equity_arr, r_arr, label):
    valid = ~np.isnan(r_arr)
    r = r_arr[valid]
    e = equity_arr[valid]
    if len(r) < 60:
        return None
    n = len(r)
    total_ret = e[-1] / 100 - 1
    years = n / TRADING_DAYS
    ann_ret = (1 + total_ret) ** (1 / years) - 1
    ann_vol = np.nanstd(r, ddof=1) * np.sqrt(TRADING_DAYS)
    sharpe = (ann_ret - RF_ANNUAL) / ann_vol if ann_vol > 0 else 0
    neg = r[r < 0]
    ds_vol = np.nanstd(neg, ddof=1) * np.sqrt(TRADING_DAYS) if len(neg) > 1 else ann_vol
    sortino = (ann_ret - RF_ANNUAL) / ds_vol if ds_vol > 0 else 0
    # Max drawdown
    peak = e[0]
    max_dd = 0
    for v in e:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < max_dd: max_dd = dd
    calmar = ann_ret / abs(max_dd) if max_dd < 0 else 0
    # % meses positivos (sobre retornos mensuales agrupados en el array filtrado)
    # Usamos el mes calendario de las fechas correspondientes a r (filtradas)
    valid_dates = ret_dates[valid]
    monthly = []
    if len(valid_dates) > 0:
        cur_year = valid_dates[0].year
        cur_month = valid_dates[0].month
        start_eq = e[0]
        for j in range(1, n):
            d = valid_dates[j]
            if d.year != cur_year or d.month != cur_month:
                # Cierre de mes
                end_eq = e[j - 1]
                monthly.append(end_eq / start_eq - 1)
                cur_year, cur_month = d.year, d.month
                start_eq = e[j]
        # Cierre del último mes
        monthly.append(e[-1] / start_eq - 1)
    pos = sum(1 for m in monthly if m > 0)
    pct_pos = pos / len(monthly) if monthly else 0
    return {
        "label": label,
        "n_days": int(n),
        "ann_return": float(ann_ret),
        "ann_volatility": float(ann_vol),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_drawdown": float(max_dd),
        "calmar": float(calmar),
        "pct_positive_months": float(pct_pos),
        "final_value_base100": float(e[-1]),
    }

for key, (label, _) in STRATEGIES.items():
    r = strategies_returns[key]
    valid = ~np.isnan(r)
    e = np.where(valid, 100 * np.cumprod(np.where(valid, 1 + r, 1.0)), np.nan)
    # No funciona np.cumprod con nan, recalcular
    e = np.full(len(r), np.nan)
    cum = 100
    for i in range(len(r)):
        if valid[i]:
            cum *= 1 + r[i]
            e[i] = cum
    m = compute_metrics(e, r, label)
    if m:
        results["metricas"][key] = m

# Métricas por régimen
regimes = [
    ("2010-2013", "2010-01-01", "2013-12-31"),
    ("2014-2018", "2014-01-01", "2018-12-31"),
    ("2019-2021", "2019-01-01", "2021-12-31"),
    ("2022-2024", "2022-01-01", "2024-12-31"),
]
regime_results = {key: [] for key in STRATEGIES}
for r_name, r_start, r_end in regimes:
    for key, (label, _) in STRATEGIES.items():
        r = strategies_returns[key]
        valid = ~np.isnan(r)
        mask = valid & (ret_dates >= r_start) & (ret_dates <= r_end)
        if mask.sum() < 60:
            continue
        r_sub = r[mask]
        n = len(r_sub)
        total = (1 + r_sub).prod() - 1
        years = n / TRADING_DAYS
        ann = (1 + total) ** (1 / years) - 1 if years > 0 else 0
        regime_results[key].append({"regime": r_name, "ann_return": float(ann), "days": int(n)})
results["regime_returns"] = regime_results

# Pesos finales (al cierre)
for key in STRATEGIES:
    w_final = current_weights[key]
    results["metadata"]["final_weights_" + key] = {t: float(w) for t, w in zip(TICKERS, w_final)}

# ---------------------------------------------------------------------------
# Guardar
# ---------------------------------------------------------------------------

(DATA_DIR / "strategies.json").write_text(
    json.dumps(results["retornos"], ensure_ascii=False), encoding="utf-8"
)
(DATA_DIR / "metrics.json").write_text(
    json.dumps({**results["metricas"], "regime_returns": results["regime_returns"]}, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
(DATA_DIR / "backtest_meta.json").write_text(
    json.dumps(results["metadata"], indent=2, ensure_ascii=False), encoding="utf-8"
)
# Pesos: archivo separado (grande)
weights_export = {}
for key, log in strategies_weights.items():
    weights_export[key] = log
(DATA_DIR / "backtest_weights.json").write_text(
    json.dumps(weights_export, ensure_ascii=False), encoding="utf-8"
)

print(f"\n[backtest] OK. Guardado en {DATA_DIR}/")
print(f"\n[backtest] Métricas:")
for key, m in results["metricas"].items():
    print(f"  {key:30s} ret={m['ann_return']*100:6.2f}% vol={m['ann_volatility']*100:5.2f}% sharpe={m['sharpe']:5.2f} maxDD={m['max_drawdown']*100:6.2f}%")
