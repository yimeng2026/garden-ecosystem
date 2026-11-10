import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
SOURCE_ROOT = next(
    parent / "toe-sylva-audit/papers/room_temp_sc/organized"
    for parent in ROOT.parents
    if (parent / "toe-sylva-audit/papers/room_temp_sc/organized").is_dir()
)


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripes = (SOURCES / "stripes-2501.15709.txt").read_text(encoding="utf-8")
        cls.finite = (SOURCES / "dwave-2211.06322.txt").read_text(encoding="utf-8")
        cls.extended = (SOURCES / "extended-hubbard-2206.03486.txt").read_text(encoding="utf-8")
        cls.global_html = (SOURCES / "global-dwave-excerpts.md").read_text(encoding="utf-8")
        cls.google = (SOURCES / "google-2408.13687.txt").read_text(encoding="utf-8")
        cls.xzzx = (SOURCES / "xzzx-surface-code.txt").read_text(encoding="utf-8")
        cls.neutral = (SOURCES / "neutral-atoms-s41586-023-06927-3.txt").read_text(encoding="utf-8")
        cls.dmrg_doc = (SOURCE_ROOT / "14-资料收集-DMRG-Hubbard模型.md").read_text(encoding="utf-8")
        cls.qec_doc = (SOURCE_ROOT / "18-资料收集-量子纠错码进展.md").read_text(encoding="utf-8")
        cls.stripes_flat = " ".join(cls.stripes.replace("\u2009", " ").split())
        cls.neutral_flat = " ".join(cls.neutral.replace("\u2009", " ").split())

    def test_finite_temperature_scope(self):
        self.assertIn("widths up to W = 6", self.finite)
        self.assertIn("T /J ≃ 0.06", self.finite)
        self.assertIn("domelike SC regime with a diverging d-wave pairing susceptibility", self.finite)
        self.assertIn("pairing correlations are\nmuch weaker", self.finite)
        self.assertIn("t′/t = ±0.17", self.finite)

    def test_global_ground_state_scope_and_metadata(self):
        self.assertIn("On large 8-leg cylinders", self.global_html)
        self.assertIn("t2/t1≳0.15", self.global_html)
        self.assertIn("not feasible to determine the exact power-law decay exponent", self.global_html)
        self.assertIn("natural ground state", self.global_html)
        self.assertIn("Grand_SQL_tJ", self.global_html)
        self.assertIn("PNAS 检索元数据：2025", self.global_html)
        self.assertIn("PMC (2024-12-10)", self.dmrg_doc)

    def test_stripes_reference_mapping_and_metastability(self):
        self.assertIn("Refs. [ 43, 44] observed ev-", self.stripes)
        self.assertIn("while Refs. [ 41, 42] drew qualita-", self.stripes)
        self.assertIn("10 − 2t or less", self.stripes_flat)
        self.assertIn("not guaranteed that the DMRG algorithm", self.stripes)
        self.assertIn("in metastable states and never reach the ground state", self.stripes)
        self.assertIn("有文献[41,42]声称", self.dmrg_doc)
        self.assertIn("有文献[43,44]得出", self.dmrg_doc)

    def test_extended_hubbard_current_and_previous_channels(self):
        self.assertIn("long four-leg cylinders", self.extended)
        self.assertIn("near-neighbor electron\nattractionV can notably enhance", self.extended)
        self.assertIn("dominantp-wave SC correlations", self.extended)
        self.assertIn("one-dimensional (1D) EHM", self.extended)
        self.assertIn("plaquetted-wave symmetry", self.extended)
        self.assertIn("exact proof of long-range ordersd-wave superconductivity", self.extended)

    def test_xzzx_threshold_noise_models(self):
        self.assertIn("minimum pc = 18.7(1)% at standard depolarizing noise", self.xzzx)
        self.assertIn("peaks pc ∼ 50% at pure X, Y and Z noise", self.xzzx)
        self.assertIn("threshold error rate of 50%", self.xzzx)
        self.assertIn("approximate maximum-likelihood decoding", self.xzzx)

    def test_google_metrics_and_prior_work(self):
        self.assertIn("a distance-7 code and a distance-5 code", self.google)
        self.assertIn("Λ = 2 .14 ± 0.02", self.google)
        self.assertIn("average decoder latency of 63 µs", self.google)
        self.assertIn("Suppressing quantum errors by\nscaling a surface code logical qubit. Nature 614, 676–\n681 (2023)", self.google)

    def test_neutral_atom_codes_and_year(self):
        self.assertIn("Nature | Vol 626 | 1 February 2024", self.neutral)
        self.assertIn("using 3D [[8,3,2]] code blocks", self.neutral)
        self.assertIn("up to 48 logical qubits", self.neutral)
        self.assertIn("Transversal entangling gates between two surface codes", self.neutral)
        self.assertIn("d = 7 surface codes", self.neutral_flat)

    def test_original_cross_domain_claims(self):
        self.assertIn("48个逻辑量子比特，距离-7保护", self.qec_doc)
        self.assertIn("首次实现", self.qec_doc)
        self.assertIn("磁通涡旋可作为量子比特", self.qec_doc)
        self.assertIn("拓扑保护 + 量子纠错 = 双重容错", self.qec_doc)
        self.assertIn("O(d) 或更好", self.qec_doc)
        self.assertIn("线性/近似线性", self.qec_doc)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
