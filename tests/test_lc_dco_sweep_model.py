import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LcDcoSweepModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(
            (ROOT / "reports" / "lc_dco_sweep.json").read_text()
        )

    def test_all_tested_points_sustain_oscillation(self):
        self.assertTrue(
            all(point["sustained_oscillation"] for point in self.report["points"])
        )

    def test_each_corner_brackets_ble_with_overlapping_codes(self):
        for summary in self.report["corner_summary"]:
            self.assertTrue(summary["sampled_envelope_brackets_ble_band"])
            self.assertGreater(summary["minimum_adjacent_overlap_hz"], 15_000_000)


if __name__ == "__main__":
    unittest.main()
