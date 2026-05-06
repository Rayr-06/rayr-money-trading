"""
HARD TRADE FILTERS
------------------
Trade-blocking rules applied BEFORE quality scoring.
If any filter fails, the candidate is rejected with a reason.

Philosophy: prefer NO TRADE over a marginal one.
"""
from __future__ import annotations
from datetime import time
import pandas as pd
from .config import FILT, STRAT


def _is_intraday(ts: pd.Timestamp, tf: str) -> bool:
    return tf in ("1m", "5m", "15m", "1h")


def time_of_day_ok(ts: pd.Timestamp, tf: str,
                   open_time=time(13, 30), close_time=time(20, 0)) -> tuple[bool, str]:
    """
    Block trades in the first N and last M minutes of the session.
    Defaults to NYSE RTH (13:30–20:00 UTC). Configure as needed.
    Daily timeframe is always OK.
    """
    if not _is_intraday(ts, tf):
        return True, ""
    t = ts.tz_convert("UTC").time() if ts.tzinfo else ts.time()
    open_min = open_time.hour * 60 + open_time.minute
    close_min = close_time.hour * 60 + close_time.minute
    cur_min = t.hour * 60 + t.minute
    if cur_min < open_min + FILT.skip_open_minutes:
        return False, "within open-blackout window"
    if cur_min > close_min - FILT.skip_close_minutes:
        return False, "within close-blackout window"
    return True, ""


def liquidity_ok(feat: pd.DataFrame) -> tuple[bool, str]:
    if "volume" not in feat or "close" not in feat:
        return True, ""
    avg_dollar_vol = float((feat["volume"] * feat["close"]).rolling(20).mean().iloc[-1])
    if avg_dollar_vol < FILT.min_avg_dollar_volume:
        return False, f"liquidity ${avg_dollar_vol:,.0f} < min"
    return True, ""


def volume_spike_ok(feat: pd.DataFrame) -> tuple[bool, str]:
    """Reject obvious news-candle spikes — they break statistical assumptions."""
    if "volume" not in feat: return True, ""
    last_vol = float(feat["volume"].iloc[-1])
    avg = float(feat["volume"].rolling(20).mean().iloc[-1])
    if avg <= 0: return True, ""
    if last_vol / avg >= STRAT.vol_spike_mult:
        return False, f"volume spike {last_vol/avg:.1f}× avg"
    return True, ""


def volatility_ok(feat: pd.DataFrame) -> tuple[bool, str]:
    if "atr_pct" not in feat or len(feat) < STRAT.atr_pct_window:
        return True, ""
    last = float(feat["atr_pct"].iloc[-1])
    win = feat["atr_pct"].iloc[-STRAT.atr_pct_window:]
    rank = float((win <= last).mean())
    if rank >= STRAT.atr_pct_extreme:
        return False, f"ATR percentile {rank:.0%} (extreme)"
    return True, ""


def blackout_ok(ts: pd.Timestamp) -> tuple[bool, str]:
    d = ts.strftime("%Y-%m-%d")
    if d in set(FILT.blackout_dates):
        return False, f"manual blackout date {d}"
    return True, ""


def run_all(feat: pd.DataFrame, ts: pd.Timestamp, tf: str) -> tuple[bool, str]:
    """Return (passed, reason). Reason empty if passed."""
    for fn in (
        lambda: time_of_day_ok(ts, tf),
        lambda: liquidity_ok(feat),
        lambda: volume_spike_ok(feat),
        lambda: volatility_ok(feat),
        lambda: blackout_ok(ts),
    ):
        ok, reason = fn()
        if not ok:
            return False, reason
    return True, ""
