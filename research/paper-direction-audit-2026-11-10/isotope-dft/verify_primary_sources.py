import csv
import sys
import unittest
from pathlib import Path

from numeric_checks import isotope_alpha, slope

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
        cls.kruglov = (SOURCES / "kruglov-1810.01113.txt").read_text(encoding="utf-8")
        cls.isotope = (SOURCES / "isotope-1912.09663.txt").read_text(encoding="utf-8")
        cls.jarvis = (SOURCES / "jarvis-2312.12694.txt").read_text(encoding="utf-8")
        cls.isotope_doc = (SOURCE_ROOT / "17-资料收集-同位素效应与压力导数.md").read_text(encoding="utf-8")
        cls.dft_doc = (SOURCE_ROOT / "19-资料收集-多层结构DFT参数.md").read_text(encoding="utf-8")

    def test_kruglov_citation_table_and_method_footnote(self):
        with (SOURCES / "kruglov-scholar.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(any("PhysRevB.101.024508" in row.get("url", "") for row in rows))
        self.assertIn("TC, K 259 271 * 249 246 203 197", self.kruglov)
        self.assertIn("* SCDFT", self.kruglov)
        self.assertIn("Eliashberg equation (with μ* = 0.2)", self.kruglov)
        self.assertIn("ωlog, K 801 906 851 1253 833 840", self.kruglov)
        self.assertIn("λ 3.94 3.75 3.42 2.29 2.77 2.63", self.kruglov)

    def test_isotope_formula_and_source_temperature_pair(self):
        self.assertIn("α =−ln[TC]LaD10− ln[TC]LaH10", self.isotope)
        self.assertIn("ln[M]D− ln[M]H", self.isotope)
        self.assertIn("Tc = 249 (180) K", self.isotope)
        self.assertIn("measured at around 150 GPa", self.isotope)
        self.assertIn("α amounts", self.isotope)
        self.assertIn("0.46", self.isotope)

    def test_jarvis_dataset_roles_and_costs(self):
        self.assertIn("over 900 hydride materials", self.jarvis)
        self.assertIn("(0 to 500) GPa", self.jarvis)
        self.assertIn("122 dynamically stable structures", self.jarvis)
        self.assertIn("over 1000 bulk", self.jarvis)
        self.assertIn("150\ntwo-dimensional (2D) superconductors", self.jarvis)
        self.assertIn("11,500 core hours", self.jarvis)
        self.assertIn("4 and 7 GPU hours", self.jarvis)
        self.assertIn("(160 - 187) K", self.jarvis)
        self.assertIn("154 K", self.jarvis)

    def test_no_direct_1000_fold_end_to_end_benchmark(self):
        lowered = self.jarvis.lower()
        for phrase in ("1000 times faster", "1000-fold speedup", "1000× speedup", "1000x faster"):
            self.assertNotIn(phrase, lowered)
        self.assertIn("significantly reduced cost", self.jarvis)

    def test_nickelate_search_scope(self):
        with (SOURCES / "nickelate-dome-scholar.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 10)
        exact_support = []
        for row in rows:
            text = f"{row.get('title', '')} {row.get('abstract', '')}".lower()
            if "ndnio2" in text and "ktao3" in text and "superconduct" in text and "4-8" in text:
                exact_support.append(row["title"])
        self.assertEqual(exact_support, [])

    def test_original_document_specific_claims(self):
        self.assertIn("α = -ln(Tc)/ln(M)", self.isotope_doc)
        self.assertIn("240 K @ 170 GPa", self.isotope_doc)
        self.assertIn("168 K @ 170 GPa", self.isotope_doc)
        self.assertIn("Phys. Rev. B 101, 224508", self.isotope_doc)
        self.assertIn("大超胞需要更密集的k点", self.dft_doc)
        self.assertIn("1000倍", self.dft_doc)
        self.assertIn("NdNiO₂/KTaO₃", self.dft_doc)
        self.assertIn("六层环体", self.dft_doc)

    def test_independent_numeric_values(self):
        self.assertAlmostEqual(isotope_alpha(240, 168), 0.514573172829758)
        self.assertAlmostEqual(isotope_alpha(249, 180), 0.468148835738406)
        self.assertAlmostEqual(isotope_alpha(203, 155), 0.389211511910938)
        self.assertEqual([slope(170, 259, 200, 271), slope(200, 271, 210, 249), slope(210, 249, 250, 246)], [0.4, -2.2, -0.075])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
