import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LnaMirrorBiasModelTest(unittest.TestCase):
    def test_low_headroom_mirror_is_rejected(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_lna_mirror_bias.json").read_text()
        )
        self.assertFalse(report["accepted_for_next_stage"])
        self.assertIsNone(report["selected"])
        self.assertEqual(report["candidate_count"], 6)
        self.assertEqual(report["passing_candidate_count"], 0)
        self.assertTrue(all(not item["passed"] for item in report["candidates"]))

        least_loaded = report["candidates"][0]
        gates = report["gates"]
        self.assertLess(
            least_loaded["minimum_lna_current_a"],
            gates["minimum_lna_current_a"],
        )
        self.assertLess(
            least_loaded["minimum_intrinsic_voltage_gain_db"],
            gates["minimum_intrinsic_voltage_gain_db"],
        )
        self.assertGreater(
            least_loaded["maximum_noise_figure_db"],
            gates["maximum_noise_figure_db"],
        )


if __name__ == "__main__":
    unittest.main()
