import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
AUDITS = ROOT.parent
SOURCE_ROOT = next(
    parent / "toe-sylva-audit/papers/room_temp_sc/organized"
    for parent in ROOT.parents
    if (parent / "toe-sylva-audit/papers/room_temp_sc/organized").is_dir()
)


def load_review(name):
    return json.loads((AUDITS / name / "review.json").read_text(encoding="utf-8"))


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.htsc = (SOURCES / "htsc-2506.03837v2.txt").read_text(encoding="utf-8")
        cls.patsnap = (SOURCES / "patsnap-excerpts.md").read_text(encoding="utf-8")
        cls.boron = (SOURCES / "boron-prb111-excerpts.md").read_text(encoding="utf-8")
        cls.main = load_review("main-claims")
        cls.validation = load_review("validation-materials")
        cls.isotope = load_review("isotope-dft")
        cls.dmrg = load_review("dmrg-qec")
        cls.methods = load_review("room-temp-methods")
        cls.kruglov_text = (AUDITS / "isotope-dft/sources/kruglov-1810.01113.txt").read_text(encoding="utf-8")

    def test_htsc_dataset_and_exclusions(self):
        self.assertIn("contains a total of 140 samples", self.htsc)
        self.assertIn("27.3 K", self.htsc)
        self.assertIn("(Tc = 160 K)", self.htsc)
        self.assertIn("must rigorously exclude these materials", self.htsc)
        self.assertIn("HTSC-2025 does not include these materials", self.htsc)
        self.assertIn("excludes unconventional superconductors", self.htsc)
        self.assertIn("https://github.com/xqh19970407/HTSC-2025", self.htsc)

    def test_li2nah17_outside_benchmark_and_document_difference(self):
        self.assertIn("(297 K and 303 K, respectively)", self.htsc)
        self.assertIn("at 300 GPa", self.htsc)
        self.assertIn("Li₂NaH₁₇", (SOURCE_ROOT / "12-资料收集-氢化物与验证进展.md").read_text(encoding="utf-8"))
        self.assertIn("340 K @ 300 GPa", (SOURCE_ROOT / "12-资料收集-氢化物与验证进展.md").read_text(encoding="utf-8"))

    def test_patsnap_secondary_role_and_threshold(self):
        self.assertIn("二手研究景观博客，不是同行评议共识文件", self.patsnap)
        self.assertIn("zero resistance above 273K", self.patsnap)
        self.assertIn("No material has satisfied all five criteria", self.patsnap)

    def test_boron_prediction_not_experiment(self):
        self.assertIn("high-throughput calculations on 96 compounds", self.boron)
        self.assertIn("highest predicted Tc of 77.1 K", self.boron)
        self.assertIn("不是常压超导已经实验实现", self.boron)

    def test_song_direct_meissner_and_replication(self):
        song = self.main["evidence"]["song"]
        self.assertEqual(song["onset_tc_k"], [271, 298])
        self.assertFalse(song["direct_meissner_completed"])
        self.assertFalse(song["independent_positive_replication"])
        self.assertFalse(song["peer_review_established"])
        self.assertEqual(song["reproducible_runs_reported"], 13)

    def test_kruglov_unit_and_pressure_methods(self):
        self.assertIn("Nf, states/f.u./Ry", self.kruglov_text)
        self.assertIn("TC, K 259 271 * 249 246 203 197", self.kruglov_text)
        self.assertIn("* SCDFT", self.kruglov_text)
        self.assertEqual(self.isotope["evidence"]["bibliography"]["kruglov_article"], "024508")
        self.assertTrue(self.isotope["evidence"]["pressure"]["mixed_method_curve"])
        self.assertFalse(self.isotope["evidence"]["pressure"]["experimental_curve_established"])

    def test_research_update_and_qec_propagation(self):
        chen = self.dmrg["evidence"]["dmrg"]["global_ground_state"]
        self.assertEqual(chen["legs"], 8)
        self.assertFalse(chen["thermodynamic_limit_proven"])
        self.assertTrue(chen["code_data_available"])
        qec = self.dmrg["evidence"]["qec"]
        self.assertFalse(qec["google"]["first_below_threshold_claim_supported"])
        self.assertFalse(qec["neutral_atoms"]["logical_48_ldpc_distance7"])
        self.assertEqual(qec["neutral_atoms"]["logical_48_code"], "3D [[8,3,2]]")

    def test_completed_status_is_not_evidence(self):
        self.assertFalse(self.validation["evidence"]["scoring"]["rubric_available"])
        self.assertGreater(self.methods["evidence"]["si"]["placeholder_count"], 0)
        self.assertFalse(self.methods["evidence"]["si"]["dft_inputs_provided"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
