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
        print("✅ Alpaca API initialized successfully")
except Exception as e:
    print(f"❌ Alpaca init failed: {e}")

# ============================================================================
# CONFIGURATION
# ============================================================================

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "SPY", "QQQ"]

TRADING_CONFIG = {
    "max_positions": 3,
    "position_size_pct": 0.15,  # 15% per position
    "min_score": 70,
    "stop_loss_pct": 0.05,  # 5%
    "take_profit_pct": 0.10,  # 10%
    "check_interval": 60,  # seconds
}

bot_running = False
bot_thread = None
bot_logs = []
trade_history = []

def add_log(message):
    """Add timestamped log entry"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    bot_logs.append(entry)
    if len(bot_logs) > 200:
        bot_logs.pop(0)
    print(entry)
    return entry

# ============================================================================
# TRADING ALGORITHM
# ============================================================================

def calculate_score(symbol, bars):
    """Multi-factor momentum score (0-100)"""
    try:
        if len(bars) < 20:
            return 0
        
        close = bars['close'].values
        volume = bars['volume'].values
        score = 0
        
        # Factor 1: Trend (50 points)
        sma_5 = close[-5:].mean()
        sma_10 = close[-10:].mean()
        sma_20 = close[-20:].mean()
        current = close[-1]
        
        if current > sma_5 > sma_10 > sma_20:
            score += 50  # Strong uptrend
        elif current > sma_10 > sma_20:
            score += 30  # Moderate uptrend
        elif current > sma_20:
            score += 15  # Weak uptrend
        
        # Factor 2: Momentum (30 points)
        week_change = (current - close[-5]) / close[-5]
        if week_change > 0.03:
            score += 30
        elif week_change > 0.01:
            score += 15
        
        # Factor 3: Volume (20 points)
        avg_volume = volume[-10:].mean()
        if volume[-1] > avg_volume * 1.2:
            score += 20
        elif volume[-1] > avg_volume:
            score += 10
        
        return min(score, 100)
    except Exception as e:
        add_log(f"   ⚠️ Score error for {symbol}: {str(e)[:30]}")
        return 0

def trading_bot():
    """Main trading bot loop"""
    global bot_running
    
    add_log("=" * 60)
    add_log("🤖 RAYR MONEY TRADING BOT ACTIVATED")
    add_log("=" * 60)
    add_log(f"📊 Monitoring: {', '.join(SYMBOLS)}")
    add_log(f"⚙️ Strategy: Momentum-based multi-factor scoring")
    add_log(f"🎯 Min Score: {TRADING_CONFIG['min_score']}/100")
    add_log(f"💼 Max Positions: {TRADING_CONFIG['max_positions']}")
    add_log(f"🛡️ Stop Loss: {TRADING_CONFIG['stop_loss_pct']*100}%")
    add_log(f"💰 Take Profit: {TRADING_CONFIG['take_profit_pct']*100}%")
    add_log(f"⏰ Check Interval: {TRADING_CONFIG['check_interval']}s")
    add_log("=" * 60)
    
    cycle = 0
    
    while bot_running:
        try:
            cycle += 1
            add_log(f"\n🔄 CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            add_log("-" * 60)
            
            # Check market hours
            clock = api.get_clock()
            if not clock.is_open:
                add_log("🌙 Market is CLOSED. Waiting for next open...")
                time.sleep(300)  # Wait 5 minutes during market close
                continue
            
            # Get account
            account = api.get_account()
            cash = float(account.cash)
            portfolio_value = float(account.portfolio_value)
            
            add_log(f"💰 Portfolio: ${portfolio_value:,.2f} | Cash: ${cash:,.2f}")
            
            # Get positions
            positions = api.list_positions()
            add_log(f"📊 Positions: {len(positions)}/{TRADING_CONFIG['max_positions']}")
            
            # Manage existing positions
            for pos in positions:
                pl_pct = float(pos.unrealized_plpc)
                add_log(f"   • {pos.symbol}: {float(pos.qty)} @ {pl_pct*100:+.2f}%")
                
                if pl_pct <= -TRADING_CONFIG['stop_loss_pct']:
                    add_log(f"🛑 STOP LOSS: Closing {pos.symbol}")
                    api.close_position(pos.symbol)
                    trade_history.append({
                        'time': datetime.now().isoformat(),
                        'action': 'SELL',
                        'symbol': pos.symbol,
                        'reason': f'Stop Loss ({pl_pct*100:.2f}%)'
                    })
                elif pl_pct >= TRADING_CONFIG['take_profit_pct']:
                    add_log(f"💰 TAKE PROFIT: Closing {pos.symbol}")
                    api.close_position(pos.symbol)
                    trade_history.append({
                        'time': datetime.now().isoformat(),
                        'action': 'SELL',
                        'symbol': pos.symbol,
                        'reason': f'Take Profit ({pl_pct*100:.2f}%)'
                    })
            
            # Look for new signals if below max
            if len(positions) < TRADING_CONFIG['max_positions']:
                add_log(f"🔍 Scanning for BUY signals...")
                
                current_symbols = [p.symbol for p in positions]
                
                for symbol in SYMBOLS:
                    if symbol in current_symbols:
                        continue
                    
                    try:
                        bars = api.get_bars(symbol, '1Day', limit=50).df
                        if bars.empty:
                            continue
                        
                        score = calculate_score(symbol, bars)
                        price = float(bars.iloc[-1]['close'])
                        
                        add_log(f"   {symbol}: Score={score}/100, ${price:.2f}")
                        
                        if score >= TRADING_CONFIG['min_score']:
                            position_value = portfolio_value * TRADING_CONFIG['position_size_pct']
                            qty = int(position_value / price)
                            
                            if qty > 0 and (qty * price) <= cash:
                                add_log(f"🎯 BUY SIGNAL: {qty} {symbol} @ ${price:.2f}")
                                
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
                                    'score': score,
                                    'order_id': order.id
                                })
                                
                                time.sleep(2)
                    
                    except Exception as e:
                        add_log(f"   ⚠️ {symbol} error: {str(e)[:40]}")
            else:
                add_log("⚠️ At max positions, monitoring only")
            
            add_log(f"⏰ Next check in {TRADING_CONFIG['check_interval']}s")
            time.sleep(TRADING_CONFIG['check_interval'])
            
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
        "app": "RAYR MONEY Trading System",
        "version": "2.0",
        "status": "running",
        "alpaca_connected": api is not None,
        "bot_running": bot_running,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    market_status = "unknown"
    try:
        if api:
            clock = api.get_clock()
            market_status = "open" if clock.is_open else "closed"
    except:
        pass
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "alpaca_api": "connected" if api else "disconnected",
        "market_status": market_status
    }

@app.get("/api/alpaca/status")
async def alpaca_status():
    if not api:
        return {"connected": False}
    try:
        account = api.get_account()
        clock = api.get_clock()
        return {
            "connected": True,
            "portfolio_value": float(account.portfolio_value),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "paper_trading": True,
            "market_open": clock.is_open
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
        "config": TRADING_CONFIG,
        "logs_count": len(bot_logs),
        "trades_count": len(trade_history),
        "recent_logs": bot_logs[-10:] if bot_logs else []
    }

@app.get("/api/bot/logs")
async def get_logs():
    return {
        "logs": bot_logs,
        "total": len(bot_logs)
    }

@app.get("/api/bot/trades")
async def get_trades():
    return {
        "trades": trade_history,
        "total": len(trade_history)
    }

@app.post("/api/bot/start")
async def start_bot():
    global bot_running, bot_thread
    
    if bot_running:
        return {"status": "already_running", "message": "Bot is already active"}
    
    bot_running = True
    bot_thread = threading.Thread(target=trading_bot, daemon=True)
    bot_thread.start()
    
    return {
        "status": "started",
        "message": "🤖 Trading bot activated! Monitor /api/bot/logs for activity."
    }

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_running
    bot_running = False
    add_log("🛑 Bot stop requested by user")
    return {"status": "stopped", "message": "Bot deactivated"}

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
        return {"success": True, "order_id": order.id, "status": order.status}
    except Exception as e:
        return {"success": False, "error": str(e)}