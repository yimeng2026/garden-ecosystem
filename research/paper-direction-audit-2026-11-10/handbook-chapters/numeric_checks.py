"""Independent arithmetic for the handbook necessity-claim audit."""

import json
import math

K_B_MEV_PER_K = 0.08617333262145133


def exponent(lam, mu):
    return 1.04 * (1 + lam) / (lam - mu * (1 + 0.62 * lam))


def tc(lam, mu, theta):
    return theta / 1.45 * math.exp(-exponent(lam, mu))


def theta_threshold(lam, mu):
    return 300 * 1.45 * math.exp(exponent(lam, mu))


def mev_to_kelvin(energy_mev):
    return energy_mev / K_B_MEV_PER_K


def critical_tc(omega_log_mev, lam, mu):
    return 11.6 * omega_log_mev / 1.2 * math.exp(-exponent(lam, mu))


def main():
    print(json.dumps({
        "formula4_lambda25_mu015_theta2100": tc(2.5, 0.15, 2100),
        "correct_example_lambda36_mu012_theta2100": tc(3.6, 0.12, 2100),
        "threshold_lambda25_mu015": theta_threshold(2.5, 0.15),
        "omega_210_mev_k": mev_to_kelvin(210),
        "omega_150_mev_k": mev_to_kelvin(150),
        "critical_anchor": critical_tc(100, 2.0, 0.15),
        "relative_error_316_298": abs(316 - 298) / 316,
    }, indent=2))


if __name__ == "__main__":
    main()
