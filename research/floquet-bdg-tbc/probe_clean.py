"""Diagnostic only: locate clean-kicked chiral failures without winding promotion."""

import numpy as np
from scipy.linalg import expm

from tbc_model import chiral_blocks, periodized, twisted_majorana_k


def main(n=20):
    period = 2 * np.pi / 7
    mu0, mu1 = np.full(n, 2.5), np.full(n, 0.2)
    kick = expm(-4 * twisted_majorana_k(mu1, 0.0, gamma=0.0, delta=0.0))
    for theta in np.linspace(-np.pi, np.pi, 17)[:-1]:
        free_half = expm(-2 * twisted_majorana_k(mu0, theta) * period)
        u_half = kick @ free_half
        u_full = u_half @ free_half
        for epsilon in (0.0, np.pi):
            result = periodized(u_half, u_full, period, period / 2, epsilon)
            if result["status"] != "ok":
                print("periodized_failure", theta, epsilon, result)
                continue
            blocks = chiral_blocks(result["u"], epsilon)
            gaps = {
                "zero": float(np.min(np.abs(np.linalg.eigvals(u_full) - 1))),
                "pi": float(np.min(np.abs(np.linalg.eigvals(u_full) + 1))),
            }
            print(
                "point",
                f"theta={theta:.12f}",
                f"epsilon={epsilon:.6f}",
                f"status={blocks['status']}",
                f"symmetry={blocks['symmetry_error']:.12e}",
                f"condition={blocks['max_condition']:.12e}",
                f"gap0={gaps['zero']:.12e}",
                f"gappi={gaps['pi']:.12e}",
            )


if __name__ == "__main__":
    main()
