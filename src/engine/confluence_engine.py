import logging
from typing import Dict, Any, List, Optional
from src.core.config import settings
from src.engine.technical_analyzer import technical_analyzer
from src.engine.snd_analyzer import snd_analyzer
from src.engine.macro_analyzer import macro_analyzer

logger = logging.getLogger("ConfluenceEngine")

class ConfluenceEngine:
    def __init__(
        self,
        weight_trend: float = settings.WEIGHT_TREND,
        weight_snd: float = settings.WEIGHT_SND,
        weight_macro: float = settings.WEIGHT_MACRO
    ):
        self.w_trend = weight_trend
        self.w_snd = weight_snd
        self.w_macro = weight_macro

        # Validate weights sum to 1.0
        total_w = self.w_trend + self.w_snd + self.w_macro
        if abs(total_w - 1.0) > 0.001:
            logger.warning("Confluence weights sum to %f (expected 1.0). Normalizing weights.", total_w)
            self.w_trend /= total_w
            self.w_snd /= total_w
            self.w_macro /= total_w

    def calculate_confluence(
        self,
        candles: List[Dict[str, Any]],
        asset_type: str = "CRYPTO"
    ) -> Dict[str, Any]:
        # 1. 40% Trend & Market Structure
        tech_res = technical_analyzer.analyze(candles)
        trend_score = tech_res["score"]
        direction = tech_res["direction"]

        # 2. 30% Key Levels / Supply & Demand
        snd_res = snd_analyzer.analyze(candles, trend_direction=direction)
        snd_score = snd_res["score"]

        # 3. 30% Macroeconomic Sentiment
        macro_res = macro_analyzer.analyze(asset_type=asset_type)
        macro_score = macro_res["score"]

        # Weighted calculation
        total_score = (self.w_trend * trend_score) + (self.w_snd * snd_score) + (self.w_macro * macro_score)
        total_score = round(max(0.0, min(100.0, total_score)), 2)

        breakdown = (
            f"{int(self.w_trend * 100)}% Tren [{trend_score:.1f}] + "
            f"{int(self.w_snd * 100)}% Level Kunci [{snd_score:.1f}] + "
            f"{int(self.w_macro * 100)}% Makro [{macro_score:.1f}]"
        )

        # Decision threshold evaluation
        if total_score >= settings.MIN_CONFLUENCE_BUY_SCORE and direction == "BULLISH":
            action = "BUY"
        elif total_score >= settings.MIN_CONFLUENCE_SELL_SCORE and direction == "BEARISH":
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "confluence_score": total_score,
            "action": action,
            "breakdown": breakdown,
            "weights": {
                "trend": self.w_trend,
                "snd": self.w_snd,
                "macro": self.w_macro
            },
            "sub_scores": {
                "trend_score": trend_score,
                "snd_score": snd_score,
                "macro_score": macro_score
            },
            "technical": tech_res,
            "snd": snd_res,
            "macro": macro_res
        }

confluence_engine = ConfluenceEngine()
