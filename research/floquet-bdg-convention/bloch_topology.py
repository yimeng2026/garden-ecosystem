"""Branch-aware Bloch Floquet topology for the Fock-checked Kitaev convention."""

import numpy as np
from scipy.linalg import expm, logm

TAU_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
TAU_Z = np.diag([1, -1]).astype(complex)


class FloquetGapError(ValueError):
    pass


def bloch_h(k, mu0, gamma, delta):
    return 2 * (-gamma * np.cos(k) - mu0) * TAU_Z + 2 * delta * np.sin(k) * TAU_Y


def bloch_floquet(k, mu0, mu1, omega, gamma, delta):
    if omega <= 0:
        raise ValueError("omega must be positive")
    period = 2 * np.pi / omega
    free = expm(-1j * bloch_h(k, mu0, gamma, delta) * period)
    half_kick = expm(1j * mu1 * TAU_Z)
    return half_kick @ free @ half_kick


def endpoint_counts(mu0, mu1, omega, gamma, delta=None):
    if not (mu0 > gamma > 0 and 0 < mu1 < np.pi / 2 and omega > 0):
        raise ValueError("Restricted endpoint formula outside its implemented domain")
    b0 = 4 * (mu0 - gamma) / omega + 2 * mu1 / np.pi
    b_pi = 4 * (mu0 + gamma) / omega + 2 * mu1 / np.pi
    low, high = sorted((b0, b_pi))
    integers = list(range(int(np.floor(low)) + 1, int(np.ceil(high))))
    return {
        "b0": float(b0),
        "b_pi": float(b_pi),
        "even_integers": [n for n in integers if n % 2 == 0],
        "odd_integers": [n for n in integers if n % 2 == 1],
        "p0": sum(n % 2 == 0 for n in integers),
        "p_pi": sum(n % 2 == 1 for n in integers),
    }


def effective_vector(u, gap_tolerance=1e-8):
    np.testing.assert_allclose(u.conj().T @ u, np.eye(2), atol=1e-10)
    trace_half = np.trace(u) / 2
    if abs(trace_half.imag) > 1e-10:
        raise FloquetGapError("SU(2) trace is not real within tolerance")
    cos_phi = float(np.clip(trace_half.real, -1, 1))
    phi = float(np.arccos(cos_phi))
    sin_phi = float(np.sin(phi))
    if sin_phi <= gap_tolerance:
        raise FloquetGapError("U is too close to ±I; effective direction is undefined")
    n_y = float(((u[1, 0] - u[0, 1]) / (2 * sin_phi)).real)
    n_z_complex = (u[1, 1] - u[0, 0]) / (2j * sin_phi)
    if abs(n_z_complex.imag) > 1e-10:
        raise FloquetGapError("Effective n_z is not real within tolerance")
    n_z = float(n_z_complex.real)
    reconstruction = cos_phi * np.eye(2) - 1j * sin_phi * (n_y * TAU_Y + n_z * TAU_Z)
    if not np.allclose(reconstruction, u, atol=2e-10):
        raise FloquetGapError("Effective vector does not reconstruct U")
    return {"phi": phi, "sin_phi": sin_phi, "n_y": n_y, "n_z": n_z, "alpha": float(np.arctan2(n_y, n_z)), "reconstruction": reconstruction}


def logm_direction(u):
    h_eff = 1j * logm(u)
    np.testing.assert_allclose(h_eff, h_eff.conj().T, atol=1e-9)
    n_y = float(((h_eff[1, 0] - h_eff[0, 1]) / (2j)).real)
    n_z = float(((h_eff[0, 0] - h_eff[1, 1]) / 2).real)
    norm = float(np.hypot(n_y, n_z))
    if norm < 1e-10:
        raise FloquetGapError("Principal log has undefined direction")
    return {"n_y": n_y / norm, "n_z": n_z / norm, "phi": norm}


def _curve(parameters, nk):
    midpoint_k = -np.pi + 2 * np.pi * (np.arange(nk) + 0.5) / nk
    k_values = np.r_[-np.pi, midpoint_k, np.pi]
    vectors = [effective_vector(bloch_floquet(float(k), **parameters)) for k in k_values]
    alpha = np.unwrap([vector["alpha"] for vector in vectors])
    winding = float((alpha[-1] - alpha[0]) / (2 * np.pi))
    return k_values, vectors, alpha, winding


def winding_convergence(parameters, sizes):
    rows = []
    for nk in sizes:
        k_values, vectors, alpha, winding = _curve(parameters, nk)
        rows.append({
            "nk": nk,
            "winding": winding,
            "nearest_integer": int(np.rint(winding)),
            "min_sin_phi": float(min(vector["sin_phi"] for vector in vectors)),
            "k_values": k_values,
            "alpha_unwrapped": alpha,
            "n_y": np.array([vector["n_y"] for vector in vectors]),
            "n_z": np.array([vector["n_z"] for vector in vectors]),
        })
    return rows
