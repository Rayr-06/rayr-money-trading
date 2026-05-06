"""
FEATURE ENGINEERING — v2
------------------------
Adds ADX, ATR-percentile rank, EMA slope, and HTF resampler on top of v1.
All vectorized.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import STRAT


# ------------ basic indicators ------------ #

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_g = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_l = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_g / avg_l.replace(0, np.nan)
    return (100 - 100/(1+rs)).fillna(50.0)


def ema(s: pd.Series, period: int) -> pd.Series:
    return s.ewm(span=period, adjust=False, min_periods=period).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    pc = close.shift(1)
    tr = pd.concat([high - low, (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()


def vwap(df: pd.DataFrame, period: int = 20) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical * df["volume"]
    return (pv.rolling(period, min_periods=1).sum()
            / df["volume"].rolling(period, min_periods=1).sum().replace(0, np.nan))


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average Directional Index — trend strength (0..100, anything >25 = trending).
    Wilder's formulation, vectorized.
    """
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = ((up > dn) & (up > 0)) * up
    minus_dm = ((dn > up) & (dn > 0)) * dn
    a = atr(df, period)
    pdi = 100 * (plus_dm.ewm(alpha=1/period, adjust=False, min_periods=period).mean() / a)
    mdi = 100 * (minus_dm.ewm(alpha=1/period, adjust=False, min_periods=period).mean() / a)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False, min_periods=period).mean().fillna(0.0)


def atr_percentile_rank(atr_pct: pd.Series, window: int) -> pd.Series:
    """Rolling rank of current ATR% within last `window` bars (0..1)."""
    return atr_pct.rolling(window, min_periods=window // 2).apply(
        lambda x: (x <= x.iloc[-1]).mean(), raw=False
    )


def ema_slope_bps(ema_series: pd.Series, lookback: int = 5) -> pd.Series:
    return (ema_series - ema_series.shift(lookback)) / ema_series.shift(lookback) \
        * 10_000 / lookback


# ------------ composite ------------ #

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = rsi(out["close"], STRAT.rsi_period)
    out["ema_fast"] = ema(out["close"], STRAT.ema_fast)
    out["ema_slow"] = ema(out["close"], STRAT.ema_slow)
    out["atr"] = atr(out, STRAT.atr_period)
    out["atr_pct"] = out["atr"] / out["close"]
    out["atr_pct_rank"] = atr_percentile_rank(out["atr_pct"], STRAT.atr_pct_window)
    out["vwap"] = vwap(out, STRAT.vwap_period)
    out["adx"] = adx(out, STRAT.adx_period)
    out["ema_slope_bps"] = ema_slope_bps(out["ema_fast"], 5)
    return out


# ------------ multi-timeframe resampler ------------ #

def resample_ohlcv(df: pd.DataFrame, rule: str = "1H") -> pd.DataFrame:
    """Resample OHLCV to a higher timeframe."""
    if df.empty: return df
    out = pd.DataFrame({
        "open":   df["open"].resample(rule).first(),
        "high":   df["high"].resample(rule).max(),
        "low":    df["low"].resample(rule).min(),
        "close":  df["close"].resample(rule).last(),
        "volume": df["volume"].resample(rule).sum(),
    }).dropna()
    return out


def build_htf_features(df: pd.DataFrame, rule: str = "1H") -> pd.DataFrame:
    htf = resample_ohlcv(df, rule)
    if htf.empty: return htf
    return build_features(htf)
