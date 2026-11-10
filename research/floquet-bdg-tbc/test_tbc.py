"""Fail-closed contracts for twisted-boundary Floquet dynamical winding."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))

from convention_model import majorana_k  # noqa: E402
from run_tbc import run_clean  # noqa: E402
from tbc_model import (  # noqa: E402
    chiral,
    chiral_blocks,
    floquet_gap,
    periodized,
    step_evolution,
    twisted_majorana_k,
    winding_convergence,
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


class TBCPeriodizationTests(unittest.TestCase):
    @staticmethod
    def propagator(n, mu0, mu1, omega, theta, time):
        period = 2 * np.pi / omega
        k0 = twisted_majorana_k(np.full(n, mu0), theta)
        k1 = twisted_majorana_k(
            np.full(n, mu1), theta, gamma=0.0, delta=0.0
        )
        return step_evolution(k0, k1, period, time), period

    def test_endpoint_and_half_period_chiral_blocks(self):
        n = 8
        u_t, period = self.propagator(n, 0.0, 0.0, 7.0, 0.371, 0.0)
        u_step, _ = self.propagator(n, 0.0, 0.0, 7.0, 0.371, period)
        for epsilon in (0.0, np.pi):
            for time in (0.0, period):
                step, _ = self.propagator(n, 0.0, 0.0, 7.0, 0.371, time)
                result = periodized(step, u_step, period, time, epsilon)
                self.assertEqual(result["status"], "ok")
                np.testing.assert_allclose(result["u"], np.eye(2 * n), atol=1e-10)
            half, _ = self.propagator(n, 0.0, 0.0, 7.0, 0.371, period / 2)
            result = periodized(half, u_step, period, period / 2, epsilon)
            self.assertEqual(result["status"], "ok")
            blocks = chiral_blocks(result["u"], epsilon)
            self.assertEqual(blocks["status"], "ok")
            self.assertLess(blocks["symmetry_error"], 1e-10)
            self.assertLess(blocks["max_condition"], 1e12)
            self.assertLess(np.max(np.abs(result["u"].conj().T @ result["u"] - np.eye(2 * n))), 1e-10)

    def test_zero_kick_zero_gap_is_rejected(self):
        n = 8
        u_step, period = self.propagator(n, 2.5, 0.0, 7.0, 0.0, 2 * np.pi / 7)
        result = periodized(u_step, u_step, period, period / 2, 0.0)
        self.assertEqual(result["status"], "gapless_or_undefined")
        self.assertIsNone(result["value"])
        self.assertLessEqual(result["bulk_gap"], 1e-8)
        self.assertEqual(result["reason"], "bulk_gap_closed")
        pi_result = periodized(u_step, u_step, period, period / 2, np.pi)
        self.assertEqual(pi_result["status"], "ok")
        self.assertLess(pi_result["unitarity_error"], 1e-10)


class TBCStaticWindingTests(unittest.TestCase):
    @staticmethod
    def parameters(mu0, omega, n=40):
        return {
            "n": n,
            "mu0": np.full(n, mu0),
            "mu1": np.zeros(n),
            "omega": omega,
            "gamma": 1.0,
            "delta": 1.0,
        }

    def assert_quantized(self, result, expected):
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["nearest_integer"], expected)
        self.assertLess(result["mesh_difference"], 1e-3)
        self.assertLess(result["integer_residual"], 1e-3)

    def test_static_topological_zero_and_pi(self):
        parameters = self.parameters(0.0, 7.0)
        self.assert_quantized(winding_convergence(parameters, 0.0), 1)
        self.assert_quantized(winding_convergence(parameters, np.pi), 0)

    def test_static_trivial_two_gap_control(self):
        parameters = self.parameters(2.5, 17.0)
        self.assert_quantized(winding_convergence(parameters, 0.0), 0)
        self.assert_quantized(winding_convergence(parameters, np.pi), 0)

    def test_static_trivial_zero_gap_is_undefined(self):
        result = winding_convergence(self.parameters(2.5, 7.0), 0.0)
        self.assertEqual(result["status"], "gapless_or_undefined")
        self.assertIsNone(result["nearest_integer"])
        self.assertLessEqual(result["min_bulk_gap"], 1e-8)


class TBCCleanBaselineTests(unittest.TestCase):
    def test_clean_kicked_matches_existing_endpoint_counts(self):
        result = run_clean(n=40, nominal_steps=(0.05, 0.025))
        self.assertEqual(result["reference"], {"p0": 1, "p_pi": 1})
        self.assertEqual(result["zero"]["status"], "ok")
        self.assertEqual(result["pi"]["status"], "ok")
        self.assertEqual(result["zero"]["nearest_integer"], result["reference"]["p0"])
        self.assertEqual(result["pi"]["nearest_integer"], result["reference"]["p_pi"])
        self.assertTrue(result["passed"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
