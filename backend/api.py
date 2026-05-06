import os
import time
import threading
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
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
    else:
        print("⚠️ Alpaca keys not found")
except Exception as e:
    print(f"❌ Alpaca init failed: {e}")

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "SPY", "QQQ"]

TRADING_CONFIG = {
    "max_positions": 5,
    "position_size_pct": 0.10,  # 10% of portfolio per position
    "min_score": 70,  # Minimum quality score to trade
    "stop_loss_pct": 0.05,  # 5% stop loss
    "take_profit_pct": 0.10,  # 10% take profit
    "check_interval": 60,  # Check every 60 seconds
}

bot_running = False
bot_thread = None
trade_log = []

# ============================================================================
# TRADING ALGORITHM
# ============================================================================

def calculate_trade_score(symbol, bars):
    """Calculate multi-factor trade quality score (0-100)"""
    try:
        if len(bars) < 50:
            return 0
        
        score = 0
        close = bars['close'].values
        volume = bars['volume'].values
        
        # Factor 1: Trend Strength (30 points)
        sma_20 = close[-20:].mean()
        sma_50 = close[-50:].mean() if len(close) >= 50 else sma_20
        
        if close[-1] > sma_20 > sma_50:
            score += 30  # Strong uptrend
        elif close[-1] > sma_20:
            score += 20  # Moderate uptrend
        elif close[-1] > sma_50:
            score += 10  # Weak uptrend
        
        # Factor 2: Volume Confirmation (25 points)
        avg_volume = volume[-20:].mean()
        recent_volume = volume[-5:].mean()
        
        if recent_volume > avg_volume * 1.2:
            score += 25  # High volume
        elif recent_volume > avg_volume:
            score += 15  # Above average
        
        # Factor 3: Volatility Check (20 points)
        returns = np.diff(close[-20:]) / close[-21:-1]
        volatility = np.std(returns)
        
        if 0.01 < volatility < 0.03:
            score += 20  # Ideal volatility
        elif volatility < 0.05:
            score += 10  # Acceptable
        
        # Factor 4: Price Action (25 points)
        last_5_returns = returns[-5:]
        positive_days = sum(1 for r in last_5_returns if r > 0)
        
        if positive_days >= 4:
            score += 25  # Strong momentum
        elif positive_days >= 3:
            score += 15  # Moderate momentum
        
        return min(score, 100)
        
    except Exception as e:
        print(f"Score calc error for {symbol}: {e}")
        return 0

def check_trade_signals():
    """Check all symbols for trade signals"""
    if not api:
        return []
    
    signals = []
    
    try:
        account = api.get_account()
        cash = float(account.cash)
        portfolio_value = float(account.portfolio_value)
        
        # Get current positions
        positions = api.list_positions()
        current_symbols = [p.symbol for p in positions]
        
        # Don't add new positions if at max
        if len(positions) >= TRADING_CONFIG['max_positions']:
            print(f"📊 At max positions ({len(positions)}/{TRADING_CONFIG['max_positions']})")
            return []
        
        for symbol in SYMBOLS:
            if symbol in current_symbols:
                continue  # Skip if already have position
            
            try:
                # Get historical data
                bars = api.get_bars(
                    symbol, 
                    '1Day', 
                    limit=100
                ).df
                
                if bars.empty:
                    continue
                
                # Calculate score
                score = calculate_trade_score(symbol, bars)
                
                if score >= TRADING_CONFIG['min_score']:
                    # Calculate position size
                    current_price = float(bars.iloc[-1]['close'])
                    position_value = portfolio_value * TRADING_CONFIG['position_size_pct']
                    qty = int(position_value / current_price)
                    
                    if qty > 0 and (qty * current_price) <= cash:
                        signals.append({
                            'symbol': symbol,
                            'score': score,
                            'price': current_price,
                            'qty': qty,
                            'action': 'BUY'
                        })
                        print(f"🎯 Signal: BUY {qty} {symbol} @ ${current_price:.2f} (Score: {score})")
                
            except Exception as e:
                print(f"Error checking {symbol}: {e}")
                continue
        
        return signals
        
    except Exception as e:
        print(f"Signal check error: {e}")
        return []

