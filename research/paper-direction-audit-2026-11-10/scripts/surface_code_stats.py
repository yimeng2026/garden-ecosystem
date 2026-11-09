"""Statistics for the independent surface-code benchmark."""
from __future__ import annotations

import itertools
import math
import statistics
from collections import defaultdict

Z_95 = 1.959963984540054


def wilson_interval(errors: int, shots: int, z: float = Z_95) -> tuple[float, float, float]:
    """Return the observed rate and its two-sided Wilson score interval."""
    if isinstance(errors, bool) or isinstance(shots, bool):
        raise ValueError("invalid counts")
    if not isinstance(errors, int) or not isinstance(shots, int) or shots <= 0 or not 0 <= errors <= shots:
        raise ValueError("invalid counts")
    if not math.isfinite(z) or z <= 0:
        raise ValueError("z must be positive and finite")
    rate = errors / shots
    denominator = 1 + z * z / shots
    center = (rate + z * z / (2 * shots)) / denominator
    radius = z * math.sqrt(rate * (1 - rate) / shots + z * z / (4 * shots * shots)) / denominator
    return rate, max(0.0, center - radius), min(1.0, center + radius)


def crossing(xs: list[float], small: list[float], large: list[float]) -> float:
    """Find one crossing of two piecewise-linear curves, where small starts above large."""
    if not (len(xs) == len(small) == len(large)) or len(xs) < 2:
        raise ValueError("crossing needs matching arrays with at least two points")
    if any(not math.isfinite(value) for value in xs + small + large):
        raise ValueError("crossing inputs must be finite")
    if any(right <= left for left, right in zip(xs, xs[1:])):
        raise ValueError("crossing x coordinates must be strictly increasing")
    differences = [a - b for a, b in zip(small, large)]
    for index in range(len(xs) - 1):
        left, right = differences[index], differences[index + 1]
        if left == 0:
            return xs[index]
        if right == 0:
            return xs[index + 1]
        if left * right < 0:
            fraction = -left / (right - left)
            return xs[index] + fraction * (xs[index + 1] - xs[index])
    raise ValueError("no crossing in bracket")


def estimate_crossings(points: list[dict]) -> dict:
    """Estimate pairwise curve crossings and retain skipped pairs explicitly."""
    groups = defaultdict(list)
    for point in points:
        if point.get("log10_rate") is not None:
            groups[point["distance"]].append(point)
    for group in groups.values():
        group.sort(key=lambda item: item["p"])
    crossings = []
    skipped = []
    for small_distance, large_distance in itertools.combinations(sorted(groups), 2):
        small = groups[small_distance]
        large = groups[large_distance]
        if [item["p"] for item in small] != [item["p"] for item in large]:
            skipped.append({"pair": [small_distance, large_distance], "reason": "probability grids differ"})
            continue
        try:
            value = crossing(
                [item["p"] for item in small],
                [item["log10_rate"] for item in small],
                [item["log10_rate"] for item in large],
            )
        except ValueError as error:
            skipped.append({"pair": [small_distance, large_distance], "reason": str(error)})
        else:
            crossings.append({"pair": [small_distance, large_distance], "p": value})
    values = [item["p"] for item in crossings]
    return {
        "crossings": crossings,
        "skipped_pairs": skipped,
        "median": statistics.median(values) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def validate_protocol(protocol: dict) -> dict:
    """Validate the frozen grid without changing any scientific input."""
    if not isinstance(protocol, dict):
        raise ValueError("protocol must be an object")
    distances = protocol.get("distances")
    probabilities = protocol.get("probabilities")
    shots = protocol.get("shots")
    if not isinstance(distances, list) or not distances:
        raise ValueError("distances must be a non-empty list")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value % 2 == 0
           for value in distances):
        raise ValueError("distances must be positive odd integers")
    if len(set(distances)) != len(distances):
        raise ValueError("distances must be unique")
    if not isinstance(probabilities, list) or not probabilities:
        raise ValueError("probabilities must be a non-empty list")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or not 0 < value < 1 for value in probabilities):
        raise ValueError("probabilities must be finite and strictly between zero and one")
    if len(set(probabilities)) != len(probabilities):
        raise ValueError("probabilities must be unique")
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer")
    if "seed_base" in protocol and (isinstance(protocol["seed_base"], bool)
                                    or not isinstance(protocol["seed_base"], int)):
        raise ValueError("seed_base must be an integer")
    return dict(protocol)
