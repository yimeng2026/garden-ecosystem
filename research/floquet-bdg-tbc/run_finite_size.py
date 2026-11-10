"""Incremental N=160 zero-gap TBC study with a fixed 11-case registry."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from run_disorder import evaluate_realization, require_baseline

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "finite_size_zero.json"


def case_registry():
    cases = [
        {"strength": strength, "seed": 0, "kind": "uniform_mean", "target": "zero"}
        for strength in (0.05, 0.1, 0.2)
    ]
    cases.extend(
        {"strength": strength, "seed": seed, "kind": "disorder", "target": "zero"}
        for strength in (0.05, 0.1)
        for seed in range(4)
    )
    return cases


def identity(case):
    return case["strength"], case["seed"], case["kind"], case["target"]


def write_atomic(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_cases(n=160, selector=None, path=OUTPUT):
    path = Path(path)
    baseline_path = ROOT / "results.json"
    require_baseline(baseline_path)
    registry = case_registry()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != "floquet-bdg-tbc-finite-size-zero-v1" or data.get("n") != n:
            raise ValueError("finite-size checkpoint metadata mismatch")
    else:
        data = {
            "schema": "floquet-bdg-tbc-finite-size-zero-v1",
            "n": n,
            "target": "zero",
            "registry_size": 11,
            "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
            "complete": False,
            "rows": [],
        }
    rows = data["rows"]
    present = {identity(row) for row in rows}
    if len(present) != len(rows):
        raise ValueError("duplicate finite-size case in checkpoint")
    for case in registry:
        if selector is not None and not selector(case):
            continue
        if identity(case) in present:
            continue
        started = time.perf_counter()
        row = evaluate_realization(
            n,
            case["seed"],
            case["strength"],
            case["kind"],
            (0.05, 0.025),
            targets=("zero",),
        )
        row["target"] = "zero"
        row["runtime_seconds"] = time.perf_counter() - started
        rows.append(row)
        present.add(identity(row))
        expected = {identity(item) for item in registry}
        data["rows"] = rows
        data["complete"] = n == 160 and present == expected and len(rows) == 11 and all(
            item["half_kick_convention_error"] <= 1e-12 for item in rows
        )
        write_atomic(path, data)
    return data


def merge_complete(path=OUTPUT):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = {identity(case) for case in case_registry()}
    present = {identity(row) for row in data.get("rows", [])}
    if (
        not data.get("complete")
        or data.get("n") != 160
        or len(data.get("rows", [])) != 11
        or present != expected
        or any(row.get("half_kick_convention_error", 1.0) > 1e-12 for row in data["rows"])
    ):
        raise ValueError("incomplete finite-size case registry")
    data["status"] = "complete_finite_size_zero"
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("disorder", "uniform_mean"))
    parser.add_argument("--strength", type=float, choices=(0.05, 0.1, 0.2))
    parser.add_argument("--seed", type=int, choices=range(4))
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.merge_only:
            data = merge_complete()
            print("finite_size_complete", len(data["rows"]))
            return 0
        def selected(case):
            return (
                (args.kind is None or case["kind"] == args.kind)
                and (args.strength is None or case["strength"] == args.strength)
                and (args.seed is None or case["seed"] == args.seed)
            )
        data = run_cases(selector=selected)
        for row in data["rows"]:
            print(
                f"N={row['n']} r={row['strength']} seed={row['seed']} kind={row['kind']} "
                f"status={row['zero']['status']} W0={row['zero']['nearest_integer']} "
                f"raw={row['zero']['value']} gap={row['zero']['min_bulk_gap']} "
                f"runtime={row['runtime_seconds']:.3f}s"
            )
        print("finite_size_rows", len(data["rows"]), "complete", data["complete"])
        return 0
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("finite_size_error", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
