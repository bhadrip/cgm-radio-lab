import random
import unittest

from model.ble import (
    CgmMeasurement,
    add_crc,
    build_cgm_advertising_pdu,
    build_cgm_air_packet_bits,
    build_test_pdu,
    bytes_to_lsb_bits,
    crc24,
    crc24_bits,
    crc_ok,
    dewhiten_bits,
    run_hard_bit_loop,
    run_cgm_air_loop,
    whiten_bits,
)


class BleModelTest(unittest.TestCase):
    def test_byte_bit_order(self):
        self.assertEqual(bytes_to_lsb_bits(bytes([0xA5])), [1, 0, 1, 0, 0, 1, 0, 1])

    def test_crc_byte_and_bit_interfaces_match(self):
        data = bytes.fromhex("00080102030405060708")
        self.assertEqual(crc24(data), crc24_bits(bytes_to_lsb_bits(data)))
        # Cross-checked against the Apache-2.0 JiaoXianjun/BTLE reference model.
        self.assertEqual(crc24(data), 0xAD1F4B)

    def test_whitening_is_self_inverse_on_all_ble_channels(self):
        bits = bytes_to_lsb_bits(bytes(range(32)))
        for channel in range(40):
            self.assertEqual(dewhiten_bits(whiten_bits(bits, channel), channel), bits)

    def test_crc_detects_single_bit_errors(self):
        packet = add_crc(build_test_pdu(b"CGM00001"))
        self.assertTrue(crc_ok(packet))
        for location in (0, 17, len(packet) - 1):
            corrupted = packet.copy()
            corrupted[location] ^= 1
            self.assertFalse(crc_ok(corrupted))

    def test_randomized_clean_loop(self):
        rng = random.Random(0xC6A)
        for _ in range(1000):
            payload = rng.randbytes(8)
            packet_length = len(add_crc(build_test_pdu(payload)))
            result = run_hard_bit_loop(payload, rng.randrange(40), [0] * packet_length)
            self.assertTrue(result.payload_recovered)
            self.assertTrue(result.crc_passed)

    def test_cgm_packet_shape(self):
        measurement = CgmMeasurement(7, 123, -256, 0x03, 91)
        pdu = build_cgm_advertising_pdu(measurement, 0xC0DEC0FFEE01)
        self.assertEqual(len(pdu), 20)
        self.assertEqual(pdu[:2], bytes((0x42, 18)))
        self.assertEqual(pdu[2:8], bytes.fromhex("01eeffc0dec0"))
        self.assertEqual(pdu[8:12], bytes((0x0B, 0xFF, 0xFF, 0xFF)))
        self.assertEqual(len(build_cgm_air_packet_bits(measurement, 0xC0DEC0FFEE01, 37)), 224)

    def test_cgm_air_loop_checks_crc_and_format(self):
        measurement = CgmMeasurement(7, 123, -256, 0x03, 91)
        address = 0xC0DEC0FFEE01
        packet_length = len(build_cgm_air_packet_bits(measurement, address, 37))
        clean = run_cgm_air_loop(measurement, address, 37, [0] * packet_length)
        self.assertTrue(clean.crc_passed)
        self.assertTrue(clean.format_passed)
        self.assertTrue(clean.payload_recovered)

        preamble_error = [0] * packet_length
        preamble_error[3] = 1
        corrupted = run_cgm_air_loop(measurement, address, 37, preamble_error)
        self.assertTrue(corrupted.crc_passed)
        self.assertFalse(corrupted.format_passed)


if __name__ == "__main__":
    unittest.main()