def execute_trade(signal):
    """Execute a trade based on signal"""
    if not api:
        return False
    
    try:
        order = api.submit_order(
            symbol=signal['symbol'],
            qty=signal['qty'],
            side=signal['action'].lower(),
            type='market',
            time_in_force='day'
        )
        
        trade_log.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': signal['symbol'],
            'action': signal['action'],
            'qty': signal['qty'],
            'price': signal['price'],
            'score': signal['score'],
            'order_id': order.id
        })
        
        print(f"✅ EXECUTED: {signal['action']} {signal['qty']} {signal['symbol']} @ ${signal['price']:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Trade execution failed: {e}")
        return False

def manage_positions():
    """Manage existing positions (stop loss, take profit)"""
    if not api:
        return
    
    try:
        positions = api.list_positions()
        
        for pos in positions:
            try:
                symbol = pos.symbol
                entry_price = float(pos.avg_entry_price)
                current_price = float(pos.current_price)
                unrealized_plpc = float(pos.unrealized_plpc)
                
                # Check stop loss
                if unrealized_plpc <= -TRADING_CONFIG['stop_loss_pct']:
                    print(f"🛑 STOP LOSS: Selling {symbol} (Loss: {unrealized_plpc*100:.2f}%)")
                    api.close_position(symbol)
                    continue
                
                # Check take profit
                if unrealized_plpc >= TRADING_CONFIG['take_profit_pct']:
                    print(f"💰 TAKE PROFIT: Selling {symbol} (Profit: {unrealized_plpc*100:.2f}%)")
                    api.close_position(symbol)
                    continue
                
            except Exception as e:
                print(f"Error managing {pos.symbol}: {e}")
                continue
                
    except Exception as e:
        print(f"Position management error: {e}")

def trading_bot_loop():
    """Main trading bot loop"""
    global bot_running
    
    print("🤖 Trading bot started!")
    
    while bot_running:
        try:
            print(f"\n{'='*60}")
            print(f"🤖 Bot Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Manage existing positions
            manage_positions()
            
            # Check for new signals
            signals = check_trade_signals()
            
            # Execute top signals
            for signal in signals[:3]:  # Max 3 new trades per cycle
                execute_trade(signal)
                time.sleep(2)  # Brief pause between orders
            
            if not signals:
                print("📊 No trade signals at this time")
            
            # Wait before next check
            time.sleep(TRADING_CONFIG['check_interval'])
            
        except Exception as e:
            print(f"🤖 Bot loop error: {e}")
            time.sleep(60)
    
    print("🤖 Trading bot stopped")

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
        "bot_running": bot_running
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "alpaca_api": "connected" if api else "disconnected"
    }

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
            "paper_trading": True,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}

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
            ],
            "total": len(positions)
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
    return {"symbols": SYMBOLS, "total": len(SYMBOLS)}

@app.get("/api/market/quotes")
async def get_quotes():
    if not api:
        return {"quotes": []}
    
    quotes_data = []
    for symbol in SYMBOLS[:5]:
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

@app.get("/api/bot/status")
async def bot_status():
    return {
        "running": bot_running,
        "status": "active" if bot_running else "stopped",
        "config": TRADING_CONFIG,
        "trade_count": len(trade_log)
    }

@app.post("/api/bot/start")
async def start_bot():
    global bot_running, bot_thread
    
    if bot_running:
        return {"status": "already_running"}
    
    bot_running = True
    bot_thread = threading.Thread(target=trading_bot_loop, daemon=True)
    bot_thread.start()
    
    return {
        "status": "started",
        "message": "🤖 Trading bot activated! Will check every 60 seconds.",
        "config": TRADING_CONFIG
    }

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_running
    bot_running = False
    return {"status": "stopped", "message": "Trading bot deactivated"}

@app.get("/api/bot/trades")
async def get_trade_log():
    return {"trades": trade_log[-50:], "total": len(trade_log)}

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
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "status": order.status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}