import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api = tradeapi.REST(os.getenv("ALPACA_API_KEY_ID"), os.getenv("ALPACA_SECRET_KEY"), "https://paper-api.alpaca.markets", api_version='v2')

PRICES = {"AAPL": 183.20, "MSFT": 420.55, "GOOGL": 140.23, "AMZN": 178.90, "META": 485.30, "NVDA": 875.60, "TSLA": 245.80, "SPY": 520.45, "QQQ": 445.20, "IWM": 195.30, "DIA": 380.75, "JPM": 195.80, "BAC": 38.45, "GS": 445.20, "WFC": 58.90, "NFLX": 625.40, "AMD": 165.30, "INTC": 42.15, "DIS": 110.80, "PYPL": 68.40, "COST": 785.90, "PEP": 172.35}

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/alpaca/status")
async def status():
    a = api.get_account()
    return {"connected": True, "portfolio_value": float(a.portfolio_value), "cash": float(a.cash), "buying_power": float(a.buying_power), "equity": float(a.equity), "paper_trading": True}

@app.get("/api/alpaca/positions")
async def positions():
    return {"positions": [{"symbol": p.symbol, "qty": float(p.qty), "avg_entry_price": float(p.avg_entry_price), "current_price": float(p.current_price), "unrealized_pl": float(p.unrealized_pl), "unrealized_plpc": float(p.unrealized_plpc)*100} for p in api.list_positions()]}

@app.get("/api/alpaca/orders")
async def orders():
    return {"orders": [{"symbol": o.symbol, "qty": float(o.qty), "side": o.side, "status": o.status, "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else 0, "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None} for o in api.list_orders(status='all', limit=50)]}

@app.get("/api/stocks/list")
async def stocks():
    return {"symbols": list(PRICES.keys())}

@app.get("/api/market/quotes")
async def quotes():
    return {"quotes": [{"symbol": s, "price": p, "bid": p*0.999, "ask": p*1.001} for s, p in PRICES.items()], "total": len(PRICES)}

@app.get("/api/bot/status")
async def bot_status():
    return {"running": False, "status": "stopped"}

@app.post("/api/bot/start")
async def start():
    return {"status": "started"}

@app.post("/api/bot/stop")
async def stop():
    return {"status": "stopped"}

@app.post("/api/trading/order")
async def order(symbol: str, qty: int, side: str):
    o = api.submit_order(symbol=symbol, qty=qty, side=side, type="market", time_in_force='day')
    return {"success": True, "order_id": o.id}
