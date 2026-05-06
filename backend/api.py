"""
RAYR MONEY v2 - Your Original System + Alpaca Paper Trading
"""
import os
import sys
from pathlib import Path

# Add trading_system to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime

# Import your original system
try:
    from trading_system.config import UNIV, EXEC, RISK, STRAT
    from trading_system.data import fetch_universe
    from trading_system.strategy import evaluate_universe
    from trading_system.backtest import run_backtest
    print("✅ Your trading system modules loaded successfully")
except Exception as e:
    print(f"⚠️ Trading system import warning: {e}")
    UNIV = None

load_dotenv()

app = FastAPI(title="RAYR MONEY Trading System", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alpaca connection
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

api = None
try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        api = tradeapi.REST(
            ALPACA_API_KEY,
            ALPACA_SECRET_KEY,
            "https://paper-api.alpaca.markets",
            api_version='v2'
        )
        print("✅ Alpaca connected")
except Exception as e:
    print(f"❌ Alpaca error: {e}")

# Fallback prices for display
PRICES = {
    "AAPL": 183.20, "MSFT": 420.55, "GOOGL": 140.23, "AMZN": 178.90,
    "META": 485.30, "NVDA": 875.60, "TSLA": 245.80, "SPY": 520.45,
    "QQQ": 445.20, "IWM": 195.30, "DIA": 380.75, "JPM": 195.80,
    "BAC": 38.45, "GS": 445.20, "WFC": 58.90, "NFLX": 625.40,
    "AMD": 165.30, "INTC": 42.15, "DIS": 110.80, "PYPL": 68.40,
    "COST": 785.90, "PEP": 172.35
}

SYMBOLS = list(PRICES.keys())

# ============================================================================
# YOUR ORIGINAL SYSTEM ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "app": "RAYR MONEY",
        "version": "2.0",
        "status": "running",
        "system": "Your Original Beautiful System + Alpaca"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "alpaca": "connected" if api else "disconnected",
        "trading_system": "loaded" if UNIV else "fallback"
    }

@app.get("/signals")
async def signals():
    """Your original signal generation"""
    if not UNIV:
        return {"error": "Trading system not loaded", "candidates": []}
    
    try:
        universe = list(UNIV.equities_us.keys())[:10]  # Top 10 for speed
        data = fetch_universe(universe, UNIV.timeframe, lookback_days=365)
        candidates = evaluate_universe(data, htf_rule="1W")
        
        return {
            "count_total": len(candidates),
            "count_accepted": sum(1 for c in candidates if c.accepted),
            "candidates": [c.to_dict() for c in candidates]
        }
    except Exception as e:
        return {"error": str(e), "candidates": []}

@app.get("/market_regime")
async def market_regime():
    """Your original regime classification"""
    if not UNIV:
        return {"regimes": []}
    
    try:
        from trading_system.regime import classify
        from trading_system.features import build_features
        
        universe = list(UNIV.equities_us.keys())[:10]
        data = fetch_universe(universe, UNIV.timeframe, lookback_days=365)
        
        regimes = []
        for sym, df in data.items():
            if len(df) < 220:
                continue
            feat = build_features(df).dropna()
            if feat.empty:
                continue
            snap = classify(feat)
            regimes.append({"symbol": sym, **snap.to_dict()})
        
        return {"regimes": regimes}
    except Exception as e:
        return {"error": str(e), "regimes": []}

@app.get("/performance")
async def performance():
    """Your original backtest"""
    if not UNIV:
        return {"error": "Trading system not loaded"}
    
    try:
        universe = list(UNIV.equities_us.keys())[:10]
        data = fetch_universe(universe, UNIV.timeframe, lookback_days=365*2)
        report = run_backtest(data)
        
        return {
            "summary": {
                "starting_equity": report.starting_equity,
                "ending_equity": report.ending_equity,
                "total_return": report.total_return,
                **report.metrics
            },
            "equity_curve": report.equity_curve[-100:],
            "trade_log": report.trade_log[-50:]
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# ALPACA INTEGRATION ENDPOINTS
# ============================================================================

@app.get("/api/alpaca/status")
async def alpaca_status():
    if not api:
        return {"connected": False, "error": "API not initialized"}
    
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
    except Exception as e:
        return {"connected": False, "error": str(e)}

@app.get("/api/alpaca/positions")
async def alpaca_positions():
    if not api:
        return {"positions": []}
    
    try:
        positions = api.list_positions()
        return {
            "positions": [{
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc) * 100
            } for p in positions]
        }
    except Exception as e:
        return {"positions": [], "error": str(e)}

@app.get("/api/alpaca/orders")
async def alpaca_orders():
    if not api:
        return {"orders": []}
    
    try:
        orders = api.list_orders(status='all', limit=50)
        return {
            "orders": [{
                "symbol": o.symbol,
                "qty": float(o.qty),
                "side": o.side,
                "status": o.status,
                "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else 0,
                "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None
            } for o in orders]
        }
    except Exception as e:
        return {"orders": [], "error": str(e)}

@app.get("/api/stocks/list")
async def stocks_list():
    return {"symbols": SYMBOLS, "total": len(SYMBOLS)}

@app.get("/api/market/quotes")
async def market_quotes():
    """Market quotes with fallback prices"""
    quotes = []
    
    for symbol, price in PRICES.items():
        quotes.append({
            "symbol": symbol,
            "price": price,
            "bid": price * 0.999,
            "ask": price * 1.001
        })
    
    return {"quotes": quotes, "total": len(quotes)}

@app.get("/api/bot/status")
async def bot_status():
    return {
        "running": False,
        "status": "Your original system is integrated - ready for live trading"
    }

@app.post("/api/trading/order")
async def place_order(symbol: str, qty: int, side: str):
    if not api:
        return {"success": False, "error": "Alpaca not connected"}
    
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