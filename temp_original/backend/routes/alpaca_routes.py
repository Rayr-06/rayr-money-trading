"""
FastAPI router for Alpaca integration.

Mount on your existing app:
    from backend.routes.alpaca_routes import router as alpaca_router
    app.include_router(alpaca_router, prefix="/api/alpaca", tags=["alpaca"])

Or run standalone via backend/main.py.
"""
from __future__ import annotations
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.alpaca_client import (
    connect_alpaca, from_stored_credentials, AlpacaError,
)
from backend.utils.credentials_store import (
    save_credentials, load_credentials, delete_credentials,
)
from backend.utils.encryption import mask


router = APIRouter()


# ---------- Schemas ----------

class ConnectBody(BaseModel):
    api_key: str = Field(..., min_length=8, max_length=64,
                         description="Alpaca API key (PK* for paper, AK* for live)")
    secret_key: str = Field(..., min_length=16, max_length=128)
    paper: bool = Field(True, description="True = paper trading (default, recommended)")

class OrderBody(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    qty: float = Field(..., gt=0)
    side: Literal["buy", "sell"]
    type: Literal["market", "limit"] = "market"
    time_in_force: Literal["day", "gtc", "ioc", "fok"] = "day"
    limit_price: Optional[float] = Field(None, gt=0)


# ---------- Helpers ----------

def _err(e: AlpacaError) -> HTTPException:
    code_map = {
        "auth_failed": status.HTTP_401_UNAUTHORIZED,
        "env_mismatch": status.HTTP_400_BAD_REQUEST,
        "insufficient_funds": status.HTTP_402_PAYMENT_REQUIRED,
        "symbol_not_tradable": status.HTTP_400_BAD_REQUEST,
        "market_closed": status.HTTP_409_CONFLICT,
        "not_connected": status.HTTP_412_PRECONDITION_FAILED,
        "missing_credentials": status.HTTP_400_BAD_REQUEST,
        "invalid_side": status.HTTP_400_BAD_REQUEST,
        "invalid_qty": status.HTTP_400_BAD_REQUEST,
        "invalid_order": status.HTTP_400_BAD_REQUEST,
        "sdk_missing": status.HTTP_503_SERVICE_UNAVAILABLE,
        "network_error": status.HTTP_502_BAD_GATEWAY,
    }
    return HTTPException(
        status_code=code_map.get(e.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail={"code": e.code, "message": str(e)},
    )


# ---------- Routes ----------

@router.post("/connect")
def connect(body: ConnectBody):
    """Validate credentials with Alpaca, then store them encrypted."""
    try:
        client = connect_alpaca(body.api_key, body.secret_key, paper=body.paper)
        account = client.get_account()
    except AlpacaError as e:
        raise _err(e)

    save_credentials(
        "alpaca",
        api_key=body.api_key,
        secret_key=body.secret_key,
        paper="true" if body.paper else "false",
    )
    return {
        "ok": True,
        "message": "Credentials validated and saved (encrypted at rest).",
        "mode": "paper" if body.paper else "live",
        "account": {
            "account_number": account["account_number"],
            "status": account["status"],
            "cash": account["cash"],
            "equity": account["equity"],
            "buying_power": account["buying_power"],
            "is_paper": account["is_paper"],
        },
    }


@router.get("/status")
def status_():
    """Lightweight check — does the backend have stored credentials?"""
    creds = load_credentials("alpaca")
    if not creds:
        return {"connected": False}
    return {
        "connected": True,
        "mode": "paper" if str(creds.get("paper", "true")).lower() != "false" else "live",
        "api_key_masked": mask(creds.get("api_key", "")),
    }


@router.delete("/disconnect")
def disconnect():
    deleted = delete_credentials("alpaca")
    return {"deleted": deleted}


@router.get("/test")
def test():
    """Verify stored credentials still work + return current account snapshot."""
    try:
        client = from_stored_credentials()
        account = client.get_account()
        clock = client.get_clock()
    except AlpacaError as e:
        raise _err(e)
    return {"ok": True, "account": account, "clock": clock}


@router.get("/account")
def account():
    try:
        return from_stored_credentials().get_account()
    except AlpacaError as e:
        raise _err(e)


@router.get("/positions")
def positions():
    try:
        return {"positions": from_stored_credentials().get_positions()}
    except AlpacaError as e:
        raise _err(e)


@router.get("/orders")
def orders(status_filter: str = "all", limit: int = 50):
    try:
        return {"orders": from_stored_credentials().list_orders(status_filter, limit)}
    except AlpacaError as e:
        raise _err(e)


@router.post("/order")
def place_order(body: OrderBody):
    try:
        client = from_stored_credentials()
        return client.place_order(
            symbol=body.symbol.upper(),
            qty=body.qty,
            side=body.side,
            type=body.type,
            time_in_force=body.time_in_force,
            limit_price=body.limit_price,
        )
    except AlpacaError as e:
        raise _err(e)


@router.delete("/positions/{symbol}")
def close_position(symbol: str):
    try:
        return from_stored_credentials().close_position(symbol.upper())
    except AlpacaError as e:
        raise _err(e)
