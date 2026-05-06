"""
RAYR MONEY - LIVE ALPACA INTEGRATION RUNNER
Author: Senior Quantitative Architect
Description: Ready-to-run live execution loop connecting your strategy models
             directly to Alpaca's high-performance Paper Trading REST API.
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv
from data import MultiTimeframePipeline
from strategy import ScoringStrategyEngine
from risk import EliteRiskEngine
from execution import AlpacaBroker

# Load secrets from local environment
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RayrMoneyAlpaca")

# API Keys (Must be configured in your local .env file)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID", "YOUR_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Asset Configuration
TICKERS = ["AAPL", "SPY"]
SECTOR_CORRELATIONS = {"Tech": ["AAPL"], "Index": ["SPY"]}

def run_live_cycle():
    """
    Core execution interval. Downloads current data, computes technical signals,
    checks portfolio concentration barriers, and posts active orders to Alpaca.
    """
    logger.info("Starting live Alpaca market scan iteration...")
    
    # 1. Initialize Pipeline & Modules
    pipeline = MultiTimeframePipeline(skip_opening_mins=30)
    scoring_engine = ScoringStrategyEngine(score_threshold=70)
    risk_engine = EliteRiskEngine(max_total_risk_pct=0.05)
    broker = AlpacaBroker(api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)
    
    # 2. Fetch current balance
    account_equity = broker.get_account_balance()
    if account_equity <= 0:
        logger.error("Could not fetch healthy Alpaca account balance. Skipping iteration.")
        return
        
    logger.info(f"Current Alpaca Account Equity: \${account_equity:.2f}")
    
    # 3. Fetch active positions from Alpaca REST endpoint
    active_positions_list = broker.get_positions()
    active_positions_dict = {pos.get("symbol"): pos for pos in active_positions_list}
    
    # 4. Check for active indicators across each ticker
    for ticker in TICKERS:
        # Fetch 5m execution and 1h confirmation historical intervals
        df_5m, df_1h = pipeline.fetch_synchronized_data(ticker, start_date="2026-01-01", end_date="2026-03-31")
        if df_5m.empty or df_1h.empty:
            logger.warning(f"Insufficient synced history for {ticker}. Skipping.")
            continue
            
        # Calculate Signals and Trade Quality Scores
        evaluation = scoring_engine.evaluate_signals(df_5m, df_1h)
        action = evaluation["action"]
        score = evaluation["score"]
        regime = evaluation["regime"]
        reason = evaluation["reason"]
        
        logger.info(f"{ticker} | Regime: {regime} | Candidate Score: {score}/100 | Signal: {action}")
        
        if action == "HOLD":
            logger.info(f"Standing aside for {ticker}: {reason}")
            continue
            
        # 5. Check risk limit barriers
        is_allowed, risk_reason = risk_engine.validate_new_execution(
            portfolio_equity=account_equity,
            active_positions=active_positions_dict,
            target_ticker=ticker,
            sector_correlations=SECTOR_CORRELATIONS
        )
        
        if not is_allowed:
            logger.warning(f"Execution blocked by Risk Engine: {risk_reason}")
            continue
            
        # 6. Position Sizing
        last_price = df_5m.iloc[-1]["close"]
        last_atr = df_5m.iloc[-1]["atr"] if "atr" in df_5m.columns else last_price * 0.015
        
        qty, stop_loss, take_profit, risk_cash = risk_engine.calculate_adaptive_size(
            capital=account_equity,
            price=last_price,
            atr=last_atr,
            confidence=evaluation.get("confidence", "LOW")
        )
        
        # 7. Execute order via Alpaca Paper API
        if action == "BUY" and ticker not in active_positions_dict:
            logger.info(f"ROUTING BUY ORDER: {qty} {ticker} @ \${last_price:.2f} (Allocated Risk: \${risk_cash})")
            order = broker.place_order(ticker, "BUY", qty, order_type="market")
            logger.info(f"Alpaca Order Response: {order}")
            
        elif action == "SELL" and ticker in active_positions_dict:
            logger.info(f"ROUTING SELL ORDER: Liquidating {ticker} @ \${last_price:.2f}")
            order = broker.place_order(ticker, "SELL", active_positions_dict[ticker].get("qty"), order_type="market")
            logger.info(f"Alpaca Order Response: {order}")

if __name__ == "__main__":
    if ALPACA_API_KEY == "YOUR_API_KEY" or ALPACA_SECRET_KEY == "YOUR_SECRET_KEY":
        logger.error("Please configure ALPACA_API_KEY_ID and ALPACA_SECRET_KEY in your local environment!")
    else:
        logger.info("RAYR MONEY Alpaca connection established. Running continuous market polling...")
        try:
            while True:
                run_live_cycle()
                logger.info("Iteration complete. Sleeping for 5 minutes (300 seconds)...")
                time.sleep(300)
        except KeyboardInterrupt:
            logger.info("Live polling cycle manually terminated.")
