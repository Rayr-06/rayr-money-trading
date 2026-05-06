"""
RAYR MONEY - SELF-IMPROVEMENT ANALYTICAL PIPELINE
Author: Senior Quantitative Architect
Description: Quantifies strategy performance. Incorporates a machine-learning ranker
             (RandomForestClassifier) to find ideal entry conditions.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from typing import List, Dict

class StrategyOptimizer:
    def __init__(self):
        self.clf = RandomForestClassifier(n_estimators=50, max_depth=3)
        self.is_trained = False
        self.collected_features = []
        self.outcomes = []

    def record_trade_features(self, features: Dict, is_win: bool):
        """Stores historical indicators and execution success rates."""
        self.collected_features.append(features)
        self.outcomes.append(1 if is_win else 0)
        
        # Incrementally update optimization model every 10 trades
        if len(self.collected_features) >= 10:
            df_feat = pd.DataFrame(self.collected_features)
            # Impute NaN variables
            df_feat.fillna(0, inplace=True)
            self.clf.fit(df_feat, self.outcomes)
            self.is_trained = True

    def recommend_filtering(self, current_features: Dict) -> bool:
        """
        Uses historical trade results to score upcoming trade entries.
        Rejects entry if probability of success is below 45%.
        """
        if not self.is_trained:
            return True # Allow execution if training data is insufficient
            
        df_curr = pd.DataFrame([current_features])
        prob = self.clf.predict_proba(df_curr)[0][1]
        return prob >= 0.45

class AnalyticalEngine:
    @staticmethod
    def compute_advanced_metrics(trades: List[Dict], initial_capital: float = 1000.0) -> Dict:
        """
        Calculates Sharpe, Sortino, Profit Factors, and Drawdowns.
        """
        if not trades:
            return {"sharpe": 0.0, "sortino": 0.0, "profit_factor": 1.0, "max_drawdown": 0.0}
            
        pnls = [t["pnl"] for t in trades]
        profits = sum(p for p in pnls if p > 0)
        losses = abs(sum(p for p in pnls if p < 0))
        
        profit_factor = profits / losses if losses > 0 else profits if profits > 0 else 1.0
        win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
        
        # Annualized metrics estimation
        returns = np.array(pnls) / initial_capital
        mean_ret = np.mean(returns) if len(returns) > 0 else 0
        std_ret = np.std(returns) if len(returns) > 0 else 0.00001
        
        sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0.0
        
        downside = returns[returns < 0]
        std_down = np.std(downside) if len(downside) > 0 else 0.00001
        sortino = (mean_ret / std_down) * np.sqrt(252) if std_down > 0 else 0.0
        
        return {
            "profit_factor": round(profit_factor, 2),
            "win_rate_pct": round(win_rate, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "total_trades": len(trades)
        }
