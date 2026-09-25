"""Neuro motif tests: LIF dynamics, WTA selection, salience map."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
from neuro.motif import DriveNetwork, LIFNeuron, salience_for


class LIFTests(unittest.TestCase):
    def test_integrates_and_fires(self):
        n = LIFNeuron(threshold=1.0, decay=0.9)
        self.assertFalse(n.step(0.4))
        self.assertFalse(n.step(0.4))
        self.assertTrue(n.step(0.4))
        self.assertEqual(n.voltage, 0.0)

    def test_leak_decays(self):
        n = LIFNeuron(threshold=10.0, decay=0.5)
        n.step(4.0)
        n.step(0.0)
        self.assertAlmostEqual(n.voltage, 2.0)

    def test_bad_params_rejected(self):
        with self.assertRaises(ValueError):
            LIFNeuron(decay=1.5)
        with self.assertRaises(ValueError):
            DriveNetwork(("only",))


class WTATests(unittest.TestCase):
    def test_strong_input_wins(self):
        net = DriveNetwork()
        winner = None
        for _ in range(10):
            winner = net.step({"calm": 0.1, "alert": 0.1, "social": 0.9}) or winner
        self.assertEqual(winner, "social")

    def test_silence_no_winner(self):
        net = DriveNetwork()
        self.assertIsNone(net.step({"calm": 0.0, "alert": 0.0, "social": 0.0}))

    def test_error_alert_wins(self):
        net = DriveNetwork()
        winner = None
        for _ in range(10):
            winner = net.step(salience_for("system_error")) or winner
        self.assertEqual(winner, "alert")


if __name__ == "__main__":
    unittest.main()
