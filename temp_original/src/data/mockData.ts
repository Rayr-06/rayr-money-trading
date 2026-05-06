// RAYR MONEY v2 — mock data (matches FastAPI v2 response shapes)

export const SUMMARY = {
  starting_equity: 1000.0,
  ending_equity: 1612.30,
  total_return: 0.6123,
  cagr: 0.1003,
  sharpe: 1.42,
  sortino: 2.08,
  calmar: 1.42,
  max_drawdown: -0.071,
  win_rate: 0.523,
  profit_factor: 2.04,
  expectancy: 6.82,
  trades: 89,                    // v2 trades LESS but BETTER
  start: "2021-01-04",
  end: "2026-01-02",
};

// Equity curve with smoother drawdowns (quality filtering = fewer bad trades)
function genEquity(): { ts: string; equity: number }[] {
  const points: { ts: string; equity: number }[] = [];
  const start = new Date("2021-01-04").getTime();
  const day = 86400000;
  let eq = 1000;
  let seed = 13;
  const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  for (let i = 0; i < 1260; i++) {
    const shock =
      (i > 200 && i < 240) || (i > 700 && i < 730) ? -0.0025 : 0.0008;
    const r = shock + (rand() - 0.5) * 0.008;
    eq = Math.max(900, eq * (1 + r));
    points.push({
      ts: new Date(start + i * day).toISOString().slice(0, 10),
      equity: +eq.toFixed(2),
    });
  }
  return points;
}
export const EQUITY_CURVE = genEquity();

// Drawdown curve derived from equity
export const DRAWDOWN_CURVE = (() => {
  let peak = -Infinity;
  return EQUITY_CURVE.map((p) => {
    peak = Math.max(peak, p.equity);
    return { ts: p.ts, dd: +(p.equity / peak - 1).toFixed(4) };
  });
})();

// Quality score histogram (output from /performance_detailed)
export const QUALITY_DIST = [
  { bucket: "0-10", count: 4 },
  { bucket: "10-20", count: 9 },
  { bucket: "20-30", count: 18 },
  { bucket: "30-40", count: 27 },
  { bucket: "40-50", count: 41 },
  { bucket: "50-60", count: 58 },
  { bucket: "60-70", count: 63 },     // ← below threshold (rejected)
  { bucket: "70-80", count: 47 },     // ← MEDIUM tier
  { bucket: "80-90", count: 28 },     // ← MEDIUM/HIGH boundary
  { bucket: "90-100", count: 12 },    // ← HIGH conviction
];

// Trade PnL distribution (in $)
export const TRADE_PNL_DIST = [
  { bin: "-50", count: 2 },
  { bin: "-30", count: 4 },
  { bin: "-15", count: 14 },
  { bin: "-5", count: 22 },
  { bin: "+5", count: 18 },
  { bin: "+15", count: 13 },
  { bin: "+30", count: 9 },
  { bin: "+60", count: 5 },
  { bin: "+100", count: 2 },
];

