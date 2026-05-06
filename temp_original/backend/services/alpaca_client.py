"""
Alpaca client wrapper.

Single responsibility: thin, safe abstraction over alpaca-py with clear
error translation. Stateless — credentials are passed per-call OR the
factory `from_stored_credentials()` builds an instance from the encrypted
credentials store.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from backend.utils.credentials_store import load_credentials


PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"


class AlpacaError(Exception):
    """Friendly, user-facing error."""
    def __init__(self, message: str, code: str = "alpaca_error"):
        super().__init__(message)
        self.code = code


@dataclass
class AlpacaClient:
    api_key: str
    secret_key: str
    paper: bool = True

    def __post_init__(self):
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
        except ImportError as e:
            raise AlpacaError(
                f"alpaca-py SDK is not installed: {e}. "
                f"Run: pip install alpaca-py==0.30.1",
                code="sdk_missing",
            )
        if not self.api_key or not self.secret_key:
            raise AlpacaError("API key and secret are required", code="missing_credentials")
        try:
            self._trading = TradingClient(self.api_key, self.secret_key, paper=self.paper)
            self._data = StockHistoricalDataClient(self.api_key, self.secret_key)
        except Exception as e:
            raise AlpacaError(f"failed to initialize client: {e}", code="init_failed")
        # Save sdk handles for later
        self._OrderSide = OrderSide
        self._TimeInForce = TimeInForce
        self._OrderType = OrderType
        self._MarketOrderRequest = MarketOrderRequest
        self._LimitOrderRequest = LimitOrderRequest
        self._QuoteReq = StockLatestQuoteRequest

    # ---------- Account ----------
    def get_account(self) -> Dict[str, Any]:
        try:
            a = self._trading.get_account()
            return {
                "account_number": a.account_number,
                "status": str(a.status),
                "currency": a.currency,
                "cash": float(a.cash),
                "equity": float(a.equity),
                "buying_power": float(a.buying_power),
                "portfolio_value": float(a.portfolio_value),
                "pattern_day_trader": bool(a.pattern_day_trader),
                "trading_blocked": bool(a.trading_blocked),
                "account_blocked": bool(a.account_blocked),
                "is_paper": str(a.account_number).startswith("PA") or self.paper,
            }
        except Exception as e:
            raise _translate(e)

    def get_clock(self) -> Dict[str, Any]:
        try:
            c = self._trading.get_clock()
            return {
                "is_open": bool(c.is_open),
                "next_open": str(c.next_open),
                "next_close": str(c.next_close),
                "timestamp": str(c.timestamp),
            }
        except Exception as e:
            raise _translate(e)

    # ---------- Positions ----------
    def get_positions(self) -> List[Dict[str, Any]]:
        try:
            ps = self._trading.get_all_positions()
            return [{
                "symbol": p.symbol,
                "qty": int(float(p.qty)),
                "side": str(p.side).lower(),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price or 0),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
            } for p in ps]
        except Exception as e:
            raise _translate(e)

    def close_position(self, symbol: str) -> Dict[str, Any]:
        try:
            self._trading.close_position(symbol)
            return {"closed": symbol}
        except Exception as e:
            raise _translate(e)

    # ---------- Orders ----------
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        side = side.lower()
        type_ = type.lower()
        tif = time_in_force.lower()
        if side not in ("buy", "sell"):
            raise AlpacaError("side must be 'buy' or 'sell'", code="invalid_side")
        if qty <= 0:
            raise AlpacaError("qty must be > 0", code="invalid_qty")
        side_enum = self._OrderSide.BUY if side == "buy" else self._OrderSide.SELL
        tif_map = {
            "day": self._TimeInForce.DAY,
            "gtc": self._TimeInForce.GTC,
            "ioc": self._TimeInForce.IOC,
            "fok": self._TimeInForce.FOK,
        }
        tif_enum = tif_map.get(tif, self._TimeInForce.DAY)

        try:
            if type_ == "market":
                req = self._MarketOrderRequest(
                    symbol=symbol, qty=qty, side=side_enum, time_in_force=tif_enum,
                )
            elif type_ == "limit":
                if limit_price is None:
                    raise AlpacaError("limit_price required for limit orders",
                                      code="invalid_order")
                req = self._LimitOrderRequest(
                    symbol=symbol, qty=qty, side=side_enum,
                    time_in_force=tif_enum, limit_price=limit_price,
                )
            else:
                raise AlpacaError(f"unsupported order type: {type}", code="invalid_order")

            o = self._trading.submit_order(req)
            return {
                "id": str(o.id),
                "client_order_id": str(o.client_order_id),
                "symbol": o.symbol,
                "qty": float(o.qty),
                "side": str(o.side).lower(),
                "type": str(o.order_type).lower(),
                "time_in_force": str(o.time_in_force).lower(),
                "status": str(o.status),
                "submitted_at": str(o.submitted_at),
            }
        except AlpacaError:
            raise
        except Exception as e:
            raise _translate(e)

    def list_orders(self, status: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            status_map = {
                "open": QueryOrderStatus.OPEN,
                "closed": QueryOrderStatus.CLOSED,
                "all": QueryOrderStatus.ALL,
            }
            req = GetOrdersRequest(status=status_map.get(status, QueryOrderStatus.ALL),
                                   limit=limit)
            orders = self._trading.get_orders(req)
            return [{
                "id": str(o.id),
                "symbol": o.symbol,
                "qty": float(o.qty or 0),
                "filled_qty": float(o.filled_qty or 0),
                "side": str(o.side).lower(),
                "status": str(o.status),
                "submitted_at": str(o.submitted_at),
                "filled_avg_price": float(o.filled_avg_price or 0),
            } for o in orders]
        except Exception as e:
            raise _translate(e)

    def get_latest_price(self, symbol: str) -> float:
        try:
            q = self._data.get_stock_latest_quote(self._QuoteReq(symbol_or_symbols=symbol))
            ask = float(q[symbol].ask_price or 0)
            bid = float(q[symbol].bid_price or 0)
            return ask if ask > 0 else bid
        except Exception as e:
            raise _translate(e)


# ---------- helpers ----------

def _translate(e: Exception) -> AlpacaError:
    """Translate raw alpaca-py errors into friendly AlpacaErrors."""
    msg = str(e).lower()
    if "401" in msg or "unauthorized" in msg or "forbidden" in msg:
        return AlpacaError(
            "Authentication rejected. Your API key or secret is invalid. "
            "Regenerate at https://app.alpaca.markets/paper/dashboard/overview",
            code="auth_failed",
        )
    if "404" in msg:
        return AlpacaError(
            "Endpoint 404 — paper/live mismatch. "
            "PK* keys require paper=true; AK* keys require paper=false.",
            code="env_mismatch",
        )
    if "insufficient" in msg:
        return AlpacaError("Insufficient buying power.", code="insufficient_funds")
    if "tradable" in msg or "asset" in msg:
        return AlpacaError("Symbol not tradable on this account.", code="symbol_not_tradable")
    if "market" in msg and "closed" in msg:
        return AlpacaError("Market is closed.", code="market_closed")
    if "timeout" in msg or "connection" in msg:
        return AlpacaError("Network error reaching Alpaca. Check connection / status page.",
                           code="network_error")
    return AlpacaError(f"Alpaca error: {e}", code="unknown")


def connect_alpaca(api_key: str, secret_key: str, paper: bool = True) -> AlpacaClient:
    """Factory — also performs an immediate auth check."""
    client = AlpacaClient(api_key=api_key, secret_key=secret_key, paper=paper)
    client.get_account()  # raises AlpacaError on bad creds
    return client


def from_stored_credentials() -> AlpacaClient:
    """Build a client from the encrypted store. Raises AlpacaError if missing."""
    creds = load_credentials("alpaca")
    if not creds:
        raise AlpacaError(
            "No Alpaca credentials saved. POST /api/alpaca/connect first.",
            code="not_connected",
        )
    paper = str(creds.get("paper", "true")).lower() != "false"
    return AlpacaClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=paper,
    )
