"""Twisted-boundary propagation on the Fock-checked Majorana Kitaev model."""

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from convention_model import majorana_k  # noqa: E402


GAP_TOLERANCE = 1e-8
CONDITION_LIMIT = 1e12


def _onsite_parameters(mu, n=None):
    values = np.asarray(mu, dtype=float)
    if values.ndim == 0:
        if n is None:
            raise ValueError("n is required for a scalar chemical potential")
        values = np.full(n, float(values))
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError("mu must be a finite scalar or a vector with at least two sites")
    if n is not None and len(values) != n:
        raise ValueError("mu length does not match n")
    return values


def chiral(n):
    """S=diag(-1,+1,...) in (a1,b1,...,aN,bN) order."""
    if not isinstance(n, (int, np.integer)) or n < 2:
        raise ValueError("n must be an integer >= 2")
    s = np.ones(2 * n)
    s[0::2] = -1.0
    return np.diag(s)


def twisted_majorana_k(mu, theta, gamma=1.0, delta=1.0, n=None):
    """Complex anti-Hermitian ring matrix with the twist on only the N->1 bond."""
    values = _onsite_parameters(mu, n)
    n = len(values)
    if not np.isfinite(theta) or not np.isfinite(gamma) or not np.isfinite(delta):
        raise ValueError("theta, gamma, and delta must be finite")
    k = np.asarray(majorana_k(n, 0.0, gamma, delta), dtype=complex)
    for j, onsite in enumerate(values):
        k[2 * j, 2 * j + 1] = -onsite / 2
        k[2 * j + 1, 2 * j] = onsite / 2
    phase = np.exp(1j * float(theta))

    def phased_bond(row, column, value):
        k[row, column] += phase * value
        k[column, row] -= np.conj(phase) * value

    phased_bond(2 * (n - 1), 1, (delta - gamma) / 4)
    phased_bond(0, 2 * (n - 1) + 1, -(delta + gamma) / 4)
    return k


def step_evolution(k0, k1, period, time):
    """Symmetric kicked time frame with time-ordered partial propagation.

    H=expm(-2 K1) is the half kick. For 0<t<T, U_step(t)=F(t)H;
    at the period endpoint, U_step(T)=H F(T)H. U_step(0)=I is the
    explicit reference-point definition across the endpoint kick.
    """
    k0, k1 = np.asarray(k0, dtype=complex), np.asarray(k1, dtype=complex)
    if k0.ndim != 2 or k0.shape[0] != k0.shape[1] or k1.shape != k0.shape:
        raise ValueError("k0 and k1 must be equal-sized square matrices")
    if not np.isfinite(period) or period <= 0 or not 0 <= time <= period:
        raise ValueError("require period > 0 and 0 <= time <= period")
    if time == 0:
        return np.eye(k0.shape[0], dtype=complex)
    half_kick = expm(-2 * k1)
    if time == period:
        return half_kick @ expm(-4 * k0 * period) @ half_kick
    return expm(-4 * k0 * time) @ half_kick


def free_evolution(k0, time, method="expm"):
    """Compute exp(-4 K0 time), optionally using the Hermitian iK eigensystem."""
    from scipy.linalg import eigh

    k0 = np.asarray(k0, dtype=complex)
    if k0.ndim != 2 or k0.shape[0] != k0.shape[1] or not np.isfinite(time):
        raise ValueError("k0 must be square and time finite")
    if method == "expm":
        return expm(-4 * k0 * time)
    if method != "eigh":
        raise ValueError("free evolution method must be expm or eigh")
    hermitian = 1j * k0
    if np.max(np.abs(hermitian - hermitian.conj().T)) > 1e-10:
        raise ValueError("iK is not Hermitian within tolerance")
    energies, vectors = eigh(hermitian)
    # K=-i(iK), hence exp(-4Kt)=Q exp(+4iEt)Q†.
    u = (vectors * np.exp(4j * energies * time)) @ vectors.conj().T
    if np.max(np.abs(u.conj().T @ u - np.eye(len(u)))) > 1e-10:
        raise RuntimeError("Hermitian free-evolution reconstruction is not unitary")
    return u


def floquet_gap(u, epsilon):
    """Minimum unit-circle distance to the requested 0 or pi gap."""
    if not np.isclose(epsilon, 0.0, atol=0, rtol=0) and not np.isclose(
        epsilon, np.pi, atol=0, rtol=0
    ):
        raise ValueError("epsilon must be exactly 0 or pi")
    return float(np.min(np.abs(np.linalg.eigvals(u) - np.exp(1j * epsilon))))


