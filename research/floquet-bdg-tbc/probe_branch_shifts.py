"""Diagnostic only: select endpoint-equivalent branches by algebraic chiral identities."""

import numpy as np
from scipy.linalg import expm, schur

from tbc_model import chiral, twisted_majorana_k


def operators(mu0, mu1, theta, n=8):
    period = 2 * np.pi / 7
    free_half = expm(-2 * twisted_majorana_k(np.full(n, mu0), theta) * period)
    half_kick = expm(-2 * twisted_majorana_k(np.full(n, mu1), theta, gamma=0.0, delta=0.0))
    u_half = free_half @ half_kick
    u_full = half_kick @ free_half @ free_half @ half_kick
    return period, u_half, u_full


def main():
    s = chiral(8)
    for label, mu0, mu1 in (("static", 0.0, 0.0), ("clean", 2.5, 0.2)):
        period, u_half, u_full = operators(mu0, mu1, 0.371)
        triangular, q = schur(u_full, output="complex")
        phi = -np.angle(np.diag(triangular))
        print("case", label)
        for epsilon in (0.0, np.pi):
            sign = -1 if epsilon == 0 else 1
            rows = []
            for valence_shift in (-1, 0, 1):
                for conduction_shift in (-1, 0, 1):
                    shifts = np.where(phi < 0, valence_shift, conduction_shift)
                    phi_eff = phi + 2 * np.pi * shifts
                    power = (q * np.exp(1j * phi_eff / 2)) @ q.conj().T
                    u_epsilon = u_half @ power
                    error = float(np.max(np.abs(s @ u_epsilon @ s - sign * u_epsilon)))
                    unitarity = float(np.max(np.abs(u_epsilon.conj().T @ u_epsilon - np.eye(len(u_epsilon)))))
                    rows.append((error, valence_shift, conduction_shift, unitarity))
            for row in sorted(rows)[:4]:
                print("epsilon", epsilon, "error,valence,conduction,unitarity", row)


if __name__ == "__main__":
    main()
