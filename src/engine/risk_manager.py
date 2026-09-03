import logging
from typing import Dict, Any
from src.core.config import settings

logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(
        self,
        max_risk_pct: float = settings.MAX_RISK_PER_TRADE_PERCENT,
        min_rr: float = settings.MIN_RISK_REWARD_RATIO,
        default_equity: float = 10000000.0
    ):
        self.max_risk_pct = max_risk_pct
        self.min_rr = min_rr
        self.default_equity = default_equity

    def calculate_trade_levels(
        self,
        entry_price: float,
        invalidation_price: float,
        action: str = "BUY",
        equity: float = 10000000.0
    ) -> Dict[str, Any]:
        if entry_price <= 0:
            return {"valid": False, "error": "Invalid entry price."}

        action = action.upper()
        if action == "BUY":
            # For BUY: invalidation must be below entry
            risk_per_unit = max(1.0, entry_price - invalidation_price)
            tp1 = entry_price + (risk_per_unit * 2.0)  # R:R 1:2
            tp2 = entry_price + (risk_per_unit * 3.0)  # R:R 1:3
            risk_pct = (risk_per_unit / entry_price) * 100.0
        elif action == "SELL":
            # For SELL: invalidation must be above entry
            risk_per_unit = max(1.0, invalidation_price - entry_price)
            tp1 = entry_price - (risk_per_unit * 2.0)
            tp2 = entry_price - (risk_per_unit * 3.0)
            risk_pct = (risk_per_unit / entry_price) * 100.0
        else:
            risk_per_unit = entry_price * 0.015
            tp1 = entry_price * 1.03
            tp2 = entry_price * 1.045
            risk_pct = 1.5

        # Position Sizing (Fixed Fractional Risk)
        # Total IDR money risked = equity * max_risk_pct
        max_risk_amount = (equity * (self.max_risk_pct / 100.0))
        if risk_per_unit > 0:
            units = max_risk_amount / risk_per_unit
            suggested_allocation = units * entry_price
        else:
            units = 0.0
            suggested_allocation = 0.0

        # Cap allocation at 50% of equity for conservative liquidity
        suggested_allocation = min(suggested_allocation, equity * 0.5)

        summary_text = (
            f"POI: {entry_price:,.2f} | "
            f"Invalidasi (Cut Loss): {invalidation_price:,.2f} (-{risk_pct:.2f}%) | "
            f"TP1 (1:2 R:R): {tp1:,.2f} | TP2 (1:3 R:R): {tp2:,.2f} | "
            f"Maksimal Risiko: {self.max_risk_pct}% (Rp {max_risk_amount:,.0f})"
        )

        return {
            "valid": True,
            "action": action,
            "poi": round(entry_price, 2),
            "invalidation": round(invalidation_price, 2),
            "risk_per_unit": round(risk_per_unit, 2),
            "risk_pct": round(risk_pct, 2),
            "tp1_rr2": round(tp1, 2),
            "tp2_rr3": round(tp2, 2),
            "suggested_allocation_idr": round(suggested_allocation, 2),
            "max_risk_amount_idr": round(max_risk_amount, 2),
            "summary": summary_text
        }

risk_manager = RiskManager()
