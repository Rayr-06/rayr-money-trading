"""
RAYR MONEY - Simplified Live Trading Runner
No FastAPI dependency - direct Alpaca integration
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
import numpy as np
import requests

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("RayrMoney")

# Configuration from .env
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
TICKERS = ["AAPL", "SPY"]
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", 70))
RISK_PCT = float(os.getenv("RISK_PCT_PER_TRADE", 0.015))

def get_alpaca_headers():
    """Return Alpaca API headers"""
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }

def check_alpaca_connection():
    """Test Alpaca connection and get account info"""
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/account",
            headers=get_alpaca_headers()
        )
        
        if response.status_code == 200:
            account = response.json()
            equity = float(account['equity'])
            cash = float(account['cash'])
            buying_power = float(account['buying_power'])
            
            logger.info(f"✅ ALPACA CONNECTED!")
            logger.info(f"   Account Equity: ${equity:,.2f}")
            logger.info(f"   Cash Balance: ${cash:,.2f}")
            logger.info(f"   Buying Power: ${buying_power:,.2f}")
            return equity
        else:
            logger.error(f"❌ Alpaca auth failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return None

def get_positions():
    """Get current positions from Alpaca"""
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/positions",
            headers=get_alpaca_headers()
        )
        
        if response.status_code == 200:
            return {pos['symbol']: pos for pos in response.json()}
        return {}
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return {}

def calculate_indicators(df):
    """Calculate technical indicators"""
    # EMAs
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
    
    # Volume
    df['volume_ma'] = df['volume'].rolling(20).mean()
    
    return df

def score_trade(df):
    """Score trade quality 0-100"""
    if len(df) < 200:
        return 0, "HOLD", "Insufficient data", "UNKNOWN"
    
    last = df.iloc[-1]
    score = 0
    factors = []
    
    # Multi-timeframe alignment (30 points)
    if last['ema_50'] > last['ema_200']:
        score += 30
        factors.append("✓ Uptrend confirmed (EMA 50 > 200)")
        regime = "STRONG_TREND"
    elif abs(last['ema_50'] - last['ema_200']) / last['ema_200'] < 0.02:
        score += 15
        factors.append("~ Range-bound (EMAs converging)")
        regime = "RANGE"
    else:
        factors.append("✗ Downtrend (EMA 50 < 200)")
        regime = "WEAK_TREND"
    
    # Trend strength - ADX proxy (25 points)
    ema_slope = (df['ema_50'].iloc[-1] - df['ema_50'].iloc[-5]) / df['ema_50'].iloc[-5]
    if ema_slope > 0.01:
        score += 25
        factors.append("✓ Strong momentum")
    elif ema_slope > 0:
        score += 15
        factors.append("~ Weak momentum")
    else:
        factors.append("✗ Negative momentum")
    
    # Volume confirmation (25 points)
    if last['volume'] > last['volume_ma'] * 1.2:
        score += 25
        factors.append("✓ High volume (>120% avg)")
    elif last['volume'] > last['volume_ma']:
        score += 15
        factors.append("~ Above average volume")
    else:
        factors.append("✗ Low volume")
    
    # Volatility fit (20 points)
    atr_pct = last['atr'] / last['close']
    if 0.01 < atr_pct < 0.03:
        score += 20
        factors.append("✓ Normal volatility")
    elif atr_pct < 0.05:
        score += 10
        factors.append("~ Acceptable volatility")
    else:
        factors.append("✗ High volatility (chaotic)")
        regime = "CHAOTIC"
    
    # RSI check (bonus/penalty)
    if 30 < last['rsi'] < 70:
        pass  # Neutral
    elif last['rsi'] < 30:
        factors.append("⚠ Oversold (RSI < 30)")
    elif last['rsi'] > 70:
        factors.append("⚠ Overbought (RSI > 70)")
        score -= 10
    
    action = "BUY" if score >= SCORE_THRESHOLD else "HOLD"
    reason = f"Score: {score}/100 | " + " | ".join(factors[:3])
    
    return score, action, reason, regime

def place_order(symbol, side, qty, dry_run=True):
    """Place order on Alpaca"""
    if dry_run:
        logger.info(f"   [DRY RUN] Would place {side} order: {qty} {symbol}")
        return {"status": "DRY_RUN", "id": "test-123"}
    
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
            logger.info(f"   ✅ Order placed: {order['id']} | Status: {order['status']}")
            return order
        else:
            logger.error(f"   ❌ Order failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"   ❌ Order error: {e}")
        return None

def run_trading_scan(equity, dry_run=True):
    """Main trading scan"""
    logger.info("=" * 70)
    logger.info(f"MARKET SCAN | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    positions = get_positions()
    logger.info(f"Current Positions: {len(positions)}")
    
    for ticker in TICKERS:
        try:
            logger.info(f"\n📊 Analyzing {ticker}...")
            
            # Download data
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            
            if df.empty:
                logger.warning(f"   ❌ No data for {ticker}")
                continue
            
            # Standardize columns
            df.columns = [c.lower() for c in df.columns]
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            
            # Get current price
            current_price = float(df['close'].iloc[-1])
            logger.info(f"   Current Price: ${current_price:.2f}")
            
            # Calculate indicators
            df = calculate_indicators(df)
            
            # Score trade
            score, action, reason, regime = score_trade(df)
            
            logger.info(f"   Regime: {regime}")
            logger.info(f"   {reason}")
            logger.info(f"   Action: {action}")
            
            # Decision logic
            if action == "BUY" and ticker not in positions:
                logger.info(f"\n   🎯 HIGH QUALITY SETUP DETECTED!")
                
                # Position sizing
                last_atr = df['atr'].iloc[-1]
                risk_amount = equity * RISK_PCT
                shares = int(risk_amount / (2 * last_atr))
                shares = max(1, shares)  # At least 1 share
                
                cost = shares * current_price
                logger.info(f"   Position Size: {shares} shares")
                logger.info(f"   Total Cost: ${cost:.2f}")
                logger.info(f"   Risk Amount: ${risk_amount:.2f}")
                logger.info(f"   Stop Loss: ${current_price - 2*last_atr:.2f}")
                logger.info(f"   Take Profit: ${current_price + 4*last_atr:.2f}")
                
                # Place order
                place_order(ticker, "BUY", shares, dry_run=dry_run)
                
            elif ticker in positions:
                pos = positions[ticker]
                entry_price = float(pos['avg_entry_price'])
                current_qty = int(pos['qty'])
                unrealized_pl = float(pos['unrealized_pl'])
                
                logger.info(f"   📌 Existing Position:")
                logger.info(f"      Entry: ${entry_price:.2f} | Qty: {current_qty}")
                logger.info(f"      P&L: ${unrealized_pl:.2f}")
                
                # Check exit conditions
                if regime == "CHAOTIC" or score < 40:
                    logger.info(f"   ⚠️ EXIT SIGNAL: {regime}")
                    place_order(ticker, "SELL", current_qty, dry_run=dry_run)
            
        except Exception as e:
            logger.error(f"   ❌ Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n" + "=" * 70)

def main():
    """Main loop"""
    logger.info("=" * 70)
    logger.info("🚀 RAYR MONEY - SIMPLIFIED TRADING SYSTEM")
    logger.info("=" * 70)
    
    # Check credentials
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        logger.error("❌ Missing Alpaca credentials in .env file!")
        logger.error("   Edit backend/.env and add:")
        logger.error("   ALPACA_API_KEY_ID=your_key_here")
        logger.error("   ALPACA_SECRET_KEY=your_secret_here")
        return
    
    # Test connection
    logger.info("\n🔌 Testing Alpaca connection...")
    equity = check_alpaca_connection()
    
    if not equity:
        logger.error("❌ Cannot connect to Alpaca. Check your API keys in .env")
        return
    
    # Determine mode
    mode = input("\n⚠️  TRADING MODE:\n   [1] DRY RUN (recommended - no real orders)\n   [2] LIVE TRADING (places real paper trades)\n   Choose (1 or 2): ")
    
    dry_run = mode != "2"
    
    if dry_run:
        logger.info("\n✅ DRY RUN MODE - No real orders will be placed")
        logger.info("   System will show what it WOULD do")
    else:
        confirm = input("\n⚠️  LIVE MODE will place REAL orders on your Alpaca paper account!\n   Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Cancelled. Switching to dry run mode.")
            dry_run = True
    
    logger.info(f"\n📊 Trading Parameters:")
    logger.info(f"   Symbols: {', '.join(TICKERS)}")
    logger.info(f"   Score Threshold: {SCORE_THRESHOLD}/100")
    logger.info(f"   Risk per Trade: {RISK_PCT*100}%")
    logger.info(f"   Scan Interval: 5 minutes")
    
    logger.info("\n✅ System Ready. Starting trading loop...")
    logger.info("   Press Ctrl+C to stop\n")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"ITERATION #{iteration}")
            
            # Refresh equity
            equity = check_alpaca_connection()
            if not equity:
                logger.error("Lost connection to Alpaca. Retrying in 1 minute...")
                time.sleep(60)
                continue
            
            # Run scan
            run_trading_scan(equity, dry_run=dry_run)
            
            # Sleep
            logger.info(f"\n💤 Sleeping for 5 minutes...")
            logger.info(f"   Next scan at: {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            logger.info("\n\n👋 Trading stopped by user")
            break
        except Exception as e:
            logger.error(f"\n❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            logger.info("Continuing after 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
