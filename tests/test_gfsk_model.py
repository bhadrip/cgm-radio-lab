import math
import unittest

from model.gfsk import (
    DEVIATION_HZ,
    FILTER_SPAN_SYMBOLS,
    HISTORY_SYMBOLS,
    MODULATION_INDEX,
    SAMPLES_PER_SYMBOL,
    SYMBOL_RATE_HZ,
    frequency_samples,
    frequency_words,
    gaussian_taps,
    iq_samples,
    symbol_phase_weights,
)


class GfskModelTest(unittest.TestCase):
    def test_filter_and_phase_tables_have_unity_dc_gain(self):
        taps = gaussian_taps()
        self.assertEqual(len(taps), FILTER_SPAN_SYMBOLS * SAMPLES_PER_SYMBOL + 1)
        self.assertAlmostEqual(sum(taps), 1.0, places=12)

        for weights in symbol_phase_weights():
            self.assertEqual(len(weights), HISTORY_SYMBOLS)
            self.assertAlmostEqual(sum(weights), 1.0, places=12)
        for weights in symbol_phase_weights(quantized_hz=True):
            self.assertEqual(sum(weights), DEVIATION_HZ)

    def test_nominal_modulation_index_and_constant_envelope(self):
        self.assertEqual(2 * DEVIATION_HZ / SYMBOL_RATE_HZ, MODULATION_INDEX)
        iq = iq_samples([0] * 8 + [1] * 8)
        self.assertTrue(all(abs(abs(sample) - 1.0) < 1e-12 for sample in iq))

    def test_1010_frequency_deviation_exceeds_bluetooth_minimum(self):
        samples = frequency_samples([0, 1] * 12)
        settled = samples[6 * SAMPLES_PER_SYMBOL : 20 * SAMPLES_PER_SYMBOL]
        centers = [
            abs(settled[index])
            for index in range(SAMPLES_PER_SYMBOL // 2, len(settled), SAMPLES_PER_SYMBOL)
        ]
        self.assertGreaterEqual(min(centers), 185_000)
        self.assertGreaterEqual(min(centers), 0.8 * DEVIATION_HZ)

    def test_quantization_stays_within_three_hz_of_reference(self):
        bits = [int(value) for value in "00101101110010100111"]
        ideal = frequency_samples(bits)
        quantized = frequency_words(bits)
        self.assertEqual(len(quantized), len(bits) * SAMPLES_PER_SYMBOL)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(ideal, quantized)), 3.0)

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            frequency_words([0, 2, 1])
        with self.assertRaises(ValueError):
            frequency_samples([0, 1], initial_bit=-1)
        with self.assertRaises(ValueError):
            gaussian_taps(span_symbols=3)


if __name__ == "__main__":
    unittest.main()
