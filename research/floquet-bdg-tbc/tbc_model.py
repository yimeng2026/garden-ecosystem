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
    """Full kick at the origin followed by free evolution; U_step(0)=I."""
    k0, k1 = np.asarray(k0, dtype=complex), np.asarray(k1, dtype=complex)
    if k0.ndim != 2 or k0.shape[0] != k0.shape[1] or k1.shape != k0.shape:
        raise ValueError("k0 and k1 must be equal-sized square matrices")
    if not np.isfinite(period) or period <= 0 or not 0 <= time <= period:
        raise ValueError("require period > 0 and 0 <= time <= period")
    if time == 0:
        return np.eye(k0.shape[0], dtype=complex)
    return expm(-4 * k1) @ expm(-4 * k0 * time)


def floquet_gap(u, epsilon):
    """Minimum unit-circle distance to the requested 0 or pi gap."""
    if not np.isclose(epsilon, 0.0, atol=0, rtol=0) and not np.isclose(
        epsilon, np.pi, atol=0, rtol=0
    ):
        raise ValueError("epsilon must be exactly 0 or pi")
    return float(np.min(np.abs(np.linalg.eigvals(u) - np.exp(1j * epsilon))))
