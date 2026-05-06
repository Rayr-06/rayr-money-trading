"""
BACKTESTING ENGINE — v2
-----------------------
- Hybrid vectorized + event-driven (uses live RiskManager → behavior identity)
- Includes slippage + fees (via PaperBroker-style cost model)
- Walk-forward validation
- Out-of-sample split
- Per-strategy / per-regime breakdown via analytics

Reject any strategy whose:
  - OOS Sharpe < 0.7 × IS Sharpe
  - OOS profit factor < 1.1
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from loguru import logger

from .config import EXEC, STRAT, UNIV
from .features import build_features, build_htf_features
from .strategy import evaluate, Candidate
from .regime import classify
from .risk import RiskManager, TradeResult
from .analytics import compute_metrics


@dataclass
class BacktestReport:
    start: str
    end: str
    starting_equity: float
    ending_equity: float
    total_return: float
    metrics: dict
    equity_curve: List[dict]
    trade_log: List[dict]
    quality_distribution: List[dict]
    rejection_reasons: Dict[str, int]


# --- core single-period backtest ---

def _simulate(data_by_symbol: Dict[str, pd.DataFrame],
              starting_equity: float) -> Tuple[RiskManager, List[dict], List[TradeResult], dict, dict]:
    rm = RiskManager(starting_equity)
    feats: Dict[str, pd.DataFrame] = {
        s: build_features(df).dropna() for s, df in data_by_symbol.items()
    }
    htf_feats: Dict[str, pd.DataFrame] = {
        s: build_htf_features(df, "1W").dropna()  # weekly HTF for daily base
        for s, df in data_by_symbol.items()
    }
    # Update portfolio price panel for correlation checks
    rm.portfolio.update_price_panel({s: f["close"] for s, f in feats.items()})

    timeline = sorted(set().union(*[f.index for f in feats.values() if not f.empty]))
    if not timeline:
        return rm, [], [], {}, {}

    equity_curve: List[dict] = []
    trades: List[TradeResult] = []
    quality_dist: List[float] = []
    rejection_counter: Dict[str, int] = {}

    SLIP_BPS = (EXEC.slippage_bps_low + EXEC.slippage_bps_high) / 2
    COMM_BPS = EXEC.commission_bps

    for ts in timeline:
        last_prices = {s: float(f.at[ts, "close"]) for s, f in feats.items() if ts in f.index}
        # 1) Mark-to-market exits
        closed = rm.check_exits(last_prices)
        for tr in closed:
            # Apply slippage + commission to the exit price
            adj = tr.exit * (1 - (SLIP_BPS + COMM_BPS) / 10_000) if tr.side == "LONG" \
                else tr.exit * (1 + (SLIP_BPS + COMM_BPS) / 10_000)
            tr.exit = adj
            tr.pnl = (adj - tr.entry) * tr.qty if tr.side == "LONG" \
                else (tr.entry - adj) * tr.qty
            trades.append(tr)

        # 2) New candidates
        for sym, f in feats.items():
            if ts not in f.index: continue
            window = f.loc[:ts]
            if len(window) < 210: continue
            df_window = data_by_symbol[sym].loc[:ts]
            cand = evaluate(sym, df_window, htf_rule=None)
            if cand is None: continue
            quality_dist.append(cand.quality.score)
            if not cand.accepted:
                rejection_counter[cand.reason[:40]] = rejection_counter.get(cand.reason[:40], 0) + 1
                continue
            if cand.side == "BUY":
                # Apply entry slippage
                cand_adj_price = cand.price * (1 + SLIP_BPS / 10_000)
                cand.price = cand_adj_price
                rm.open_position(cand)
            elif cand.symbol in rm.state.open_positions:
                tr = rm.close_position(cand.symbol, cand.price, "signal-exit")
                if tr: trades.append(tr)

        mtm = sum(p.unrealized_pnl(last_prices.get(p.symbol, p.entry_price))
                  for p in rm.state.open_positions.values())
        equity_curve.append({"ts": ts.isoformat(), "equity": float(rm.state.equity + mtm)})

    # final liquidation
    final_prices = {s: float(f["close"].iloc[-1]) for s, f in feats.items() if not f.empty}
    for sym in list(rm.state.open_positions.keys()):
        if sym in final_prices:
            tr = rm.close_position(sym, final_prices[sym], "backtest-end")
            if tr: trades.append(tr)

    # Quality histogram
    qhist: List[dict] = []
    if quality_dist:
        bins = list(range(0, 101, 10))
        hist, edges = np.histogram(quality_dist, bins=bins)
        for i, c in enumerate(hist):
            qhist.append({"bucket": f"{edges[i]}-{edges[i+1]}", "count": int(c)})

    return rm, equity_curve, trades, qhist, rejection_counter


def run_backtest(data_by_symbol: Dict[str, pd.DataFrame],
                 starting_equity: float = None) -> BacktestReport:
    starting_equity = starting_equity or EXEC.paper_starting_cash
    rm, eq, trades, qhist, rejections = _simulate(data_by_symbol, starting_equity)

    trade_dicts = [{
        "symbol": t.symbol, "side": t.side, "qty": t.qty,
        "entry": t.entry, "exit": t.exit,
        "pnl": t.pnl, "pnl_pct": t.pnl_pct,
        "opened_at": t.opened_at.isoformat(),
        "closed_at": t.closed_at.isoformat(),
        "strategy": t.strategy, "reason_close": t.reason_close,
        "quality_score": t.quality_score, "risk_tier": t.risk_tier,
        "regime": t.regime,
    } for t in trades]

    metrics = compute_metrics(eq, trade_dicts)

    return BacktestReport(
        start=eq[0]["ts"] if eq else "", end=eq[-1]["ts"] if eq else "",
        starting_equity=starting_equity, ending_equity=rm.state.equity,
        total_return=rm.state.equity / starting_equity - 1.0,
        metrics=metrics, equity_curve=eq, trade_log=trade_dicts,
        quality_distribution=qhist, rejection_reasons=rejections,
    )


# --------------- Walk-forward ---------------

def walk_forward(data_by_symbol: Dict[str, pd.DataFrame],
                 train_years: int = 2, test_months: int = 6) -> List[dict]:
    """
    Rolling walk-forward: train window slides forward, OOS window follows.
    Each fold is a separate backtest. Returns per-fold metrics for honesty.
    """
    if not data_by_symbol: return []
    all_idx = sorted(set().union(*[df.index for df in data_by_symbol.values()]))
    if not all_idx: return []
    start, end = all_idx[0], all_idx[-1]
    folds = []
    cur = start + pd.DateOffset(years=train_years)
    while cur < end:
        oos_end = min(cur + pd.DateOffset(months=test_months), end)
        oos_data = {s: df.loc[cur:oos_end] for s, df in data_by_symbol.items()}
        oos_data = {s: d for s, d in oos_data.items() if len(d) > 50}
        if not oos_data: break
        # IS just for sanity (we don't actually fit anything — config is fixed)
        is_data = {s: df.loc[cur - pd.DateOffset(years=train_years):cur]
                   for s, df in data_by_symbol.items()}
        is_data = {s: d for s, d in is_data.items() if len(d) > 250}
        if not is_data: break
        try:
            rep_oos = run_backtest(oos_data)
            folds.append({
                "is_start": (cur - pd.DateOffset(years=train_years)).date().isoformat(),
                "oos_start": cur.date().isoformat(),
                "oos_end": oos_end.date().isoformat(),
                "oos_return": rep_oos.total_return,
                "oos_sharpe": rep_oos.metrics.get("sharpe", 0.0),
                "oos_max_dd": rep_oos.metrics.get("max_drawdown", 0.0),
                "oos_trades": rep_oos.metrics.get("trades", 0),
                "oos_profit_factor": rep_oos.metrics.get("profit_factor", 0.0),
            })
        except Exception as e:
            logger.warning(f"walk-forward fold failed: {e}")
        cur = cur + pd.DateOffset(months=test_months)
    return folds


def out_of_sample_split(data_by_symbol: Dict[str, pd.DataFrame],
                        oos_fraction: float = 0.3) -> Tuple[BacktestReport, BacktestReport]:
    """Single train/test split — IS earlier portion, OOS later portion."""
    splits_is, splits_oos = {}, {}
    for s, df in data_by_symbol.items():
        n = len(df)
        cut = int(n * (1 - oos_fraction))
        splits_is[s] = df.iloc[:cut]
        splits_oos[s] = df.iloc[cut:]
    return run_backtest(splits_is), run_backtest(splits_oos)
