"""Run the frozen surface-code circuit-level Monte Carlo protocol."""
from __future__ import annotations

import csv
import importlib.metadata
import json
import math
import platform
from pathlib import Path

import pymatching
import stim

from surface_code_stats import estimate_crossings, protocol_digest, validate_protocol, wilson_interval

AUDIT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = AUDIT_DIR / "surface-code-threshold" / "protocol.json"
DEFAULT_RESULTS = AUDIT_DIR / "surface-code-threshold" / "results.json"
DEFAULT_CSV = AUDIT_DIR / "surface-code-threshold" / "results.csv"


def build_circuit(distance: int, p: float, rounds: int | None = None):
    if isinstance(distance, bool) or not isinstance(distance, int) or distance <= 0 or distance % 2 == 0:
        raise ValueError("distance must be a positive odd integer")
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p < 1:
        raise ValueError("p must be finite and between zero (inclusive) and one (exclusive)")
    rounds = distance if rounds is None else rounds
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds <= 0:
        raise ValueError("rounds must be a positive integer")
    return stim.Circuit.generated(
        "surface_code:rotated_memory_x",
        distance=distance,
        rounds=rounds,
        after_clifford_depolarization=p,
        before_round_data_depolarization=p,
        after_reset_flip_probability=p,
        before_measure_flip_probability=p,
    )


def run_point(distance: int, p: float, shots: int, seed: int) -> dict:
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    circuit = build_circuit(distance, p)
    model = circuit.detector_error_model(decompose_errors=True)
    matching = pymatching.Matching.from_detector_error_model(model)
    sampler = circuit.compile_detector_sampler(seed=seed)
    syndrome, actual_observables = sampler.sample(shots=shots, separate_observables=True)
    predicted_observables = matching.decode_batch(syndrome)
    errors = sum(bool((actual_observables[index] != predicted_observables[index]).any())
                 for index in range(shots))
    rate, low, high = wilson_interval(errors, shots)
    return {
        "distance": distance,
        "p": p,
        "shots": shots,
        "seed": seed,
        "errors": errors,
        "rate": rate,
        "wilson95_low": low,
        "wilson95_high": high,
        "log10_rate": math.log10(rate) if rate > 0 else None,
    }


def dependency_versions() -> dict:
    return {
        "python": platform.python_version(),
        "stim": importlib.metadata.version("stim"),
        "pymatching": importlib.metadata.version("pymatching"),
        "numpy": importlib.metadata.version("numpy"),
    }


def main() -> int:
    protocol_bytes = DEFAULT_PROTOCOL.read_bytes()
    protocol = validate_protocol(json.loads(protocol_bytes))
    points = []
    for distance in protocol["distances"]:
        for index, probability in enumerate(protocol["probabilities"]):
            seed = protocol["seed_base"] + distance * 1000 + index
            result = run_point(distance, probability, protocol["shots"], seed)
            points.append(result)
            print(json.dumps({"completed": f"d={distance},p={probability}", "errors": result["errors"],
                              "shots": result["shots"], "rate": result["rate"]}, ensure_ascii=False), flush=True)
    crossing_summary = estimate_crossings(points)
    payload = {
        "schema": "surface-code-threshold-results-v1",
        "protocol_sha256": protocol_digest(protocol_bytes),
        "protocol": protocol,
        "dependencies": dependency_versions(),
        "points": points,
        "zero_rate_points": [{"distance": item["distance"], "p": item["p"], "shots": item["shots"]}
                             for item in points if item["rate"] == 0],
        "crossing_summary": crossing_summary,
        "evidence_boundary": "These are real results only for the frozen circuit-level protocol. The crossing estimate is exploratory and is not an FSS fit or a reproduction of the manuscript's missing original simulation.",
    }
    DEFAULT_RESULTS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8", newline="\n")
    with DEFAULT_CSV.open("w", encoding="utf-8", newline="") as handle:
        fields = ["distance", "p", "shots", "seed", "errors", "rate",
                  "wilson95_low", "wilson95_high", "log10_rate"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(points)
    print(json.dumps({"points": len(points), "crossing_summary": crossing_summary,
                      "dependencies": payload["dependencies"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
