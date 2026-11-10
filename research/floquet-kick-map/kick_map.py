"""Uniform kick map with explicit gapless endpoint handling."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from disorder_model import disordered_floquet, observe_candidate  # noqa: E402
from convention_model import quasienergy_spectrum  # noqa: E402


def uniform_floquet(n, a, omega=7.0, gamma=1.0, delta=1.0, mu0=2.5):
    if a < 0 or a >= np.pi / 2 or omega <= 0:
        raise ValueError("require 0 <= a < pi/2 and omega > 0")
    return disordered_floquet(n, mu0, np.ones(n), a, omega, gamma, delta)


def safe_endpoint_counts(a, mu0=2.5, gamma=1.0, omega=7.0):
    if a < 0 or a >= np.pi / 2 or not (mu0 > gamma > 0) or omega <= 0:
        raise ValueError("outside the restricted endpoint domain")
    b0 = 4 * (mu0 - gamma) / omega + 2 * a / np.pi
    b_pi = 4 * (mu0 + gamma) / omega + 2 * a / np.pi
    singular = min(abs(b0 - round(b0)), abs(b_pi - round(b_pi))) < 1e-9
    if singular:
        return {"status": "gapless_or_undefined", "b0": float(b0), "b_pi": float(b_pi), "p0": None, "p_pi": None}
    low, high = sorted((b0, b_pi))
    integers = list(range(int(np.floor(low)) + 1, int(np.ceil(high))))
    return {
        "status": "ok",
        "b0": float(b0),
        "b_pi": float(b_pi),
        "p0": sum(n % 2 == 0 for n in integers),
        "p_pi": sum(n % 2 == 1 for n in integers),
        "even_integers": [n for n in integers if n % 2 == 0],
        "odd_integers": [n for n in integers if n % 2 == 1],
    }


def evaluate_uniform(n, a):
    u, period = uniform_floquet(n, a)
    spectrum = quasienergy_spectrum(u, period)
    return {
        "unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
        "zero": observe_candidate(spectrum, n, 1.0),
        "pi": observe_candidate(spectrum, n, -1.0),
    }