export const SIGNALS = [
  {
    symbol: "NVDA", side: "BUY", strategy: "trend_following",
    price: 487.21, atr: 9.84,
    regime: { label: "STRONG_TREND_UP", adx: 32.4, atr_pct_rank: 0.55, ema_slope_bps: 14.2, confidence: 0.91 },
    quality: { score: 88, trend_pts: 28, volume_pts: 20, volatility_pts: 20, mtf_pts: 30 - 10 },
    accepted: true, risk_tier: "HIGH",
    reason: "EMA cross-up + price>VWAP + trend regime",
  },
  {
    symbol: "SPY", side: "BUY", strategy: "mean_reversion",
    price: 472.55, atr: 4.12,
    regime: { label: "RANGE", adx: 14.8, atr_pct_rank: 0.31, ema_slope_bps: 1.2, confidence: 0.7 },
    quality: { score: 74, trend_pts: 8, volume_pts: 16, volatility_pts: 20, mtf_pts: 30 },
    accepted: true, risk_tier: "MEDIUM",
    reason: "RSI 28.4->32.1",
  },
  {
    symbol: "AAPL", side: "BUY", strategy: "mean_reversion",
    price: 198.11, atr: 3.06,
    regime: { label: "RANGE", adx: 12.1, atr_pct_rank: 0.22, ema_slope_bps: -0.8, confidence: 0.65 },
    quality: { score: 58, trend_pts: 4, volume_pts: 8, volatility_pts: 16, mtf_pts: 30 },
    accepted: false, risk_tier: "LOW",
    reason: "quality 58 < 70",
  },
  {
    symbol: "XOM", side: "SELL", strategy: "trend_following",
    price: 102.40, atr: 2.81,
    regime: { label: "WEAK_TREND_DN", adx: 21.5, atr_pct_rank: 0.62, ema_slope_bps: -8.4, confidence: 0.6 },
    quality: { score: 71, trend_pts: 18, volume_pts: 12, volatility_pts: 16, mtf_pts: 25 },
    accepted: true, risk_tier: "MEDIUM",
    reason: "EMA cross-down + price<VWAP + trend regime",
  },
  {
    symbol: "JPM", side: "BUY", strategy: "trend_following",
    price: 168.22, atr: 3.34,
    regime: { label: "CHAOTIC", adx: 18.2, atr_pct_rank: 0.94, ema_slope_bps: 4.1, confidence: 0.4 },
    quality: { score: 0, trend_pts: 0, volume_pts: 0, volatility_pts: 0, mtf_pts: 0 },
    accepted: false, risk_tier: "LOW",
    reason: "filter: ATR percentile 94% (extreme)",
  },
];

// /market_regime endpoint
export const REGIMES = [
  { symbol: "SPY", label: "RANGE", adx: 14.8, atr_pct_rank: 0.31, ema_slope_bps: 1.2, confidence: 0.7 },
  { symbol: "QQQ", label: "STRONG_TREND_UP", adx: 28.1, atr_pct_rank: 0.48, ema_slope_bps: 11.4, confidence: 0.85 },
  { symbol: "AAPL", label: "RANGE", adx: 12.1, atr_pct_rank: 0.22, ema_slope_bps: -0.8, confidence: 0.65 },
  { symbol: "MSFT", label: "WEAK_TREND_UP", adx: 20.4, atr_pct_rank: 0.41, ema_slope_bps: 5.2, confidence: 0.62 },
  { symbol: "NVDA", label: "STRONG_TREND_UP", adx: 32.4, atr_pct_rank: 0.55, ema_slope_bps: 14.2, confidence: 0.91 },
  { symbol: "JPM", label: "CHAOTIC", adx: 18.2, atr_pct_rank: 0.94, ema_slope_bps: 4.1, confidence: 0.4 },
  { symbol: "XOM", label: "WEAK_TREND_DN", adx: 21.5, atr_pct_rank: 0.62, ema_slope_bps: -8.4, confidence: 0.6 },
  { symbol: "UNH", label: "RANGE", adx: 11.4, atr_pct_rank: 0.18, ema_slope_bps: 0.4, confidence: 0.6 },
];

export const POSITIONS = {
  equity: 1612.30,
  cash: 712.18,
  halted: false,
  halt_reason: "",
  consecutive_losses: 1,
  open: [
    {
      symbol: "MSFT", side: "LONG", qty: 1, entry: 412.55,
      stop: 401.84, target: 432.11, strategy: "trend_following",
      quality_score: 81, risk_tier: "MEDIUM", trail_active: false,
      opened_at: "2025-12-28T14:35:00Z",
    },
    {
      symbol: "NVDA", side: "LONG", qty: 2, entry: 478.10,
      stop: 478.10, target: 507.62, strategy: "trend_following",   // BE trail engaged
      quality_score: 89, risk_tier: "HIGH", trail_active: true,
      opened_at: "2025-12-30T15:10:00Z",
    },
  ],
};

