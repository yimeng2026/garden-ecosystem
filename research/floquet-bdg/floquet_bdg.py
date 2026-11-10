"""Finite quadratic Kitaev-chain Floquet calculations in a Majorana basis.

Conventions follow H = -γ(c†_j c_(j+1)+h.c.) - μ(2n_j-1)
+ Δ(c_j c_(j+1)+h.c.), with H = i Σ K_rs Γ_r Γ_s and ℏ=1.
No interactions, dissipation, self-consistent pairing or material Tc model.
"""

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm


@dataclass(frozen=True)
class ModelParameters:
    gamma: float = 1.0
    delta: float = 1.0
    mu0: float = 2.5
    mu1: float = 0.2
    omega: float = 7.0


def majorana_k(n, mu, gamma=1.0, delta=1.0):
    """Return the real antisymmetric quadratic generator in (a_j,b_j) order."""
    if not isinstance(n, (int, np.integer)) or n < 2:
        raise ValueError("n must be an integer >= 2")
    k = np.zeros((2 * n, 2 * n), dtype=float)

    def antisymmetric(i, j, value):
        k[i, j] += value
        k[j, i] -= value

    for j in range(n):
        antisymmetric(2 * j, 2 * j + 1, -float(mu))
    for j in range(n - 1):
        antisymmetric(2 * j, 2 * (j + 1) + 1, (delta - gamma) / 2)
        antisymmetric(2 * (j + 1), 2 * j + 1, -(delta + gamma) / 2)
    return k


def static_null_vectors(n):
    """Exact uncoupled a_1 and b_N vectors at μ=0 and γ=Δ."""
    left = np.zeros(2 * n)
    right = np.zeros(2 * n)
    left[0] = 1.0
    right[-1] = 1.0
    return left, right


def kicked_floquet(n, mu0, mu1, omega, gamma=1.0, delta=1.0):
    """Symmetric exact free/kick/free Floquet operator; no Fourier cutoff."""
    if omega <= 0:
        raise ValueError("omega must be positive")
    period = 2 * np.pi / omega
    free = expm(-4 * majorana_k(n, mu0, gamma, delta) * period)
    # μ1 multiplies δ(t), so only the onsite matrix enters, without T.
    half_kick = expm(-2 * majorana_k(n, mu1, gamma=0.0, delta=0.0))
    return half_kick @ free @ half_kick, float(period)


def endpoint_mode_counts(mu0, mu1, gamma, omega):
    """Analytic p0/pπ for μ0>γ>0 and 0<μ1<π/2 only."""
    if not (mu0 > gamma > 0 and 0 < mu1 < np.pi / 2 and omega > 0):
        raise ValueError("This restricted endpoint formula is outside its implemented domain")
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
        "domain": "mu0>gamma>0 and 0<mu1<pi/2; integers strictly between b0 and b_pi",
    }


def quasienergy_spectrum(u, period):
    """Diagonalize U; phase is arg(λ) mod 2π and ε=-phase/T modulo 2π/T."""
    eigenvalues, eigenvectors = np.linalg.eig(u)
    phase = np.mod(np.angle(eigenvalues), 2 * np.pi)
    order = np.argsort(phase)
    return {
        "eigenvalues": eigenvalues[order],
        "eigenvectors": eigenvectors[:, order],
        "phase": phase[order],
        "quasienergy": -phase[order] / period,
        "period": period,
    }


def site_weights(eigenvectors, n):
    """Sum Majorana a/b probabilities per site, normalized for every eigenvector."""
    if eigenvectors.shape[0] != 2 * n:
        raise ValueError("Eigenvector dimension does not match n")
    probability = np.abs(eigenvectors) ** 2
    per_site = probability.reshape((n, 2, eigenvectors.shape[1])).sum(axis=1)
    norms = per_site.sum(axis=0, keepdims=True)
    if np.any(norms <= 0):
        raise ValueError("Encountered an eigenvector with zero norm")
    return per_site / norms


def candidate_modes(spectrum, n, target, edge_fraction=0.1):
    """Nearest two λ candidates plus independent localization and bulk separation."""
    if target not in (1.0, -1.0):
        raise ValueError("Only Floquet zero (+1) and pi (-1) targets are supported")
    distances = np.abs(spectrum["eigenvalues"] - target)
    indices = np.argsort(distances)[:2]
    bulk_distance = float(np.sort(distances)[2])
    if bulk_distance <= 0:
        raise ValueError("Cannot separate candidates from a degenerate bulk target")
    weights = site_weights(spectrum["eigenvectors"], n)
    edge_sites = max(1, int(np.ceil(edge_fraction * n)))
    edge_indices = np.r_[np.arange(edge_sites), np.arange(n - edge_sites, n)]
    edge_weights = weights[edge_indices][:, indices].sum(axis=0)
    return {
        "target": target,
        "indices": [int(i) for i in indices],
        "eigenvalues": spectrum["eigenvalues"][indices],
        "distances": distances[indices],
        "bulk_distance": bulk_distance,
        "separation_ratios": distances[indices] / bulk_distance,
        "edge_weights": edge_weights,
        "left_weights": weights[:edge_sites][:, indices].sum(axis=0),
        "right_weights": weights[n - edge_sites :][:, indices].sum(axis=0),
        "edge_sites_per_end": edge_sites,
        "localized": edge_weights > 0.5,
        "separated": distances[indices] / bulk_distance < 0.1,
    }
