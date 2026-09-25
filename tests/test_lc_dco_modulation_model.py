import json
import unittest
from pathlib import Path

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.dco import ble_channel_center_hz
from model.lc_dco_modulation import (
    calibrate_channel,
    control_voltage_for_frequency,
    control_waveform,
    frequency_for_control_voltage,
)


ROOT = Path(__file__).resolve().parents[1]


class LcDcoModulationModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = json.loads(
            (ROOT / "reports" / "lc_dco_sweep.json").read_text()
        )["points"]
        cls.points += json.loads(
            (ROOT / "reports" / "lc_dco_local_calibration.json").read_text()
        )["points"]
        cls.measurement = CgmMeasurement(0x1234, 123, -256, 0x03, 91)

    def test_every_advertising_channel_has_fixed_code_margin(self):
        for corner in ("typical", "ff", "ss"):
            for channel in (37, 38, 39):
                calibration = calibrate_channel(self.points, corner, channel)
                self.assertGreaterEqual(calibration.worst_case_margin_hz, 2_000_000)

    def test_complete_packet_maps_without_control_saturation(self):
        for corner in ("typical", "ff", "ss"):
            for channel in (37, 38, 39):
                bits = build_cgm_air_packet_bits(
                    self.measurement, 0xC0DEC0FFEE01, channel
                )
                calibration, offsets, voltages = control_waveform(
                    self.points, corner, channel, bits
                )
                self.assertEqual(len(offsets), 224 * 16)
                self.assertEqual(len(voltages), len(offsets))
                self.assertTrue(all(0.0 <= voltage <= 1.8 for voltage in voltages))
                self.assertIn(calibration.coarse_code, range(16))

    def test_static_inverse_mapping_round_trips(self):
        for corner in ("typical", "ff", "ss"):
            for channel in (37, 38, 39):
                calibration = calibrate_channel(self.points, corner, channel)
                center_hz = ble_channel_center_hz(channel)
                for offset_hz in (-250_000, 0, 250_000):
                    requested_hz = center_hz + offset_hz
                    control_v = control_voltage_for_frequency(
                        self.points, calibration, requested_hz
                    )
                    realized_hz = frequency_for_control_voltage(
                        self.points, calibration, control_v
                    )
                    self.assertAlmostEqual(realized_hz, requested_hz, places=5)

    def test_local_calibration_converges_within_fifty_kilohertz(self):
        grouped = {}
        for point in json.loads(
            (ROOT / "reports" / "lc_dco_local_calibration.json").read_text()
        )["points"]:
            key = (point["corner"], point["channel"], point["target_frequency_hz"])
            grouped[key] = point
        self.assertEqual(len(grouped), 27)
        report = json.loads(
            (ROOT / "reports" / "lc_dco_local_calibration.json").read_text()
        )
        self.assertTrue(report["passed"])
        self.assertLessEqual(
            max(abs(point["calibration_error_hz"]) for point in grouped.values()),
            50_000,
        )

    def test_dynamic_typical_channel_37_tracks_within_reported_limits(self):
        report = json.loads((ROOT / "reports" / "lc_dco_dynamic.json").read_text())
        self.assertEqual(report["corner"], "typical")
        self.assertEqual(report["channel"], 37)
        self.assertEqual(report["measured_samples"], 48)
        self.assertEqual(report["bias_dac_bits"], 7)
        self.assertEqual(report["modulation_dac_bits"], 6)
        self.assertEqual(report["drive_resistance_ohm"], 1_000)
        self.assertEqual(report["control_load_f"], 10e-12)
        self.assertEqual(report["modulation_trim_codes"], -1)
        self.assertTrue(report["passed"])
        self.assertLessEqual(
            report["maximum_absolute_frequency_error_hz"],
            report["maximum_absolute_frequency_error_limit_hz"],
        )
        self.assertLessEqual(
            abs(report["mean_frequency_error_hz"]),
            report["mean_frequency_error_limit_hz"],
        )


if __name__ == "__main__":
    unittest.main()
