"""
RAYR MONEY v2 — entrypoint.
Commands:
  python -m trading_system.main once         # one cycle
  python -m trading_system.main live         # scheduler loop
  python -m trading_system.main backtest     # 5y backtest
  python -m trading_system.main walkforward  # walk-forward validation
"""
from __future__ import annotations
import sys
import json
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler

from .config import UNIV, EXEC, STRAT
from .data import fetch_universe
from .strategy import evaluate_universe
from .risk import RiskManager
from .execution import get_broker, OrderRejected
from .backtest import run_backtest, walk_forward, out_of_sample_split
from .analytics import log_trade, log_feature
from . import notify


_risk: RiskManager | None = None
_broker = None


def _bootstrap():
    global _risk, _broker
    if _broker is None:
        _broker = get_broker()
    if _risk is None:
        cash = _broker.get_cash()
        _risk = RiskManager(cash)
    return _risk, _broker


def trading_cycle() -> None:
    rm, br = _bootstrap()
    rm.roll_day()
    if rm.state.halted:
        logger.warning(f"halted: {rm.state.halt_reason}")
        return

    universe = list((UNIV.equities_us if EXEC.broker in ("alpaca", "paper")
                     else UNIV.equities_in).keys())
    data = fetch_universe(universe, UNIV.timeframe, lookback_days=365 * 3)
    rm.portfolio.update_price_panel({s: df["close"] for s, df in data.items()})

    # 1) Mark to market exits
    last_prices = {s: float(df["close"].iloc[-1]) for s, df in data.items()}
    closed = rm.check_exits(last_prices)
    for tr in closed:
        try:
            br.submit_order(tr.symbol, "SELL" if tr.side == "LONG" else "BUY", tr.qty)
        except OrderRejected as e:
            logger.error(f"exit rejected: {e}")
        log_trade({
            "symbol": tr.symbol, "side": tr.side, "qty": tr.qty,
            "entry": tr.entry, "exit": tr.exit, "pnl": tr.pnl,
            "pnl_pct": tr.pnl_pct, "strategy": tr.strategy,
            "reason_close": tr.reason_close,
            "quality_score": tr.quality_score, "risk_tier": tr.risk_tier,
        })
        notify.send(
            f"🔚 *CLOSE* {tr.symbol} {tr.side} pnl={tr.pnl:.2f} ({tr.pnl_pct:.2%}) "
            f"reason={tr.reason_close}"
        )

    # 2) Generate + filter + score candidates
    candidates = evaluate_universe(data, htf_rule="1W")
    accepted = [c for c in candidates if c.accepted]
    logger.info(f"{len(candidates)} candidates, {len(accepted)} above quality {STRAT.quality_min_score}")

    # Log every candidate (winners and losers — feeds self-improvement loop)
    for c in candidates:
        log_feature(c.to_dict())

    for cand in accepted:
        ok, reason = rm.approve(cand)
        if not ok:
            logger.info(f"reject {cand.symbol}: {reason}")
            continue
        pos = rm.open_position(cand)
        if pos is None: continue
        try:
            br.submit_order(cand.symbol, cand.side, pos.qty,
                            atr_pct_hint=cand.atr / max(cand.price, 1e-9))
            notify.send(
                f"🟢 *OPEN* {cand.side} {pos.qty} {cand.symbol} @ {cand.price:.2f}\n"
                f"strat={cand.strategy} regime={cand.regime.label} "
                f"q={cand.quality.score:.0f} ({cand.risk_tier()})\n"
                f"stop={pos.stop_price:.2f} tp={pos.take_profit:.2f}"
            )
        except OrderRejected as e:
            logger.error(f"open rejected: {e}")
            rm.state.open_positions.pop(cand.symbol, None)

    if rm.state.halted:
        notify.send(f"🛑 *KILL SWITCH* {rm.state.halt_reason}")


def run_live() -> None:
    sched = BlockingScheduler(timezone="UTC")
    sched.add_job(trading_cycle, "cron",
                  day_of_week="mon-fri", hour="13-20", minute="*/5")
    logger.info("live scheduler started")
    notify.send("🚀 RAYR MONEY *online*")
    trading_cycle()
    sched.start()


def run_backtest_cli() -> None:
    universe = list((UNIV.equities_us if EXEC.broker in ("alpaca", "paper")
                     else UNIV.equities_in).keys())
    data = fetch_universe(universe, UNIV.timeframe, lookback_days=365 * 5)
    rep = run_backtest(data)
    summary = {
        "starting_equity": rep.starting_equity,
        "ending_equity": rep.ending_equity,
        "total_return": rep.total_return,
        **{k: v for k, v in rep.metrics.items()
           if k not in ("by_strategy", "by_regime", "drawdown_curve")},
    }
    print(json.dumps(summary, indent=2, default=str))
    print(f"\n{rep.metrics.get('trades', 0)} trades | "
          f"win {rep.metrics.get('win_rate',0):.1%} | "
          f"PF {rep.metrics.get('profit_factor',0):.2f} | "
          f"Sharpe {rep.metrics.get('sharpe',0):.2f} | "
          f"MaxDD {rep.metrics.get('max_drawdown',0):.1%}")


def run_walkforward_cli() -> None:
    universe = list((UNIV.equities_us if EXEC.broker in ("alpaca", "paper")
                     else UNIV.equities_in).keys())
    data = fetch_universe(universe, UNIV.timeframe, lookback_days=365 * 5)
    folds = walk_forward(data, train_years=2, test_months=6)
    print(json.dumps(folds, indent=2, default=str))
    if folds:
        avg_sharpe = sum(f["oos_sharpe"] for f in folds) / len(folds)
        avg_pf = sum(f["oos_profit_factor"] for f in folds
                     if f["oos_profit_factor"] != float("inf")) / len(folds)
        print(f"\nWalk-forward avg OOS Sharpe: {avg_sharpe:.2f} | avg PF: {avg_pf:.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":            trading_cycle()
    elif cmd == "live":          run_live()
    elif cmd == "backtest":      run_backtest_cli()
    elif cmd == "walkforward":   run_walkforward_cli()
    elif cmd == "verify":
        from .verify import run_verification
        success = run_verification(allow_live="--live" in sys.argv)
        sys.exit(0 if success else 1)
    else:
        print(f"unknown command: {cmd}")
        print("Available: once | live | backtest | walkforward | verify")
        sys.exit(1)
