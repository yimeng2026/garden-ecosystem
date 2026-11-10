"""Fail-closed contracts for twisted-boundary Floquet dynamical winding."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))

from convention_model import majorana_k  # noqa: E402
from tbc_model import (  # noqa: E402
    chiral,
    floquet_gap,
    step_evolution,
    twisted_majorana_k,
)


class TBCStructureTests(unittest.TestCase):
    def test_chiral_and_tbc(self):
        n, theta = 8, 0.371
        s = chiral(n)
        k = twisted_majorana_k(np.full(n, 2.5), theta)
        self.assertLess(np.max(np.abs(s @ s - np.eye(2 * n))), 1e-13)
        self.assertLess(np.max(np.abs(s @ k @ s + k)), 1e-13)
        self.assertLess(np.max(np.abs(k.conj().T + k)), 1e-13)
        np.testing.assert_allclose(
            k,
            twisted_majorana_k(np.full(n, 2.5), theta + 2 * np.pi),
            atol=1e-13,
        )
        expected_ring = majorana_k(n, 2.5)
        expected_ring[2 * (n - 1), 1] = 0.0
        expected_ring[1, 2 * (n - 1)] = 0.0
        expected_ring[0, 2 * (n - 1) + 1] = -0.5
        expected_ring[2 * (n - 1) + 1, 0] = 0.5
        np.testing.assert_allclose(
            twisted_majorana_k(np.full(n, 2.5), 0.0).real,
            expected_ring,
            atol=1e-14,
        )

    def test_disordered_onsite_terms_and_chiral(self):
        n = 8
        mu = np.linspace(2.3, 2.7, n)
        k = twisted_majorana_k(mu, -0.731)
        self.assertLess(np.max(np.abs(chiral(n) @ k @ chiral(n) + k)), 1e-13)
        for j, value in enumerate(mu):
            self.assertAlmostEqual(k[2 * j, 2 * j + 1].real, -value / 2)
            self.assertAlmostEqual(k[2 * j, 2 * j + 1].imag, 0.0)

    def test_step_origin_and_unitarity(self):
        n = 8
        k0 = twisted_majorana_k(np.full(n, 2.5), 0.371)
        k1 = twisted_majorana_k(np.full(n, 0.2), 0.371, gamma=0.0, delta=0.0)
        period = 2 * np.pi / 7
        np.testing.assert_allclose(
            step_evolution(k0, k1, period, 0.0), np.eye(2 * n), atol=1e-14
        )
        u = step_evolution(k0, k1, period, period)
        self.assertLess(np.max(np.abs(u.conj().T @ u - np.eye(2 * n))), 1e-11)
        self.assertAlmostEqual(floquet_gap(u, 0.0), float(np.min(np.abs(np.linalg.eigvals(u) - 1))))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
