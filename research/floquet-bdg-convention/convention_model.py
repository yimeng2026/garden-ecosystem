"""Fock-checked quadratic Kitaev model in (a_j,b_j) Majorana order.

H = -γ(c†_j c_(j+1)+h.c.) - μ(2n_j-1)
    + Δ(c_j c_(j+1)+h.c.), H=iΣK_rsΓ_rΓ_s, ℏ=1.
The full antisymmetric sum includes both ab and ba, hence the 1/2 matrix elements.
"""

import numpy as np
from scipy.linalg import expm


def majorana_k(n, mu, gamma=1.0, delta=1.0):
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError("n must be a positive integer")
    k = np.zeros((2 * n, 2 * n), dtype=float)

    def antisymmetric(i, j, value):
        k[i, j] += value
        k[j, i] -= value

    for j in range(n):
        antisymmetric(2 * j, 2 * j + 1, -float(mu) / 2)
    for j in range(n - 1):
        antisymmetric(2 * j, 2 * (j + 1) + 1, (delta - gamma) / 4)
        antisymmetric(2 * (j + 1), 2 * j + 1, -(delta + gamma) / 4)
    return k


def static_null_vectors(n):
    left = np.zeros(2 * n)
    right = np.zeros(2 * n)
    left[0] = 1.0
    right[-1] = 1.0
    return left, right


def kicked_floquet(n, mu0, mu1, omega, gamma=1.0, delta=1.0):
    if omega <= 0:
        raise ValueError("omega must be positive")
    period = 2 * np.pi / omega
    free = expm(-4 * majorana_k(n, mu0, gamma, delta) * period)
    half_kick = expm(-2 * majorana_k(n, mu1, gamma=0.0, delta=0.0))
    return half_kick @ free @ half_kick, float(period)


def quasienergy_spectrum(u, period):
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
    if eigenvectors.shape[0] != 2 * n:
        raise ValueError("Eigenvector dimension does not match n")
    probability = np.abs(eigenvectors) ** 2
    per_site = probability.reshape((n, 2, eigenvectors.shape[1])).sum(axis=1)
    norms = per_site.sum(axis=0, keepdims=True)
    if np.any(norms <= 0):
        raise ValueError("Encountered an eigenvector with zero norm")
    return per_site / norms


def candidate_modes(spectrum, n, target, edge_fraction=0.1):
    if target not in (1.0, -1.0):
        raise ValueError("Only +1 and -1 targets are supported")
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
