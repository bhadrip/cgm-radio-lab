import json
import unittest
from pathlib import Path

from scripts.run_gf180_lna_linearity import available_power_source_peak_v


ROOT = Path(__file__).resolve().parents[1]


class LnaLinearityModelTest(unittest.TestCase):
    def test_available_power_conversion(self):
        self.assertAlmostEqual(available_power_source_peak_v(-30.0), 0.02)

    def test_report_brackets_two_tone_compression(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_lna_linearity.json").read_text()
        )
        self.assertEqual(len(report["summaries"]), 3)
        self.assertEqual(report["tone_frequencies_hz"], [2.43e9, 2.45e9])
        self.assertEqual(report["im3_frequencies_hz"], [2.41e9, 2.47e9])
        for summary in report["summaries"]:
            self.assertEqual(len(summary["points"]), 7)
            self.assertEqual(
                summary["two_tone_1db_compression_bracket_per_tone_dbm"],
                [-20.0, -15.0],
            )
            low_level_gain = summary["low_level_intrinsic_voltage_gain_db"]
            minus_ten = next(
                point
                for point in summary["points"]
                if point["input_power_per_tone_dbm"] == -10.0
            )
            self.assertGreater(
                low_level_gain - minus_ten["intrinsic_voltage_gain_db"], 1.0
            )


if __name__ == "__main__":
    unittest.main()
