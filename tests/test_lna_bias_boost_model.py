import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LnaBiasBoostModelTest(unittest.TestCase):
    def test_lowest_power_passing_bias_state_is_selected(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_lna_bias_boost.json").read_text()
        )
        selected = report["selected"]
        gates = report["gates"]
        self.assertTrue(report["accepted_for_next_stage"])
        self.assertEqual(report["candidate_count"], 8)
        self.assertAlmostEqual(selected["bias_current_a"], 6e-3)
        self.assertTrue(selected["passed"])
        self.assertLessEqual(
            selected["maximum_gain_compression_db"],
            gates["maximum_gain_compression_db"],
        )
        self.assertGreaterEqual(
            selected["minimum_strong_input_gain_db"],
            gates["minimum_strong_input_gain_db"],
        )
        self.assertLessEqual(
            selected["maximum_noise_figure_db"],
            gates["maximum_noise_figure_db"],
        )
        self.assertGreaterEqual(
            selected["minimum_input_return_loss_db"],
            gates["minimum_input_return_loss_db"],
        )
        lower_biases = [
            candidate
            for candidate in report["candidates"]
            if candidate["bias_current_a"] < selected["bias_current_a"]
        ]
        self.assertTrue(all(not candidate["passed"] for candidate in lower_biases))


if __name__ == "__main__":
    unittest.main()
