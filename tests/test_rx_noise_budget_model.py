import json
import unittest
from pathlib import Path

from scripts.run_rx_noise_budget import (
    STAGES,
    cascaded_noise_figure_db,
    thermal_noise_density_dbm_hz,
)


ROOT = Path(__file__).resolve().parents[1]


class RxNoiseBudgetModelTest(unittest.TestCase):
    def test_friis_cascade_matches_committed_budget(self):
        report = json.loads((ROOT / "reports" / "rx_noise_budget.json").read_text())
        self.assertAlmostEqual(
            cascaded_noise_figure_db(STAGES),
            report["cascade_noise_figure_db"],
            places=9,
        )
        self.assertTrue(report["noise_budget_passed"])
        self.assertGreater(report["project_target_margin_db"], 9.5)
        self.assertEqual(report["required_input_dynamic_range_db"], 70.0)

    def test_hot_temperature_sets_the_noise_budget(self):
        report = json.loads((ROOT / "reports" / "rx_noise_budget.json").read_text())
        self.assertEqual(report["budget_temperature_c"], 85.0)
        self.assertAlmostEqual(
            thermal_noise_density_dbm_hz(85.0),
            report["thermal_noise_density_dbm_hz"],
            places=9,
        )
        with self.assertRaises(ValueError):
            thermal_noise_density_dbm_hz(-273.15)

    def test_empty_cascade_is_rejected(self):
        with self.assertRaises(ValueError):
            cascaded_noise_figure_db(())


if __name__ == "__main__":
    unittest.main()
