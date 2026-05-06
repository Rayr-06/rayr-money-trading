"""
RAYR MONEY - COMPREHENSIVE PORTFOLIO RISK CONTROLLER
Author: Senior Quantitative Architect
Description: Advanced risk management. Enforces maximum total open exposure (5%),
             correlation barriers, and adaptive volatility-adjusted position sizing.
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger("RayrMoneyLogger")

class EliteRiskEngine:
    def __init__(
        self,
        max_total_risk_pct: float = 0.05, # Max 5% of portfolio total risk
        atr_multiplier: float = 2.0,
        kill_consecutive_losses: int = 3
    ):
        self.max_total_risk_pct = max_total_risk_pct
        self.atr_multiplier = atr_multiplier
        self.kill_consecutive_losses = kill_consecutive_losses
        
        # State Tracking
        self.consecutive_losses = 0
        self.kill_switch_active = False

    def validate_new_execution(
        self,
        portfolio_equity: float,
        active_positions: Dict,
        target_ticker: str,
        sector_correlations: Dict[str, list]
    ) -> Tuple[bool, str]:
        """
        Ensures portfolio limits are strictly respected.
        """
        if self.kill_switch_active:
            return False, "PORTFOLIO_LOCK: Kill Switch engaged due to consecutive losses."

        if self.consecutive_losses >= self.kill_consecutive_losses:
            self.kill_switch_active = True
            return False, "KILL_SWITCH_ENGAGED: Structural loss limit breached. Halting."

        # 1. Total Open Exposure Cap (Max 5% total open risk)
        current_risk_committed = sum(pos.get("risk_amount", 0) for pos in active_positions.values())
        if current_risk_committed >= portfolio_equity * self.max_total_risk_pct:
            return False, f"RISK_LIMIT_EXCEEDED: Total open risk ({current_risk_committed}) exceeds 5% cap."

        # 2. Sector / Correlation Concentration Filter
        # Reject trades if we already hold highly correlated assets in the same segment
        target_sector = None
        for sector, tickers in sector_correlations.items():
            if target_ticker in tickers:
                target_sector = sector
                break
                
        if target_sector:
            sector_positions = sum(1 for pos in active_positions.keys() if pos in sector_correlations.get(target_sector, []))
            if sector_positions >= 2:
                return False, f"CONCENTRATION_LIMIT: Already holding {sector_positions} assets inside {target_sector} sector."

        return True, "VALIDATED: All structural risk barriers healthy."

    def calculate_adaptive_size(
        self,
        capital: float,
        price: float,
        atr: float,
        confidence: str
    ) -> Tuple[int, float, float, float]:
        """
        Calculates dynamic size and stop/take-profit targets.
        Sizing adjusts based on trade quality confidence:
        - HIGH Confidence: 1.5% Risk of capital
        - MEDIUM Confidence: 1.0% Risk of capital
        - LOW Confidence: 0.5% Risk of capital
        """
        risk_map = {"HIGH": 0.015, "MEDIUM": 0.010, "LOW": 0.005}
        risk_pct = risk_map.get(confidence, 0.005)
        
        risk_cash = capital * risk_pct
        stop_distance = max(atr * self.atr_multiplier, price * 0.01) # Minimum 1% hard barrier
        
        # ATR-based Stop-Loss & Take Profit targets (1:2 Risk/Reward)
        qty = int(risk_cash / stop_distance)
        if qty <= 0:
            qty = 1
            
        # Prevent allocation larger than 100% of capital
        if qty * price > capital:
            qty = int(capital / price)
            
        stop_loss = price - stop_distance
        take_profit = price + (stop_distance * 2.0)
        
        return qty, round(stop_loss, 2), round(take_profit, 2), round(risk_cash, 2)

    def register_outcome(self, is_win: bool):
        if is_win:
            self.consecutive_losses = 0
            logger.info("Trade closed as profitable. Resetting loss counters.")
        else:
            self.consecutive_losses += 1
            logger.warning(f"Loss logged. Consecutive: {self.consecutive_losses}/{self.kill_consecutive_losses}")
            if self.consecutive_losses >= self.kill_consecutive_losses:
                self.kill_switch_active = True
                logger.critical("SYSTEM CRITICAL SHUTDOWN: Consecutively failed trades. Manual restart required.")
