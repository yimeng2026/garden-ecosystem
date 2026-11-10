"""Chemical-potential-kick disorder on the Fock-corrected Kitaev model."""

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-localization"))
from convention_model import candidate_modes, majorana_k, quasienergy_spectrum  # noqa: E402
from localization_analysis import subspace_metrics  # noqa: E402


def beta_sequence(seed, n, max_size=320):
    if not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if not 1 <= n <= max_size:
        raise ValueError("n is outside the shared sequence domain")
    return np.random.default_rng(20261111 + int(seed)).random(max_size)[:n]


def chemical_kick(amplitudes):
    """Exact half-kick for each onsite μ_n; no matrix-exponential approximation."""
    amplitudes = np.asarray(amplitudes, dtype=float)
    if amplitudes.ndim != 1 or len(amplitudes) == 0:
        raise ValueError("amplitudes must be a nonempty one-dimensional array")
    n = len(amplitudes)
    kick = np.zeros((2 * n, 2 * n))
    cosine = np.cos(amplitudes)
    sine = np.sin(amplitudes)
    kick[0::2, 0::2] = np.diag(cosine)
    kick[1::2, 1::2] = np.diag(cosine)
    kick[0::2, 1::2] = np.diag(sine)
    kick[1::2, 0::2] = np.diag(-sine)
    return kick


def disordered_floquet(n, mu0, beta, strength, omega, gamma=1.0, delta=1.0):
    beta = np.asarray(beta, dtype=float)
    if beta.shape != (n,):
        raise ValueError("beta dimension does not match n")
    if strength < 0 or omega <= 0:
        raise ValueError("strength must be nonnegative and omega positive")
    period = 2 * np.pi / omega
    free = expm(-4 * majorana_k(n, mu0, gamma, delta) * period)
    kick = chemical_kick(strength * beta)
    return kick @ free @ kick, float(period)


def observe_candidate(spectrum, n, target):
    candidate = candidate_modes(spectrum, n, target)
    distances = np.abs(spectrum["eigenvalues"] - target)
    indices = candidate["indices"]
    second_indices = np.argsort(distances)[2:4]
    metrics = subspace_metrics(spectrum["eigenvectors"][:, indices], n)
    second_metrics = subspace_metrics(spectrum["eigenvectors"][:, second_indices], n)
    profile = metrics["profile"]
    edge_sites = max(1, int(np.ceil(0.1 * n)))
    edge_indices = np.r_[np.arange(edge_sites), np.arange(n - edge_sites, n)]
    edge_weight = float(profile[edge_indices].sum())
    separation = float(max(candidate["separation_ratios"]))
    return {
        "eigenvalues_real": [float(spectrum["eigenvalues"][i].real) for i in indices],
        "eigenvalues_imag": [float(spectrum["eigenvalues"][i].imag) for i in indices],
        "distances": [float(value) for value in candidate["distances"]],
        "separation_ratios": [float(value) for value in candidate["separation_ratios"]],
        "edge_weight": edge_weight,
        "subspace_ipr": metrics["subspace_ipr"],
        "second_pair_subspace_ipr": second_metrics["subspace_ipr"],
        "joint_pass": bool(separation < 0.1 and edge_weight > 0.5),
        "profile": profile,
    }
