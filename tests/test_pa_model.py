import json
import math
import unittest
from pathlib import Path

from scripts.run_gf180_pa import FREQUENCY_HZ, fundamental_rms, tone_rms


ROOT = Path(__file__).resolve().parents[1]


class PaModelTest(unittest.TestCase):
    def test_fundamental_extractor_recovers_sine_rms(self):
        sample_step_s = 1.0 / FREQUENCY_HZ / 128
        times_s = [index * sample_step_s for index in range(128 * 20 + 1)]
        values = [
            math.sin(2.0 * math.pi * FREQUENCY_HZ * time_s)
            for time_s in times_s
        ]
        self.assertAlmostEqual(fundamental_rms(times_s, values), 1 / math.sqrt(2), 3)

    def test_harmonic_extractor_separates_tones(self):
        sample_step_s = 1.0 / FREQUENCY_HZ / 128
        times_s = [index * sample_step_s for index in range(128 * 20 + 1)]
        values = [
            math.sin(2.0 * math.pi * FREQUENCY_HZ * time_s)
            + 0.25 * math.sin(6.0 * math.pi * FREQUENCY_HZ * time_s)
            for time_s in times_s
        ]
        self.assertAlmostEqual(tone_rms(times_s, values, 2), 0.0, 3)
        self.assertAlmostEqual(tone_rms(times_s, values, 3), 0.25 / math.sqrt(2), 3)

    def test_pa_power_codes_cover_requested_levels_across_pvt(self):
        report = json.loads((ROOT / "reports" / "gf180_pa.json").read_text())
        self.assertTrue(report["passed"])
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["maximum_power_code"], 128)
        self.assertLessEqual(report["maximum_level_error_db"], 1.0)
        self.assertEqual(len(report["calibration"]), 15)
        self.assertIn("worst_selected_second_harmonic_dbc", report)
        self.assertIn("worst_selected_third_harmonic_dbc", report)
        self.assertLess(
            report["worst_selected_second_harmonic_dbc"], 0.0
        )
        self.assertLess(report["worst_selected_third_harmonic_dbc"], 0.0)
        self.assertTrue(
            all(
                "third_harmonic_output_power_dbm" in point
                for point in report["calibration"]
            )
        )
        self.assertLess(
            report["maximum_selected_energy_per_224us_burst_j"], 1e-6
        )

    def test_pa_real_load_sweep_keeps_calibrated_baseline(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_pa_load_sweep.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["loads_ohm"],
            [25.0, 35.0, 50.0, 75.0, 100.0, 150.0, 200.0],
        )
        self.assertEqual(len(report["summaries"]), 3)
        self.assertTrue(
            all(len(summary["points"]) == 7 for summary in report["summaries"])
        )


if __name__ == "__main__":
    unittest.main()
