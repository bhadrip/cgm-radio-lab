import json
import unittest
from pathlib import Path

from scripts.size_pa_match import FREQUENCY_HZ, component_values, network_point


ROOT = Path(__file__).resolve().parents[1]


class PaMatchModelTest(unittest.TestCase):
    def test_ideal_network_transforms_fifty_to_one_hundred_fifty_ohms(self):
        inductance_h, capacitance_f = component_values()
        self.assertAlmostEqual(inductance_h, 4.61227620982124e-9, places=15)
        self.assertAlmostEqual(capacitance_f, 6.149701613094987e-13, places=18)
        point = network_point(FREQUENCY_HZ, None)
        self.assertAlmostEqual(point["input_resistance_ohm"], 150.0, places=9)
        self.assertAlmostEqual(point["input_reactance_ohm"], 0.0, places=9)
        self.assertAlmostEqual(point["transducer_gain_db"], 0.0, places=9)

    def test_q_ten_candidate_records_loss_and_harmonic_rejection(self):
        report = json.loads((ROOT / "reports" / "pa_match_screen.json").read_text())
        selected = report["screening_result"]
        self.assertEqual(report["status"], "candidate_only")
        self.assertAlmostEqual(selected["inductor_q"], 10.0)
        self.assertLess(selected["fundamental_insertion_loss_db"], 1.0)
        self.assertGreater(
            selected["third_harmonic_rejection_relative_to_fundamental_db"],
            13.0,
        )


if __name__ == "__main__":
    unittest.main()
