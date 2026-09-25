import json
import math
import unittest
from pathlib import Path

from model.lc_dco import (
    estimate_tuning,
    mim_capacitance_ff,
    nmoscap_capacitance_ff,
    nmoscap_slope_ff_per_v,
)


ROOT = Path(__file__).resolve().parents[1]


class LcDcoModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = json.loads(
            (ROOT / "reports" / "lc_vco_sweep.json").read_text()
        )["points"]

    def test_minimum_mim_is_far_larger_than_50khz_equivalent(self):
        minimum_mim_ff = mim_capacitance_ff(5.0)
        estimate = estimate_tuning(self.points, "typical", 2_441_000_000)
        self.assertAlmostEqual(minimum_mim_ff, 44.33, places=2)
        self.assertLess(estimate.capacitance_for_50khz_ff, 0.06)
        self.assertGreater(minimum_mim_ff / estimate.capacitance_for_50khz_ff, 800)

    def test_all_corners_interpolate_the_ble_band(self):
        for corner in ("typical", "ff", "ss"):
            high = estimate_tuning(self.points, corner, 2_480_000_000)
            low = estimate_tuning(self.points, corner, 2_402_000_000)
            self.assertLess(high.interpolated_side_um, low.interpolated_side_um)
            self.assertGreater(high.local_gain_hz_per_ff, 800_000)
            self.assertLess(high.local_gain_hz_per_ff, 1_000_000)

    def test_sixteen_minimum_moscaps_overlap_one_mim_step(self):
        for corner in ("typical", "ff", "ss"):
            tuning_span = nmoscap_capacitance_ff(
                1.8, 16, corner
            ) - nmoscap_capacitance_ff(0.0, 16, corner)
            self.assertGreater(tuning_span, mim_capacitance_ff(5.0, corner))

    def test_fine_control_needs_sub_millivolt_steps(self):
        transition_v = 3.9375 / 6.25
        gain = estimate_tuning(
            self.points, "typical", 2_441_000_000
        ).local_gain_hz_per_ff
        voltage_step = 50_000 / (
            gain * nmoscap_slope_ff_per_v(transition_v, 16)
        )
        self.assertTrue(math.isclose(voltage_step, 0.000274, rel_tol=0.02))


if __name__ == "__main__":
    unittest.main()
