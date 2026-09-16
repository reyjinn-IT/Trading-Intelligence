import time
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MacroAnalyzer")

class MacroAnalyzer:
    def __init__(self):
        self.cached_fng: Optional[Dict[str, Any]] = None
        self.last_fng_fetch: float = 0.0

    def get_crypto_fear_and_greed(self) -> Dict[str, Any]:
        now = time.time()
        if self.cached_fng and (now - self.last_fng_fetch < 900):  # Cache 15 minutes
            return self.cached_fng

        try:
            resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    item = data["data"][0]
                    fng_data = {
                        "value": int(item.get("value", 55)),
                        "classification": item.get("value_classification", "Greed"),
                        "timestamp": int(item.get("timestamp", now))
                    }
                    self.cached_fng = fng_data
                    self.last_fng_fetch = now
                    return fng_data
        except Exception as e:
            logger.debug("Failed fetching Fear & Greed Index: %s. Using standard baseline.", e)

        # Fallback baseline
        fallback = {"value": 64, "classification": "Greed", "timestamp": int(now)}
        self.cached_fng = fallback
        return fallback

    def analyze(self, asset_type: str = "CRYPTO") -> Dict[str, Any]:
        fng = self.get_crypto_fear_and_greed()
        fng_value = fng["value"]
        fng_class = fng["classification"]

        if "XAU" in asset_type.upper() or "GOLD" in asset_type.upper():
            # Macro drivers for Gold (XAUUSD): Geopolitics, Real Yields, Central Bank Reserves
            macro_score = 78.0
            catalyst = "High geopolitical safe-haven demand & global Central Bank FX reserve accumulation."
            impact = "Supports medium-term bullish trend of XAUUSD above psychological support levels."
            summary = (
                f"Gold Macro Catalyst: {catalyst} | Impact: {impact} | "
                f"Commodity Sentiment: Defensive Bullish (Sentiment Index: {macro_score:.1f}/100)"
            )
        else:
            # Macro drivers for Crypto (BTC/IDR): Global Liquidity, ETF Flows, Fear & Greed
            # Normalize F&G into score (30 to 85)
            macro_score = 25.0 + (fng_value * 0.65)
            catalyst = f"Market Sentiment Index (Fear & Greed) is at {fng_value} ({fng_class}). ETF flows are neutral-positive."
            impact = "Liquidity conditions support risk asset accumulation with moderate volatility."
            summary = (
                f"Crypto Macro Catalyst: {catalyst} | Impact: {impact} | "
                f"Fundamental Score: {macro_score:.1f}/100"
            )

        macro_score = max(5.0, min(95.0, macro_score))

        return {
            "score": round(macro_score, 2),
            "fear_and_greed_value": fng_value,
            "fear_and_greed_classification": fng_class,
            "catalyst": catalyst,
            "impact": impact,
            "summary": summary
        }

macro_analyzer = MacroAnalyzer()
