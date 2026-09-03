"""Unit tests for Risk Manager and PRD Mandatory 5-Point Evaluation Output."""
import unittest
from src.engine.risk_manager import RiskManager
from src.engine.evaluator import evaluator


class TestRiskAndEvaluator(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(max_risk_pct=2.0, min_rr=2.0, default_equity=10000000.0)

    def test_risk_manager_buy_levels(self):
        """Ensure POI, invalidation, TP1 (1:2 R:R), and TP2 (1:3 R:R) are correctly computed."""
        entry = 1000.0
        invalidation = 950.0  # Risk per unit = 50.0
        levels = self.rm.calculate_trade_levels(entry_price=entry, invalidation_price=invalidation, action="BUY")

        self.assertTrue(levels["valid"])
        self.assertEqual(levels["risk_per_unit"], 50.0)
        self.assertEqual(levels["tp1_rr2"], 1100.0)  # 1000 + (50 * 2)
        self.assertEqual(levels["tp2_rr3"], 1150.0)  # 1000 + (50 * 3)
        self.assertEqual(levels["max_risk_amount_idr"], 200000.0)  # 2% of 10M

    def test_mandatory_evaluation_format_keys(self):
        """Verify that evaluation output contains all 5 mandatory sections per PRD Section 3."""
        eval_result = evaluator.evaluate_pair("btc_idr", print_report=False)

        # 1. Pencocokan Memori: (Korelasi dengan jurnal/data historis)
        self.assertIn("memory_match", eval_result)
        self.assertTrue(len(eval_result["memory_match"]) > 0)

        # 2. Analisis Teknikal: (Struktur tren dan level kunci saat ini)
        self.assertIn("technical_analysis", eval_result)
        self.assertTrue(len(eval_result["technical_analysis"]) > 0)

        # 3. Analisis Fundamental: (Katalis berita dan dampaknya)
        self.assertIn("fundamental_analysis", eval_result)
        self.assertTrue(len(eval_result["fundamental_analysis"]) > 0)

        # 4. Skor Konfluensi: (% Probabilitas berdasarkan total pembobotan)
        self.assertIn("confluence_score", eval_result)
        self.assertGreaterEqual(eval_result["confluence_score"], 0.0)
        self.assertLessEqual(eval_result["confluence_score"], 100.0)

        # 5. POI & Invalidasi: (Level pantau (POI) dan batas toleransi kegagalan setup)
        self.assertIn("poi_invalidation", eval_result)
        self.assertTrue(len(eval_result["poi_invalidation"]) > 0)


if __name__ == "__main__":
    unittest.main()
