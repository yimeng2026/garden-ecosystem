"""Diagnostic only: compare full-kick time-origin conventions before changing the model."""

import numpy as np
from scipy.linalg import expm

from tbc_model import chiral_blocks, periodized, twisted_majorana_k


def main(n=8, theta=0.371):
    period = 2 * np.pi / 7
    k0 = twisted_majorana_k(np.full(n, 2.5), theta)
    kick = expm(-4 * twisted_majorana_k(np.full(n, 0.2), theta, gamma=0.0, delta=0.0))
    free_half = expm(-2 * k0 * period)
    free_full = free_half @ free_half
    half_kick = expm(-2 * twisted_majorana_k(np.full(n, 0.2), theta, gamma=0.0, delta=0.0))
    protocols = {
        "origin_left": (kick @ free_half, kick @ free_full),
        "end_left": (free_half, kick @ free_full),
        "end_right": (free_half, free_full @ kick),
        "symmetric_frame": (half_kick @ free_half @ half_kick, half_kick @ free_full @ half_kick),
        "symmetric_time_ordered": (free_half @ half_kick, half_kick @ free_full @ half_kick),
    }
    reference = protocols["origin_left"][1]
    for name, (u_half, u_full) in protocols.items():
        print(name, "floquet_spectral_max_difference", float(np.max(np.abs(np.sort(np.angle(np.linalg.eigvals(u_full))) - np.sort(np.angle(np.linalg.eigvals(reference)))))))
        for epsilon in (0.0, np.pi):
            result = periodized(u_half, u_full, period, period / 2, epsilon)
            if result["status"] != "ok":
                print(name, epsilon, result)
                continue
            blocks = chiral_blocks(result["u"], epsilon)
            print(name, "epsilon", epsilon, "status", blocks["status"], "symmetry", blocks["symmetry_error"], "unitarity", result["unitarity_error"])


if __name__ == "__main__":
    main()
