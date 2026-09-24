import json
import math
import unittest
from pathlib import Path

from scripts.run_gf180_pa import FREQUENCY_HZ, fundamental_rms


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

    def test_pa_power_codes_cover_requested_levels_across_pvt(self):
        report = json.loads((ROOT / "reports" / "gf180_pa.json").read_text())
        self.assertTrue(report["passed"])
        self.assertEqual(report["maximum_power_code"], 128)
        self.assertLessEqual(report["maximum_level_error_db"], 1.0)
        self.assertEqual(len(report["calibration"]), 15)
        self.assertLess(
            report["maximum_selected_energy_per_224us_burst_j"], 1e-6
        )


if __name__ == "__main__":
    unittest.main()
