"""
RAYR MONEY - ADVANCED FEATURE ENGINEERING
Author: Senior Quantitative Architect
Description: Mathematically models technical features without bulky external dependencies.
             Calculates ADX, True Range, ATR, EMA Slopes, and Volatility percentiles.
"""

import pandas as pd
import numpy as np

class FeatureGenerator:
    def __init__(self, adx_period: int = 14, atr_period: int = 14):
        self.adx_period = adx_period
        self.atr_period = atr_period

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < max(self.adx_period * 2, 50):
            return df
            
        df = df.copy()
        
        # 1. EMA slopes
        df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["ema_slope"] = df["ema_50"].diff(3) / df["ema_50"].shift(3) * 100 # % change over 3 bars
        
        # 2. RSI (14)
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / np.where(avg_loss == 0, 0.00001, avg_loss)
        df["rsi"] = 100 - (100 / (1 + rs))

        # 3. ATR
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift(1))
        low_close = np.abs(df["low"] - df["close"].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=self.atr_period).mean()
        
        # 4. Volatility Percentile (Past 200 bars)
        df["atr_p90"] = df["atr"].rolling(200).quantile(0.90)
        df["atr_p10"] = df["atr"].rolling(200).quantile(0.10)
        
        # 5. ADX (Average Directional Index) for trend strength
        up_move = df["high"].diff()
        down_move = df["low"].shift(1) - df["low"]
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        tr_smooth = tr.rolling(self.adx_period).sum()
        plus_di = 100 * (pd.Series(plus_dm).rolling(self.adx_period).sum() / np.where(tr_smooth == 0, 0.00001, tr_smooth))
        minus_di = 100 * (pd.Series(minus_dm).rolling(self.adx_period).sum() / np.where(tr_smooth == 0, 0.00001, tr_smooth))
        
        dx = 100 * np.abs(plus_di - minus_di) / np.where((plus_di + minus_di) == 0, 0.00001, (plus_di + minus_di))
        df["adx"] = pd.Series(dx).rolling(self.adx_period).mean()
        
        # 6. VWAP
        tp = (df["high"] + df["low"] + df["close"]) / 3
        df["vwap"] = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
        df["vwap"] = df["vwap"].fillna(df["close"])

        return df
