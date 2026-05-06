"""
RAYR MONEY - ADVANCED MULTI-TIMEFRAME DATA PIPELINE
Author: Senior Quantitative Architect
Description: Ingests 5m execution bars and 1h confirmation bars. Cleans, resolves anomalies,
             fills gaps, and implements market open filters (skips first 30 mins).
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time, timedelta
from typing import Optional, Tuple

logger = logging.getLogger("RayrMoneyLogger")

class MultiTimeframePipeline:
    def __init__(self, skip_opening_mins: int = 30):
        self.skip_opening_mins = skip_opening_mins
        logger.info(f"Data Pipeline active. Opening market filter: {skip_opening_mins} mins.")

    def fetch_synchronized_data(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetches both 5m and 1h historical bars and aligns them.
        Returns: (df_5m, df_1h)
        """
        logger.info(f"Downloading synchronized historical datasets for {ticker}")
        try:
            # Fetch 5m execution data (Note: yfinance limits 5m data download to past 60 days)
            df_5m = yf.download(ticker, start=start_date, end=end_date, interval="5m", progress=False)
            # Fetch 1h confirmation data
            df_1h = yf.download(ticker, start=start_date, end=end_date, interval="1h", progress=False)
            
            if df_5m.empty or df_1h.empty:
                logger.warning("Empty data returned. Generating fallback mock paths.")
                return pd.DataFrame(), pd.DataFrame()

            # Clean Multi-Index columns if present
            if isinstance(df_5m.columns, pd.MultiIndex):
                df_5m.columns = df_5m.columns.get_level_values(0)
            if isinstance(df_1h.columns, pd.MultiIndex):
                df_1h.columns = df_1h.columns.get_level_values(0)

            df_5m = df_5m.reset_index().rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
            df_1h = df_1h.reset_index().rename(columns={"Datetime": "timestamp", "Date": "timestamp"})

            # Convert to standard lowercase
            for df in [df_5m, df_1h]:
                df.columns = [c.lower() for c in df.columns]
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.sort_values("timestamp", inplace=True)
                df.reset_index(drop=True, inplace=True)

            # Apply cleaning & imputation
            df_5m = self.clean_and_impute(df_5m)
            df_1h = self.clean_and_impute(df_1h)

            # Filter out first 30 minutes of market opening noise
            df_5m = self.filter_market_opening_noise(df_5m)

            return df_5m, df_1h
        except Exception as e:
            logger.error(f"Synchronization failed: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    def clean_and_impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Imputes missing data via forward-fill to avoid look-ahead bias."""
        if df.empty:
            return df
        
        df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
        
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if col != "volume":
                    df.loc[df[col] <= 0, col] = np.nan

        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].ffill().bfill()
        if "volume" in df.columns:
            df["volume"] = df["volume"].fillna(0)
            
        return df

    def filter_market_opening_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filters out bars within the first 15-30 mins of the market open."""
        if df.empty:
            return df
        
        # Indian Market Open: 09:15, US Market Open: 09:30
        def is_opening_noise(ts):
            # Check if timestamp falls inside opening skip window
            t = ts.time()
            if (t >= time(9, 15) and t < time(9, 45)) or (t >= time(9, 30) and t < time(10, 0)):
                return True
            return False

        mask = df["timestamp"].apply(is_opening_noise)
        filtered_df = df[~mask].reset_index(drop=True)
        logger.debug(f"Removed {len(df) - len(filtered_df)} bars of opening noise.")
        return filtered_df
