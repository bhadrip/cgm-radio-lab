import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PaMatchCosimModelTest(unittest.TestCase):
    def test_selected_match_meets_schematic_selection_screens(self):
        report = json.loads((ROOT / "reports" / "gf180_pa_match.json").read_text())
        selected = report["selected"]
        self.assertTrue(report["calibration_passed"])
        self.assertTrue(report["accepted_for_next_stage"])
        self.assertEqual(len(report["candidates"]), 25)
        self.assertEqual(len(selected["corners"]), 3)
        self.assertLessEqual(
            selected["maximum_absolute_power_error_db"],
            report["selection_screens"]["maximum_power_error_db"],
        )
        self.assertLessEqual(
            selected["maximum_power_code"],
            128 - report["selection_screens"]["minimum_power_code_headroom"],
        )
        self.assertLessEqual(
            selected["maximum_energy_per_224us_burst_j"],
            report["selection_screens"]["maximum_energy_per_224us_burst_j"],
        )
        self.assertGreater(report["minimum_third_harmonic_improvement_db"], 15.0)


if __name__ == "__main__":
    unittest.main()
