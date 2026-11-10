"""Contracts for independent Bloch Floquet topology and endpoint invariants."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bloch_topology import (  # noqa: E402
    bloch_floquet,
    effective_vector,
    endpoint_counts,
    logm_direction,
    winding_convergence,
)

PARAMETERS = {"mu0": 2.5, "mu1": 0.2, "omega": 7.0, "gamma": 1.0, "delta": 1.0}


class BlochTopologyTests(unittest.TestCase):
    def test_k0_and_kpi_phases_match_endpoint_quantities(self):
        counts = endpoint_counts(**PARAMETERS)
        self.assertEqual((counts["p0"], counts["p_pi"]), (1, 1))
        # With our negative hopping, k=0 carries b_pi and k=pi carries b0.
        for k, b in ((0.0, counts["b_pi"]), (np.pi, counts["b0"])):
            u = bloch_floquet(k, **PARAMETERS)
            np.testing.assert_allclose(u, np.diag([np.exp(1j * np.pi * b), np.exp(-1j * np.pi * b)]), atol=2e-13)

    def test_effective_vector_reconstructs_unitary(self):
        u = bloch_floquet(0.731, **PARAMETERS)
        vector = effective_vector(u)
        self.assertGreater(vector["sin_phi"], 1e-6)
        np.testing.assert_allclose(vector["reconstruction"], u, atol=2e-13)
        self.assertAlmostEqual(vector["n_y"] ** 2 + vector["n_z"] ** 2, 1.0, places=12)

    def test_logm_matches_branch_free_direction_away_from_gap_closing(self):
        for k in (-0.731, 0.217, 1.13):
            u = bloch_floquet(k, **PARAMETERS)
            vector = effective_vector(u)
            log_vector = logm_direction(u)
            dot = vector["n_y"] * log_vector["n_y"] + vector["n_z"] * log_vector["n_z"]
            self.assertAlmostEqual(dot, 1.0, places=10)

    def test_winding_converges_to_literature_reference_and_control(self):
        rows = winding_convergence(PARAMETERS, [512, 1024, 2048, 4096])
        for row in rows:
            self.assertGreater(row["min_sin_phi"], 1e-6)
            self.assertLess(abs(row["winding"] - row["nearest_integer"]), 1e-6)
            self.assertEqual(abs(row["nearest_integer"]), 2)
        self.assertLess(abs(rows[-1]["winding"] - rows[-2]["winding"]), 1e-6)
        # At omega=7 the undriven mu0=2.5 control is Floquet-gapless at k=0.
        # omega=17 is a gapped trivial control and matches the literature reference.
        control = dict(PARAMETERS, mu1=0.0, omega=17.0)
        control_row = winding_convergence(control, [2048])[0]
        self.assertEqual(control_row["nearest_integer"], 0)
        self.assertLess(abs(control_row["winding"]), 1e-6)
        topological = dict(PARAMETERS, mu0=0.0, mu1=0.0)
        topological_row = winding_convergence(topological, [2048])[0]
        self.assertEqual(abs(topological_row["nearest_integer"]), 1)
        self.assertLess(abs(abs(topological_row["winding"]) - 1), 1e-6)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
