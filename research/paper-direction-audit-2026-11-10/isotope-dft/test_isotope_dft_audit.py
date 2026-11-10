import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "isotope_pressure": "6199a3f71c53ffe6dfe9505f942d713cdb8b8c8da87d35913898163c04366c07",
    "multilayer_dft": "ef31a1048fe415dfff433effc7fd7caefc4b124b320b104eb5e595e6d0752c5c",
    "kruglov_pdf": "25632b30de626a14d2607f9c4ae1c0c57e78b4af2e0723985a6558e00c1555a4",
    "isotope_pdf": "b5c69550005f7b4e926b12a60078a649d9939cbf6af51e07f42eec4063cfb6a6",
    "jarvis_pdf": "de1d282d5924f1a695e47a52f4e6bb8d696aea3e423ae894ca165452b47a03ab",
    "nickelate_search": "c82c8d735270ac6a154682dfcac6507e3d59224520fd15c5478be93b9e371fa4",
}


class IsotopeDftAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"isotope_lineage", "method_aware_pressure", "reproducible_dft", "ml_benchmark_governance"},
        )
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, EXPECTED_HASHES)

    def test_isotope_recompute(self):
        rows = self.data["evidence"]["isotope"]
        self.assertAlmostEqual(rows["printed_lah10"]["alpha"], 0.514573172829758)
        self.assertAlmostEqual(rows["durajski_lah10"]["alpha"], 0.468148835738406)
        self.assertAlmostEqual(rows["h3s"]["alpha"], 0.389211511910938)
        self.assertEqual(rows["printed_lah10"]["claimed_alpha"], 0.46)
        self.assertEqual(rows["durajski_lah10"]["pressure_gpa"], 150)
        self.assertFalse(rows["mechanism_uniquely_proven"])

    def test_pressure_arithmetic_and_method_roles(self):
        rows = self.data["evidence"]["pressure"]["rows"]
        self.assertEqual([row["slope"] for row in rows], [0.4, -2.2, -0.075])
        self.assertEqual(rows[0]["methods"], ["Eliashberg", "SCDFT"])
        self.assertEqual(rows[1]["methods"], ["SCDFT", "Eliashberg"])
        self.assertEqual(rows[2]["methods"], ["Eliashberg", "Eliashberg"])
        self.assertTrue(all(row["arithmetic_matches"] for row in rows))
        self.assertTrue(self.data["evidence"]["pressure"]["mixed_method_curve"])
        self.assertFalse(self.data["evidence"]["pressure"]["experimental_curve_established"])
        self.assertEqual(self.data["evidence"]["bibliography"]["kruglov_article"], "024508")
        self.assertEqual(self.data["evidence"]["bibliography"]["printed_article"], "224508")

    def test_jarvis_roles_and_speed_boundary(self):
        row = self.data["evidence"]["jarvis"]
        self.assertEqual(row["previous_zero_pressure_bulk"], 1000)
        self.assertEqual(row["previous_zero_pressure_2d"], 150)
        self.assertEqual(row["new_hydride_count_label"], "over 900")
        self.assertEqual(row["new_pressure_range_gpa"], [0, 500])
        self.assertEqual(row["stable_candidates"], 122)
        self.assertEqual(row["dft_core_hours"], 11500)
        self.assertEqual(row["training_gpu_hours"], [4, 7])
        self.assertTrue(row["previous_datasets_confirmed"])
        self.assertFalse(row["speedup_1000_directly_supported"])

    def test_dft_and_nickelate_boundaries(self):
        dft = self.data["evidence"]["dft"]
        self.assertFalse(dft["large_supercell_always_requires_denser_k"])
        self.assertFalse(dft["r2scan_error_universal"])
        self.assertFalse(dft["six_layer_ring_ready_for_input"])
        nickelate = self.data["evidence"]["nickelate"]
        self.assertEqual(nickelate["search_result_count"], 10)
        self.assertFalse(nickelate["exact_dome_source_found"])
        self.assertTrue(nickelate["negative_result_scope_limited"])

    def test_corrections_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 8)
        for key in (
            "dft_rerun",
            "phonon_convergence",
            "ml_speed_benchmark",
            "nickelate_dome_verified",
            "six_layer_ring_defined",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_figure_scope(self):
        for label in ("Eliashberg", "SCDFT", "0.514573", "0.468149", "跨方法"):
            self.assertIn(label, self.data["figure"]["labels"])
        self.assertFalse(self.data["figure"]["experimental_percentage_plotted"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("0.514573", "024508", "跨方法", "1000 倍", "图 1", "全库审计尚未完成"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
            footnotes = package.read("word/footnotes.xml").decode("utf-8")
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 5)
        self.assertIn(b"PAGE", footer)
        self.assertIn("同位素压力与多层 DFT", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in ("024508", "1912.09663", "2312.12694", "nickelate-dome-scholar.csv", "17-资料收集-同位素效应与压力导数.md", "19-资料收集-多层结构DFT参数.md"):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
