import { useState, useEffect } from 'react';

export default function DiagnosticDashboard() {
  const [diagnostics, setDiagnostics] = useState({
    backendReachable: null,
    quotesWorking: null,
    alpacaWorking: null,
    errors: []
  });

  useEffect(() => {
    const runDiagnostics = async () => {
      const BACKEND = 'https://rayr-money-trading.onrender.com';
      const results = { errors: [] };

      // Test 1: Can we reach backend at all?
      try {
        const healthResponse = await fetch(`${BACKEND}/health`);
        const healthData = await healthResponse.json();
        results.backendReachable = true;
        console.log('✅ Backend reachable:', healthData);
      } catch (error) {
        results.backendReachable = false;
        results.errors.push(`Backend unreachable: ${error.message}`);
        console.error('❌ Backend error:', error);
      }

      // Test 2: Market quotes
      try {
        const quotesResponse = await fetch(`${BACKEND}/api/market/quotes`);
        const quotesData = await quotesResponse.json();
        results.quotesWorking = quotesData.total > 0;
        console.log('✅ Quotes response:', quotesData);
      } catch (error) {
        results.quotesWorking = false;
        results.errors.push(`Quotes failed: ${error.message}`);
        console.error('❌ Quotes error:', error);
      }

      // Test 3: Alpaca
      try {
        const alpacaResponse = await fetch(`${BACKEND}/api/alpaca/status`);
        const alpacaData = await alpacaResponse.json();
        results.alpacaWorking = alpacaData.connected;
        console.log('✅ Alpaca response:', alpacaData);
      } catch (error) {
        results.alpacaWorking = false;
        results.errors.push(`Alpaca failed: ${error.message}`);
        console.error('❌ Alpaca error:', error);
      }

      setDiagnostics(results);
    };

    runDiagnostics();
  }, []);

  return (
    <div style={{padding: '20px', fontFamily: 'monospace'}}>
      <h1>🔬 System Diagnostics</h1>
      
      <div style={{background: '#1a1a1a', padding: '20px', borderRadius: '8px', marginTop: '20px'}}>
        <h2>Connection Tests:</h2>
        
        <div style={{marginTop: '10px'}}>
          <span style={{color: diagnostics.backendReachable ? '#0f0' : '#f00', fontSize: '24px'}}>
            {diagnostics.backendReachable === null ? '⏳' : diagnostics.backendReachable ? '✅' : '❌'}
          </span>
          {' Backend Reachable'}
        </div>

        <div style={{marginTop: '10px'}}>
          <span style={{color: diagnostics.quotesWorking ? '#0f0' : '#f00', fontSize: '24px'}}>
            {diagnostics.quotesWorking === null ? '⏳' : diagnostics.quotesWorking ? '✅' : '❌'}
          </span>
          {' Market Quotes Working'}
        </div>

        <div style={{marginTop: '10px'}}>
          <span style={{color: diagnostics.alpacaWorking ? '#0f0' : '#f00', fontSize: '24px'}}>
            {diagnostics.alpacaWorking === null ? '⏳' : diagnostics.alpacaWorking ? '✅' : '❌'}
          </span>
          {' Alpaca Connected'}
        </div>

        {diagnostics.errors.length > 0 && (
          <div style={{marginTop: '20px', color: '#f00'}}>
            <h3>Errors:</h3>
            {diagnostics.errors.map((err, i) => (
              <div key={i}>• {err}</div>
            ))}
          </div>
        )}

        <div style={{marginTop: '20px', color: '#888'}}>
          <p>Open Browser Console (F12) to see detailed logs</p>
          <p>Backend: https://rayr-money-trading.onrender.com</p>
        </div>
      </div>
    </div>
  );
}