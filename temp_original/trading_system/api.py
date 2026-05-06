"""
RAYR MONEY v2 — REST API for the dashboard.
"""
from __future__ import annotations
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import UNIV, EXEC, RISK, STRAT
from .data import fetch_universe
from .strategy import evaluate_universe
from .regime import classify
from .features import build_features
from .backtest import run_backtest, walk_forward, out_of_sample_split
from .analytics import compute_metrics, train_quality_ranker
from .main import _bootstrap, trading_cycle


app = FastAPI(title="RAYR MONEY API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def _universe():
    return list((UNIV.equities_us if EXEC.broker in ("alpaca", "paper")
                 else UNIV.equities_in).keys())


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "ts": datetime.utcnow().isoformat()}


@app.get("/signals")
def signals():
    """Live candidates (accepted + rejected, with quality breakdown)."""
    data = fetch_universe(_universe(), UNIV.timeframe, lookback_days=365 * 2)
    cands = evaluate_universe(data, htf_rule="1W")
    return {
        "count_total": len(cands),
        "count_accepted": sum(1 for c in cands if c.accepted),
        "candidates": [c.to_dict() for c in cands],
    }


@app.get("/trade_quality_score")
def trade_quality_score():
    """Returns the quality breakdown for every symbol that produced a raw signal."""
    data = fetch_universe(_universe(), UNIV.timeframe, lookback_days=365 * 2)
    cands = evaluate_universe(data, htf_rule="1W")
    return {
        "threshold_min": STRAT.quality_min_score,
        "threshold_high": STRAT.quality_high_score,
        "scores": [
            {"symbol": c.symbol, "side": c.side, "tier": c.risk_tier(),
             "accepted": c.accepted, **c.quality.to_dict()}
            for c in cands
        ],
    }


@app.get("/market_regime")
def market_regime():
    data = fetch_universe(_universe(), UNIV.timeframe, lookback_days=365 * 2)
    out = []
    for sym, df in data.items():
        if len(df) < 220: continue
        feat = build_features(df).dropna()
        if feat.empty: continue
        snap = classify(feat)
        out.append({"symbol": sym, **snap.to_dict()})
    return {"regimes": out}


@app.get("/positions")
def positions():
    rm, br = _bootstrap()
    return {
        "equity": rm.state.equity,
        "cash": br.get_cash(),
        "halted": rm.state.halted,
        "halt_reason": rm.state.halt_reason,
        "consecutive_losses": rm.state.consecutive_losses,
        "open": [
            {
                "symbol": p.symbol, "side": p.side, "qty": p.qty,
                "entry": p.entry_price, "stop": p.stop_price,
                "target": p.take_profit, "strategy": p.strategy,
                "quality_score": p.quality_score, "risk_tier": p.risk_tier,
                "trail_active": p.trail_active,
                "opened_at": p.opened_at.isoformat(),
            } for p in rm.state.open_positions.values()
        ],
    }


@app.get("/risk_state")
def risk_state():
    rm, _ = _bootstrap()
    total_open_risk = sum(
        abs(p.entry_price - p.stop_price) * p.qty
        for p in rm.state.open_positions.values()
    )
    daily_pnl_pct = rm.state.realized_pnl_today / max(rm.state.starting_equity_today, 1e-9)
    weekly_pnl_pct = rm.state.realized_pnl_week / max(rm.state.starting_equity_week, 1e-9)
    return {
        "equity": rm.state.equity,
        "halted": rm.state.halted, "halt_reason": rm.state.halt_reason,
        "consecutive_losses": rm.state.consecutive_losses,
        "max_consecutive_losses": RISK.max_consecutive_losses,
        "daily_pnl_pct": daily_pnl_pct,
        "max_daily_loss": RISK.max_daily_loss,
        "weekly_pnl_pct": weekly_pnl_pct,
        "max_weekly_loss": RISK.max_weekly_loss,
        "total_open_risk_pct": total_open_risk / max(rm.state.equity, 1e-9),
        "max_portfolio_risk": RISK.max_portfolio_risk,
        "open_positions": len(rm.state.open_positions),
        "max_concurrent_positions": RISK.max_concurrent_positions,
    }


@app.get("/performance")
def performance(years: int = 3):
    data = fetch_universe(_universe(), UNIV.timeframe, lookback_days=365*years)
    if not data: raise HTTPException(503, "no data")
    rep = run_backtest(data)
    return {
        "summary": {
            "starting_equity": rep.starting_equity,
            "ending_equity": rep.ending_equity,
            "total_return": rep.total_return,
            **rep.metrics,
        },
        "equity_curve": rep.equity_curve[-500:],
        "trade_log": rep.trade_log[-100:],
    }


@app.get("/performance_detailed")
def performance_detailed(years: int = 3):
    data = fetch_universe(_universe(), UNIV.timeframe, lookback_days=365*years)
    if not data: raise HTTPException(503, "no data")
    rep = run_backtest(data)
    is_rep, oos_rep = out_of_sample_split(data, oos_fraction=0.3)
    folds = walk_forward(data, train_years=2, test_months=6)
    return {
        "summary": rep.metrics,
        "in_sample": {
            "return": is_rep.total_return,
            "sharpe": is_rep.metrics.get("sharpe", 0.0),
            "max_dd": is_rep.metrics.get("max_drawdown", 0.0),
            "trades": is_rep.metrics.get("trades", 0),
        },
        "out_of_sample": {
            "return": oos_rep.total_return,
            "sharpe": oos_rep.metrics.get("sharpe", 0.0),
            "max_dd": oos_rep.metrics.get("max_drawdown", 0.0),
            "trades": oos_rep.metrics.get("trades", 0),
        },
        "walk_forward_folds": folds,
        "quality_distribution": rep.quality_distribution,
        "rejection_reasons": rep.rejection_reasons,
        "by_strategy": rep.metrics.get("by_strategy", {}),
        "by_regime": rep.metrics.get("by_regime", {}),
        "drawdown_curve": rep.metrics.get("drawdown_curve", []),
    }


@app.post("/run-cycle")
def run_cycle():
    trading_cycle()
    return {"ok": True, "ts": datetime.utcnow().isoformat()}


@app.post("/kill-switch")
def kill_switch():
    rm, _ = _bootstrap()
    rm.state.halted = True
    rm.state.halt_reason = "manual override"
    return {"halted": True, "reason": rm.state.halt_reason}


@app.post("/resume")
def resume():
    rm, _ = _bootstrap()
    rm.state.halted = False; rm.state.halt_reason = ""
    rm.state.consecutive_losses = 0
    return {"halted": False}


@app.post("/train-ranker")
def train_ranker():
    """Train the optional self-improvement quality ranker on logged trades."""
    return train_quality_ranker()
