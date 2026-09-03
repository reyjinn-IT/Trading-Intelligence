"""Supply & Demand (SND) and Key Level Analyzer for 30% Confluence Scoring."""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


class SNDAnalyzer:
    def __init__(self):
        pass

    def identify_key_levels(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify Support & Resistance levels, Order Blocks, and Supply/Demand zones.
        """
        if not candles or len(candles) < 10:
            return {"support": 0.0, "resistance": 0.0, "zones": []}

        df = pd.DataFrame(candles)
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        current_price = closes[-1]

        # Rolling pivot highs & lows
        swing_highs = []
        swing_lows = []
        window = 3
        for i in range(window, len(df) - window):
            if highs[i] == np.max(highs[i - window : i + window + 1]):
                swing_highs.append(highs[i])
            if lows[i] == np.min(lows[i - window : i + window + 1]):
                swing_lows.append(lows[i])

        nearest_support = max([l for l in swing_lows if l < current_price], default=min(lows))
        nearest_resistance = min([h for h in swing_highs if h > current_price], default=max(highs))

        # Identify Demand Zone (DBR) below current price
        demand_high = nearest_support
        demand_low = demand_high * 0.992

        # Identify Supply Zone (RBD) above current price
        supply_low = nearest_resistance
        supply_high = supply_low * 1.008

        return {
            "current_price": current_price,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "demand_zone": {"low": round(demand_low, 2), "high": round(demand_high, 2)},
            "supply_zone": {"low": round(supply_low, 2), "high": round(supply_high, 2)}
        }

    def analyze(self, candles: List[Dict[str, Any]], trend_direction: str = "BULLISH") -> Dict[str, Any]:
        """
        Analyze Key Levels / SND (30% of total confluence).
        Determines POI (Point of Interest), Invalidation Level, and SND score (0 - 100).
        """
        if not candles or len(candles) < 10:
            return {
                "score": 50.0,
                "poi": 0.0,
                "invalidation": 0.0,
                "zone_desc": "Zona SND netral / data terbatas.",
                "summary": "Level Kunci: Netral (data terbatas)."
            }

        levels = self.identify_key_levels(candles)
        cur_px = levels["current_price"]
        sup = levels["nearest_support"]
        res = levels["nearest_resistance"]
        demand = levels["demand_zone"]
        supply = levels["supply_zone"]

        score = 50.0
        zone_desc = "Harga berada di area Mid-Range antar level kunci."
        
        # Calculate distance to demand and supply
        dist_to_demand_pct = abs(cur_px - demand["high"]) / cur_px * 100.0
        dist_to_supply_pct = abs(supply["low"] - cur_px) / cur_px * 100.0

        if trend_direction == "BULLISH":
            # Best entry is near or at Demand Zone / Support
            if dist_to_demand_pct < 1.0:
                score = 88.0
                poi = demand["high"]
                invalidation = demand["low"] * 0.996  # Just below demand
                zone_desc = f"Harga sedang merefleksi area Demand Zone / Order Block ({demand['low']:,.2f} - {demand['high']:,.2f})."
            elif dist_to_supply_pct < 1.0:
                score = 40.0
                poi = cur_px
                invalidation = sup * 0.99
                zone_desc = f"Harga mendekati Supply Zone kuat ({supply['low']:,.2f}); resiko rejection tinggi untuk buy."
            else:
                score = 65.0
                poi = demand["high"]
                invalidation = sup * 0.992
                zone_desc = f"Harga berada di atas Support {sup:,.2f}; menunggu retracement ke Demand {demand['high']:,.2f}."

        elif trend_direction == "BEARISH":
            # Best entry is near or at Supply Zone / Resistance
            if dist_to_supply_pct < 1.0:
                score = 85.0
                poi = supply["low"]
                invalidation = supply["high"] * 1.004
                zone_desc = f"Harga menguji Supply Zone ({supply['low']:,.2f} - {supply['high']:,.2f}); potensi sell rejection tinggi."
            elif dist_to_demand_pct < 1.0:
                score = 35.0
                poi = cur_px
                invalidation = res * 1.01
                zone_desc = f"Harga mendekati area Demand {demand['high']:,.2f}; resiko bounce tinggi."
            else:
                score = 55.0
                poi = supply["low"]
                invalidation = res * 1.008
                zone_desc = f"Harga di bawah Resistance {res:,.2f}; menunggu pullback ke Supply {supply['low']:,.2f}."
        else:
            # Sideways
            score = 50.0
            poi = (sup + res) / 2.0
            invalidation = sup * 0.99
            zone_desc = f"Pasar sideway dalam rentang Support {sup:,.2f} dan Resistance {res:,.2f}."

        score = max(5.0, min(95.0, score))
        summary = (
            f"Level Kunci & SND: {zone_desc} | "
            f"Support: {sup:,.2f}, Resistance: {res:,.2f}, "
            f"POI Teridentifikasi: {poi:,.2f}"
        )

        return {
            "score": round(score, 2),
            "poi": round(poi, 2),
            "invalidation": round(invalidation, 2),
            "nearest_support": round(sup, 2),
            "nearest_resistance": round(res, 2),
            "demand_zone": demand,
            "supply_zone": supply,
            "zone_desc": zone_desc,
            "summary": summary
        }


snd_analyzer = SNDAnalyzer()
