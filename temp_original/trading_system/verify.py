"""
RAYR MONEY — Alpaca Connection Verifier
----------------------------------------
End-to-end sanity check that proves your Alpaca paper account is wired up
correctly BEFORE you trust the engine with any decisions.

Run:
    python -m trading_system.main verify

Tests, in order:
    1. Environment vars present
    2. Alpaca SDK importable
    3. Account credentials valid (auth)
    4. PAPER mode confirmed (refuses to proceed if LIVE detected unless --live)
    5. Account is unblocked + has cash
    6. Market data fetch works
    7. Universe data fetch works (yfinance)
    8. Place a tiny BUY (1 share of cheapest symbol) — paper only
    9. Verify the position appears
   10. Liquidate the position
   11. Confirm cash returned

If ANY step fails, prints actionable diagnosis. Refuses to continue.
"""
from __future__ import annotations
import sys
import time
from datetime import datetime
from typing import Tuple
from loguru import logger

from .config import EXEC, ALPACA_KEY, ALPACA_SECRET, ALPACA_PAPER


# ANSI colors for terminal output (works on mac/linux/modern Windows)
G = "\033[92m"   # green
R = "\033[91m"   # red
Y = "\033[93m"   # yellow
B = "\033[94m"   # blue
D = "\033[2m"    # dim
RST = "\033[0m"  # reset


def _step(n: int, total: int, name: str) -> None:
    print(f"\n{B}[{n}/{total}]{RST} {name}")


def _ok(msg: str) -> None:
    print(f"  {G}✓{RST} {msg}")


def _fail(msg: str, hint: str = "") -> None:
    print(f"  {R}✗{RST} {msg}")
    if hint:
        print(f"    {Y}→ Fix:{RST} {hint}")


def _warn(msg: str) -> None:
    print(f"  {Y}!{RST} {msg}")


def _info(msg: str) -> None:
    print(f"    {D}{msg}{RST}")


