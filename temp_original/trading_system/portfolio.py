"""
PORTFOLIO RISK ENGINE
---------------------
Cross-position risk that the per-trade RiskManager cannot see:
  - Total open risk (sum of stop distances × qty)
  - Sector concentration
  - Correlation between candidate and existing positions
  - Aggregate beta / exposure caps
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable
import numpy as np
import pandas as pd
from loguru import logger
from .config import RISK, UNIV


@dataclass
class PortfolioCheck:
    ok: bool
    reason: str
    total_risk_pct: float
    sector_exposure_pct: float
    max_correlation: float


def sector_for(symbol: str) -> str:
    return UNIV.equities_us.get(symbol) or UNIV.equities_in.get(symbol, "OTHER")


def _correlation(a: pd.Series, b: pd.Series, lookback: int = 60) -> float:
    a = a.pct_change().dropna().iloc[-lookback:]
    b = b.pct_change().dropna().iloc[-lookback:]
    n = min(len(a), len(b))
    if n < 20: return 0.0
    return float(np.corrcoef(a.values[-n:], b.values[-n:])[0, 1])


class PortfolioRisk:
    def __init__(self):
        self.price_panel: Dict[str, pd.Series] = {}

    def update_price_panel(self, prices_by_symbol: Dict[str, pd.Series]) -> None:
        self.price_panel = prices_by_symbol

    def evaluate(
        self,
        candidate_symbol: str,
        candidate_risk_dollars: float,
        candidate_notional: float,
        equity: float,
        open_positions: Iterable,  # iterable of risk.Position
    ) -> PortfolioCheck:
        # 1) Total open risk (existing stop-distance $ + candidate)
        total_risk = candidate_risk_dollars
        for p in open_positions:
            stop_dist = abs(p.entry_price - p.stop_price)
            total_risk += stop_dist * p.qty
        total_risk_pct = total_risk / max(equity, 1e-9)
        if total_risk_pct > RISK.max_portfolio_risk:
            return PortfolioCheck(False,
                f"portfolio risk {total_risk_pct:.2%} > cap {RISK.max_portfolio_risk:.0%}",
                total_risk_pct, 0.0, 0.0)

        # 2) Sector exposure (notional)
        cand_sector = sector_for(candidate_symbol)
        sector_notional = candidate_notional
        for p in open_positions:
            if sector_for(p.symbol) == cand_sector:
                sector_notional += p.entry_price * p.qty
        sector_exposure_pct = sector_notional / max(equity, 1e-9)
        if sector_exposure_pct > RISK.max_sector_exposure:
            return PortfolioCheck(False,
                f"sector {cand_sector} exposure {sector_exposure_pct:.0%} > cap",
                total_risk_pct, sector_exposure_pct, 0.0)

        # 3) Correlation with each existing position
        max_corr = 0.0
        cand_series = self.price_panel.get(candidate_symbol)
        if cand_series is not None:
            for p in open_positions:
                other = self.price_panel.get(p.symbol)
                if other is None: continue
                c = abs(_correlation(cand_series, other))
                if c > max_corr: max_corr = c
            if max_corr > RISK.max_correlation:
                return PortfolioCheck(False,
                    f"correlation {max_corr:.2f} > cap {RISK.max_correlation}",
                    total_risk_pct, sector_exposure_pct, max_corr)

        return PortfolioCheck(True, "ok", total_risk_pct, sector_exposure_pct, max_corr)
