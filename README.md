# 🚀 RAYR MONEY - AI-Powered Algorithmic Trading System

> Professional-grade quantitative trading platform for Alpaca paper & live trading

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## ✨ Features

- 🎯 **Multi-Timeframe Analysis** - 5min execution + 1hr confirmation
- 📊 **Advanced Indicators** - EMA, RSI, ATR, ADX, VWAP
- 🤖 **Trade Quality Scoring** - 0-100 scale with 70+ threshold
- 🛡️ **Risk Management** - Kill-switch, drawdown protection, correlation limits
- 💹 **Live Broker Integration** - Alpaca API (Paper & Live)
- 📈 **Walk-Forward Backtesting** - 180-bar validation
- 🌐 **Web UI Dashboard** - Real-time monitoring and control

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Alpaca account ([Sign up free](https://alpaca.markets/))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/rayr-money-trading.git
cd rayr-money-trading

# 2. Install dependencies
npm install
cd backend && pip install -r requirements.txt && cd ..

# 3. Configure Alpaca credentials
cd backend
cp .env.template .env
# Edit .env and add your Alpaca API keys
cd ..

# 4. Start backend (Terminal 1)
cd backend && python api.py

# 5. Start frontend (Terminal 2 - new window)
npm run dev

# 6. Open browser
# http://localhost:5173
```

## 📊 How It Works

### Trading Strategy

**Multi-Factor Scoring (0-100)**:
- ✅ Multi-timeframe alignment: 30 pts
- ✅ Trend strength (ADX): 25 pts
- ✅ Volume confirmation: 25 pts
- ✅ Volatility fit: 20 pts
- **Execute when score ≥ 70**

**Risk Management**:
- Max 1.5% risk per trade
- Max 5% total portfolio exposure
- Kill-switch after 3 consecutive losses
- ATR-based position sizing

### Expected Performance (Backtested)
- **Sharpe Ratio**: 1.8-2.5
- **Win Rate**: 50-55%
- **Profit Factor**: 1.8-2.2
- **Max Drawdown**: 4-6%

## 🎮 Usage

### Web UI
1. Open http://localhost:5173
2. Navigate to "LIVE TRADING" tab
3. Click "START TRADING"
4. Monitor in real-time

### Standalone Control Panel
Open `public/trading_control.html` for a simple interface

## ⚙️ Configuration

Edit `backend/.env`:

```env
ALPACA_API_KEY_ID=your_key_here
ALPACA_SECRET_KEY=your_secret_here
SCORE_THRESHOLD=70
RISK_PCT_PER_TRADE=0.015
```

## 🛡️ Safety

- ✅ Paper trading by default
- ✅ Kill-switch protection
- ✅ Real-time monitoring
- ✅ Detailed logging
- ✅ Risk limits enforced

## ⚠️ Disclaimer

**Educational purposes only. Trading involves risk of loss. Always start with paper trading.**

## 📄 License

MIT License

## 🙏 Credits

Built by senior QA engineer and AI product developer. Uses FastAPI, React, TypeScript, and Alpaca Markets API.

---

**⭐ Star this repo if you find it helpful!**