// /risk_state endpoint
export const RISK_STATE = {
  equity: 1612.30,
  halted: false, halt_reason: "",
  consecutive_losses: 1, max_consecutive_losses: 3,
  daily_pnl_pct: -0.008, max_daily_loss: 0.04,
  weekly_pnl_pct: 0.012, max_weekly_loss: 0.08,
  total_open_risk_pct: 0.022, max_portfolio_risk: 0.05,
  open_positions: 2, max_concurrent_positions: 3,
};

// In-sample / out-of-sample comparison
export const IS_OOS = {
  in_sample: { return: 0.42, sharpe: 1.51, max_dd: -0.064, trades: 62 },
  out_of_sample: { return: 0.19, sharpe: 1.28, max_dd: -0.071, trades: 27 },
};

// Walk-forward folds
export const WALK_FORWARD = [
  { oos_start: "2023-01-01", oos_end: "2023-07-01", oos_return: 0.058, oos_sharpe: 1.21, oos_max_dd: -0.041, oos_profit_factor: 1.84, oos_trades: 11 },
  { oos_start: "2023-07-01", oos_end: "2024-01-01", oos_return: 0.072, oos_sharpe: 1.44, oos_max_dd: -0.052, oos_profit_factor: 2.11, oos_trades: 9 },
  { oos_start: "2024-01-01", oos_end: "2024-07-01", oos_return: -0.018, oos_sharpe: -0.32, oos_max_dd: -0.068, oos_profit_factor: 0.81, oos_trades: 8 },
  { oos_start: "2024-07-01", oos_end: "2025-01-01", oos_return: 0.094, oos_sharpe: 1.78, oos_max_dd: -0.038, oos_profit_factor: 2.42, oos_trades: 12 },
  { oos_start: "2025-01-01", oos_end: "2025-07-01", oos_return: 0.061, oos_sharpe: 1.32, oos_max_dd: -0.044, oos_profit_factor: 1.94, oos_trades: 10 },
  { oos_start: "2025-07-01", oos_end: "2026-01-01", oos_return: 0.048, oos_sharpe: 1.18, oos_max_dd: -0.039, oos_profit_factor: 1.71, oos_trades: 7 },
];

// By-strategy and by-regime breakdown
export const BY_STRATEGY = {
  trend_following: { trades: 47, pnl: 412.30, wins: 28, win_rate: 0.596 },
  mean_reversion: { trades: 42, pnl: 199.00, wins: 19, win_rate: 0.452 },
};

export const BY_REGIME = {
  STRONG_TREND_UP: { trades: 22, pnl: 248.10, wins: 15, win_rate: 0.682 },
  WEAK_TREND_UP: { trades: 15, pnl: 92.40, wins: 9, win_rate: 0.600 },
  STRONG_TREND_DN: { trades: 6, pnl: 41.20, wins: 4, win_rate: 0.667 },
  WEAK_TREND_DN: { trades: 4, pnl: 30.60, wins: 2, win_rate: 0.500 },
  RANGE: { trades: 42, pnl: 199.00, wins: 19, win_rate: 0.452 },
};

// Rejection reasons (why trades were filtered out)
export const REJECTION_REASONS = {
  "quality below threshold": 138,
  "ATR percentile 90%+ (extreme)": 47,
  "filter: volume spike 3.4× avg": 28,
  "max concurrent positions": 19,
  "portfolio: correlation 0.81 > cap": 14,
  "portfolio: sector TECH exposure 44%": 11,
  "size rounds to 0": 8,
};

