"""
RISK MANAGEMENT ENGINE — v2
---------------------------
Upgrades:
  - Dynamic, quality-tiered per-trade risk (0.5% / 1.0% / 1.5%)
  - Portfolio-level checks (delegated to PortfolioRisk)
  - Trailing stop activation after price moves N×ATR in our favor
  - Weekly loss circuit breaker
  - All trades flow through approve() → open_position()
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import math
import pandas as pd
from loguru import logger
from .config import RISK
from .strategy import Candidate
from .portfolio import PortfolioRisk


@dataclass
class Position:
    symbol: str
    side: str           # 'LONG' / 'SHORT'
    qty: int
    entry_price: float
    stop_price: float
    take_profit: float
    opened_at: datetime
    strategy: str
    quality_score: float
    risk_tier: str
    initial_stop: float = 0.0
    trail_active: bool = False
    atr_at_entry: float = 0.0

    def __post_init__(self):
        if self.initial_stop == 0.0:
            self.initial_stop = self.stop_price

    def unrealized_pnl(self, last_price: float) -> float:
        if self.side == "LONG":
            return (last_price - self.entry_price) * self.qty
        return (self.entry_price - last_price) * self.qty


@dataclass
class TradeResult:
    symbol: str
    side: str
    qty: int
    entry: float
    exit: float
    pnl: float
    pnl_pct: float
    opened_at: datetime
    closed_at: datetime
    strategy: str
    reason_close: str
    quality_score: float
    risk_tier: str
    regime: str = ""


@dataclass
class RiskState:
    equity: float
    starting_equity_today: float
    starting_equity_week: float
    realized_pnl_today: float = 0.0
    realized_pnl_week: float = 0.0
    consecutive_losses: int = 0
    halted: bool = False
    halt_reason: str = ""
    today: date = field(default_factory=date.today)
    week_start: date = field(default_factory=date.today)
    open_positions: Dict[str, Position] = field(default_factory=dict)


class RiskManager:
    def __init__(self, starting_equity: float):
        today = date.today()
        # Anchor week to monday
        week_start = today - timedelta(days=today.weekday())
        self.state = RiskState(
            equity=starting_equity,
            starting_equity_today=starting_equity,
            starting_equity_week=starting_equity,
            week_start=week_start,
        )
        self.portfolio = PortfolioRisk()

    # ---------------- Time rolls ---------------- #
    def roll_day(self, today: Optional[date] = None) -> None:
        today = today or date.today()
        if today != self.state.today:
            self.state.today = today
            self.state.starting_equity_today = self.state.equity
            self.state.realized_pnl_today = 0.0
            self.state.halted = False
            self.state.halt_reason = ""
        # Weekly roll
        ws = today - timedelta(days=today.weekday())
        if ws != self.state.week_start:
            self.state.week_start = ws
            self.state.starting_equity_week = self.state.equity
            self.state.realized_pnl_week = 0.0

    # ---------------- Sizing ---------------- #
    def _risk_pct_for(self, candidate: Candidate) -> float:
        tier = candidate.risk_tier()
        if tier == "HIGH":   return RISK.risk_high
        if tier == "MEDIUM": return RISK.risk_medium
        return RISK.risk_low

    def position_size(self, candidate: Candidate) -> int:
        risk_pct = self._risk_pct_for(candidate)
        risk_dollars = self.state.equity * risk_pct
        stop_dist = max(RISK.atr_stop_mult * candidate.atr, 1e-6)
        qty_by_risk = math.floor(risk_dollars / stop_dist)
        usable = self.state.equity * (1 - RISK.cash_buffer)
        qty_by_cash = math.floor(usable / candidate.price) if candidate.price > 0 else 0
        return max(0, min(qty_by_risk, qty_by_cash))

    def stop_and_target(self, candidate: Candidate) -> tuple[float, float]:
        d_stop = RISK.atr_stop_mult * candidate.atr
        d_tp = RISK.atr_tp_mult * candidate.atr
        if candidate.side == "BUY":
            return candidate.price - d_stop, candidate.price + d_tp
        return candidate.price + d_stop, candidate.price - d_tp

    # ---------------- Approval ---------------- #
    def approve(self, candidate: Candidate) -> tuple[bool, str]:
        self.roll_day()
        if not candidate.accepted:
            return False, candidate.reason
        if self.state.halted:
            return False, f"halted: {self.state.halt_reason}"
        if self.state.consecutive_losses >= RISK.max_consecutive_losses:
            self.state.halted = True
            self.state.halt_reason = f"kill-switch: {self.state.consecutive_losses} losses"
            return False, self.state.halt_reason
        # Daily loss cap
        loss_pct_d = self.state.realized_pnl_today / max(self.state.starting_equity_today, 1e-9)
        if loss_pct_d <= -RISK.max_daily_loss:
            self.state.halted = True
            self.state.halt_reason = f"daily loss cap {loss_pct_d:.2%}"
            return False, self.state.halt_reason
        # Weekly loss cap
        loss_pct_w = self.state.realized_pnl_week / max(self.state.starting_equity_week, 1e-9)
        if loss_pct_w <= -RISK.max_weekly_loss:
            self.state.halted = True
            self.state.halt_reason = f"weekly loss cap {loss_pct_w:.2%}"
            return False, self.state.halt_reason
        if len(self.state.open_positions) >= RISK.max_concurrent_positions:
            return False, "max concurrent positions"
        if candidate.symbol in self.state.open_positions:
            return False, "already in a position"

        qty = self.position_size(candidate)
        if qty <= 0:
            return False, "size rounds to 0"

        # Portfolio-level checks
        risk_dollars = self.state.equity * self._risk_pct_for(candidate)
        notional = qty * candidate.price
        pcheck = self.portfolio.evaluate(
            candidate.symbol, risk_dollars, notional, self.state.equity,
            self.state.open_positions.values(),
        )
        if not pcheck.ok:
            return False, f"portfolio: {pcheck.reason}"
        return True, "ok"

    # ---------------- Lifecycle ---------------- #
    def open_position(self, candidate: Candidate) -> Optional[Position]:
        ok, reason = self.approve(candidate)
        if not ok:
            logger.info(f"[risk] reject {candidate.symbol} {candidate.side}: {reason}")
            return None
        qty = self.position_size(candidate)
        stop, tp = self.stop_and_target(candidate)
        pos = Position(
            symbol=candidate.symbol,
            side="LONG" if candidate.side == "BUY" else "SHORT",
            qty=qty, entry_price=candidate.price,
            stop_price=stop, take_profit=tp,
            opened_at=datetime.utcnow(), strategy=candidate.strategy,
            quality_score=candidate.quality.score,
            risk_tier=candidate.risk_tier(),
            atr_at_entry=candidate.atr,
        )
        self.state.open_positions[candidate.symbol] = pos
        logger.info(
            f"[risk] OPEN {pos.side} {pos.qty} {pos.symbol} @ {pos.entry_price:.2f} "
            f"[{pos.risk_tier} q={pos.quality_score:.0f}] stop={pos.stop_price:.2f} tp={pos.take_profit:.2f}"
        )
        return pos

    def close_position(self, symbol: str, exit_price: float,
                       reason: str, regime: str = "") -> Optional[TradeResult]:
        pos = self.state.open_positions.pop(symbol, None)
        if pos is None: return None
        pnl = pos.unrealized_pnl(exit_price)
        pnl_pct = pnl / (pos.entry_price * pos.qty) if pos.qty > 0 else 0.0
        self.state.equity += pnl
        self.state.realized_pnl_today += pnl
        self.state.realized_pnl_week += pnl
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0
        return TradeResult(
            symbol=symbol, side=pos.side, qty=pos.qty,
            entry=pos.entry_price, exit=exit_price,
            pnl=pnl, pnl_pct=pnl_pct,
            opened_at=pos.opened_at, closed_at=datetime.utcnow(),
            strategy=pos.strategy, reason_close=reason,
            quality_score=pos.quality_score, risk_tier=pos.risk_tier,
            regime=regime,
        )

    def _maybe_trail(self, pos: Position, last_price: float) -> None:
        """Move stop to break-even after `trail_activation_atr` × ATR move in favor."""
        trigger = RISK.trail_activation_atr * pos.atr_at_entry
        if pos.side == "LONG":
            if not pos.trail_active and last_price - pos.entry_price >= trigger:
                pos.stop_price = max(pos.stop_price, pos.entry_price)
                pos.trail_active = True
                logger.info(f"[trail] {pos.symbol} stop -> BE {pos.stop_price:.2f}")
        else:
            if not pos.trail_active and pos.entry_price - last_price >= trigger:
                pos.stop_price = min(pos.stop_price, pos.entry_price)
                pos.trail_active = True

    def check_exits(self, last_prices: Dict[str, float]) -> List[TradeResult]:
        closed: List[TradeResult] = []
        for sym, pos in list(self.state.open_positions.items()):
            px = last_prices.get(sym)
            if px is None: continue
            self._maybe_trail(pos, px)
            hit_stop = (pos.side == "LONG" and px <= pos.stop_price) or \
                       (pos.side == "SHORT" and px >= pos.stop_price)
            hit_tp = (pos.side == "LONG" and px >= pos.take_profit) or \
                     (pos.side == "SHORT" and px <= pos.take_profit)
            if hit_stop:
                tr = self.close_position(sym, px, "stop-loss")
                if tr: closed.append(tr)
            elif hit_tp:
                tr = self.close_position(sym, px, "take-profit")
                if tr: closed.append(tr)
        return closed
