"""Master Evaluator implementing the Mandatory Evaluation Output required by PRD Section 3."""
import logging
from typing import Dict, Any, Optional
from src.core.config import settings
from src.core.logger import format_mandatory_evaluation_report, print_rich_evaluation_report, logger
from src.core.deadman_switch import deadman_switch
from src.exchange.indodax_client import indodax_client
from src.exchange.xauusd_client import xauusd_client
from src.memory.in_context_memory import in_context_memory
from src.engine.confluence_engine import confluence_engine
from src.engine.risk_manager import risk_manager


class TradingEvaluator:
    def __init__(self):
        # Register deadman switch cancel order callback
        deadman_switch.register_cancel_callback(indodax_client.cancel_all_open_orders)

    def evaluate_pair(
        self,
        pair: str = "btc_idr",
        timeframe: str = "1h",
        print_report: bool = True
    ) -> Dict[str, Any]:
        """
        Execute full market analysis pipeline and generate the PRD Mandatory 5-Point Evaluation Output.
        """
        pair_lower = pair.lower()
        is_gold = "xau" in pair_lower or "gold" in pair_lower

        # 1. Ingest candles and ticker
        if is_gold:
            candles = xauusd_client.get_klines(timeframe=timeframe, limit=80)
            ticker = xauusd_client.get_ticker()
            asset_type = "GOLD"
        else:
            candles = indodax_client.get_klines(pair=pair_lower, timeframe=timeframe, limit=80)
            ticker = indodax_client.get_ticker(pair=pair_lower)
            asset_type = "CRYPTO"

        current_price = ticker.get("last", 0.0)

        # 2. Confluence Engine (40% Trend, 30% SND, 30% Macro)
        conf_result = confluence_engine.calculate_confluence(candles, asset_type=asset_type)
        confluence_score = conf_result["confluence_score"]
        action = conf_result["action"]
        breakdown = conf_result["breakdown"]

        tech_data = conf_result["technical"]
        snd_data = conf_result["snd"]
        macro_data = conf_result["macro"]

        # 3. In-Context Learning Memory Matching & Technical Pattern Learning
        memory_result = in_context_memory.match_memory(
            pair=pair,
            current_trend=tech_data["direction"],
            macro_sentiment_score=macro_data["score"] - 50.0,
            candles=candles,
            current_rsi=tech_data.get("rsi", 50.0),
            current_price=current_price
        )

        # 4. Risk Management (POI & Invalidation Calculation)
        poi_price = snd_data.get("poi", current_price)
        invalidation_price = snd_data.get("invalidation", current_price * 0.98)

        risk_levels = risk_manager.calculate_trade_levels(
            entry_price=poi_price if poi_price > 0 else current_price,
            invalidation_price=invalidation_price,
            action="BUY" if action == "BUY" else ("SELL" if action == "SELL" else "BUY")
        )

        # Build evaluation output
        mandatory_evaluation = {
            "pair": pair.upper(),
            "action": action,
            "current_price": current_price,
            "memory_match": memory_result.get("summary"),
            "technical_analysis": f"{tech_data.get('summary')} | {snd_data.get('zone_desc')}",
            "fundamental_analysis": macro_data.get("summary"),
            "confluence_score": confluence_score,
            "confluence_breakdown": breakdown,
            "poi_invalidation": risk_levels.get("summary"),
            "sub_scores": conf_result["sub_scores"],
            "risk_details": risk_levels,
            "timestamp": ticker.get("server_time")
        }

        # Log and display
        if print_report:
            print_rich_evaluation_report(mandatory_evaluation)

        return mandatory_evaluation

    def execute_evaluated_trade(self, eval_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute trade based on evaluation if conditions pass safety thresholds and Deadman switch is armed.
        """
        pair = eval_data.get("pair", "BTC_IDR").lower()
        action = eval_data.get("action", "HOLD")
        score = eval_data.get("confluence_score", 0.0)

        # Check safety switch
        deadman_status = deadman_switch.get_status()
        if deadman_switch.is_armed and not deadman_status["is_safe"]:
            logger.error("Trade rejected: Deadman Switch is triggered or unsafe.")
            return {"status": "REJECTED", "reason": "Deadman Switch safety lock active."}

        if action not in ["BUY", "SELL"]:
            return {"status": "SKIPPED", "reason": f"Decision is {action}. Confluence threshold not satisfied."}

        min_score = settings.MIN_CONFLUENCE_BUY_SCORE if action == "BUY" else settings.MIN_CONFLUENCE_SELL_SCORE
        if score < min_score:
            return {"status": "SKIPPED", "reason": f"Score {score}% below required {min_score}%."}

        # Send heartbeat to deadman switch
        deadman_switch.heartbeat()

        # Calculate sizing
        risk_details = eval_data.get("risk_details", {})
        allocation = risk_details.get("suggested_allocation_idr", 500000.0)
        entry_price = eval_data.get("current_price", 1000000000.0)

        # Only execute on Indodax supported crypto pairs
        if "XAU" in pair:
            return {
                "status": "SIGNAL_GENERATED",
                "message": f"XAUUSD {action} Signal confirmed ({score}% Confluence). Semi-automated manual execution required for gold.",
                "details": eval_data
            }

        # Crypto execution via Indodax Client (Paper or Live)
        order_res = indodax_client.create_order(
            pair=pair,
            order_type=action.lower(),
            price=entry_price,
            amount=allocation
        )

        return {
            "status": "EXECUTED",
            "mode": "LIVE" if settings.LIVE_TRADING else "PAPER_TRADING",
            "order_result": order_res,
            "evaluation": eval_data
        }


evaluator = TradingEvaluator()
