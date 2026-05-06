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
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ALPACA CONFIGURATION
# ============================================================================

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API
api = None
try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        api = tradeapi.REST(
            ALPACA_API_KEY,
            ALPACA_SECRET_KEY,
            ALPACA_BASE_URL,
            api_version='v2'
        )
        print("✅ Alpaca API initialized successfully")
    else:
        print("⚠️ Alpaca API keys not found in environment")
except Exception as e:
    print(f"❌ Alpaca API initialization failed: {e}")

# ============================================================================
# STOCK SYMBOLS
# ============================================================================

SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "SPY", "QQQ", "IWM", "DIA",
    "JPM", "BAC", "GS", "WFC",
    "NFLX", "AMD", "INTC", "DIS", "PYPL", "COST", "PEP"
]

# ============================================================================
# BASIC ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "RAYR MONEY Trading System",
        "version": "2.0",
        "status": "running",
        "alpaca_connected": api is not None,
        "timestamp": datetime.now().isoformat()
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
            "error": "Alpaca API not initialized",
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
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
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
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
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
        "total": len(SYMBOLS)
    }

@app.get("/api/market/quotes")
async def get_market_quotes():
    """Get simple market quotes"""
    if not api:
        return {"error": "Alpaca API not initialized", "quotes": []}
    
    quotes_data = []
    for symbol in SYMBOLS[:5]:  # Only first 5 to avoid timeouts
        try:
            bars = api.get_bars(symbol, "1Day", limit=1).df
            if not bars.empty:
                price = float(bars.iloc[-1]['close'])
                quotes_data.append({
                    "symbol": symbol,
                    "price": price,
                    "bid": price * 0.999,
                    "ask": price * 1.001
                })
        except:
            continue
    
    return {"quotes": quotes_data, "total": len(quotes_data)}

# Bot status
bot_running = False

@app.get("/api/bot/status")
async def bot_status():
    """Get bot status"""
    return {"running": bot_running, "status": "active" if bot_running else "stopped"}

@app.post("/api/bot/start")
async def start_bot():
    """Start bot"""
    global bot_running
    bot_running = True
    return {"status": "started", "message": "Bot started (demo mode)"}

@app.post("/api/bot/stop")
async def stop_bot():
    """Stop bot"""
    global bot_running
    bot_running = False
    return {"status": "stopped", "message": "Bot stopped"}

@app.post("/api/trading/order")
async def place_order(symbol: str, qty: int, side: str):
    """Place order"""
    if not api:
        return {"success": False, "error": "API not initialized"}
    
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="market",
            time_in_force='day'
        )
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "status": order.status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}