"""Regression checks for the explicitly unvalidated DEE diagnostic."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from convention_model import majorana_k  # noqa: E402
from fock_reference import fermion_operators, fock_hamiltonian, majorana_operators  # noqa: E402
from probe_dee import correlation  # noqa: E402
from probe_fock_dee import dee, site_entropy  # noqa: E402


class DEE_Diagnostics(unittest.TestCase):
    def test_negative_status_is_explicit(self):
        text = (ROOT / "DEE_DIAGNOSTIC.md").read_text(encoding="utf-8")
        self.assertIn("method_not_validated", text)
        self.assertIn("不能用于宣称候选受到拓扑保护", text)

    def test_two_site_fock_ground_matches_sign_correlation(self):
        c = fermion_operators(2)
        h = fock_hamiltonian(c, 0.5, 1.0, 1.0)
        _, vectors = np.linalg.eigh(h)
        psi = vectors[:, 0]
        gammas = majorana_operators(c)
        direct = np.array([[psi.conj() @ (gammas[m] @ gammas[n]) @ psi for n in range(4)] for m in range(4)])
        np.testing.assert_allclose(direct, correlation(majorana_k(2, 0.5)), atol=1e-12)

    def test_partition_complement_is_right_middle_quarter(self):
        n = 8
        a = np.arange(n // 2)
        overlap = np.arange(n // 4, n // 2)
        right = np.arange(3 * n // 4, n)
        b = np.r_[overlap, right]
        union = np.unique(np.r_[a, b])
        self.assertEqual(overlap.tolist(), np.intersect1d(a, b).tolist())
        self.assertEqual(np.setdiff1d(np.arange(n), union).tolist(), [4, 5])

    def test_full_fock_negative_regression_is_preserved(self):
        n = 8
        c = fermion_operators(n)
        h = fock_hamiltonian(c, 0.5, 1.0, 1.0)
        _, vectors = np.linalg.eigh(h)
        psi = vectors[:, 0]
        self.assertAlmostEqual(dee(psi, n), 0.014057209514146796, places=12)
        self.assertAlmostEqual(site_entropy(psi, n, [0]), 0.5687362834145154, delta=1e-6)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
