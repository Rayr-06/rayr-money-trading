"""
RAYR MONEY - UNIFIED LIVE TRADING BACKEND
Serves the web UI AND executes real Alpaca trades
Run this once, everything works together
"""

import os
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from threading import Thread
import json

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("RayrMoney")

# Configuration
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
TICKERS = ["AAPL", "SPY"]
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", 70))
RISK_PCT = float(os.getenv("RISK_PCT_PER_TRADE", 0.015))

# Global state
trading_active = False
system_logs = []
positions = []
orders = []
account_balance = 100000.0

app = FastAPI()

# CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def add_log(message: str):
    """Add log to system logs"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    system_logs.append(log_entry)
    logger.info(message)
    # Keep only last 100 logs
    if len(system_logs) > 100:
        system_logs.pop(0)

def get_alpaca_headers():
    """Return Alpaca API headers"""
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }

def get_account_info():
    """Get Alpaca account info"""
    global account_balance
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/account",
            headers=get_alpaca_headers()
        )
        if response.status_code == 200:
            account = response.json()
            account_balance = float(account['equity'])
            return account
        return None
    except Exception as e:
        add_log(f"âŒ Error fetching account: {e}")
        return None

def get_positions():
    """Get current positions from Alpaca"""
    global positions
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/positions",
            headers=get_alpaca_headers()
        )
        if response.status_code == 200:
            positions = response.json()
            return positions
        return []
    except Exception as e:
        add_log(f"âŒ Error fetching positions: {e}")
        return []

def get_orders():
    """Get recent orders from Alpaca"""
    global orders
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/orders?status=all&limit=20",
            headers=get_alpaca_headers()
        )
        if response.status_code == 200:
            orders = response.json()
            return orders
        return []
    except Exception as e:
        add_log(f"âŒ Error fetching orders: {e}")
        return []

def calculate_indicators(df):
    """Calculate technical indicators"""
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    df['volume_ma'] = df['volume'].rolling(20).mean()
    
    return df

def score_trade(df):
    """Score trade quality 0-100"""
    if len(df) < 200:
        return 0, "HOLD", "Insufficient data", "UNKNOWN"
    
    last = df.iloc[-1]
    score = 0
    
    # Trend (30 points)
    if last['ema_50'] > last['ema_200']:
        score += 30
        regime = "STRONG_TREND"
    elif abs(last['ema_50'] - last['ema_200']) / last['ema_200'] < 0.02:
        score += 15
        regime = "RANGE"
    else:
        regime = "WEAK_TREND"
    
    # Momentum (25 points)
    ema_slope = (df['ema_50'].iloc[-1] - df['ema_50'].iloc[-5]) / df['ema_50'].iloc[-5]
    if ema_slope > 0.01:
        score += 25
    elif ema_slope > 0:
        score += 15
    
    # Volume (25 points)
    if last['volume'] > last['volume_ma'] * 1.2:
        score += 25
    elif last['volume'] > last['volume_ma']:
        score += 15
    
    # Volatility (20 points)
    atr_pct = last['atr'] / last['close']
    if 0.01 < atr_pct < 0.03:
        score += 20
    elif atr_pct < 0.05:
        score += 10
    else:
        regime = "CHAOTIC"
    
    # RSI penalty
    if last['rsi'] > 70:
        score -= 10
    
    action = "BUY" if score >= SCORE_THRESHOLD else "HOLD"
    reason = f"Score: {score}/100 - {regime}"
    
    return score, action, reason, regime

def place_order(symbol, side, qty):
    """Place order on Alpaca"""
    order_data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "day"
    }
    
    try:
        response = requests.post(
            f"{ALPACA_BASE_URL}/v2/orders",
            json=order_data,
            headers=get_alpaca_headers()
        )
        
        if response.status_code in [200, 201]:
            order = response.json()
            add_log(f"âœ… ORDER PLACED: {side} {qty} {symbol} - Order ID: {order['id']}")
            return order
        else:
            add_log(f"âŒ Order failed: {response.text}")
            return None
    except Exception as e:
        add_log(f"âŒ Order error: {e}")
        return None

def trading_loop():
    """Main trading loop - runs in background"""
    global trading_active
    
    add_log("ðŸš€ RAYR MONEY Trading Bot Started")
    add_log(f"ðŸ“Š Monitoring: {', '.join(TICKERS)}")
    add_log(f"âš™ï¸ Score Threshold: {SCORE_THRESHOLD}/100")
    add_log(f"ðŸ’° Risk per Trade: {RISK_PCT*100}%")
    
    iteration = 0
    
    while True:
        if not trading_active:
            time.sleep(10)
            continue
        
        try:
            iteration += 1
            add_log(f"ðŸ”„ Market Scan #{iteration}")
            
            # Get account info
            account = get_account_info()
            if not account:
                add_log("âŒ Lost connection to Alpaca")
                time.sleep(60)
                continue
            
            equity = float(account['equity'])
            add_log(f"ðŸ’µ Account Equity: ${equity:,.2f}")
            
            # Get current positions
            current_positions = get_positions()
            position_symbols = {p['symbol']: p for p in current_positions}
            
            # Scan each ticker
            for ticker in TICKERS:
                try:
                    add_log(f"ðŸ“Š Analyzing {ticker}...")
                    
                    # Download data
                    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
                    
                    if df.empty:
                        add_log(f"âš ï¸ No data for {ticker} (market may be closed)")
                        continue
                    
                    # Standardize
                    df.columns = [c.lower() for c in df.columns]
                    df = df.reset_index()
                    df.columns = [c.lower() for c in df.columns]
                    
                    current_price = float(df['close'].iloc[-1])
                    
                    # Calculate indicators
                    df = calculate_indicators(df)
                    
                    # Score
                    score, action, reason, regime = score_trade(df)
                    
                    add_log(f"   {ticker}: {regime} | {reason}")
                    
                    # Trading logic
                    if action == "BUY" and ticker not in position_symbols:
                        add_log(f"ðŸŽ¯ HIGH QUALITY SETUP: {ticker}")
                        
                        # Position sizing
                        atr = df['atr'].iloc[-1]
                        risk_amount = equity * RISK_PCT
                        shares = max(1, int(risk_amount / (2 * atr)))
                        
                        add_log(f"   Placing order: {shares} shares @ ${current_price:.2f}")
                        place_order(ticker, "BUY", shares)
                        
                    elif ticker in position_symbols:
                        if regime == "CHAOTIC" or score < 40:
                            pos = position_symbols[ticker]
                            qty = int(pos['qty'])
                            add_log(f"âš ï¸ EXIT SIGNAL: {ticker} ({regime})")
                            place_order(ticker, "SELL", qty)
                
                except Exception as e:
                    add_log(f"âŒ Error analyzing {ticker}: {str(e)}")
            
            # Update positions and orders
            get_positions()
            get_orders()
            
            add_log(f"ðŸ’¤ Sleeping 5 minutes...")
            time.sleep(300)  # 5 minutes
            
        except Exception as e:
            add_log(f"âŒ Error in trading loop: {str(e)}")
            time.sleep(60)

# API Endpoints

@app.get("/")
def read_root():
    return {"status": "RAYR MONEY Live Trading Backend", "trading_active": trading_active}

@app.post("/start_trading")
def start_trading():
    global trading_active
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        return {"success": False, "message": "Alpaca credentials not configured"}
    
    trading_active = True
    add_log("ðŸŸ¢ TRADING ACTIVATED")
    return {"success": True, "message": "Trading started"}

@app.post("/stop_trading")
def stop_trading():
    global trading_active
    trading_active = False
    add_log("ðŸ”´ TRADING STOPPED")
    return {"success": True, "message": "Trading stopped"}

@app.get("/status")
def get_status():
    """Get current system status"""
    account = get_account_info()
    current_positions = get_positions()
    recent_orders = get_orders()
    
    return {
        "trading_active": trading_active,
        "account": {
            "equity": account_balance,
            "cash": float(account.get('cash', 0)) if account else 0,
            "buying_power": float(account.get('buying_power', 0)) if account else 0
        },
        "positions": current_positions,
        "recent_orders": recent_orders[:10],
        "system_logs": system_logs[-20:]
    }

@app.get("/logs")
def get_logs():
    """Get system logs"""
    return {"logs": system_logs[-50:]}

@app.post("/test_connection")
def test_connection():
    """Test Alpaca connection"""
    account = get_account_info()
    if account:
        return {
            "success": True,
            "equity": float(account['equity']),
            "cash": float(account['cash']),
            "buying_power": float(account['buying_power'])
        }
    return {"success": False, "message": "Connection failed"}

def start_background_trading():
    """Start trading loop in background thread"""
    thread = Thread(target=trading_loop, daemon=True)
    thread.start()
    logger.info("Background trading thread started")

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("ðŸš€ RAYR MONEY - UNIFIED TRADING BACKEND")
    logger.info("=" * 70)
    
    # Check credentials
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        logger.warning("âš ï¸ Alpaca credentials not found in .env")
        logger.warning("   Add them to backend/.env to enable trading")
    else:
        logger.info("âœ… Alpaca credentials loaded")
        # Test connection
        account = get_account_info()
        if account:
            logger.info(f"âœ… Connected to Alpaca Paper Trading")
            logger.info(f"   Balance: ${float(account['equity']):,.2f}")
        else:
            logger.warning("âš ï¸ Could not connect to Alpaca")
    
    # Start background trading thread
    start_background_trading()
    
    logger.info("\nðŸ“¡ Starting API server on http://localhost:8000")
    logger.info("ðŸŒ Open your web UI and click 'START TRADING' to begin")
    logger.info("\nAPI Endpoints:")
    logger.info("  POST /start_trading  - Start the trading bot")
    logger.info("  POST /stop_trading   - Stop the trading bot")
    logger.info("  GET  /status         - Get current status")
    logger.info("  GET  /logs           - Get system logs")
    logger.info("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
