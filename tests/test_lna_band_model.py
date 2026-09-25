import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LnaBandModelTest(unittest.TestCase):
    def test_selected_lna_passes_every_channel_and_corner(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_lna_band.json").read_text()
        )
        gates = report["gates"]
        self.assertTrue(report["passed"])
        self.assertEqual(report["channel_count"], 40)
        self.assertEqual(len(report["summaries"]), 3)
        self.assertTrue(all(len(item["points"]) == 40 for item in report["summaries"]))
        self.assertGreaterEqual(
            report["minimum_intrinsic_voltage_gain_db"],
            gates["minimum_intrinsic_voltage_gain_db"],
        )
        self.assertLessEqual(
            report["maximum_noise_figure_db"],
            gates["maximum_noise_figure_db"],
        )
        self.assertGreaterEqual(
            report["minimum_input_return_loss_db"],
            gates["minimum_input_return_loss_db"],
        )


if __name__ == "__main__":
    unittest.main()
