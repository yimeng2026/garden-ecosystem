"""Numerically distinguish K-matrix parameter from full rotation angle."""

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import beta_sequence, chemical_kick  # noqa: E402
from tbc_model import twisted_majorana_k  # noqa: E402


def main():
    n = 8
    beta = beta_sequence(0, n)
    reference = chemical_kick(0.1 * beta)
    for factor in (1.0, 2.0):
        k1 = twisted_majorana_k(factor * 0.1 * beta, 0.0, gamma=0.0, delta=0.0)
        half_kick = expm(-2 * k1)
        print(f"K parameter factor={factor}: half-kick max difference={np.max(np.abs(half_kick-reference)):.12e}")
    print("interpretation: K parameter r*beta gives half-kick angle r*beta and full symmetric rotation angle 2*r*beta")


if __name__ == "__main__":
    main()
