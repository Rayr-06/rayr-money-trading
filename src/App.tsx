import './index.css'
import EnhancedDashboard from './EnhancedDashboard'
import './EnhancedDashboard.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 p-6">
        <h1 className="text-3xl font-bold text-cyan-400">
          ⚡ RAYR MONEY Trading System
        </h1>
        <p className="text-gray-400 mt-2">
          Live Algorithmic Trading Platform v2.0
        </p>
      </header>
      
      <main className="container mx-auto">
        <EnhancedDashboard />
      </main>
      
      <footer className="bg-gray-800 border-t border-gray-700 p-4 text-center text-gray-400 mt-8">
        © 2026 RAYR MONEY. All Rights Reserved.
      </footer>
    </div>
  )
}

export default App