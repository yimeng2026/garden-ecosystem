"""Diagnostic only: expose periodization branch and finite-ring gap failures."""

import numpy as np
from scipy.linalg import expm

from tbc_model import chiral, periodized, step_evolution, twisted_majorana_k


def static_case(mu, omega, theta, n=8):
    period = 2 * np.pi / omega
    k0 = twisted_majorana_k(np.full(n, mu), theta)
    k1 = np.zeros_like(k0)
    step = step_evolution(k0, k1, period, period)
    half = step_evolution(k0, k1, period, period / 2)
    values, vectors = np.linalg.eig(step)
    print(f"mu={mu} omega={omega} theta={theta} n={n}")
    print("eigenvalue_distances", {str(e): float(np.min(np.abs(values - np.exp(1j * e)))) for e in (0.0, np.pi)})
    print("eigenvector_condition", float(np.linalg.cond(vectors)))
    s = chiral(n)
    for epsilon in (0.0, np.pi):
        result = periodized(half, step, period, period / 2, epsilon)
        print("branch", epsilon, "status", result["status"], "gap", result["bulk_gap"])
        if result["status"] == "ok":
            sign = -1 if epsilon == 0 else 1
            print("symmetry_error", float(np.max(np.abs(s @ result["u"] @ s - sign * result["u"]))))
            print("diag_norms", float(np.max(np.abs(result["u"][0::2, 0::2]))), float(np.max(np.abs(result["u"][1::2, 1::2]))))
        else:
            print("unitarity_error", result.get("unitarity_error"))
    print("direct_expm_unitarity", float(np.max(np.abs(step.conj().T @ step - np.eye(2 * n)))))


if __name__ == "__main__":
    static_case(0.0, 7.0, 0.371)
    static_case(2.5, 7.0, 0.0)
