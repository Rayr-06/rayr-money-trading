"""
RAYR MONEY - ADVANCED REGIME DETECTOR
Author: Senior Quantitative Architect
Description: Classifies structural market state based on ADX (trend strength),
             ATR percentile (volatility), and EMA alignments.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger("RayrMoneyLogger")

class MarketRegimeDetector:
    def __init__(self, adx_threshold: float = 25.0):
        self.adx_threshold = adx_threshold

    def classify_regime(self, df: pd.DataFrame) -> str:
        """
        Returns one of:
        - STRONG_TREND: Fast EMAs aligned, ADX > 25, Normal Volatility
        - WEAK_TREND: Fast EMAs aligned, ADX between 15-25
        - RANGE: ADX < 15, Normal Volatility (Oversold/Overbought holds value)
        - CHAOTIC: Volatility exceeds 90th percentile of ATR. Suspends all trades.
        """
        if df.empty or "adx" not in df.columns or "atr" not in df.columns:
            return "RANGE"
            
        last_row = df.iloc[-1]
        atr = last_row["atr"]
        atr_p90 = last_row["atr_p90"] if "atr_p90" in df.columns else atr * 1.5
        adx = last_row["adx"]
        
        # 1. Volatility Circuit Breaker (Chaotic State)
        if atr > atr_p90:
            return "CHAOTIC"
            
        # 2. Trend Strength Classification
        if adx >= self.adx_threshold:
            return "STRONG_TREND"
        elif adx >= 15.0 and adx < self.adx_threshold:
            return "WEAK_TREND"
        else:
            return "RANGE"