def periodized(u_step_t, u_step_T, period, time, epsilon, gap_tolerance=GAP_TOLERANCE):
    """Endpoint- and chiral-consistent spectral periodization using a unitary Schur basis."""
    from scipy.linalg import schur

    if epsilon not in (0.0, np.pi):
        raise ValueError("epsilon must be exactly 0 or pi")
    if period <= 0 or not 0 <= time <= period:
        raise ValueError("require period > 0 and 0 <= time <= period")
    triangular, vectors = schur(u_step_T, output="complex")
    values = np.diag(triangular)
    normality_error = float(np.max(np.abs(triangular - np.diag(values))))
    if normality_error > 1e-9:
        return {
            "status": "nonnormal_schur",
            "reason": "unitary_schur_not_diagonal",
            "normality_error": normality_error,
            "value": None,
        }
    gap = float(np.min(np.abs(values - np.exp(1j * epsilon))))
    if gap <= gap_tolerance:
        return {
            "status": "gapless_or_undefined",
            "reason": "bulk_gap_closed",
            "bulk_gap": gap,
            "value": None,
        }
    phi = -np.angle(values)
    # The conduction -2pi shift is essential: statically U_0(T/2)=sign(H)
    # and U_pi(T/2)=-I, rather than I and sign(H), respectively.
    phi_eff = np.where(phi < 0, 2 * epsilon - np.abs(phi), np.abs(phi) - 2 * np.pi)
    factors = np.exp(1j * phi_eff * time / period)
    power = (vectors * factors) @ vectors.conj().T
    u_epsilon = np.asarray(u_step_t, dtype=complex) @ power
    unitarity_error = float(
        np.max(np.abs(u_epsilon.conj().T @ u_epsilon - np.eye(len(u_epsilon))))
    )
    if unitarity_error > 1e-9:
        return {
            "status": "nonunitary",
            "reason": "periodized_unitarity_failed",
            "bulk_gap": gap,
            "unitarity_error": unitarity_error,
            "value": None,
        }
    return {
        "status": "ok",
        "u": u_epsilon,
        "bulk_gap": gap,
        "unitarity_error": unitarity_error,
        "normality_error": normality_error,
        "phi": phi,
        "phi_eff": phi_eff,
        "value": u_epsilon,
    }


def chiral_blocks(u_half, epsilon, condition_limit=CONDITION_LIMIT):
    """Extract +/- blocks directly from interleaved Majorana chiral sectors."""
    u = np.asarray(u_half, dtype=complex)
    if u.ndim != 2 or u.shape[0] != u.shape[1] or u.shape[0] % 2:
        raise ValueError("u_half must be an even-dimensional square matrix")
    if epsilon not in (0.0, np.pi):
        raise ValueError("epsilon must be exactly 0 or pi")
    negative, positive = np.arange(0, len(u), 2), np.arange(1, len(u), 2)
    s = np.diag(np.where(np.arange(len(u)) % 2 == 0, -1.0, 1.0))
    sign = -1.0 if epsilon == 0.0 else 1.0
    symmetry_error = float(np.max(np.abs(s @ u @ s - sign * u)))
    if epsilon == 0.0:
        blocks = {
            "plus": u[np.ix_(negative, positive)],
            "minus": u[np.ix_(positive, negative)],
        }
    else:
        blocks = {
            "plus": u[np.ix_(negative, negative)],
            "minus": u[np.ix_(positive, positive)],
        }
    conditions = {name: float(np.linalg.cond(block)) for name, block in blocks.items()}
    max_condition = max(conditions.values())
    result = {
        "symmetry_error": symmetry_error,
        "conditions": conditions,
        "max_condition": max_condition,
        "value": None,
    }
    if symmetry_error > 1e-9:
        return dict(result, status="invalid_chiral_block", reason="half_period_chiral_failed")
    if not np.isfinite(max_condition) or max_condition > condition_limit:
        return dict(result, status="singular_chiral_block", reason="block_condition_failed")
    return dict(result, status="ok", blocks=blocks, value=blocks)


def _parameters(parameters):
    required = {"n", "mu0", "mu1", "omega", "gamma", "delta"}
    if set(parameters) != required:
        raise ValueError(f"parameters must contain exactly {sorted(required)}")
    n = parameters["n"]
    mu0 = _onsite_parameters(parameters["mu0"], n)
    mu1 = _onsite_parameters(parameters["mu1"], n)
    omega, gamma, delta = (float(parameters[key]) for key in ("omega", "gamma", "delta"))
    if omega <= 0 or not np.isfinite([omega, gamma, delta]).all():
        raise ValueError("omega must be positive and all couplings finite")
    return n, mu0, mu1, omega, gamma, delta