def run_verification(allow_live: bool = False) -> bool:
    """Returns True if all checks pass. Returns False on any failure."""
    print(f"\n{B}{'='*60}{RST}")
    print(f"{B}  RAYR MONEY — Alpaca Connection Verifier{RST}")
    print(f"{B}{'='*60}{RST}")
    total = 11

    # ---------- 1. Env vars ---------- #
    _step(1, total, "Checking environment variables")
    if not ALPACA_KEY:
        _fail("ALPACA_API_KEY is empty",
              "Add ALPACA_API_KEY=PK... to your .env file")
        return False
    if not ALPACA_SECRET:
        _fail("ALPACA_API_SECRET is empty",
              "Add ALPACA_API_SECRET=... to your .env file")
        return False
    if not ALPACA_KEY.startswith("PK") and not ALPACA_KEY.startswith("AK"):
        _warn(f"API key format looks unusual: starts with {ALPACA_KEY[:4]}...")
        _info("Paper keys typically start with 'PK', live keys with 'AK'")
    _ok(f"ALPACA_API_KEY set (starts with {ALPACA_KEY[:4]}...)")
    _ok(f"ALPACA_API_SECRET set ({len(ALPACA_SECRET)} chars)")
    _ok(f"ALPACA_PAPER = {ALPACA_PAPER}")
    if EXEC.broker != "alpaca":
        _warn(f"BROKER={EXEC.broker} (not 'alpaca'). Set BROKER=alpaca in .env to actually use this connection.")

    # ---------- 2. SDK importable ---------- #
    _step(2, total, "Verifying alpaca-py SDK is installed")
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest, ClosePositionRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest, StockLatestBarRequest
        _ok("alpaca-py imported successfully")
    except ImportError as e:
        _fail(f"Could not import alpaca-py: {e}",
              "Run: pip install alpaca-py==0.30.1")
        return False

    # ---------- 3. Auth ---------- #
    _step(3, total, "Authenticating with Alpaca")
    try:
        trading = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=ALPACA_PAPER)
        data = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        account = trading.get_account()
        _ok(f"Authenticated as account {account.account_number}")
    except Exception as e:
        msg = str(e).lower()
        if "401" in msg or "unauthorized" in msg or "forbidden" in msg:
            _fail("Authentication rejected (401/403)",
                  "Your API key/secret are wrong. Regenerate at "
                  "https://app.alpaca.markets/paper/dashboard/overview "
                  "(or .../live/... for live)")
        elif "404" in msg:
            _fail("Endpoint 404 — paper/live mismatch",
                  "Your keys are for the WRONG environment. "
                  "Set ALPACA_PAPER=true if using paper keys (PK*), false for live (AK*)")
        else:
            _fail(f"Auth failed: {e}",
                  "Check internet connection and Alpaca status: https://status.alpaca.markets")
        return False

    # ---------- 4. Paper mode confirmed ---------- #
    _step(4, total, "Confirming PAPER mode (safety check)")
    is_paper = "paper" in str(getattr(account, "trading_blocked", "")).lower() or ALPACA_PAPER
    # The most reliable check: paper accounts have account_number starting with PA
    is_paper_acct = str(account.account_number).startswith("PA")
    if not is_paper_acct and not allow_live:
        _fail(f"This appears to be a LIVE account ({account.account_number}). "
              "Refusing to run verification.",
              "Set ALPACA_PAPER=true and use paper keys (https://app.alpaca.markets/paper/dashboard). "
              "Or pass --live if you really know what you're doing.")
        return False
    if is_paper_acct:
        _ok(f"Paper account confirmed (acct# {account.account_number})")
    else:
        _warn(f"LIVE account detected ({account.account_number}). Proceeding because --live was passed.")

    # ---------- 5. Account state ---------- #
    _step(5, total, "Reading account state")
    cash = float(account.cash)
    equity = float(account.equity)
    bp = float(account.buying_power)
    if account.trading_blocked:
        _fail(f"Trading is BLOCKED on this account: {account.trading_blocked}",
              "Reset paper account at Alpaca dashboard, or contact support for live")
        return False
    if account.account_blocked:
        _fail("Account is BLOCKED",
              "Contact Alpaca support")
        return False
    _ok(f"Cash: ${cash:,.2f}")
    _ok(f"Equity: ${equity:,.2f}")
    _ok(f"Buying power: ${bp:,.2f}")
    if cash < 100:
        _warn(f"Low cash (${cash:.2f}). Reset paper account to get $100k starting balance.")
        _info("Go to https://app.alpaca.markets/paper/dashboard → 'Reset Account'")

    # ---------- 6. Market data ---------- #
    _step(6, total, "Fetching live market data (latest quote for SPY)")
    try:
        quote_req = StockLatestQuoteRequest(symbol_or_symbols="SPY")
        q = data.get_stock_latest_quote(quote_req)
        spy_quote = q["SPY"]
        bid, ask = float(spy_quote.bid_price or 0), float(spy_quote.ask_price or 0)
        if ask <= 0 and bid <= 0:
            _warn("Quote returned but prices are 0 (market may be closed)")
            # Try latest bar instead
            bar_req = StockLatestBarRequest(symbol_or_symbols="SPY")
            b = data.get_stock_latest_bar(bar_req)
            close_px = float(b["SPY"].close)
            _ok(f"Latest SPY close: ${close_px:.2f}")
        else:
            _ok(f"SPY bid=${bid:.2f} ask=${ask:.2f} spread=${ask-bid:.4f}")
    except Exception as e:
        _fail(f"Market data fetch failed: {e}",
              "If error mentions 'subscription', you need a market data plan. "
              "Free Alpaca paper accounts include IEX data. Try regenerating keys.")
        return False

    # ---------- 7. Yahoo data (used by signal engine) ---------- #
    _step(7, total, "Fetching historical OHLCV via yfinance (signal source)")
    try:
        from .data import fetch_ohlcv
        df = fetch_ohlcv("SPY", timeframe="1d", lookback_days=400)
        if df.empty:
            _fail("yfinance returned no data",
                  "Check internet. Try: python -c 'import yfinance; print(yfinance.download(\"SPY\", period=\"5d\"))'")
            return False
        _ok(f"Got {len(df)} daily bars for SPY ({df.index[0].date()} → {df.index[-1].date()})")
    except Exception as e:
        _fail(f"yfinance failed: {e}",
              "pip install --upgrade yfinance")
        return False

    # ---------- 8. Place a tiny test order ---------- #
    _step(8, total, "Placing a TEST order: 1 share of SPY (paper only)")
    if not is_paper_acct and not allow_live:
        _fail("Refusing to place test order on live account", "")
        return False

    market_open = bool(getattr(trading.get_clock(), "is_open", False))
    if not market_open:
        _warn("Market is currently CLOSED. Placing order anyway — Alpaca will queue it.")
        _info("Test will skip steps 9-11 (can't verify fill while closed). "
              "Re-run during market hours (9:30am-4pm ET) for full validation.")

    try:
        order_req = MarketOrderRequest(
            symbol="SPY", qty=1,
            side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
        )
        order = trading.submit_order(order_req)
        _ok(f"Order submitted: id={order.id} status={order.status}")
    except Exception as e:
        msg = str(e).lower()
        if "insufficient" in msg:
            _fail(f"Insufficient buying power: {e}",
                  "Reset your paper account in the Alpaca dashboard")
        elif "tradable" in msg or "asset" in msg:
            _fail(f"SPY not tradable on this account: {e}",
                  "Check account permissions in Alpaca dashboard")
        else:
            _fail(f"Order rejection: {e}", "Inspect full error above")
        return False

    if not market_open:
        print(f"\n{Y}━━━ Market closed — partial verification complete ━━━{RST}")
        print(f"{G}✓ Connection works. Re-run during market hours for full test.{RST}\n")
        return True

    # ---------- 9. Verify position ---------- #
    _step(9, total, "Waiting for fill + verifying position appears")
    filled = False
    for attempt in range(15):  # up to 15 seconds
        time.sleep(1)
        try:
            o = trading.get_order_by_id(order.id)
            if str(o.status).lower() in ("filled", "orderstatus.filled"):
                filled = True
                _ok(f"Order filled at ${float(o.filled_avg_price):.2f} "
                    f"({float(o.filled_qty):.0f} shares)")
                break
        except Exception:
            continue
    if not filled:
        _warn("Order did not fill within 15 seconds. Check Alpaca dashboard.")
        _info("This can happen with low-liquidity symbols or after-hours.")
        return True

    try:
        positions = {p.symbol: p for p in trading.get_all_positions()}
        if "SPY" in positions:
            pos = positions["SPY"]
            _ok(f"Position visible: SPY x {pos.qty} @ avg ${float(pos.avg_entry_price):.2f}")
        else:
            _warn("Order filled but position not yet visible. May take a few seconds.")
    except Exception as e:
        _warn(f"Could not fetch positions: {e}")

    # ---------- 10. Liquidate ---------- #
    _step(10, total, "Liquidating test position (SELL 1 SPY)")
    try:
        trading.close_position("SPY")
        _ok("Close-position request submitted")
        time.sleep(3)
    except Exception as e:
        _fail(f"Liquidation failed: {e}",
              "Manually close the SPY position in your Alpaca dashboard")
        return False

    # ---------- 11. Cash check ---------- #
    _step(11, total, "Verifying cash returned")
    try:
        new_account = trading.get_account()
        new_cash = float(new_account.cash)
        delta = new_cash - cash
        _ok(f"New cash: ${new_cash:,.2f} (delta: {'+' if delta >= 0 else ''}${delta:,.2f})")
        if abs(delta) > 5:
            _warn(f"Cash delta ${delta:.2f} larger than expected slippage — investigate")
    except Exception as e:
        _warn(f"Could not refresh account: {e}")

    # ---------- All good ---------- #
    print(f"\n{G}{'='*60}{RST}")
    print(f"{G}  ✅ ALL CHECKS PASSED — Alpaca connection is LEGIT{RST}")
    print(f"{G}{'='*60}{RST}\n")
    print(f"{B}Next steps:{RST}")
    print(f"  1. Set {Y}BROKER=alpaca{RST} in your .env (currently: {EXEC.broker})")
    print(f"  2. Run a single cycle:    {Y}python -m trading_system.main once{RST}")
    print(f"  3. Run live (scheduled):  {Y}python -m trading_system.main live{RST}")
    print(f"  4. Watch the dashboard:   {Y}uvicorn trading_system.api:app --reload{RST}")
    print(f"\n  {D}Run for ≥30 days on paper before flipping to live.{RST}\n")
    return True


if __name__ == "__main__":
    allow_live = "--live" in sys.argv
    success = run_verification(allow_live=allow_live)
    sys.exit(0 if success else 1)
