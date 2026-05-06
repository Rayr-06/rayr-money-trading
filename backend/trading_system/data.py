"""
DATA LAYER
----------
- Fetches historical + live OHLCV
- Cleans / forward-fills / drops bad rows
- Provides a single normalized DataFrame interface for downstream modules

Columns produced: ['open','high','low','close','volume']  (lowercase)
Index: timezone-aware UTC DatetimeIndex
"""
from __future__ import annotations
import time
from typing import Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


_CACHE: Dict[str, pd.DataFrame] = {}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, index, dtypes; drop bad rows."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    keep = ["open", "high", "low", "close", "volume"]
    df = df[[c for c in keep if c in df.columns]]
    # Coerce numeric, drop rows with NaN in OHLC
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    # Volume can be missing on some indices — fill with 0
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0)
    # Ensure UTC tz-aware index
    if df.index.tz is None:
        df.index = pd.to_datetime(df.index, utc=True)
    else:
        df.index = df.index.tz_convert("UTC")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def fetch_ohlcv(
    symbol: str,
    timeframe: str = "1d",
    lookback_days: int = 365 * 3,
    source: str = "yfinance",
) -> pd.DataFrame:
    """
    Fetch OHLCV for a symbol. Source is yfinance by default
    (free + works for both US and Indian equities via .NS suffix).
    """
    cache_key = f"{symbol}|{timeframe}|{lookback_days}|{source}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    if source == "yfinance":
        if yf is None:
            raise RuntimeError("yfinance not installed")
        # Yahoo intraday limits: 1m -> 7d, 5m -> 60d, 1h -> 730d
        period_map = {"1m": "7d", "5m": "60d", "1h": "730d", "1d": f"{lookback_days}d"}
        interval_map = {"1m": "1m", "5m": "5m", "1h": "60m", "1d": "1d"}
        for attempt in range(3):
            try:
                raw = yf.download(
                    symbol,
                    period=period_map.get(timeframe, "365d"),
                    interval=interval_map.get(timeframe, "1d"),
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.get_level_values(0)
                df = _normalize(raw)
                if not df.empty:
                    _CACHE[cache_key] = df
                    return df
            except Exception as e:
                logger.warning(f"[{symbol}] fetch attempt {attempt+1} failed: {e}")
                time.sleep(1.5 * (attempt + 1))
        logger.error(f"[{symbol}] no data after retries")
        return pd.DataFrame()

    raise NotImplementedError(f"data source '{source}' not supported")


def latest_bar(symbol: str, timeframe: str = "1d") -> Optional[pd.Series]:
    df = fetch_ohlcv(symbol, timeframe, lookback_days=10)
    if df.empty:
        return None
    return df.iloc[-1]


def fetch_universe(
    symbols, timeframe: str = "1d", lookback_days: int = 365 * 3
) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for s in symbols:
        df = fetch_ohlcv(s, timeframe, lookback_days)
        if not df.empty and len(df) > 250:  # need enough bars for EMA200
            out[s] = df
        else:
            logger.warning(f"skipping {s}: insufficient data ({len(df)} bars)")
    return out
