import json
import unittest
from pathlib import Path

from model.lc_dco_dac import (
    SegmentedDacEncoding,
    SegmentedVoltageDac,
    VoltageDac,
)


ROOT = Path(__file__).resolve().parents[1]


class LcDcoDacModelTest(unittest.TestCase):
    def test_full_scale_endpoints_and_midscale(self):
        dac = VoltageDac(12)
        self.assertEqual(dac.code_for_voltage(0.0), 0)
        self.assertEqual(dac.code_for_voltage(1.8), 4095)
        self.assertAlmostEqual(dac.voltage_for_code(2048), 2048 * dac.lsb_v)

    def test_invalid_ranges_and_codes_are_rejected(self):
        with self.assertRaises(ValueError):
            VoltageDac(0)
        with self.assertRaises(ValueError):
            VoltageDac(12, 1.0, 1.0)
        dac = VoltageDac(12)
        with self.assertRaises(ValueError):
            dac.code_for_voltage(1.9)
        with self.assertRaises(ValueError):
            dac.voltage_for_code(4096)

    def test_report_selects_twelve_bits(self):
        report = json.loads(
            (ROOT / "reports" / "lc_dco_dac_resolution.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["selected_bits"], 12)
        summaries = {summary["bits"]: summary for summary in report["summaries"]}
        self.assertFalse(summaries[11]["meets_error_budget"])
        self.assertTrue(summaries[12]["meets_error_budget"])

    def test_segmented_dac_holds_bias_while_modulation_changes(self):
        dac = SegmentedVoltageDac(
            VoltageDac(7, 0.9, 1.4), VoltageDac(6, -0.008, 0.008)
        )
        bias_code, modulation_codes, outputs = dac.quantize_waveform(
            1.067, [1.064, 1.067, 1.070]
        )
        self.assertIn(bias_code, range(128))
        self.assertEqual(len(set(modulation_codes)), 3)
        self.assertEqual(len(outputs), 3)

    def test_segmented_report_selects_seven_plus_six_bits(self):
        report = json.loads(
            (ROOT / "reports" / "lc_dco_segmented_dac.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["selected_bias_bits"], 7)
        self.assertEqual(report["selected_modulation_bits"], 6)

    def test_loaded_driver_boundary_is_measured(self):
        report = json.loads(
            (ROOT / "reports" / "lc_dco_drive_settling.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["recommended_trim_codes"], -2)
        by_pair = {
            (summary["drive_resistance_ohm"], summary["control_load_f"]): summary
            for summary in report["summaries"]
        }
        self.assertTrue(by_pair[(2_500, 10e-12)]["passed"])
        self.assertFalse(by_pair[(5_000, 10e-12)]["passed"])

    def test_nonideality_budget_requires_seven_fast_bits(self):
        report = json.loads(
            (ROOT / "reports" / "lc_dco_dac_nonidealities.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["selected_modulation_bits"], 7)
        summaries = {
            summary["modulation_bits"]: summary for summary in report["summaries"]
        }
        self.assertFalse(summaries[6]["meets_error_limit"])
        self.assertTrue(summaries[7]["meets_error_limit"])

    def test_segmented_encoding_bounds_binary_carry_glitch(self):
        binary = SegmentedDacEncoding(7, 0)
        self.assertEqual(sum(binary.transition_events(63, 64)), 1)
        self.assertEqual(binary.worst_case_glitch_excursion_codes(63, 64), 63)
        segmented = SegmentedDacEncoding(7, 5)
        self.assertEqual(segmented.binary_lsb_bits, 2)
        self.assertEqual(segmented.switched_element_count, 33)
        self.assertEqual(segmented.worst_case_glitch_excursion_codes(59, 60), 3)

    def test_transition_budget_selects_five_plus_two_segmentation(self):
        report = json.loads(
            (ROOT / "reports" / "lc_dco_dac_transition.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["selected_thermometer_msb_bits"], 5)
        self.assertEqual(report["selected_binary_lsb_bits"], 2)
        summaries = {
            summary["thermometer_msb_bits"]: summary
            for summary in report["summaries"]
        }
        self.assertFalse(summaries[4]["meets_error_limit"])
        self.assertTrue(summaries[5]["meets_error_limit"])


if __name__ == "__main__":
    unittest.main()