def winding(parameters, nominal_step, epsilon, branch="plus", keep_curve=False, free_method="expm"):
    """Evaluate one chiral-block winding on a periodic central-difference grid."""
    if branch not in ("plus", "minus"):
        raise ValueError("branch must be plus or minus")
    if nominal_step <= 0:
        raise ValueError("nominal_step must be positive")
    n, mu0, mu1, omega, gamma, delta = _parameters(parameters)
    period = 2 * np.pi / omega
    m = int(round(2 * np.pi / nominal_step))
    if m < 8:
        raise ValueError("theta grid is too coarse for a central difference")
    h = 2 * np.pi / m
    theta_values = -np.pi + h * np.arange(m)
    kick_matrix = twisted_majorana_k(mu1, 0.0, gamma=0.0, delta=0.0)
    half_kick = expm(-2 * kick_matrix)
    blocks = []
    curve = []
    min_gap = np.inf
    max_condition = 0.0
    max_unitarity = 0.0
    max_normality = 0.0
    for theta in theta_values:
        k0 = twisted_majorana_k(mu0, theta, gamma, delta)
        free_half = free_evolution(k0, period / 2, method=free_method)
        u_half = free_half @ half_kick
        u_full = half_kick @ free_half @ free_half @ half_kick
        period_result = periodized(u_half, u_full, period, period / 2, epsilon)
        if period_result["status"] != "ok":
            return {
                "status": period_result["status"],
                "reason": period_result["reason"],
                "failed_theta": float(theta),
                "value": None,
                "nearest_integer": None,
                "min_bulk_gap": float(period_result.get("bulk_gap", np.nan)),
                "nominal_step": float(nominal_step),
                "actual_step": h,
                "points": m,
            }
        block_result = chiral_blocks(period_result["u"], epsilon)
        min_gap = min(min_gap, period_result["bulk_gap"])
        max_unitarity = max(max_unitarity, period_result["unitarity_error"])
        max_normality = max(max_normality, period_result["normality_error"])
        max_condition = max(max_condition, block_result["max_condition"])
        if block_result["status"] != "ok":
            return {
                "status": block_result["status"],
                "reason": block_result["reason"],
                "failed_theta": float(theta),
                "value": None,
                "nearest_integer": None,
                "min_bulk_gap": float(min_gap),
                "max_block_condition": float(max_condition),
                "nominal_step": float(nominal_step),
                "actual_step": h,
                "points": m,
            }
        block = block_result["blocks"][branch]
        blocks.append(block)
        if keep_curve:
            determinant = np.linalg.det(block)
            curve.append({
                "theta": float(theta),
                "bulk_gap": float(period_result["bulk_gap"]),
                "block_condition": float(block_result["conditions"][branch]),
                "determinant_phase": float(np.angle(determinant)),
            })
    array = np.asarray(blocks)
    derivatives = (np.roll(array, -1, axis=0) - np.roll(array, 1, axis=0)) / (2 * h)
    integrand = np.asarray([
        np.trace(np.linalg.solve(block, derivative))
        for block, derivative in zip(array, derivatives)
    ])
    raw = (1j / (2 * np.pi)) * h * np.sum(integrand)
    value = float(abs(raw.real))
    closest = int(round(value))
    residual = float(abs(value - closest))
    quantized = residual < 1e-3
    if keep_curve:
        for row, z in zip(curve, integrand):
            row["integrand_real"] = float(z.real)
            row["integrand_imag"] = float(z.imag)
    return {
        "status": "ok" if quantized else "not_converged",
        "reason": None if quantized else "integer_residual_above_tolerance",
        "value": value,
        "raw_real": float(raw.real),
        "raw_imag": float(raw.imag),
        "nearest_integer": closest if quantized else None,
        "integer_residual": residual,
        "min_bulk_gap": float(min_gap),
        "max_block_condition": float(max_condition),
        "max_unitarity_error": float(max_unitarity),
        "max_normality_error": float(max_normality),
        "nominal_step": float(nominal_step),
        "actual_step": h,
        "points": m,
        "branch": branch,
        "epsilon": float(epsilon),
        "curve": curve if keep_curve else None,
    }


def winding_convergence(parameters, epsilon, nominal_steps=(0.05, 0.025), keep_curve=False, free_method="expm"):
    """Require integer quantization and agreement on exactly two theta grids."""
    if len(nominal_steps) != 2:
        raise ValueError("production winding convergence requires exactly two grids")
    rows = [
        winding(parameters, step, epsilon, keep_curve=keep_curve, free_method=free_method)
        for step in nominal_steps
    ]
    base = {
        "epsilon": float(epsilon),
        "free_method": free_method,
        "rows": rows,
        "value": None,
        "nearest_integer": None,
        "mesh_difference": None,
        "integer_residual": None,
        "min_bulk_gap": min(row["min_bulk_gap"] for row in rows),
    }
    failed = next((row for row in rows if row["status"] != "ok"), None)
    if failed is not None:
        return dict(base, status=failed["status"], reason=failed["reason"], passed=False)
    difference = float(abs(rows[-1]["value"] - rows[0]["value"]))
    residual = float(max(row["integer_residual"] for row in rows))
    nearest = rows[-1]["nearest_integer"]
    if difference >= 1e-3 or nearest != rows[0]["nearest_integer"]:
        return dict(
            base,
            status="not_converged",
            reason="theta_mesh_disagreement",
            value=rows[-1]["value"],
            mesh_difference=difference,
            integer_residual=residual,
            passed=False,
        )
    return dict(
        base,
        status="ok",
        reason=None,
        value=rows[-1]["value"],
        nearest_integer=nearest,
        mesh_difference=difference,
        integer_residual=residual,
        passed=True,
    )
