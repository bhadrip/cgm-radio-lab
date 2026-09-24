import random
import unittest

from model.ble import (
    add_crc,
    build_test_pdu,
    bytes_to_lsb_bits,
    crc24,
    crc24_bits,
    crc_ok,
    dewhiten_bits,
    run_hard_bit_loop,
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


if __name__ == "__main__":
    unittest.main()
