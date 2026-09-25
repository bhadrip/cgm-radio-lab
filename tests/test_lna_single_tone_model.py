import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LnaSingleToneModelTest(unittest.TestCase):
    def test_bias_boost_passes_pr11_schematic_screen(self):
        report = json.loads(
            (ROOT / "reports" / "gf180_lna_single_tone.json").read_text()
        )
        modes = {mode["name"]: mode for mode in report["modes"]}
        normal = modes["normal"]
        boost = modes["bias_boost"]
        self.assertEqual(report["pr11_maximum_input_dbm"], -10.0)
        self.assertTrue(report["accepted_for_next_stage"])
        self.assertFalse(normal["passed"])
        self.assertTrue(boost["passed"])
        self.assertGreater(
            normal["maximum_input_gain_compression_db"],
            report["maximum_gain_compression_db"],
        )
        self.assertLessEqual(
            boost["maximum_input_gain_compression_db"],
            report["maximum_gain_compression_db"],
        )
        self.assertAlmostEqual(boost["configuration"]["bias_current_a"], 6e-3)
        for mode in modes.values():
            self.assertEqual(len(mode["summaries"]), 3)
            self.assertTrue(
                all(len(summary["points"]) == 6 for summary in mode["summaries"])
            )


if __name__ == "__main__":
    unittest.main()
