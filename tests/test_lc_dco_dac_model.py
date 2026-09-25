import json
import unittest
from pathlib import Path

from model.lc_dco_dac import SegmentedVoltageDac, VoltageDac


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


if __name__ == "__main__":
    unittest.main()
