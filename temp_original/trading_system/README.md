# RAYR MONEY 💸

A modular, broker-agnostic algorithmic trading system designed for **survivability first, returns second**. Built for solo operators with $1k–$50k capital.

> **No magic. No overfitting. No martingale.**
> Two robust regime-aware strategies, strict ATR-based risk, hard kill switch.

---

## Architecture

```
trading_system/
├── config.py        # Risk + strategy + execution params (single source of truth)
├── data.py          # OHLCV fetch + normalize (yfinance default)
├── features.py      # RSI, EMA(50/200), ATR, VWAP + regime classifier
├── strategy.py      # Mean Reversion + Trend Following
├── risk.py          # Position sizing, stops, daily loss cap, kill switch
├── execution.py     # Paper / Alpaca / Zerodha broker abstraction
├── backtest.py      # Vectorized + event-driven hybrid (uses live RiskManager)
├── notify.py        # Telegram alerts
├── api.py           # FastAPI endpoints (/signals /positions /performance)
└── main.py          # CLI: once | live | backtest
```

## Risk parameters (defaults — edit in `config.py`)

| Param | Value | Why |
|---|---|---|
| `risk_per_trade` | 1% | Survives ~50 consecutive losses |
| `max_daily_loss` | 5% | Auto-halt for the day |
| `max_consecutive_losses` | 3 | Kill switch — manual reset required |
| `max_concurrent_positions` | 3 | Diversification + margin safety |
| `atr_stop_mult` | 2.0× | Beyond typical noise |
| `atr_tp_mult` | 3.0× | 1.5:1 reward/risk minimum |
| `cash_buffer` | 10% | Slippage + fees + margin |

## Strategies

**A. Mean Reversion** — only when regime = `RANGE`
- Long when RSI(14) crosses up through 30
- Exit when RSI crosses down through 70

**B. Trend Following** — only when regime = `TREND`
- Long on EMA50/EMA200 golden cross **+ price > VWAP + volume > 20-period avg**
- Short on death cross with mirrored confirms (long-only on paper broker)

**Regime classifier:**
- `HIGH_VOL` (no trade): ATR/price > 4%
- `TREND`: |EMA50 − EMA200| / EMA200 > 0.5%
- `RANGE`: everything else

## Quickstart (paper)

```bash
cd trading_system
pip install -r requirements.txt
cp .env.example .env          # leave BROKER=paper

# 1) Backtest
python -m trading_system.main backtest

# 2) Single live cycle
python -m trading_system.main once

# 3) Live with built-in scheduler
python -m trading_system.main live

# 4) HTTP API for the dashboard
uvicorn trading_system.api:app --reload --port 8000
```

## Connecting brokers

### Alpaca (recommended for testing — free paper account, US equities)
1. Sign up at https://alpaca.markets and create a paper account
2. Generate API key + secret in dashboard
3. Set in `.env`:
   ```
   BROKER=alpaca
   ALPACA_API_KEY=...
   ALPACA_API_SECRET=...
   ALPACA_PAPER=true
   ```
4. Run `python -m trading_system.main once` — orders route to Alpaca paper.

### Zerodha (Indian equities)
1. Subscribe to Kite Connect (₹2000/mo) at https://kite.trade
2. Generate `api_key`, then run the OAuth flow to obtain `access_token` (refreshes daily)
3. Set:
   ```
   BROKER=zerodha
   ZERODHA_API_KEY=...
   ZERODHA_ACCESS_TOKEN=...   # refresh daily via login script
   ```
4. **Workaround if API restricted:** use webhook mode — point a TradingView alert (created from the Pine version of these strategies) at a self-hosted bridge that calls Kite. The signal payload format is `signal.to_dict()` JSON.

## Telegram alerts

1. Create a bot via @BotFather → get `TELEGRAM_TOKEN`
2. Send your bot a message, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find `chat_id`
3. Set both in `.env`. You'll receive open/close/halt notifications.

## Deployment

**Local (cron):**
```cron
*/5 13-20 * * 1-5  cd /path/to/repo && /usr/bin/python -m trading_system.main once >> bot.log 2>&1
```

**Cloud (Railway / Fly.io / VPS):**
- `Dockerfile` runs `python -m trading_system.main live`
- Set env vars in the platform secrets manager
- Add a healthcheck on the FastAPI `/health` endpoint

## Backtest example output (5y, US equities, $1000 start)

```
{
  "starting_equity": 1000.00,
  "ending_equity":   1738.42,
  "total_return":    0.7384,
  "cagr":            0.1166,
  "sharpe":          1.04,
  "sortino":         1.41,
  "max_drawdown":   -0.118,
  "win_rate":        0.486,
  "profit_factor":   1.58,
  "expectancy":      4.11,
  "trades":          179
}
```
*Numbers above are illustrative — re-run on your machine; markets evolve.*

## API endpoints (for fintech dashboard integration)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness probe |
| GET | `/signals` | live candidate signals (regime + reason) |
| GET | `/positions` | open positions, equity, halt state |
| GET | `/performance?years=3` | backtest summary + equity curve + trade log |
| POST | `/run-cycle` | manual cycle trigger |
| POST | `/kill-switch` | force halt |
| POST | `/resume` | clear halt + loss streak |

---

## ⚠️ Realistic risk warnings

1. **You will lose money.** Even profitable systems have 30–50% drawdowns in adverse regimes. With $1000, even a 10% drawdown is meaningful.
2. **Past backtests ≠ future results.** Walk-forward test before going live.
3. **Slippage and fees on small capital are brutal.** With $1k and 3 bps commission per side, you need ~12 bps edge per trade just to break even. Trade infrequently.
4. **Indian short-selling is restricted to intraday (MIS).** The system disables shorts on Zerodha by default; only the EMA crossover *long* signals execute.
5. **Daily access-token refresh is required for Zerodha.** Plan for a manual or scripted login each morning.
6. **The kill switch exists for a reason.** Do not bypass it. If it triggers, walk away from the screen for 24 hours and review.
7. **Never deploy live without ≥30 days of paper trading on the exact same configuration.**
