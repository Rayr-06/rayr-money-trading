"""
EXECUTION ENGINE — v2
---------------------
Realistic broker simulation:
  - Slippage sampled from a band that widens with current ATR%
  - Synthetic latency
  - Probabilistic order rejection / partial fills
  - Same Paper / Alpaca / Zerodha trio behind one interface
"""
from __future__ import annotations
import time
import random
from typing import Dict, Optional
from datetime import datetime
from loguru import logger
from .config import EXEC, ALPACA_KEY, ALPACA_SECRET, ALPACA_PAPER
from .config import ZERODHA_API_KEY, ZERODHA_ACCESS_TOKEN
from .data import latest_bar


class BrokerError(Exception):
    pass


class OrderRejected(BrokerError):
    pass


# ----------------- Paper ----------------- #

class PaperBroker:
    """In-memory paper broker with slippage / latency / rejection modeling."""
    def __init__(self, starting_cash: float):
        self.cash = starting_cash
        self.positions: Dict[str, Dict] = {}
        self.orders = []
        random.seed(42)

    def get_cash(self) -> float:
        return self.cash

    def get_price(self, symbol: str) -> float:
        bar = latest_bar(symbol)
        if bar is None: raise BrokerError(f"no price for {symbol}")
        return float(bar["close"])

    def _slippage_bps(self, atr_pct_hint: float = 0.02) -> float:
        # Wider band when ATR% is high — vol-aware fill quality
        scale = max(0.3, min(2.0, atr_pct_hint / 0.02))
        return random.uniform(EXEC.slippage_bps_low,
                              EXEC.slippage_bps_high) * scale

    def submit_order(self, symbol: str, side: str, qty: int,
                     atr_pct_hint: float = 0.02) -> dict:
        # 1) Latency
        time.sleep(random.uniform(EXEC.latency_ms_low, EXEC.latency_ms_high) / 1000.0)
        # 2) Rejection
        if random.random() < EXEC.reject_prob:
            raise OrderRejected(f"{symbol} {side} {qty} rejected")
        # 3) Partial fill
        fill_qty = qty
        if random.random() < EXEC.partial_fill_prob:
            fill_qty = max(1, int(qty * random.uniform(0.4, 0.9)))
        ref_px = self.get_price(symbol)
        slip = self._slippage_bps(atr_pct_hint) / 10_000
        fill_px = ref_px * (1 + slip) if side == "BUY" else ref_px * (1 - slip)
        commission = fill_px * fill_qty * (EXEC.commission_bps / 10_000)
        signed = fill_qty if side == "BUY" else -fill_qty
        notional = fill_px * fill_qty
        if side == "BUY":
            self.cash -= (notional + commission)
        else:
            self.cash += (notional - commission)
        prev = self.positions.get(symbol, {"qty": 0, "avg": 0.0})
        new_qty = prev["qty"] + signed
        if new_qty == 0:
            self.positions.pop(symbol, None)
        else:
            if (prev["qty"] >= 0 and signed > 0) or (prev["qty"] <= 0 and signed < 0):
                self.positions[symbol] = {
                    "qty": new_qty,
                    "avg": (prev["qty"]*prev["avg"] + signed*fill_px)/new_qty if new_qty else fill_px,
                }
            else:
                self.positions[symbol] = {"qty": new_qty, "avg": prev["avg"]}
        order = {
            "id": f"paper-{len(self.orders)+1}", "symbol": symbol,
            "side": side, "qty_requested": qty, "qty_filled": fill_qty,
            "fill_price": fill_px, "slippage_bps": slip*10_000,
            "commission": commission, "ts": datetime.utcnow().isoformat(),
        }
        self.orders.append(order)
        logger.info(f"[paper] {side} {fill_qty}/{qty} {symbol} @ {fill_px:.2f} "
                    f"slip={slip*10_000:.1f}bps cash={self.cash:.2f}")
        return order

    def cancel_all(self) -> None: return None


# ----------------- Alpaca ----------------- #

