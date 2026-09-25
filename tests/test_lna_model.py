import json
import unittest
from pathlib import Path

from scripts.run_gf180_lna import lna_device_lines


ROOT = Path(__file__).resolve().parents[1]


class LnaModelTest(unittest.TestCase):
    def test_device_generator_splits_wide_lna(self):
        devices = lna_device_lines(200.0).splitlines()
        self.assertGreater(len(devices), 1)
        self.assertTrue(all("nf=" in device for device in devices))

    def test_selected_lna_passes_sampled_pvt_gates(self):
        report = json.loads((ROOT / "reports" / "gf180_lna.json").read_text())
        selected = report["selected"]
        gates = report["selection_gates"]
        self.assertTrue(report["accepted_for_next_stage"])
        self.assertEqual(report["candidate_count"], 25)
        self.assertGreater(report["passing_candidate_count"], 0)
        self.assertGreaterEqual(
            selected["minimum_intrinsic_voltage_gain_db"],
            gates["minimum_intrinsic_voltage_gain_db"],
        )
        self.assertLessEqual(
            selected["maximum_noise_figure_db"],
            gates["maximum_noise_figure_db"],
        )
        self.assertGreaterEqual(
            selected["minimum_input_return_loss_db"],
            gates["minimum_input_return_loss_db"],
        )


if __name__ == "__main__":
    unittest.main()
