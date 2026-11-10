import json
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_workspace():
    for parent in ROOT.parents:
        if (parent / "toe-sylva-audit/papers/room_temp_sc").is_dir():
            return parent
    raise FileNotFoundError("workspace source root")


WORKSPACE = find_workspace()
SOURCE_ROOT = WORKSPACE / "toe-sylva-audit/papers/room_temp_sc"
PRIOR = WORKSPACE / ".worktrees/room-temp-theory-audit/research/paper-direction-audit-2026-11-10/main-claims/review.json"
if not PRIOR.exists():
    PRIOR = ROOT.parent / "main-claims/review.json"


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theory = (SOURCE_ROOT / "organized/03-理论框架/01-理论框架.md").read_text(encoding="utf-8")
        cls.breakthrough = (SOURCE_ROOT / "organized/06-突破详解/01-2025年10月突破.md").read_text(encoding="utf-8")
        cls.prior = json.loads(PRIOR.read_text(encoding="utf-8"))

    def test_independent_proof_debt_counts(self):
        admits = re.findall(r"^\s*admit\b", self.theory, flags=re.MULTILINE)
        sorries = re.findall(r"^\s*sorry\b", self.theory, flags=re.MULTILINE)
        self.assertEqual(len(admits), 17)
        self.assertEqual(len(sorries), 5)
        self.assertEqual(len(admits) + len(sorries), 22)

    def test_theory_is_explicit_draft_not_machine_verification(self):
        self.assertIn("0.1-alpha", self.theory)
        self.assertIn("理论框架草案", self.theory)
        self.assertIn("∃ (params : MicroscopicParameters)", self.theory)
        self.assertIn("∀ (mat : Material)", self.theory)
        self.assertIn("确保文档在 Lean 4 中可编译通过", self.theory)

    def test_breakthrough_claims_and_date(self):
        self.assertIn("298-316 K", self.breakthrough)
        self.assertIn("13次独立实验", self.breakthrough)
        self.assertIn("P6/mmm (准二维", self.breakthrough)
        self.assertIn("完美验证论文核心定理", self.breakthrough)
        self.assertIn("**文档生成时间**: 2025-04-19", self.breakthrough)
        self.assertIn("2025年10月", self.breakthrough)
        self.assertLess("2025-04-19", "2025-10-01")
        self.assertLess(298, 300)

    def test_prior_positive_and_negative_experimental_roles(self):
        song = self.prior["evidence"]["song"]
        semenok = self.prior["evidence"]["semenok"]
        self.assertEqual(song["onset_tc_k"], [271, 298])
        self.assertEqual(song["reproducible_runs_reported"], 13)
        self.assertFalse(song["peer_review_established"])
        self.assertFalse(song["independent_positive_replication"])
        self.assertFalse(song["direct_meissner_completed"])
        self.assertEqual(semenok["unsuccessful_attempts"], 7)
        self.assertIn("不是对 Song 或整个材料族的最终否证", semenok["evidence_role"])

    def test_pnas_is_prediction_not_experiment(self):
        pnas = self.prior["evidence"]["pnas_prediction"]
        self.assertEqual(pnas["role"], "2024 理论预测")
        self.assertEqual([row["maximum_tc_k"] for row in pnas["predictions"]], [316, 331])
        self.assertEqual([row["pressure_gpa"] for row in pnas["predictions"]], [167, 250])

    def test_critical_anchor_recompute_and_scope(self):
        critical = self.prior["evidence"]["critical_manifold"]
        anchor = critical["temperature_anchors"][0]
        lam = anchor["lambda"]
        mu = anchor["mu_star"]
        omega = anchor["omega_log_meV"]
        exponent = -1.04 * (1 + lam) / (lam - mu * (1 + 0.62 * lam))
        recomputed = critical["K_per_meV"] * omega / critical["denominator_temperature"] * math.exp(exponent)
        self.assertAlmostEqual(recomputed, anchor["tc_K"])
        self.assertLess(recomputed, 300)
        self.assertFalse(critical["full_eliashberg_theory_refuted"])
        self.assertFalse(critical["material_prediction"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
