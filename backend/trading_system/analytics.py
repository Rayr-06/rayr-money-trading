"""
PERFORMANCE ANALYTICS + SELF-IMPROVEMENT FEATURE LOG
----------------------------------------------------
- Append every trade to a structured JSONL log (trades.jsonl)
- Append every trade-quality decision (taken or rejected) to features.jsonl
- Compute summary metrics: Sharpe, Sortino, profit factor, max DD,
  per-strategy / per-regime breakdown
- Optional: train a tiny logistic ranker on historical features
  to weight future trade-quality scores (self-improvement loop)
"""
from __future__ import annotations
import os
import json
import math
from datetime import datetime
from typing import Dict, List, Iterable
from pathlib import Path
import numpy as np
import pandas as pd
from loguru import logger
from .config import ANLY


def _ensure_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def log_feature(record: dict) -> None:
    _ensure_dir(ANLY.feature_log_path)
    record = {**record, "ts_logged": datetime.utcnow().isoformat()}
    with open(ANLY.feature_log_path, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def log_trade(record: dict) -> None:
    _ensure_dir(ANLY.trade_log_path)
    record = {**record, "ts_logged": datetime.utcnow().isoformat()}
    with open(ANLY.trade_log_path, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def load_trades() -> pd.DataFrame:
    if not os.path.exists(ANLY.trade_log_path): return pd.DataFrame()
    rows = []
    with open(ANLY.trade_log_path) as f:
        for line in f:
            try: rows.append(json.loads(line))
            except json.JSONDecodeError: continue
    return pd.DataFrame(rows)


# ----------------- Metrics ----------------- #

def compute_metrics(equity_curve: List[dict],
                    trades: List[dict]) -> Dict:
    if not equity_curve:
        return {}
    eq = pd.Series(
        [p["equity"] for p in equity_curve],
        index=pd.to_datetime([p["ts"] for p in equity_curve]),
    )
    rets = eq.pct_change().dropna()

    sharpe = sortino = 0.0
    if len(rets) > 1 and rets.std() > 0:
        sharpe = float(np.sqrt(252) * rets.mean() / rets.std())
        downside = rets[rets < 0]
        if len(downside) > 1 and downside.std() > 0:
            sortino = float(np.sqrt(252) * rets.mean() / downside.std())

    rolling_max = eq.cummax()
    drawdown = eq / rolling_max - 1.0
    max_dd = float(drawdown.min()) if not drawdown.empty else 0.0

    # Calmar = CAGR / |MaxDD|
    days = max((eq.index[-1] - eq.index[0]).days, 1)
    years = days / 365.25
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0

    pnls = [t["pnl"] for t in trades] if trades else []
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = len(wins) / len(pnls) if pnls else 0.0
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else (
        float("inf") if wins else 0.0)
    expectancy = sum(pnls) / len(pnls) if pnls else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0

    # Per-strategy + per-regime
    by_strategy = _group_pnl(trades, "strategy")
    by_regime = _group_pnl(trades, "regime")

    # Drawdown curve (downsample to keep API responses small)
    dd_curve = [
        {"ts": ts.isoformat(), "dd": float(v)}
        for ts, v in drawdown.iloc[::max(1, len(drawdown)//500)].items()
    ]

    return {
        "sharpe": sharpe, "sortino": sortino, "calmar": calmar,
        "max_drawdown": max_dd, "cagr": cagr,
        "win_rate": win_rate, "profit_factor": profit_factor,
        "expectancy": expectancy, "avg_win": avg_win, "avg_loss": avg_loss,
        "trades": len(pnls),
        "by_strategy": by_strategy, "by_regime": by_regime,
        "drawdown_curve": dd_curve,
    }


def _group_pnl(trades: List[dict], key: str) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for t in trades:
        k = t.get(key, "n/a")
        b = out.setdefault(k, {"trades": 0, "pnl": 0.0, "wins": 0})
        b["trades"] += 1
        b["pnl"] += t["pnl"]
        if t["pnl"] > 0: b["wins"] += 1
    for k, b in out.items():
        b["win_rate"] = b["wins"] / b["trades"] if b["trades"] else 0.0
        b["pnl"] = round(b["pnl"], 2)
    return out


# --------- Optional: simple self-improvement ranker --------- #

def train_quality_ranker() -> Dict:
    """
    Trains a logistic regression on historical (features → was_winner).
    Returns coefficient dict you can persist & multiply against future quality
    scores. Designed to fail gracefully if there's not enough data.
    """
    df = load_trades()
    if len(df) < 50:
        return {"trained": False, "reason": "need >=50 trades"}
    cols = ["quality_score", "atr_pct_rank", "adx", "ema_slope_bps"]
    feats = df[[c for c in cols if c in df.columns]].apply(
        pd.to_numeric, errors="coerce").dropna()
    if len(feats) < 30: return {"trained": False, "reason": "feature gaps"}
    y = (df.loc[feats.index, "pnl"] > 0).astype(int).values
    X = feats.values
    # Standardize
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd
    # Simple ridge logistic via numpy (avoid sklearn dep)
    w = np.zeros(Xs.shape[1])
    lr, l2 = 0.05, 0.01
    for _ in range(400):
        p = 1 / (1 + np.exp(-Xs @ w))
        grad = Xs.T @ (p - y) / len(y) + l2 * w
        w -= lr * grad
    return {
        "trained": True, "n_samples": int(len(y)),
        "coef": dict(zip(feats.columns, w.tolist())),
        "mu": mu.tolist(), "sd": sd.tolist(),
    }