export const TRADES = [
  { closed_at: "2025-12-22", symbol: "NVDA", side: "LONG", qty: 1, entry: 451.20, exit: 478.84, pnl: 27.64, pnl_pct: 0.0613, strategy: "trend_following", regime: "STRONG_TREND_UP", quality_score: 91, risk_tier: "HIGH", reason_close: "take-profit" },
  { closed_at: "2025-12-19", symbol: "AAPL", side: "LONG", qty: 2, entry: 192.10, exit: 188.40, pnl: -7.40, pnl_pct: -0.0193, strategy: "mean_reversion", regime: "RANGE", quality_score: 73, risk_tier: "MEDIUM", reason_close: "stop-loss" },
  { closed_at: "2025-12-15", symbol: "SPY", side: "LONG", qty: 2, entry: 462.30, exit: 471.85, pnl: 19.10, pnl_pct: 0.0207, strategy: "mean_reversion", regime: "RANGE", quality_score: 76, risk_tier: "MEDIUM", reason_close: "take-profit" },
  { closed_at: "2025-12-08", symbol: "MSFT", side: "LONG", qty: 1, entry: 398.40, exit: 412.20, pnl: 13.80, pnl_pct: 0.0346, strategy: "trend_following", regime: "WEAK_TREND_UP", quality_score: 78, risk_tier: "MEDIUM", reason_close: "take-profit" },
  { closed_at: "2025-12-02", symbol: "QQQ", side: "LONG", qty: 1, entry: 401.80, exit: 401.80, pnl: 0.00, pnl_pct: 0.0, strategy: "trend_following", regime: "WEAK_TREND_UP", quality_score: 71, risk_tier: "MEDIUM", reason_close: "trailing-BE" },
  { closed_at: "2025-11-21", symbol: "NVDA", side: "LONG", qty: 1, entry: 438.10, exit: 461.50, pnl: 23.40, pnl_pct: 0.0534, strategy: "trend_following", regime: "STRONG_TREND_UP", quality_score: 88, risk_tier: "HIGH", reason_close: "take-profit" },
  { closed_at: "2025-11-14", symbol: "AAPL", side: "LONG", qty: 2, entry: 184.20, exit: 187.90, pnl: 7.40, pnl_pct: 0.0201, strategy: "mean_reversion", regime: "RANGE", quality_score: 75, risk_tier: "MEDIUM", reason_close: "signal-exit" },
  { closed_at: "2025-11-08", symbol: "SPY", side: "LONG", qty: 2, entry: 455.00, exit: 449.20, pnl: -11.60, pnl_pct: -0.0127, strategy: "mean_reversion", regime: "RANGE", quality_score: 72, risk_tier: "MEDIUM", reason_close: "stop-loss" },
];

export const FILES = [
  { name: "config.py", lines: 95, role: "Risk + strategy + filter + execution config" },
  { name: "data.py", lines: 96, role: "OHLCV fetch + normalize" },
  { name: "features.py", lines: 110, role: "RSI/EMA/ATR/VWAP/ADX + ATR-percentile + slope + HTF resampler" },
  { name: "regime.py", lines: 96, role: "5-state regime classifier (STRONG/WEAK trend, RANGE, CHAOTIC)" },
  { name: "filters.py", lines: 88, role: "Time-of-day, liquidity, vol-spike, ATR-extreme blackouts" },
  { name: "quality.py", lines: 122, role: "0-100 trade quality scorer + risk-tier mapping" },
  { name: "strategy.py", lines: 134, role: "Mean-reversion + Trend-following → Candidate objects" },
  { name: "portfolio.py", lines: 95, role: "Portfolio risk: correlation, sector, total-risk caps" },
  { name: "risk.py", lines: 215, role: "Tiered sizing, trailing stops, daily+weekly circuit breakers, kill-switch" },
  { name: "execution.py", lines: 188, role: "Paper/Alpaca/Zerodha + slippage band + latency + rejections" },
  { name: "backtest.py", lines: 178, role: "Hybrid backtester + walk-forward + IS/OOS split" },
  { name: "analytics.py", lines: 138, role: "Structured trade/feature logs + metrics + ranker training" },
  { name: "api.py", lines: 158, role: "FastAPI v2: /trade_quality_score /market_regime /risk_state /performance_detailed" },
  { name: "main.py", lines: 138, role: "CLI: once | live | backtest | walkforward" },
  { name: "notify.py", lines: 24, role: "Telegram alerts" },
];
