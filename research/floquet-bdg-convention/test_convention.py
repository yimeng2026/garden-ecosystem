"""Physical convention contracts for the corrected Majorana implementation."""

import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from convention_model import kicked_floquet, majorana_k, static_null_vectors  # noqa: E402
from fock_reference import (  # noqa: E402
    fermion_operators,
    fock_hamiltonian,
    heisenberg_majorana,
    majorana_fock_hamiltonian,
    majorana_operators,
)


class ConventionTests(unittest.TestCase):
    def test_single_site_fock_time_evolution(self):
        mu, time = 0.37, 0.41
        k = majorana_k(1, mu)
        u = expm(-4 * k * time)
        expected = np.array([[np.cos(2 * mu * time), np.sin(2 * mu * time)], [-np.sin(2 * mu * time), np.cos(2 * mu * time)]])
        np.testing.assert_allclose(u, expected, atol=1e-13)
        c = fermion_operators(1)
        gammas = majorana_operators(c)
        direct = heisenberg_majorana(fock_hamiltonian(c, mu, 0, 0), gammas, time)
        for column in range(2):
            transported = sum((u[row, column] * gammas[row] for row in range(2)), start=np.zeros((2, 2), dtype=complex))
            np.testing.assert_allclose(direct[column], transported, atol=1e-12)

    def test_two_site_fock_matrix_matches_every_element(self):
        mu, gamma, delta = 0.37, 0.81, 0.53
        c = fermion_operators(2)
        gammas = majorana_operators(c)
        reference = fock_hamiltonian(c, mu, gamma, delta)
        represented = majorana_fock_hamiltonian(majorana_k(2, mu, gamma, delta), gammas)
        np.testing.assert_allclose(reference, represented, atol=2e-13)
        self.assertGreater(np.linalg.norm(reference), 1.0)

    def test_generator_is_antisymmetric_and_static_null_space_survives(self):
        for n in (4, 12):
            k = majorana_k(n, 0.0)
            np.testing.assert_allclose(k, -k.T, atol=0)
            for vector in static_null_vectors(n):
                np.testing.assert_allclose(k @ vector, np.zeros(2 * n), atol=1e-15)

    def test_kicked_floquet_is_real_orthogonal(self):
        u, period = kicked_floquet(10, 2.5, 0.2, 7.0)
        self.assertTrue(np.isrealobj(u))
        np.testing.assert_allclose(u.T @ u, np.eye(20), atol=2e-13)
        self.assertAlmostEqual(period, 2 * np.pi / 7)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
