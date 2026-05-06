"""
RAYR MONEY - ALPACA HIGH-PERFORMANCE REST CLIENT
Author: Senior Full-Stack Quantitative Architect
Description: Handles core communication with Alpaca's high-speed REST API.
             Dynamically switches base endpoints between Paper and Live modes.
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger("RayrMoneyAlpacaClient")

class AlpacaClient:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        
        # Determine Base URL
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        }
        logger.info(f"Alpaca Client initialized in {'PAPER' if paper else 'LIVE'} mode.")

    def get_account_info(self) -> Dict:
        """Fetches account summary details including portfolio value & buying power."""
        url = f"{self.base_url}/v2/account"
        try:
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Alpaca Account Fetch failed with code {response.status_code}: {response.text}")
                return {"error": f"HTTP_{response.status_code}", "detail": response.text}
        except Exception as e:
            logger.error(f"Exception during account fetch: {str(e)}")
            return {"error": "CONNECTION_FAILURE", "detail": str(e)}

    def place_execution_order(
        self, 
        symbol: str, 
        qty: int, 
        side: str, 
        order_type: str = "market", 
        time_in_force: str = "gtc"
    ) -> Dict:
        """Dispatches buy or sell execution orders cleanly to the Alpaca order book."""
        url = f"{self.base_url}/v2/orders"
        payload = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower()
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=8)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Order rejection with status {response.status_code}: {response.text}")
                return {"error": f"REJECTED_HTTP_{response.status_code}", "detail": response.text}
        except Exception as e:
            logger.error(f"Exception during order placement: {str(e)}")
            return {"error": "EXECUTION_EXCEPTION", "detail": str(e)}

    def get_open_positions(self) -> List[Dict]:
        """Queries currently active holdings and average fill prices."""
        url = f"{self.base_url}/v2/positions"
        try:
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch active positions: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception during positions fetch: {str(e)}")
            return []
