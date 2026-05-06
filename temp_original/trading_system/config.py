"""
RAYR MONEY v2.0 — central configuration.
All risk + strategy + execution parameters live here so they can be
audited, version-controlled, and changed without code edits.
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


# ============================ RISK ============================ #
@dataclass(frozen=True)
class RiskConfig:
    # Tiered per-trade risk (driven by quality score)
    risk_high: float = 0.015      # quality >= 85
    risk_medium: float = 0.010    # quality >= 70
    risk_low: float = 0.005       # quality >= score_threshold (60)
    # Hard caps
    max_daily_loss: float = 0.04          # 4% — tighter than v1
    max_weekly_loss: float = 0.08         # weekly circuit breaker
    max_consecutive_losses: int = 3
    max_concurrent_positions: int = 3
    # Portfolio-level exposure caps
    max_portfolio_risk: float = 0.05      # sum of per-trade risk on all open positions
    max_sector_exposure: float = 0.40     # of equity, in any single sector
    max_correlation: float = 0.75         # don't add a position if |corr| with existing > this
    # ATR stop / target
    atr_stop_mult: float = 2.0
    atr_tp_mult: float = 3.0
    cash_buffer: float = 0.10
    # Trailing stop activation: move stop to BE after price moves N×ATR in favor
    trail_activation_atr: float = 1.5


# ========================= STRATEGY =========================== #
@dataclass(frozen=True)
class StrategyConfig:
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    ema_fast: int = 50
    ema_slow: int = 200
    atr_period: int = 14
    adx_period: int = 14
    vwap_period: int = 20
    # Quality scoring
    quality_min_score: float = 70.0       # below this = no trade
    quality_high_score: float = 85.0      # high-confidence tier
    # Multi-timeframe
    htf_resample: str = "1H"              # higher timeframe for confirmation
    # ATR percentile windows
    atr_pct_window: int = 100             # bars used for percentile rank
    atr_pct_extreme: float = 0.90         # >= 90th percentile = no-trade
    atr_pct_low: float = 0.20             # quiet markets
    # ADX thresholds
    adx_strong_trend: float = 25.0
    adx_weak_trend: float = 18.0
    # Volume spike filter (news candles)
    vol_spike_mult: float = 3.0           # vol > 3× 20-period avg = no trade


# ========================= FILTERS ============================ #
@dataclass(frozen=True)
class FilterConfig:
    # Time-of-day blocks (in minutes since market open)
    skip_open_minutes: int = 30
    skip_close_minutes: int = 10
    # Liquidity
    min_avg_dollar_volume: float = 5_000_000   # 5M$/day minimum
    # Earnings / news blackout days (manual list)
    blackout_dates: List[str] = field(default_factory=list)


# ======================== EXECUTION =========================== #
@dataclass(frozen=True)
class ExecutionConfig:
    broker: str = os.getenv("BROKER", "paper")  # 'paper' | 'alpaca' | 'zerodha'
    paper_starting_cash: float = float(os.getenv("PAPER_CASH", "1000"))
    # Realistic slippage band — sampled per-fill
    slippage_bps_low: float = 5.0     # 0.05% in calm markets
    slippage_bps_high: float = 20.0   # 0.20% in volatile markets
    commission_bps: float = 3.0
    # Synthetic execution latency (ms)
    latency_ms_low: int = 80
    latency_ms_high: int = 250
    # Probability the broker rejects / partially fills (sanity for backtest)
    reject_prob: float = 0.01
    partial_fill_prob: float = 0.02


# ========================= UNIVERSE =========================== #
@dataclass(frozen=True)
class UniverseConfig:
    # Liquid, single-name + index ETFs. Sector tags drive correlation/exposure caps.
    equities_us: Dict[str, str] = field(default_factory=lambda: {
        "SPY": "BROAD", "QQQ": "TECH",
        "AAPL": "TECH", "MSFT": "TECH", "NVDA": "TECH",
        "JPM": "FIN", "XOM": "ENERGY", "UNH": "HEALTH",
    })
    equities_in: Dict[str, str] = field(default_factory=lambda: {
        "RELIANCE.NS": "ENERGY", "TCS.NS": "TECH",
        "INFY.NS": "TECH", "HDFCBANK.NS": "FIN", "ICICIBANK.NS": "FIN",
    })
    timeframe: str = "1d"           # base timeframe (5m for intraday systems)
    htf_timeframe: str = "1d"       # confirmation timeframe (resampled)


# ======================== ANALYTICS =========================== #
@dataclass(frozen=True)
class AnalyticsConfig:
    trade_log_path: str = os.getenv("TRADE_LOG", "logs/trades.jsonl")
    feature_log_path: str = os.getenv("FEATURE_LOG", "logs/features.jsonl")
    metrics_snapshot_path: str = os.getenv("METRICS_PATH", "logs/metrics.json")


RISK = RiskConfig()
STRAT = StrategyConfig()
FILT = FilterConfig()
EXEC = ExecutionConfig()
UNIV = UniverseConfig()
ANLY = AnalyticsConfig()

# Secrets
ALPACA_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET = os.getenv("ALPACA_API_SECRET", "")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() == "true"
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
ZERODHA_ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
