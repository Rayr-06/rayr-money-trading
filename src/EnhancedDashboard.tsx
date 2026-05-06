import { useState, useEffect } from 'react';

export default function EnhancedDashboard() {
  const [alpacaStatus, setAlpacaStatus] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [botStatus, setBotStatus] = useState({ running: false });
  const [selectedStock, setSelectedStock] = useState(null);
  const [orderQty, setOrderQty] = useState(1);
  const [orderSide, setOrderSide] = useState('buy');
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState('waking');

  const BACKEND_URL = 'https://rayr-money-trading.onrender.com';

  // Wake up backend first
  useEffect(() => {
    const wakeBackend = async () => {
      setBackendStatus('waking');
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000); // 60s timeout
        
        const res = await fetch(`${BACKEND_URL}/health`, {
          signal: controller.signal
        });
        clearTimeout(timeout);
        
        if (res.ok) {
          setBackendStatus('ready');
          setLoading(false);
        }
      } catch (err) {
        console.log('Backend waking up...', err.message);
        setBackendStatus('waking');
        // Retry after 5 seconds
        setTimeout(wakeBackend, 5000);
      }
    };
    wakeBackend();
  }, []);

  // Fetch Alpaca status
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/alpaca/status`);
        const data = await res.json();
        setAlpacaStatus(data);
      } catch (err) {
        console.error('Status fetch failed:', err);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  // Fetch positions
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchPositions = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/alpaca/positions`);
        const data = await res.json();
        setPositions(data.positions || []);
      } catch (err) {
        console.error('Positions fetch failed:', err);
      }
    };
    fetchPositions();
    const interval = setInterval(fetchPositions, 10000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  // Fetch orders
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchOrders = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/alpaca/orders`);
        const data = await res.json();
        setOrders(data.orders || []);
      } catch (err) {
        console.error('Orders fetch failed:', err);
      }
    };
    fetchOrders();
    const interval = setInterval(fetchOrders, 15000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  // Fetch stock list
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchStocks = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/stocks/list`);
        const data = await res.json();
        setStocks(data.symbols || []);
      } catch (err) {
        console.error('Stocks fetch failed:', err);
      }
    };
    fetchStocks();
  }, [backendStatus]);

  // Fetch market quotes
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchQuotes = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/market/quotes`);
        const data = await res.json();
        setQuotes(data.quotes || []);
      } catch (err) {
        console.error('Quotes fetch failed:', err);
      }
    };
    fetchQuotes();
    const interval = setInterval(fetchQuotes, 30000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  // Fetch bot status
  useEffect(() => {
    if (backendStatus !== 'ready') return;
    
    const fetchBotStatus = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/bot/status`);
        const data = await res.json();
        setBotStatus(data);
      } catch (err) {
        console.error('Bot status fetch failed:', err);
      }
    };
    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 5000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  const placeOrder = async () => {
    if (!selectedStock) {
      alert('Please select a stock first!');
      return;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/trading/order?symbol=${selectedStock}&qty=${orderQty}&side=${orderSide}`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.success) {
        alert(`✅ Order placed: ${orderSide.toUpperCase()} ${orderQty} ${selectedStock}`);
        setSelectedStock(null);
        setOrderQty(1);
      } else {
        alert(`❌ Order failed: ${data.error}`);
      }
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    }
  };

  const toggleBot = async () => {
    try {
      const endpoint = botStatus.running ? '/api/bot/stop' : '/api/bot/start';
      const res = await fetch(`${BACKEND_URL}${endpoint}`, { method: 'POST' });
      const data = await res.json();
      alert(data.message);
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    }
  };

  const getQuoteForSymbol = (symbol) => {
    return quotes.find(q => q.symbol === symbol);
  };

  if (loading && backendStatus === 'waking') {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <h2>🚀 Starting Trading System...</h2>
        <p>Waking up backend server (this takes 30-60 seconds on first load)</p>
        <p className="loading-tip">Render free tier spins down after 15min of inactivity</p>
      </div>
    );
  }

  return (
    <div className="trading-dashboard">
      {/* Alpaca Status */}
      <div className="status-card">
        <h2>🔌 Alpaca Connection</h2>
        {alpacaStatus ? (
          <>
            <div className={`status-indicator ${alpacaStatus.connected ? 'connected' : 'disconnected'}`}>
              {alpacaStatus.connected ? '🟢 CONNECTED' : '🔴 DISCONNECTED'}
            </div>
            {alpacaStatus.connected && (
              <div className="account-info">
                <p><strong>Mode:</strong> {alpacaStatus.paper_trading ? '📄 PAPER TRADING' : '💰 LIVE TRADING'}</p>
                <p><strong>Portfolio Value:</strong> ${alpacaStatus.portfolio_value?.toFixed(2)}</p>
                <p><strong>Cash:</strong> ${alpacaStatus.cash?.toFixed(2)}</p>
                <p><strong>Buying Power:</strong> ${alpacaStatus.buying_power?.toFixed(2)}</p>
              </div>
            )}
          </>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* Auto-Trading Bot */}
      <div className="bot-control-card">
        <h2>🤖 Auto-Trading Bot</h2>
        <div className="bot-status">
          <div className={`bot-indicator ${botStatus.running ? 'running' : 'stopped'}`}>
            {botStatus.running ? '🟢 BOT ACTIVE' : '🔴 BOT STOPPED'}
          </div>
          <button onClick={toggleBot} className="bot-button">
            {botStatus.running ? 'STOP BOT' : 'START BOT'}
          </button>
        </div>
        <p className="bot-description">
          {botStatus.running 
            ? '🤖 Bot is actively monitoring and trading...' 
            : '💤 Bot is stopped. Click START to activate auto-trading.'}
        </p>
      </div>

      {/* Manual Trading */}
      <div className="trading-panel">
        <h2>🎯 Manual Trade</h2>
        <div className="trade-form">
          <select 
            value={selectedStock || ''} 
            onChange={(e) => setSelectedStock(e.target.value)}
            className="trade-select"
          >
            <option value="">Select Stock...</option>
            {stocks.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
          
          <input 
            type="number" 
            value={orderQty} 
            onChange={(e) => setOrderQty(parseInt(e.target.value))}
            min="1"
            className="trade-input"
          />
          
          <select 
            value={orderSide} 
            onChange={(e) => setOrderSide(e.target.value)}
            className="trade-select"
          >
            <option value="buy">BUY</option>
            <option value="sell">SELL</option>
          </select>
          
          <button onClick={placeOrder} className="trade-button">
            Place Market Order
          </button>
        </div>
      </div>

      {/* Stock Grid */}
      <div className="stocks-section">
        <h2>📊 Live Market Data ({quotes.length} stocks loaded)</h2>
        <div className="stock-grid-prices">
          {stocks.map(symbol => {
            const quote = getQuoteForSymbol(symbol);
            return (
              <div 
                key={symbol} 
                className={`stock-card ${selectedStock === symbol ? 'selected' : ''}`}
                onClick={() => setSelectedStock(symbol)}
              >
                <div className="stock-symbol">{symbol}</div>
                {quote ? (
                  <>
                    <div className="stock-price">${quote.price?.toFixed(2)}</div>
                    <div className="stock-spread">
                      Bid: ${quote.bid?.toFixed(2)} | Ask: ${quote.ask?.toFixed(2)}
                    </div>
                  </>
                ) : (
                  <div className="stock-price-loading">⏳ Loading...</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Positions */}
      <div className="positions-section">
        <h2>💼 Open Positions ({positions.length})</h2>
        {positions.length > 0 ? (
          <table className="positions-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Entry</th>
                <th>Current</th>
                <th>P&L</th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos, idx) => (
                <tr key={idx}>
                  <td><strong>{pos.symbol}</strong></td>
                  <td>{pos.qty}</td>
                  <td>${pos.avg_entry_price?.toFixed(2)}</td>
                  <td>${pos.current_price?.toFixed(2)}</td>
                  <td className={pos.unrealized_pl >= 0 ? 'profit' : 'loss'}>
                    ${pos.unrealized_pl?.toFixed(2)}
                  </td>
                  <td className={pos.unrealized_plpc >= 0 ? 'profit' : 'loss'}>
                    {pos.unrealized_plpc?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No open positions</p>
        )}
      </div>

      {/* Orders */}
      <div className="orders-section">
        <h2>📝 Recent Orders (Last 10)</h2>
        {orders.slice(0, 10).length > 0 ? (
          <table className="orders-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Status</th>
                <th>Price</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 10).map((order, idx) => (
                <tr key={idx}>
                  <td><strong>{order.symbol}</strong></td>
                  <td className={order.side === 'buy' ? 'buy' : 'sell'}>{order.side?.toUpperCase()}</td>
                  <td>{order.qty}</td>
                  <td className={`status-${order.status}`}>{order.status}</td>
                  <td>${order.filled_avg_price?.toFixed(2) || '-'}</td>
                  <td>{order.submitted_at ? new Date(order.submitted_at).toLocaleTimeString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No recent orders</p>
        )}
      </div>
    </div>
  );
}