import unittest
import time
from src.exchange.indodax_client import IndodaxClient
from src.core.deadman_switch import DeadmanSwitch

class TestExchangeAndDeadman(unittest.TestCase):
    def test_hmac_sha512_signature(self):
        client = IndodaxClient(api_key="test_key", secret_key="test_secret", live=True)
        payload = "method=getInfo&timestamp=1700000000000&recvWindow=5000"
        sig = client._generate_signature(payload)
        self.assertIsInstance(sig, str)
        self.assertEqual(len(sig), 128)  # SHA-512 hex is 128 characters

    def test_paper_trading_execution(self):
        client = IndodaxClient(live=False)
        init_idr = client.paper_balances["idr"]

        # Buy BTC with 500,000 IDR
        buy_res = client.create_order(pair="btc_idr", order_type="buy", price=1000000000.0, amount=500000.0)
        self.assertEqual(buy_res["success"], 1)
        self.assertEqual(client.paper_balances["idr"], init_idr - 500000.0)
        self.assertGreater(client.paper_balances["btc"], 0.0)

    def test_deadman_switch_timeout_and_callback(self):
        called = False

        def emergency_callback():
            nonlocal called
            called = True

        # Short timeout of 1 second for unit test
        dm = DeadmanSwitch(timeout_seconds=1)
        dm.register_cancel_callback(emergency_callback)
        dm.arm()

        time.sleep(1.2)
        # Force check
        dm._monitor_loop() if not dm.is_triggered else None

        self.assertTrue(dm.is_triggered)
        self.assertTrue(called)
        dm.disarm()

if __name__ == "__main__":
    unittest.main()
