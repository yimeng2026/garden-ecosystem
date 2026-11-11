"""Direct two-end coverage and preregistered recovery-scale assessments."""

import numpy as np


def end_cumulative(profile):
    profile = np.asarray(profile, dtype=float)
    if profile.ndim != 1 or len(profile) < 2 or np.any(profile < 0) or not np.isclose(profile.sum(), 1.0, atol=1e-10):
        raise ValueError("profile must be a normalized nonnegative one-dimensional distribution")
    return np.cumsum(profile + profile[::-1])


def coverage_lengths(profile, thresholds=(0.5, 0.9, 0.99)):
    cumulative = end_cumulative(profile)
    return {
        f"L{int(round(100 * threshold))}": int(np.searchsorted(cumulative, threshold, side="left") + 1)
        for threshold in thresholds
    }


def fixed_width_masses(profile, widths=(5, 10, 20, 40)):
    profile = np.asarray(profile, dtype=float)
    result = {}
    for width in widths:
        if width > len(profile) // 2:
            raise ValueError("fixed width exceeds half the chain")
        result[str(width)] = float(profile[:width].sum() + profile[-width:].sum())
    return result


def center_mass(profile, fraction=0.2):
    profile = np.asarray(profile, dtype=float)
    if not 0 < fraction <= 1:
        raise ValueError("center fraction must be in (0,1]")
    start = int(np.floor((1 - fraction) * len(profile) / 2))
    stop = int(np.ceil((1 + fraction) * len(profile) / 2))
    return float(profile[start:stop].sum())


def assess_recovery(rows):
    """Apply the preregistered plateau rule, or return not_established."""
    if len(rows) != 3 or [row["n"] for row in rows] != [80, 160, 320]:
        raise ValueError("assessment requires ordered N=80/160/320 rows")
    previous, latest = rows[-2], rows[-1]
    if latest["joint_pass"]:
        return {
            "status": "measured_recovered", "next_size": None,
            "l50_bracket_times_ten": None, "reason": "endpoint joint criterion already measured at N=320",
        }
    l50_change = abs(latest["L50"] - previous["L50"]) / previous["L50"]
    mass20_ratio = latest["mass20"] / previous["mass20"] if previous["mass20"] > 0 else 0.0
    criteria = {
        "l50_last_two_change_at_most_0p25": l50_change <= 0.25,
        "fixed_width20_mass_ratio_at_least_0p8": mass20_ratio >= 0.8,
        "n320_separation_below_0p1": latest["separation"] < 0.1,
    }
    next_size = max(400, int(100 * np.ceil(latest["L50"] / 10)))
    if all(criteria.values()):
        return {
            "status": "bounded_diagnostic", "next_size": next_size,
            "l50_bracket_times_ten": sorted([10 * previous["L50"], 10 * latest["L50"]]),
            "criteria": criteria,
            "l50_last_two_relative_change": float(l50_change),
            "mass20_last_two_ratio": float(mass20_ratio),
            "reason": "plateau criteria satisfied; next size is a diagnostic, not a recovery prediction",
        }
    return {
        "status": "not_established", "next_size": next_size,
        "l50_bracket_times_ten": None, "criteria": criteria,
        "l50_last_two_relative_change": float(l50_change),
        "mass20_last_two_ratio": float(mass20_ratio),
        "reason": "plateau criteria failed; no recovery bracket is justified",
    }
