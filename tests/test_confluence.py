"""Unit tests for Confluence Scoring Engine (40% - 30% - 30%)."""
import unittest
from src.engine.confluence_engine import ConfluenceEngine
from src.engine.technical_analyzer import TechnicalAnalyzer
from src.engine.snd_analyzer import SNDAnalyzer
from src.engine.macro_analyzer import MacroAnalyzer


class TestConfluenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConfluenceEngine(weight_trend=0.40, weight_snd=0.30, weight_macro=0.30)

    def test_weights_sum_to_one(self):
        """Ensure confluence weights accurately sum to 1.0 (100%)."""
        total = self.engine.w_trend + self.engine.w_snd + self.engine.w_macro
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_confluence_calculation_formula(self):
        """Ensure mathematical calculation matches 0.40*T + 0.30*S + 0.30*M."""
        # Simulated dummy candle series
        candles = []
        base_px = 1000000000.0
        for i in range(30):
            candles.append({
                "timestamp": 1700000000 + (i * 3600),
                "open": base_px + (i * 1000000),
                "high": base_px + (i * 1000000) + 500000,
                "low": base_px + (i * 1000000) - 200000,
                "close": base_px + (i * 1000000) + 400000,
                "volume": 10.0
            })

        result = self.engine.calculate_confluence(candles, asset_type="CRYPTO")
        score = result["confluence_score"]
        sub = result["sub_scores"]

        expected = (0.40 * sub["trend_score"]) + (0.30 * sub["snd_score"]) + (0.30 * sub["macro_score"])
        self.assertAlmostEqual(score, round(expected, 2), places=1)
        self.assertIn("breakdown", result)
        self.assertIn("action", result)
        self.assertIn(result["action"], ["BUY", "SELL", "HOLD"])


if __name__ == "__main__":
    unittest.main()
