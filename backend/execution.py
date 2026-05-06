"""
RAYR MONEY - ULTRA-REALISTIC EXECUTION LAYER
Author: Senior Quantitative Architect
Description: Mimics physical low-latency execution including network latency delays,
             variable slippage modeling, and broker order rejections.
"""

import time
import random
import logging
from typing import Dict

logger = logging.getLogger("RayrMoneyLogger")

class HighFidelityBrokerSimulator:
    def __init__(self, initial_capital: float = 1000.0):
        self.balance = initial_capital
        self.positions = {}
        self.order_id_counter = 5000
        
    def execute_order(
        self,
        ticker: str,
        side: str,
        qty: int,
        market_price: float,
        slippage_factor: float = 0.001, # Default 0.1% slippage
        transaction_fee_pct: float = 0.0003 # 0.03% Exchange clearance fee
    ) -> Dict:
        """
        Fills order modeling network latency and variable slippage.
        """
        self.order_id_counter += 1
        
        # 1. Simulate Network Latency Delay (50ms to 200ms)
        latency = random.uniform(0.05, 0.20)
        time.sleep(latency)
        
        # 2. Broker Order Rejection Risk (0.5% structural failure rate)
        if random.random() < 0.005:
            logger.error(f"Execution failure: Exchange rejected order {self.order_id_counter} for {ticker}")
            return {"status": "REJECTED", "reason": "EXCHANGE_LMT_ORDER_BOOK_OUT_OF_SYNC"}

        # 3. Model Slippage
        fill_price = market_price
        if side.upper() == "BUY":
            fill_price *= (1 + slippage_factor)
        else:
            fill_price *= (1 - slippage_factor)
            
        fill_price = round(fill_price, 2)
        total_value = fill_price * qty
        fee = total_value * transaction_fee_pct
        
        if side.upper() == "BUY":
            total_cost = total_value + fee
            if total_cost > self.balance:
                return {"status": "REJECTED", "reason": "INSUFFICIENT_MARGIN_CALL"}
            self.balance -= total_cost
            self.positions[ticker] = self.positions.get(ticker, 0) + qty
        else:
            if self.positions.get(ticker, 0) < qty:
                return {"status": "REJECTED", "reason": "SHORT_SALE_RESTRICTION"}
            revenue = total_value - fee
            self.balance += revenue
            self.positions[ticker] -= qty
            if self.positions[ticker] == 0:
                del self.positions[ticker]
                
        logger.info(f"Order filled: {side} {qty} shares of {ticker} @ {fill_price}. Fee: \${fee:.2f} (Latency: {latency*1000:.1f}ms)")
        return {
            "status": "FILLED",
            "order_id": self.order_id_counter,
            "ticker": ticker,
            "side": side,
            "qty": qty,
            "price": fill_price,
            "fee": round(fee, 2),
            "remaining_balance": round(self.balance, 2)
        }
