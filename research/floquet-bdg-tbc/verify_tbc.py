"""Independent determinant-phase check; does not call the production winding integrator."""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm, schur

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from convention_model import majorana_k  # noqa: E402


def independent_matrix(mu, theta, gamma, delta):
    mu = np.asarray(mu, dtype=float)
    n = len(mu)
    k = np.asarray(majorana_k(n, 0.0, gamma, delta), dtype=complex)
    for j, value in enumerate(mu):
        k[2 * j, 2 * j + 1] = -value / 2
        k[2 * j + 1, 2 * j] = value / 2
    phase = np.exp(1j * theta)
    for row, column, value in (
        (2 * (n - 1), 1, (delta - gamma) / 4),
        (0, 2 * (n - 1) + 1, -(delta + gamma) / 4),
    ):
        k[row, column] += phase * value
        k[column, row] -= np.conj(phase) * value
    return k


def determinant_winding(n, mu0, mu1, omega, epsilon, nominal_step=0.00625):
    """Reconstruct propagation and use net det(block) phase, not Tr(U^-1 dU)."""
    period = 2 * np.pi / omega
    m = int(round(2 * np.pi / nominal_step))
    h = 2 * np.pi / m
    theta_values = -np.pi + h * np.arange(m)
    half_kick = expm(-2 * independent_matrix(np.full(n, mu1), 0.0, 0.0, 0.0))
    phases, gaps, symmetry_errors, conditions = [], [], [], []
    negative, positive = np.arange(0, 2 * n, 2), np.arange(1, 2 * n, 2)
    s = np.diag(np.where(np.arange(2 * n) % 2 == 0, -1.0, 1.0))
    for theta in theta_values:
        free_half = expm(-2 * independent_matrix(np.full(n, mu0), theta, 1.0, 1.0) * period)
        u_half = free_half @ half_kick
        u_full = half_kick @ free_half @ free_half @ half_kick
        triangular, q = schur(u_full, output="complex")
        values = np.diag(triangular)
        if np.max(np.abs(triangular - np.diag(values))) > 1e-9:
            raise ValueError("Schur diagonalization failed for a unitary propagator")
        gap = float(np.min(np.abs(values - np.exp(1j * epsilon))))
        if gap <= 1e-8:
            raise ValueError("independent check encountered a closed requested gap")
        phi = -np.angle(values)
        phi_eff = np.where(phi < 0, 2 * epsilon - np.abs(phi), np.abs(phi) - 2 * np.pi)
        power = (q * np.exp(1j * phi_eff / 2)) @ q.conj().T
        u = u_half @ power
        sign = -1.0 if epsilon == 0.0 else 1.0
        symmetry_errors.append(float(np.max(np.abs(s @ u @ s - sign * u))))
        if epsilon == 0.0:
            block = u[np.ix_(negative, positive)]
        else:
            block = u[np.ix_(negative, negative)]
        determinant = np.linalg.det(block)
        if abs(determinant) < 1e-14:
            raise ValueError("singular independent chiral block")
        phases.append(np.angle(determinant))
        gaps.append(gap)
        conditions.append(float(np.linalg.cond(block)))
    unwrapped = np.unwrap(np.r_[phases, phases[0]])
    raw = float(-(unwrapped[-1] - unwrapped[0]) / (2 * np.pi))
    value = abs(raw)
    nearest = int(round(value))
    residual = abs(value - nearest)
    passed = (
        max(symmetry_errors) < 1e-9
        and max(conditions) < 1e12
        and residual < 1e-3
    )
    return {
        "status": "ok" if passed else "not_converged",
        "method": "independent Schur reconstruction and unwrapped det(block) phase",
        "nominal_step": nominal_step,
        "actual_step": h,
        "points": m,
        "raw_signed": raw,
        "value": value,
        "nearest_integer": nearest if residual < 1e-3 else None,
        "integer_residual": residual,
        "min_bulk_gap": min(gaps),
        "max_symmetry_error": max(symmetry_errors),
        "max_block_condition": max(conditions),
        "passed": passed,
    }


def main():
    stored = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
    checks = {
        "static_topological_zero": determinant_winding(40, 0.0, 0.0, 7.0, 0.0),
        "static_topological_pi": determinant_winding(40, 0.0, 0.0, 7.0, np.pi),
        "clean_zero_n80": determinant_winding(80, 2.5, 0.2, 7.0, 0.0),
        "clean_pi_n80": determinant_winding(80, 2.5, 0.2, 7.0, np.pi),
    }
    expected = {
        "static_topological_zero": stored["static"]["topological_omega7"]["zero"]["nearest_integer"],
        "static_topological_pi": stored["static"]["topological_omega7"]["pi"]["nearest_integer"],
        "clean_zero_n80": stored["clean"]["zero"]["nearest_integer"],
        "clean_pi_n80": stored["clean"]["pi"]["nearest_integer"],
    }
    comparisons = {
        name: {
            "stored_nearest_integer": expected[name],
            "independent_nearest_integer": row["nearest_integer"],
            "absolute_raw_difference": abs(row["value"] - abs(expected[name])),
            "agrees": row["passed"] and row["nearest_integer"] == expected[name],
        }
        for name, row in checks.items()
    }
    passed = all(row["agrees"] for row in comparisons.values())
    output = {
        "schema": "floquet-bdg-tbc-independent-verification-v1",
        "checks": checks,
        "comparisons": comparisons,
        "passed": passed,
        "scope": "finite quadratic static and clean-kicked baselines; not disorder or thermodynamic-limit proof",
    }
    (ROOT / "independent_verification.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, row in checks.items():
        print(name, json.dumps(row, ensure_ascii=False))
        print("comparison", json.dumps(comparisons[name], ensure_ascii=False))
    print("independent_passed", passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