class AlpacaBroker:
    """
    Alpaca broker (paper or live). Uses alpaca-py SDK.
    Provides clear, actionable error messages on common misconfigurations.
    """
    def __init__(self):
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest, StockLatestBarRequest
        except ImportError as e:
            raise BrokerError(
                f"alpaca-py not installed: {e}\n"
                f"  → pip install alpaca-py==0.30.1"
            )
        if not ALPACA_KEY:
            raise BrokerError(
                "ALPACA_API_KEY is empty.\n"
                "  → Get keys: https://app.alpaca.markets/paper/dashboard/overview\n"
                "  → Add to .env: ALPACA_API_KEY=PK..."
            )
        if not ALPACA_SECRET:
            raise BrokerError(
                "ALPACA_API_SECRET is empty.\n"
                "  → Add to .env: ALPACA_API_SECRET=..."
            )
        try:
            self._client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=ALPACA_PAPER)
            self._data = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
            # Test auth immediately
            acct = self._client.get_account()
            mode = "PAPER" if ALPACA_PAPER else "LIVE"
            logger.info(f"[alpaca] connected as {acct.account_number} ({mode}) "
                        f"cash=${float(acct.cash):,.2f}")
            if not ALPACA_PAPER and not str(acct.account_number).startswith("AK"):
                logger.warning("[alpaca] ALPACA_PAPER=false but account looks like paper — check keys")
        except Exception as e:
            msg = str(e).lower()
            if "401" in msg or "unauthorized" in msg:
                raise BrokerError(
                    f"Alpaca auth REJECTED (401). Your keys are wrong.\n"
                    f"  → Regenerate at https://app.alpaca.markets/paper/dashboard/overview\n"
                    f"  → Make sure paper keys (PK*) match ALPACA_PAPER=true"
                )
            if "404" in msg:
                raise BrokerError(
                    f"Alpaca 404 — paper/live mismatch.\n"
                    f"  → ALPACA_PAPER must be 'true' for PK* keys, 'false' for AK* keys"
                )
            raise BrokerError(f"Alpaca connection failed: {e}")

        self._OrderSide, self._TimeInForce = OrderSide, TimeInForce
        self._MarketOrderRequest = MarketOrderRequest
        self._QuoteReq = StockLatestQuoteRequest
        self._BarReq = StockLatestBarRequest

    def get_cash(self) -> float:
        return float(self._client.get_account().cash)

    def get_equity(self) -> float:
        return float(self._client.get_account().equity)

    def is_market_open(self) -> bool:
        try:
            return bool(self._client.get_clock().is_open)
        except Exception:
            return False

    def get_price(self, symbol: str) -> float:
        try:
            q = self._data.get_stock_latest_quote(self._QuoteReq(symbol_or_symbols=symbol))
            ask = float(q[symbol].ask_price or 0)
            bid = float(q[symbol].bid_price or 0)
            if ask > 0: return ask
            if bid > 0: return bid
            # Fallback to latest bar (works after-hours)
            b = self._data.get_stock_latest_bar(self._BarReq(symbol_or_symbols=symbol))
            return float(b[symbol].close)
        except Exception as e:
            raise BrokerError(f"could not fetch price for {symbol}: {e}")

    def get_positions(self) -> dict:
        try:
            return {p.symbol: {
                "qty": int(float(p.qty)),
                "avg_entry": float(p.avg_entry_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
            } for p in self._client.get_all_positions()}
        except Exception as e:
            logger.warning(f"[alpaca] get_positions failed: {e}")
            return {}

    def submit_order(self, symbol: str, side: str, qty: int,
                     atr_pct_hint: float = 0.02) -> dict:
        try:
            req = self._MarketOrderRequest(
                symbol=symbol, qty=qty,
                side=self._OrderSide.BUY if side == "BUY" else self._OrderSide.SELL,
                time_in_force=self._TimeInForce.DAY,
            )
            o = self._client.submit_order(req)
            logger.info(f"[alpaca] {side} {qty} {symbol} → order {o.id} ({o.status})")
            return {"id": str(o.id), "symbol": symbol, "side": side,
                    "qty": qty, "status": str(o.status)}
        except Exception as e:
            msg = str(e).lower()
            if "insufficient" in msg:
                raise OrderRejected(f"insufficient buying power for {symbol}: {e}")
            if "tradable" in msg or "asset" in msg:
                raise OrderRejected(f"{symbol} not tradable: {e}")
            if "market" in msg and "closed" in msg:
                raise OrderRejected(f"market closed: {e}")
            raise OrderRejected(f"alpaca rejected order: {e}")

    def close_position(self, symbol: str) -> dict:
        try:
            self._client.close_position(symbol)
            return {"closed": symbol}
        except Exception as e:
            raise OrderRejected(f"close_position {symbol} failed: {e}")

    def cancel_all(self) -> None:
        self._client.cancel_orders()


# ----------------- Zerodha ----------------- #

class ZerodhaBroker:
    def __init__(self):
        try:
            from kiteconnect import KiteConnect
        except ImportError as e:
            raise BrokerError(f"kiteconnect not installed: {e}")
        if not ZERODHA_API_KEY or not ZERODHA_ACCESS_TOKEN:
            raise BrokerError("ZERODHA keys not set")
        self._kite = KiteConnect(api_key=ZERODHA_API_KEY)
        self._kite.set_access_token(ZERODHA_ACCESS_TOKEN)

    def get_cash(self) -> float:
        return float(self._kite.margins("equity")["available"]["live_balance"])

    def get_price(self, symbol: str) -> float:
        return float(self._kite.ltp([symbol])[symbol]["last_price"])

    def submit_order(self, symbol: str, side: str, qty: int, atr_pct_hint: float = 0.02) -> dict:
        exch, ts = symbol.split(":")
        oid = self._kite.place_order(
            variety=self._kite.VARIETY_REGULAR, exchange=exch, tradingsymbol=ts,
            transaction_type=(self._kite.TRANSACTION_TYPE_BUY if side == "BUY"
                              else self._kite.TRANSACTION_TYPE_SELL),
            quantity=qty, product=self._kite.PRODUCT_CNC,
            order_type=self._kite.ORDER_TYPE_MARKET,
        )
        return {"id": oid, "symbol": symbol, "side": side, "qty": qty}

    def cancel_all(self) -> None:
        for o in self._kite.orders():
            if o["status"] in ("OPEN", "TRIGGER PENDING"):
                self._kite.cancel_order(variety=o["variety"], order_id=o["order_id"])


def get_broker():
    b = EXEC.broker.lower()
    if b == "paper":   return PaperBroker(EXEC.paper_starting_cash)
    if b == "alpaca":  return AlpacaBroker()
    if b == "zerodha": return ZerodhaBroker()
    raise BrokerError(f"unknown broker '{EXEC.broker}'")
