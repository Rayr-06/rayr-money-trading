"""
TRADE QUALITY SCORING ENGINE
----------------------------
Every candidate trade is scored 0..100 across 4 dimensions:
   trend_strength (ADX)            — 30 pts
   volume_confirm                  — 20 pts
   volatility_fit (ATR percentile) — 20 pts
   mtf_alignment                   — 30 pts

Trades scoring below STRAT.quality_min_score are REJECTED.
Trades scoring above STRAT.quality_high_score qualify for the high-risk tier.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from .config import STRAT
from .regime import LONG_REGIMES, SHORT_REGIMES, TREND_REGIMES


@dataclass
class QualityBreakdown:
    score: float
    trend_pts: float
    volume_pts: float
    volatility_pts: float
    mtf_pts: float
    notes: str

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "trend_pts": round(self.trend_pts, 1),
            "volume_pts": round(self.volume_pts, 1),
            "volatility_pts": round(self.volatility_pts, 1),
            "mtf_pts": round(self.mtf_pts, 1),
            "notes": self.notes,
        }


def _trend_pts(adx: float) -> float:
    # 0 at ADX=10, 30 at ADX>=35, linear in between
    if adx <= 10: return 0.0
    if adx >= 35: return 30.0
    return 30.0 * (adx - 10) / 25.0


def _volume_pts(last_vol: float, vol_avg: float) -> float:
    if vol_avg <= 0: return 10.0
    ratio = last_vol / vol_avg
    # Sweet spot is 1.2x – 2.5x avg. Below 0.8x = weak. Above 4x = news/spike (penalize).
    if ratio < 0.8: return 0.0
    if ratio < 1.2: return 8.0
    if ratio <= 2.5: return 20.0
    if ratio <= 4.0: return 12.0
    return 4.0  # Suspicious spike — partial credit only


def _volatility_pts(atr_rank: float) -> float:
    # We want NORMAL volatility. 0.2–0.7 percentile = sweet spot.
    if atr_rank < 0.10 or atr_rank > 0.90: return 0.0
    if 0.20 <= atr_rank <= 0.70: return 20.0
    # Tapering edges
    if atr_rank < 0.20: return 20.0 * (atr_rank - 0.10) / 0.10
    return 20.0 * (0.90 - atr_rank) / 0.20


def _mtf_pts(side: str, htf_feat: Optional[pd.DataFrame]) -> tuple[float, str]:
    """Higher-timeframe alignment: HTF EMA50 > EMA200 supports BUY, etc."""
    if htf_feat is None or htf_feat.empty:
        return 10.0, "no HTF data — neutral credit"
    last = htf_feat.iloc[-1]
    if pd.isna(last.get("ema_fast")) or pd.isna(last.get("ema_slow")):
        return 10.0, "HTF emas not ready"
    htf_bull = last["ema_fast"] > last["ema_slow"]
    htf_above_vwap = last["close"] > last.get("vwap", last["close"])
    if side == "BUY":
        if htf_bull and htf_above_vwap: return 30.0, "HTF bullish + above VWAP"
        if htf_bull: return 20.0, "HTF bullish"
        if htf_above_vwap: return 10.0, "HTF mixed (above VWAP)"
        return 0.0, "HTF bearish — reject by score"
    else:  # SELL
        if (not htf_bull) and (not htf_above_vwap): return 30.0, "HTF bearish + below VWAP"
        if not htf_bull: return 20.0, "HTF bearish"
        if not htf_above_vwap: return 10.0, "HTF mixed (below VWAP)"
        return 0.0, "HTF bullish — reject by score"


def score_trade(
    side: str,
    feat: pd.DataFrame,
    htf_feat: Optional[pd.DataFrame],
    regime_label: str,
) -> QualityBreakdown:
    last = feat.iloc[-1]
    vol_avg = feat["volume"].rolling(20).mean().iloc[-1] if "volume" in feat else 0
    atr_rank = float(
        (feat["atr_pct"].iloc[-STRAT.atr_pct_window:] <= last["atr_pct"]).mean()
    ) if len(feat) >= STRAT.atr_pct_window else 0.5

    t = _trend_pts(float(last.get("adx", 0.0)))
    v = _volume_pts(float(last.get("volume", 0.0)), float(vol_avg or 0.0))
    vol = _volatility_pts(atr_rank)
    mtf, note = _mtf_pts(side, htf_feat)

    score = t + v + vol + mtf

    # Regime sanity overlays
    if regime_label not in TREND_REGIMES and side == "BUY" and t > 15:
        # Trend points without trend regime is suspicious
        score -= 10
    if (side == "BUY" and regime_label in SHORT_REGIMES) or \
       (side == "SELL" and regime_label in LONG_REGIMES):
        score -= 25  # severe regime conflict

    return QualityBreakdown(
        score=max(0.0, min(100.0, score)),
        trend_pts=t, volume_pts=v, volatility_pts=vol, mtf_pts=mtf,
        notes=note,
    )
