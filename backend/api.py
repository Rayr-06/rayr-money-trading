import os
import time
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np

load_dotenv()

app = FastAPI(title="RAYR MONEY Trading System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ALPACA SETUP
# ============================================================================

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

api = None
try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')
        print("✅ Alpaca API initialized")
except Exception as e:
    print(f"❌ Alpaca init failed: {e}")

# ============================================================================
# CONFIGURATION
# ============================================================================

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "SPY", "QQQ"]

bot_running = False
bot_thread = None
bot_logs = []
trade_history = []

def add_log(message):
    """Add log entry with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    bot_logs.append(log_entry)
    if len(bot_logs) > 100:
        bot_logs.pop(0)
    print(log_entry)

# ============================================================================
# TRADING BOT
# ============================================================================

def calculate_score(symbol, bars):
    """Simple momentum score"""
    try:
        if len(bars) < 20:
            return 0
        
        close = bars['close'].values
        sma_10 = close[-10:].mean()
        sma_20 = close[-20:].mean()
        current = close[-1]
        
        score = 0
        
        # Uptrend
        if current > sma_10 > sma_20:
            score += 50
        
        # Recent momentum
        recent_change = (current - close[-5]) / close[-5]
        if recent_change > 0.02:
            score += 30
        elif recent_change > 0:
            score += 15
        
        # Volume
        volume = bars['volume'].values
        if volume[-1] > volume[-5:].mean():
            score += 20
        
        return min(score, 100)
    except:
        return 0

def trading_bot():
    """Main bot loop with detailed logging"""
    global bot_running
    
    add_log("🤖 Trading bot STARTED!")
    add_log(f"📊 Monitoring {len(SYMBOLS)} stocks: {', '.join(SYMBOLS)}")
    add_log("⏰ Checking market every 60 seconds...")
    
    cycle = 0
    
    while bot_running:
        try:
            cycle += 1
            add_log(f"\n{'='*50}")
            add_log(f"🔄 Cycle #{cycle}")
            add_log(f"{'='*50}")
            
            # Get account info
            account = api.get_account()
            cash = float(account.cash)
            portfolio_value = float(account.portfolio_value)
            
            add_log(f"💰 Portfolio: ${portfolio_value:,.2f} | Cash: ${cash:,.2f}")
            
            # Check positions
            positions = api.list_positions()
            add_log(f"📊 Current positions: {len(positions)}")
            
            if len(positions) >= 3:
                add_log("⚠️  At max positions (3/3), managing existing only")
                
                # Manage positions
                for pos in positions:
                    pl_pct = float(pos.unrealized_plpc) * 100
                    add_log(f"   • {pos.symbol}: {float(pos.qty)} shares @ {pl_pct:+.2f}%")
                    
                    if pl_pct <= -5:
                        add_log(f"🛑 STOP LOSS triggered for {pos.symbol}")
                        api.close_position(pos.symbol)
                        trade_history.append({
                            'time': datetime.now().isoformat(),
                            'action': 'SELL (Stop Loss)',
                            'symbol': pos.symbol,
                            'reason': f'Loss: {pl_pct:.2f}%'
                        })
                    elif pl_pct >= 10:
                        add_log(f"💰 TAKE PROFIT triggered for {pos.symbol}")
                        api.close_position(pos.symbol)
                        trade_history.append({
                            'time': datetime.now().isoformat(),
                            'action': 'SELL (Take Profit)',
                            'symbol': pos.symbol,
                            'reason': f'Profit: {pl_pct:.2f}%'
                        })
            else:
                # Look for new trades
                add_log(f"🔍 Scanning {len(SYMBOLS)} stocks for signals...")
                
                current_symbols = [p.symbol for p in positions]
                
                for symbol in SYMBOLS:
                    if symbol in current_symbols:
                        continue
                    
                    try:
                        # Get data
                        bars = api.get_bars(symbol, '1Day', limit=50).df
                        if bars.empty:
                            continue
                        
                        score = calculate_score(symbol, bars)
                        price = float(bars.iloc[-1]['close'])
                        
                        add_log(f"   {symbol}: Score={score}/100, Price=${price:.2f}")
                        
                        if score >= 70:
                            # Calculate qty
                            position_value = portfolio_value * 0.15  # 15% per position
                            qty = int(position_value / price)
                            
                            if qty > 0 and (qty * price) <= cash:
                                add_log(f"🎯 SIGNAL: BUY {qty} {symbol} @ ${price:.2f} (Score: {score})")
                                
                                # Place order
                                order = api.submit_order(
                                    symbol=symbol,
                                    qty=qty,
                                    side='buy',
                                    type='market',
                                    time_in_force='day'
                                )
                                
                                add_log(f"✅ ORDER PLACED: {order.id}")
                                
                                trade_history.append({
                                    'time': datetime.now().isoformat(),
                                    'action': 'BUY',
                                    'symbol': symbol,
                                    'qty': qty,
                                    'price': price,
                                    'score': score
                                })
                                
                                time.sleep(2)
                    
                    except Exception as e:
                        add_log(f"   ⚠️  Error checking {symbol}: {str(e)[:50]}")
            
            add_log(f"⏰ Next check in 60 seconds...")
            time.sleep(60)
            
        except Exception as e:
            add_log(f"❌ Bot error: {e}")
            time.sleep(60)
    
    add_log("🛑 Trading bot STOPPED")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "app": "RAYR MONEY",
        "version": "2.0",
        "status": "running",
        "bot_running": bot_running
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
    """Get market quotes"""
    if not api:
        return {"quotes": [], "total": 0}
    
    quotes = []
    for symbol in SYMBOLS[:5]:
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
            continue
    
    return {"quotes": quotes, "total": len(quotes)}

@app.get("/api/bot/status")
async def bot_status():
    return {
        "running": bot_running,
        "status": "active" if bot_running else "stopped",
        "logs": bot_logs[-20:],  # Last 20 log entries
        "trades": len(trade_history)
    }

@app.get("/api/bot/logs")
async def get_logs():
    """Get full bot activity logs"""
    return {
        "logs": bot_logs,
        "total": len(bot_logs)
    }

@app.get("/api/bot/trades")
async def get_trades():
    """Get bot trade history"""
    return {
        "trades": trade_history,
        "total": len(trade_history)
    }

@app.post("/api/bot/start")
async def start_bot():
    global bot_running, bot_thread
    
    if bot_running:
        return {"status": "already_running"}
    
    bot_running = True
    bot_thread = threading.Thread(target=trading_bot, daemon=True)
    bot_thread.start()
    
    return {
        "status": "started",
        "message": "🤖 Bot activated! Check /api/bot/logs for activity."
    }

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_running
    bot_running = False
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