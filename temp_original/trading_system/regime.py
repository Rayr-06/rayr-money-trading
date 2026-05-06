"""
ADVANCED MARKET REGIME DETECTION
--------------------------------
Replaces v1's simple ATR/EMA-gap classifier with a 3-signal consensus:
  - ATR percentile  -> volatility state
  - ADX             -> trend strength
  - EMA slope       -> directional bias

Outputs one of:
  STRONG_TREND_UP / STRONG_TREND_DN  -> trend strategy at full size
  WEAK_TREND_UP / WEAK_TREND_DN      -> trend strategy at half size
  RANGE                              -> mean-reversion strategy
  CHAOTIC                            -> NO TRADE
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .config import STRAT


# Regime constants (string labels are stable for logging/analytics)
STRONG_TREND_UP = "STRONG_TREND_UP"
STRONG_TREND_DN = "STRONG_TREND_DN"
WEAK_TREND_UP = "WEAK_TREND_UP"
WEAK_TREND_DN = "WEAK_TREND_DN"
RANGE = "RANGE"
CHAOTIC = "CHAOTIC"

TREND_REGIMES = {STRONG_TREND_UP, STRONG_TREND_DN, WEAK_TREND_UP, WEAK_TREND_DN}
LONG_REGIMES = {STRONG_TREND_UP, WEAK_TREND_UP}
SHORT_REGIMES = {STRONG_TREND_DN, WEAK_TREND_DN}


@dataclass
class RegimeSnapshot:
    label: str
    adx: float
    atr_pct_rank: float    # 0.0–1.0
    ema_slope_bps: float   # bps/bar
    confidence: float      # 0.0–1.0 — agreement between signals

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "adx": float(self.adx),
            "atr_pct_rank": float(self.atr_pct_rank),
            "ema_slope_bps": float(self.ema_slope_bps),
            "confidence": float(self.confidence),
        }


def classify(feat: pd.DataFrame) -> RegimeSnapshot:
    """
    Compute the regime for the LAST bar of `feat`. `feat` must already have:
      atr, atr_pct, ema_fast, ema_slow, adx
    """
    if len(feat) < STRAT.atr_pct_window:
        return RegimeSnapshot(CHAOTIC, 0.0, 0.5, 0.0, 0.0)

    last = feat.iloc[-1]
    # 1) Volatility state via ATR percentile rank over recent window
    win = feat["atr_pct"].iloc[-STRAT.atr_pct_window:]
    rank = float((win <= last["atr_pct"]).mean())   # 0..1

    # 2) Trend strength via ADX
    adx = float(last["adx"]) if not np.isnan(last["adx"]) else 0.0

    # 3) Directional bias via EMA50 slope (5-bar)
    if len(feat) >= 6:
        slope_bps = float(
            (feat["ema_fast"].iloc[-1] - feat["ema_fast"].iloc[-6])
            / max(feat["ema_fast"].iloc[-6], 1e-9) * 10_000 / 5
        )
    else:
        slope_bps = 0.0
    direction = 1 if slope_bps > 0 else (-1 if slope_bps < 0 else 0)

    # ----- Decision tree -----
    if rank >= STRAT.atr_pct_extreme:
        # Extreme volatility → don't trade regardless of trend signals
        return RegimeSnapshot(CHAOTIC, adx, rank, slope_bps, 0.9)

    if adx >= STRAT.adx_strong_trend and direction != 0:
        label = STRONG_TREND_UP if direction > 0 else STRONG_TREND_DN
        # Confidence rises with ADX above the threshold
        conf = min(1.0, 0.7 + (adx - STRAT.adx_strong_trend) / 50)
        return RegimeSnapshot(label, adx, rank, slope_bps, conf)

    if adx >= STRAT.adx_weak_trend and direction != 0:
        label = WEAK_TREND_UP if direction > 0 else WEAK_TREND_DN
        conf = 0.5 + (adx - STRAT.adx_weak_trend) / 40
        return RegimeSnapshot(label, adx, rank, slope_bps, conf)

    # Low ADX + non-extreme vol = mean-reverting environment
    if rank <= 0.7 and adx < STRAT.adx_weak_trend:
        return RegimeSnapshot(RANGE, adx, rank, slope_bps, 0.7)

    return RegimeSnapshot(CHAOTIC, adx, rank, slope_bps, 0.4)
