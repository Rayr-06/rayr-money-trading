"""
RAYR MONEY - ELITE STRATEGY & SCORING ENGINE
Author: Senior Quantitative Architect
Description: Executes a multi-timeframe quantitative model. Evaluates trades
             against a rigorous multi-factor scoring model. Rejects scores < 70/100.
"""

import logging
import pandas as pd
from typing import Dict, Tuple
from features import FeatureGenerator
from regime import MarketRegimeDetector

logger = logging.getLogger("RayrMoneyLogger")

class ScoringStrategyEngine:
    def __init__(self, score_threshold: int = 70):
        self.score_threshold = score_threshold
        self.fg = FeatureGenerator()
        self.mrd = MarketRegimeDetector()

    def evaluate_signals(self, df_5m: pd.DataFrame, df_1h: pd.DataFrame) -> Dict:
        """
        Performs dual-timeframe verification and scores trade validity.
        Returns: Dict containing action, score, regime, and target risk modifier.
        """
        # Calculate features
        df_5m = self.fg.calculate_indicators(df_5m)
        df_1h = self.fg.calculate_indicators(df_1h)
        
        if df_5m.empty or "adx" not in df_5m.columns or df_1h.empty or "adx" not in df_1h.columns:
            return {"action": "HOLD", "score": 0, "regime": "CHAOTIC", "reason": "Insufficient history"}

        regime = self.mrd.classify_regime(df_5m)
        last_5m = df_5m.iloc[-1]
        last_1h = df_1h.iloc[-1]
        
        if regime == "CHAOTIC":
            return {"action": "HOLD", "score": 0, "regime": regime, "reason": "Market in Chaotic Regime - Execution suspended"}

        # Base signals
        action = "HOLD"
        
        # Strategy A: Trend Crossover (Only inside STRONG_TREND or WEAK_TREND regimes)
        if regime in ["STRONG_TREND", "WEAK_TREND"]:
            if last_5m["close"] > last_5m["ema_50"] and last_5m["ema_slope"] > 0.05:
                action = "BUY"
            elif last_5m["close"] < last_5m["ema_50"] and last_5m["ema_slope"] < -0.05:
                action = "SELL"
                
        # Strategy B: Mean Reversion (Only inside RANGE regimes)
        elif regime == "RANGE":
            if last_5m["rsi"] < 30:
                action = "BUY"
            elif last_5m["rsi"] > 70:
                action = "SELL"

        if action == "HOLD":
            return {"action": "HOLD", "score": 0, "regime": regime, "reason": "No entry triggers met."}

        # --- TRADE QUALITY SCORING ENGINE ---
        score = 0
        
        # Factor 1: Multi-Timeframe Alignment (30 Points)
        # Verify higher timeframe (1h) supports the trade direction
        if action == "BUY":
            if last_1h["close"] > last_1h["ema_50"]:
                score += 30
        elif action == "SELL":
            if last_1h["close"] < last_1h["ema_50"]:
                score += 30
                
        # Factor 2: Trend Strength (ADX) Confirmation (25 Points)
        if regime == "STRONG_TREND":
            score += 25
        elif regime == "WEAK_TREND":
            score += 15
        elif regime == "RANGE" and last_5m["adx"] < 15:
            score += 25 # High range confidence for reversion
            
        # Factor 3: Volume Confirmation (25 Points)
        # Volume must exceed its 20-period simple moving average
        vol_sma_20 = df_5m["volume"].tail(20).mean()
        if last_5m["volume"] > vol_sma_20 * 1.15:
            score += 25
        elif last_5m["volume"] > vol_sma_20:
            score += 15
            
        # Factor 4: Volatility Fit (20 Points)
        # Avoid buying in over-extended volatility spikes (news candles)
        atr_p10 = last_5m["atr_p10"] if "atr_p10" in df_5m.columns else 0
        atr_p90 = last_5m["atr_p90"] if "atr_p90" in df_5m.columns else 9999
        if atr_p10 < last_5m["atr"] < (atr_p90 * 0.85):
            score += 20
        else:
            score += 5 # Volatility is either dead or extremely spiked

        # --- SCORE EVALUATION & FILTER BARRIER ---
        if score < self.score_threshold:
            logger.info(f"Signal rejected. Score {score}/100 below structural limit ({self.score_threshold}).")
            return {"action": "HOLD", "score": score, "regime": regime, "reason": f"Low Trade Quality Score: {score}/100"}

        # Dynamic Sizing Classifier based on confidence score
        confidence = "LOW"
        if score >= 85:
            confidence = "HIGH"
        elif score >= 70:
            confidence = "MEDIUM"

        return {
            "action": action,
            "score": score,
            "regime": regime,
            "confidence": confidence,
            "reason": f"Validated Trade quality score: {score}/100"
        }
