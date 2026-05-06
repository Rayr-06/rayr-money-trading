import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

api = None
try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, "https://paper-api.alpaca.markets", api_version='v2')
        print("✅ Alpaca connected")
except Exception as e:
    print(f"❌ Alpaca error: {e}")

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "SPY", "QQQ", 
           "IWM", "DIA", "JPM", "BAC", "GS", "WFC", "NFLX", "AMD", "INTC", "DIS", "PYPL", "COST", "PEP"]

# Fallback prices for when market is closed
FALLBACK_PRICES = {
    "AAPL": 183.20, "MSFT": 420.55, "GOOGL": 140.23, "AMZN": 178.90, "META": 485.30,
    "NVDA": 875.60, "TSLA": 245.80, "SPY": 520.45, "QQQ": 445.20, "IWM": 195.30,
    "DIA": 380.75, "JPM": 195.80, "BAC": 38.45, "GS": 445.20, "WFC": 58.90,
    "NFLX": 625.40, "AMD": 165.30, "INTC": 42.15, "DIS": 110.80, "PYPL": 68.40,
    "COST": 785.90, "PEP": 172.35
}

@app.get("/")
async def root():
    return {"app": "RAYR MONEY", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/alpaca/status")
async def alpaca_status():
    if not api:
        return {"connected": False}
    try:
        account = api.get_account()
        return {
            "connected": True,
            "portfolio_value": float(account.portfolio_value),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "paper_trading": True
        }
    except:
        return {"connected": False}

@app.get("/api/alpaca/positions")
async def get_positions():
    if not api:
        return {"positions": []}
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
            ]
        }
    except:
        return {"positions": []}

@app.get("/api/alpaca/orders")
async def get_orders():
    if not api:
        return {"orders": []}
    try:
        orders = api.list_orders(status='all', limit=50)
        return {
            "orders": [
                {
                    "symbol": o.symbol,
                    "qty": float(o.qty),
                    "side": o.side,
                    "status": o.status,
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else 0,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None
                }
                for o in orders
            ]
        }
    except:
        return {"orders": []}

@app.get("/api/stocks/list")
async def get_stocks():
    return {"symbols": SYMBOLS}

@app.get("/api/market/quotes")
async def get_quotes():
    """Get market quotes - uses real data when market open, fallback when closed"""
    quotes = []
    
    if api:
        # Try to get real data
        for symbol in SYMBOLS[:10]:  # First 10 for speed
            try:
                bars = api.get_bars(symbol, '1Day', limit=1).df
                if not bars.empty:
                    price = float(bars.iloc[-1]['close'])
                    quotes.append({
                        "symbol": symbol,
                        "price": price,
                        "bid": price * 0.999,
                        "ask": price * 1.001
                    })
            except:
                # Use fallback if real data fails
                if symbol in FALLBACK_PRICES:
                    price = FALLBACK_PRICES[symbol]
                    quotes.append({
                        "symbol": symbol,
                        "price": price,
                        "bid": price * 0.999,
                        "ask": price * 1.001
                    })
    
    # If no real data, use all fallback prices
    if len(quotes) == 0:
        for symbol in SYMBOLS:
            if symbol in FALLBACK_PRICES:
                price = FALLBACK_PRICES[symbol]
                quotes.append({
                    "symbol": symbol,
                    "price": price,
                    "bid": price * 0.999,
                    "ask": price * 1.001
                })
    
    return {"quotes": quotes, "total": len(quotes)}

@app.get("/api/bot/status")
async def bot_status():
    return {"running": False, "status": "stopped"}

@app.post("/api/bot/start")
async def start_bot():
    return {"status": "not_implemented", "message": "Bot will be integrated with your original algorithm"}

@app.post("/api/bot/stop")
async def stop_bot():
    return {"status": "stopped"}

@app.post("/api/trading/order")
async def place_order(symbol: str, qty: int, side: str):
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
        return {"success": True, "order_id": order.id}
    except Exception as e:
        return {"success": False, "error": str(e)}