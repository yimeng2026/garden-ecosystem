"""Arithmetic spot check for the formula printed in the material-prediction report."""

import math


def simplified_tc(omega_log_k, lam, mu_star):
    exponent = -1.04 * (1.0 + lam) / (lam - mu_star * (1.0 + 0.62 * lam))
    return omega_log_k / 1.2 * math.exp(exponent), exponent


def main():
    cases = {
        "H3S_table": (1200.0, 2.0, 0.13, 203.0),
        "H-S-Cl_table": (1500.0, 2.5, 0.12, 320.0),
    }
    for name, (omega, lam, mu, claimed) in cases.items():
        value, exponent = simplified_tc(omega, lam, mu)
        print(f"{name}: computed={value:.15f} K; claimed={claimed:g} K; exponent={exponent:.15f}; difference={value - claimed:.15f} K")


if __name__ == "__main__":
    main()
