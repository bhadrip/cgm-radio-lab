import unittest

from model.dco import (
    DCO_GAIN_HZ_PER_LSB,
    ble_channel_center_hz,
    dco_codes,
    realized_offsets_hz,
)


class DcoModelTest(unittest.TestCase):
    def test_ble_channel_frequency_map(self):
        self.assertEqual(ble_channel_center_hz(37), 2_402_000_000)
        self.assertEqual(ble_channel_center_hz(38), 2_426_000_000)
        self.assertEqual(ble_channel_center_hz(39), 2_480_000_000)
        self.assertEqual(ble_channel_center_hz(0), 2_404_000_000)
        self.assertEqual(ble_channel_center_hz(10), 2_424_000_000)
        self.assertEqual(ble_channel_center_hz(11), 2_428_000_000)
        self.assertEqual(ble_channel_center_hz(36), 2_478_000_000)

    def test_error_feedback_resolves_below_one_dco_step(self):
        target_hz = 17_500
        base_code = 2048
        codes, saturated = dco_codes([target_hz] * 1000, base_code)
        realized = realized_offsets_hz(codes, base_code)
        self.assertFalse(any(saturated))
        self.assertLessEqual(
            abs(sum(realized) / len(realized) - target_hz),
            DCO_GAIN_HZ_PER_LSB / len(realized),
        )

    def test_saturation_is_reported(self):
        low_codes, low_flags = dco_codes([-250_000], 0)
        high_codes, high_flags = dco_codes([250_000], 4095)
        self.assertEqual(low_codes, [0])
        self.assertEqual(high_codes, [4095])
        self.assertEqual(low_flags, [True])
        self.assertEqual(high_flags, [True])

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            ble_channel_center_hz(40)
        with self.assertRaises(ValueError):
            dco_codes([0], -1)
        with self.assertRaises(ValueError):
            dco_codes([0], 0, gain_hz_per_lsb=0)


if __name__ == "__main__":
    unittest.main()
