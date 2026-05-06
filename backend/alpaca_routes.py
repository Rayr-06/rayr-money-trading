"""
RAYR MONEY - ALPACA FASTAPI ROUTER WORKSPACE
Author: Senior Full-Stack Quantitative Architect
Description: Production FastAPI microservice routes. Keeps API keys encrypted on-server,
             validates inputs, and routes low-latency trade orders cleanly.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from encryption import SecureVault
from alpaca_client import AlpacaClient

router = APIRouter(prefix="/api/alpaca", tags=["Alpaca Integration"])

# In-Memory Cache (Simulating secure encrypted database)
SECURE_DB = {}
vault = SecureVault()

class ConnectionRequest(BaseModel):
    api_key: str
    secret_key: str
    paper: bool = True

class OrderRequest(BaseModel):
    symbol: str
    qty: int
    side: str

def get_live_client() -> AlpacaClient:
    """Helper dependency to decrypt stored keys and initialize the Client."""
    encrypted_key = SECURE_DB.get("enc_api_key")
    encrypted_secret = SECURE_DB.get("enc_secret_key")
    paper_mode = SECURE_DB.get("paper_mode", True)
    
    if not encrypted_key or not encrypted_secret:
        raise HTTPException(status_code=401, detail="Alpaca credentials not configured. Save keys first.")
        
    decrypted_key = vault.decrypt_credential(encrypted_key)
    decrypted_secret = vault.decrypt_credential(encrypted_secret)
    
    return AlpacaClient(api_key=decrypted_key, secret_key=decrypted_secret, paper=paper_mode)

@router.post("/connect")
def connect_alpaca_credentials(payload: ConnectionRequest):
    """POST /api/alpaca/connect - Encrypts and saves credentials on the server."""
    if not payload.api_key or not payload.secret_key:
        raise HTTPException(status_code=400, detail="Missing API Key or Secret.")
        
    try:
        # Encrypt securely before storing
        SECURE_DB["enc_api_key"] = vault.encrypt_credential(payload.api_key)
        SECURE_DB["enc_secret_key"] = vault.encrypt_credential(payload.secret_key)
        SECURE_DB["paper_mode"] = payload.paper
        
        # Test connection immediately
        client = AlpacaClient(api_key=payload.api_key, secret_key=payload.secret_key, paper=payload.paper)
        info = client.get_account_info()
        
        if "error" in info:
            raise HTTPException(status_code=400, detail=f"Alpaca rejection: {info.get('detail', 'Invalid keys')}")
            
        return {
            "status": "CONNECTED",
            "message": "Alpaca credentials encrypted and verified successfully.",
            "mode": "PAPER" if payload.paper else "LIVE",
            "portfolio_value": info.get("portfolio_value", "0.00"),
            "buying_power": info.get("buying_power", "0.00")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption Connection failure: {str(e)}")

@router.get("/account")
def get_alpaca_account_details(client: AlpacaClient = Depends(get_live_client)):
    """GET /api/alpaca/account - Fetches live balance details."""
    info = client.get_account_info()
    if "error" in info:
        raise HTTPException(status_code=400, detail=info.get("detail", "Error retrieving details"))
    return info

@router.post("/order")
def place_alpaca_trade(payload: OrderRequest, client: AlpacaClient = Depends(get_live_client)):
    """POST /api/alpaca/order - Places a verified market trade order."""
    res = client.place_execution_order(symbol=payload.symbol, qty=payload.qty, side=payload.side)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res.get("detail", "Execution rejected."))
    return res

@router.get("/positions")
def get_alpaca_positions(client: AlpacaClient = Depends(get_live_client)):
    """GET /api/alpaca/positions - Retrieves open holdings."""
    return client.get_open_positions()

@router.get("/test")
def test_alpaca_connectivity(client: AlpacaClient = Depends(get_live_client)):
    """GET /api/alpaca/test - Verifies connectivity status and returns balance."""
    info = client.get_account_info()
    if "error" in info:
        return {"connected": False, "status": "REJECTED", "detail": info.get("detail")}
    return {
        "connected": True,
        "status": "AUTHENTICATED",
        "portfolio_value": info.get("portfolio_value", "0.00"),
        "buying_power": info.get("buying_power", "0.00")
    }
