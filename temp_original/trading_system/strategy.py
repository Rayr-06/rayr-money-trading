"""
STRATEGY ENGINE — v2
--------------------
Unchanged signal primitives (mean reversion + trend following), but now wrapped
with a `Candidate` object that carries:
  - regime snapshot
  - quality score breakdown
  - filter pass/fail reason

Candidates with quality < threshold are still RETURNED so the analytics layer
can log rejection reasons (self-improvement loop). The risk engine refuses to
open any candidate with `accepted=False`.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import pandas as pd

from .config import STRAT
from .features import build_features, build_htf_features
from .regime import (
    classify, RegimeSnapshot,
    LONG_REGIMES, SHORT_REGIMES, RANGE, CHAOTIC, TREND_REGIMES,
)
from .quality import score_trade, QualityBreakdown
from .filters import run_all as run_filters


@dataclass
class Candidate:
    symbol: str
    side: str            # 'BUY' / 'SELL'
    strategy: str
    price: float
    atr: float
    timestamp: pd.Timestamp
    regime: RegimeSnapshot
    quality: QualityBreakdown
    accepted: bool
    reason: str          # human-readable accept/reject reason

    def risk_tier(self) -> str:
        if self.quality.score >= STRAT.quality_high_score: return "HIGH"
        if self.quality.score >= STRAT.quality_min_score:  return "MEDIUM"
        return "LOW"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol, "side": self.side, "strategy": self.strategy,
            "price": float(self.price), "atr": float(self.atr),
            "timestamp": self.timestamp.isoformat(),
            "regime": self.regime.to_dict(),
            "quality": self.quality.to_dict(),
            "accepted": self.accepted, "reason": self.reason,
            "risk_tier": self.risk_tier(),
        }


# ----- raw signal logic (regime-gated) ----- #

def _mean_reversion(symbol, feat, regime: RegimeSnapshot) -> Optional[dict]:
    if regime.label != RANGE: return None
    last, prev = feat.iloc[-1], feat.iloc[-2]
    if prev["rsi"] < STRAT.rsi_oversold <= last["rsi"]:
        return {"side": "BUY", "strategy": "mean_reversion",
                "reason": f"RSI {prev['rsi']:.1f}->{last['rsi']:.1f}"}
    if prev["rsi"] > STRAT.rsi_overbought >= last["rsi"]:
        return {"side": "SELL", "strategy": "mean_reversion",
                "reason": f"RSI {prev['rsi']:.1f}->{last['rsi']:.1f}"}
    return None


def _trend_following(symbol, feat, regime: RegimeSnapshot) -> Optional[dict]:
    if regime.label not in TREND_REGIMES: return None
    last, prev = feat.iloc[-1], feat.iloc[-2]
    crossed_up = (prev["ema_fast"] <= prev["ema_slow"]
                  and last["ema_fast"] > last["ema_slow"])
    crossed_dn = (prev["ema_fast"] >= prev["ema_slow"]
                  and last["ema_fast"] < last["ema_slow"])
    if crossed_up and regime.label in LONG_REGIMES and last["close"] > last["vwap"]:
        return {"side": "BUY", "strategy": "trend_following",
                "reason": "EMA cross-up + price>VWAP + trend regime"}
    if crossed_dn and regime.label in SHORT_REGIMES and last["close"] < last["vwap"]:
        return {"side": "SELL", "strategy": "trend_following",
                "reason": "EMA cross-down + price<VWAP + trend regime"}
    return None


def evaluate(symbol: str, df: pd.DataFrame, htf_rule: str | None = None) -> Optional[Candidate]:
    """
    Build features → classify regime → run filters → score → emit Candidate.
    Returns None if no raw signal at all (no point logging non-events).
    """
    if df is None or len(df) < STRAT.ema_slow + 10:
        return None
    feat = build_features(df).dropna()
    if feat.empty: return None
    htf_feat = (build_htf_features(df, htf_rule).dropna()
                if htf_rule else None)

    regime = classify(feat)
    raw = _trend_following(symbol, feat, regime) or _mean_reversion(symbol, feat, regime)
    if raw is None: return None

    last = feat.iloc[-1]

    # Hard filters first (cheap rejects)
    ok, freason = run_filters(feat, feat.index[-1], "1d")
    if not ok:
        return Candidate(
            symbol=symbol, side=raw["side"], strategy=raw["strategy"],
            price=float(last["close"]), atr=float(last["atr"]),
            timestamp=feat.index[-1], regime=regime,
            quality=QualityBreakdown(0, 0, 0, 0, 0, "filter rejected"),
            accepted=False, reason=f"filter: {freason}",
        )

    # Quality scoring
    qb = score_trade(raw["side"], feat, htf_feat, regime.label)
    accepted = qb.score >= STRAT.quality_min_score
    reason = (raw["reason"] if accepted
              else f"quality {qb.score:.0f} < {STRAT.quality_min_score:.0f}")
    return Candidate(
        symbol=symbol, side=raw["side"], strategy=raw["strategy"],
        price=float(last["close"]), atr=float(last["atr"]),
        timestamp=feat.index[-1], regime=regime, quality=qb,
        accepted=accepted, reason=reason,
    )


def evaluate_universe(data_by_symbol: Dict[str, pd.DataFrame],
                      htf_rule: str | None = "1D") -> List[Candidate]:
    out: List[Candidate] = []
    for sym, df in data_by_symbol.items():
        cand = evaluate(sym, df, htf_rule=htf_rule)
        if cand is not None:
            out.append(cand)
    # Sort accepted-first, by quality score descending
    out.sort(key=lambda c: (c.accepted, c.quality.score), reverse=True)
    return out
