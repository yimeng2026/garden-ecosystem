"""Targeted N=320 zero-gap TBC study with per-case atomic checkpoints."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from run_disorder import beta_for, evaluate_realization, require_baseline

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "n320_zero.json"


def n320_registry():
    return [
        {"strength": 0.05, "seed": 2, "kind": "disorder", "target": "zero", "endpoint_class": "recovered"},
        {"strength": 0.05, "seed": 3, "kind": "disorder", "target": "zero", "endpoint_class": "recovered"},
        {"strength": 0.1, "seed": 2, "kind": "disorder", "target": "zero", "endpoint_class": "recovered"},
        {"strength": 0.05, "seed": 0, "kind": "disorder", "target": "zero", "endpoint_class": "not_recovered"},
        {"strength": 0.1, "seed": 0, "kind": "disorder", "target": "zero", "endpoint_class": "not_recovered"},
        {"strength": 0.05, "seed": 0, "kind": "uniform_mean", "target": "zero", "endpoint_class": "uniform_control"},
        {"strength": 0.1, "seed": 0, "kind": "uniform_mean", "target": "zero", "endpoint_class": "uniform_control"},
    ]


def identity(case):
    return case["strength"], case["seed"], case["kind"], case["target"]


def write_atomic(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_n320(n=320, selector=None, path=OUTPUT):
    path = Path(path)
    baseline_path = ROOT / "results.json"
    require_baseline(baseline_path)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != "floquet-bdg-tbc-n320-zero-v1" or data.get("n") != n:
            raise ValueError("N320 checkpoint metadata mismatch")
    else:
        data = {
            "schema": "floquet-bdg-tbc-n320-zero-v1", "n": n, "target": "zero",
            "registry_size": 7, "free_method": "eigh",
            "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
            "complete": False, "rows": [],
        }
    rows = data["rows"]
    present = {identity(row) for row in rows}
    if len(present) != len(rows):
        raise ValueError("duplicate N320 case")
    registry = n320_registry()
    for case in registry:
        if selector is not None and not selector(case):
            continue
        if identity(case) in present:
            continue
        started = time.perf_counter()
        row = evaluate_realization(
            n, case["seed"], case["strength"], case["kind"], (0.05, 0.025),
            targets=("zero",), free_method="eigh",
        )
        row["target"] = "zero"
        row["endpoint_class"] = case["endpoint_class"]
        row["runtime_seconds"] = time.perf_counter() - started
        rows.append(row)
        present.add(identity(row))
        expected = {identity(item) for item in registry}
        data["rows"] = rows
        data["complete"] = n == 320 and present == expected and len(rows) == 7 and all(
            item["half_kick_convention_error"] <= 1e-12 and item["free_method"] == "eigh" for item in rows
        )
        write_atomic(path, data)
    return data


def merge_n320(path=OUTPUT):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = {identity(case) for case in n320_registry()}
    rows = data.get("rows", [])
    present = {identity(row) for row in rows}
    valid_hashes = all(
        row["beta_sha256"] == hashlib.sha256(
            (beta_for(row["seed"], 320) if row["kind"] == "disorder" else np.ones(320)).tobytes()
        ).hexdigest()
        for row in rows
    )
    if (
        not data.get("complete") or data.get("n") != 320 or len(rows) != 7 or present != expected
        or any(row.get("half_kick_convention_error", 1.0) > 1e-12 or row.get("free_method") != "eigh" for row in rows)
        or not valid_hashes
    ):
        raise ValueError("incomplete N320 case registry")
    data["status"] = "complete_n320_zero"
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("disorder", "uniform_mean"))
    parser.add_argument("--strength", type=float, choices=(0.05, 0.1))
    parser.add_argument("--seed", type=int, choices=range(4))
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.merge_only:
            data = merge_n320()
            print("n320_complete", len(data["rows"]))
            return 0
        def selected(case):
            return (
                (args.kind is None or case["kind"] == args.kind)
                and (args.strength is None or case["strength"] == args.strength)
                and (args.seed is None or case["seed"] == args.seed)
            )
        data = run_n320(selector=selected)
        for row in data["rows"]:
            print(
                f"N={row['n']} r={row['strength']} seed={row['seed']} kind={row['kind']} "
                f"class={row['endpoint_class']} status={row['zero']['status']} "
                f"W0={row['zero']['nearest_integer']} raw={row['zero']['value']} "
                f"gap={row['zero']['min_bulk_gap']} runtime={row['runtime_seconds']:.3f}s"
            )
        print("n320_rows", len(data["rows"]), "complete", data["complete"])
        return 0
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("n320_error", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
