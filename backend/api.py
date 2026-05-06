import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="RAYR MONEY Trading API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rayr-money-trading.pages.dev",
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ALPACA CONFIGURATION
# ============================================================================

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading

# Initialize Alpaca API
try:
    api = tradeapi.REST(
        ALPACA_API_KEY,
        ALPACA_SECRET_KEY,
        ALPACA_BASE_URL,
        api_version='v2'
    )
    print("✅ Alpaca API initialized successfully")
except Exception as e:
    print(f"❌ Alpaca API initialization failed: {e}")
    api = None

# ============================================================================
# STOCK SYMBOLS
# ============================================================================

SYMBOLS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    # Market ETFs
    "SPY", "QQQ", "IWM", "DIA",
    # Finance
    "JPM", "BAC", "GS", "WFC",
    # Popular
    "NFLX", "AMD", "INTC", "DIS", "PYPL", "COST", "PEP"
]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "RAYR MONEY Trading System",
        "version": "2.0",
        "status": "running",
        "alpaca_connected": api is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "alpaca_api": "connected" if api else "disconnected"
    }

@app.get("/api/alpaca/status")
async def get_alpaca_status():
    """Get Alpaca connection status and account info"""
    if not api:
        return {
            "connected": False,
            "error": "Alpaca API not initialized. Check your API keys.",
            "keys_present": {
                "api_key": bool(ALPACA_API_KEY),
                "secret_key": bool(ALPACA_SECRET_KEY)
            }
        }
    
    try:
        account = api.get_account()
        return {
            "connected": True,
            "account_status": account.status,
            "portfolio_value": float(account.portfolio_value),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "paper_trading": True,
            "day_trade_count": int(account.daytrade_count),
            "pattern_day_trader": account.pattern_day_trader,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "keys_present": {
                "api_key": bool(ALPACA_API_KEY),
                "secret_key": bool(ALPACA_SECRET_KEY)
            }
        }

@app.get("/api/alpaca/positions")
async def get_positions():
    """Get current positions"""
    if not api:
        return {"error": "Alpaca API not initialized", "positions": []}
    
    try:
        positions = api.list_positions()
        return {
            "positions": [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "side": p.side,
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_plpc": float(p.unrealized_plpc) * 100
                }
                for p in positions
            ],
            "total": len(positions)
        }
    except Exception as e:
        return {"error": str(e), "positions": []}

@app.get("/api/alpaca/orders")
async def get_orders():
    """Get recent orders"""
    if not api:
        return {"error": "Alpaca API not initialized", "orders": []}
    
    try:
        orders = api.list_orders(status='all', limit=50)
        return {
            "orders": [
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "qty": float(o.qty),
                    "side": o.side,
                    "type": o.type,
                    "status": o.status,
                    "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else 0,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None
                }
                for o in orders
            ],
            "total": len(orders)
        }
    except Exception as e:
        return {"error": str(e), "orders": []}

@app.get("/api/stocks/list")
async def get_stocks():
    """Get list of monitored stocks"""
    return {
        "symbols": SYMBOLS,
        "total": len(SYMBOLS),
        "categories": {
            "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
            "etfs": ["SPY", "QQQ", "IWM", "DIA"],
            "finance": ["JPM", "BAC", "GS", "WFC"],
            "popular": ["NFLX", "AMD", "INTC", "DIS", "PYPL", "COST", "PEP"]
        }
    }

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)