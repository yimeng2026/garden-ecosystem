"""Pre-registered tail, envelope and IPR estimators for finite edge modes."""

import numpy as np
from scipy.optimize import least_squares


def tail_deficit_lengths(sizes, edge_weights, edge_fraction=0.1):
    rows = []
    for n1, n2, e1, e2 in zip(sizes, sizes[1:], edge_weights, edge_weights[1:]):
        d1, d2 = 1 - e1, 1 - e2
        row = {"n1": n1, "n2": n2, "deficit1": float(d1), "deficit2": float(d2)}
        if not (0 < e1 < 1 and 0 < e2 < 1 and d1 > d2 > 0):
            row.update({"status": "undefined", "xi_tail": None, "reason": "Tail deficits must be positive and strictly decreasing"})
        else:
            denominator = np.log(d2) - np.log(d1)
            xi = -2 * edge_fraction * (n2 - n1) / denominator
            if not np.isfinite(xi) or xi <= 0:
                row.update({"status": "undefined", "xi_tail": None, "reason": "Non-positive or undefined fitted length"})
            else:
                row.update({"status": "ok", "xi_tail": float(xi), "reason": None})
        rows.append(row)
    return rows


def fit_envelope(profile):
    profile = np.asarray(profile, dtype=float)
    n = len(profile)
    if n < 4 or np.any(profile < 0) or not np.isclose(profile.sum(), 1.0, atol=1e-8):
        raise ValueError("profile must be a normalized nonnegative site distribution")
    j = np.arange(n, dtype=float)

    def model(params):
        amplitude, background, xi = params
        return background + amplitude * (np.exp(-2 * j / xi) + np.exp(-2 * (n - 1 - j) / xi))

    initial = np.array([max(float(profile.max()) / 2, 1e-10), max(float(profile.min()), 1e-12), n / 20])
    fit = least_squares(
        lambda params: model(params) - profile,
        initial,
        bounds=([0.0, 0.0, 0.05], [2.0, 1.0, 4.0 * n]),
        x_scale="jac",
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-10,
        max_nfev=10000,
    )
    amplitude, background, xi = [float(value) for value in fit.x]
    residual = model(fit.x) - profile
    sse = float(residual @ residual)
    centered = profile - profile.mean()
    sst = float(centered @ centered)
    return {
        "amplitude": amplitude,
        "background": background,
        "xi_env": xi,
        "r_squared": 1 - sse / sst if sst > 0 else 1.0,
        "sse": sse,
        "optimizer_success": bool(fit.success),
        "optimality": float(fit.optimality),
        "nfev": int(fit.nfev),
    }


def subspace_metrics(vectors, n):
    """Basis-invariant rank-two projector weight and ∑_m ρ_mm²."""
    q, _ = np.linalg.qr(vectors)
    diagonal = np.einsum("ij,ij->i", q, q.conj()).real
    if diagonal.shape[0] != 2 * n:
        raise ValueError("vector dimension does not match n")
    profile = diagonal.reshape((n, 2)).sum(axis=1) / 2
    return {"profile": profile, "subspace_ipr": float(diagonal @ diagonal)}


def assess_short_chain(studies, tail_rows, envelope_rows):
    criteria = {}
    for target in ("zero", "pi"):
        first = studies[-2][target]
        last = studies[-1][target]
        first_ipr = first["subspace_ipr"]
        last_ipr = last["subspace_ipr"]
        ipr_relative_change = abs(last_ipr - first_ipr) / first_ipr
        second_decay = first["second_pair_subspace_ipr"] / last["second_pair_subspace_ipr"]
        second_n_ipr_ratio = (studies[-1]["n"] * last["second_pair_subspace_ipr"]) / (studies[-2]["n"] * first["second_pair_subspace_ipr"])
        tails = [row for row in tail_rows[target][-2:] if row["status"] == "ok"]
        if len(tails) == 2:
            lengths = [row["xi_tail"] for row in tails]
            tail_ratio = max(lengths) / min(lengths)
        else:
            tail_ratio = float("inf")
        env_first = envelope_rows[target][-2]
        env_last = envelope_rows[target][-1]
        env_relative_change = abs(env_last["xi_env"] - env_first["xi_env"]) / env_first["xi_env"]
        checks = {
            "first_pair_subspace_ipr_plateau": ipr_relative_change < 0.1,
            "second_pair_extended_ipr_decays": second_decay > 1.5,
            "second_pair_n_ipr_bounded": 0.5 < second_n_ipr_ratio < 2,
            "tail_lengths_stable_within_factor_2": tail_ratio <= 2,
            "envelope_lengths_stable_within_25_percent": env_relative_change < 0.25,
            "envelope_r_squared_above_0_5": min(env_first["r_squared"], env_last["r_squared"]) > 0.5,
            "largest_size_original_candidate_rule": max(last["separation_ratios"]) < 0.1 and min(last["edge_weights"]) > 0.5,
        }
        criteria[target] = {
            "checks": checks,
            "metrics": {
                "first_pair_subspace_ipr_relative_change": float(ipr_relative_change),
                "second_pair_subspace_ipr_decay_factor": float(second_decay),
                "second_pair_n_subspace_ipr_ratio": float(second_n_ipr_ratio),
                "tail_length_ratio": float(tail_ratio),
                "envelope_relative_change": float(env_relative_change),
                "last_two_envelope_r_squared": [env_first["r_squared"], env_last["r_squared"]],
            },
        }
    passed = all(all(row["checks"].values()) for row in criteria.values())
    return {
        "status": "short_chain_regime_supported" if passed else "partial_or_inconclusive",
        "criteria": criteria,
        "full_size_rule_status": "inconclusive_preserved",
        "thermodynamic_limit_proof": False,
        "interpretation": "Evidence concerns the current finite quadratic model only; it is not a material or experimental result.",
    }
