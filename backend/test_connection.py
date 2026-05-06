#!/usr/bin/env python3
"""Quick test to verify Alpaca connection"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🔍 ALPACA CONNECTION TEST")
print("=" * 60)

api_key = os.getenv("ALPACA_API_KEY_ID")
secret_key = os.getenv("ALPACA_SECRET_KEY")

print(f"API Key present: {bool(api_key)}")
print(f"Secret Key present: {bool(secret_key)}")

if api_key and secret_key:
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(
            api_key,
            secret_key,
            "https://paper-api.alpaca.markets",
            api_version='v2'
        )
        account = api.get_account()
        print(f"✅ CONNECTED!")
        print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"Cash: ${float(account.cash):,.2f}")
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
else:
    print("❌ API keys not found in environment!")
    
print("=" * 60)
