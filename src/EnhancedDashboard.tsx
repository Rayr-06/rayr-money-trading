import { useState, useEffect } from 'react';

export default function TradingDashboard() {
  const [alpacaStatus, setAlpacaStatus] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Fetch Alpaca status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/alpaca/status');
        const data = await res.json();
        setAlpacaStatus(data);
      } catch (err) {
        console.error('Status fetch failed:', err);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  // Fetch positions
  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const res = await fetch('/api/alpaca/positions');
        const data = await res.json();
        setPositions(data.positions || []);
      } catch (err) {
        console.error('Positions fetch failed:', err);
      }
    };
    fetchPositions();
    const interval = setInterval(fetchPositions, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, []);

  // Fetch orders
  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const res = await fetch('/api/alpaca/orders');
        const data = await res.json();
        setOrders(data.orders || []);
      } catch (err) {
        console.error('Orders fetch failed:', err);
      }
    };
    fetchOrders();
    const interval = setInterval(fetchOrders, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch stock list
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await fetch('/api/stocks/list');
        const data = await res.json();
        setStocks(data.symbols || []);
      } catch (err) {
        console.error('Stocks fetch failed:', err);
      }
    };
    fetchStocks();
  }, []);

  return (
    <div className="trading-dashboard">
      {/* Alpaca Status Card */}
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
                <p><strong>Equity:</strong> ${alpacaStatus.equity?.toFixed(2)}</p>
              </div>
            )}
          </>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* Stock Selector */}
      <div className="stocks-section">
        <h2>📊 Monitored Stocks ({stocks.length})</h2>
        <div className="stock-categories">
          <button onClick={() => setSelectedCategory('all')}>All</button>
          <button onClick={() => setSelectedCategory('tech')}>Tech</button>
          <button onClick={() => setSelectedCategory('etfs')}>ETFs</button>
          <button onClick={() => setSelectedCategory('finance')}>Finance</button>
        </div>
        <div className="stock-grid">
          {stocks.map(symbol => (
            <div key={symbol} className="stock-chip">{symbol}</div>
          ))}
        </div>
      </div>

      {/* Current Positions */}
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

      {/* Recent Orders */}
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
                <th>Filled Price</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 10).map((order, idx) => (
                <tr key={idx}>
                  <td><strong>{order.symbol}</strong></td>
                  <td className={order.side === 'buy' ? 'buy' : 'sell'}>{order.side.toUpperCase()}</td>
                  <td>{order.qty}</td>
                  <td className={`status-${order.status}`}>{order.status}</td>
                  <td>${order.filled_avg_price?.toFixed(2) || '-'}</td>
                  <td>{new Date(order.submitted_at).toLocaleTimeString()}</td>
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
