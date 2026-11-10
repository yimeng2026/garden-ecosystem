"""Independent determinant-phase checks for the N=160 finite-size registry."""

import argparse
import json
from pathlib import Path

import numpy as np

from run_disorder import beta_for
from verify_tbc import determinant_winding

ROOT = Path(__file__).resolve().parent


def selected_cases(data):
    rows = data["rows"]
    controls = [row for row in rows if row["kind"] == "uniform_mean"]
    controls.append(next(row for row in rows if row["kind"] == "disorder" and row["strength"] == 0.05 and row["seed"] == 0))
    remaining = [next(row for row in rows if row["kind"] == "disorder" and row["strength"] == 0.1 and row["seed"] == 0)]
    remaining.extend(
        next(row for row in rows if row["kind"] == "disorder" and row["strength"] == 0.05 and row["seed"] == seed)
        for seed in (2, 3)
    )
    for row in rows:
        if row["kind"] == "disorder" and row["zero"]["status"] != "ok" and row not in remaining:
            remaining.append(row)
    return controls, remaining


def verify(rows, nominal_step):
    checks = []
    for row in rows:
        beta = beta_for(row["seed"], row["n"]) if row["kind"] == "disorder" else np.ones(row["n"])
        independent = determinant_winding(
            row["n"], np.full(row["n"], 2.5), row["strength"] * beta,
            7.0, 0.0, nominal_step=nominal_step,
        )
        production = row["zero"]
        agreement = bool(independent["passed"] and independent["nearest_integer"] == production["nearest_integer"])
        checks.append({
            "n": row["n"], "strength": row["strength"], "seed": row["seed"], "kind": row["kind"],
            "target": "zero", "production_status": production["status"],
            "production_nearest_integer": production["nearest_integer"],
            "independent": independent, "integer_agreement": agreement,
        })
        print(
            f"r={row['strength']} seed={row['seed']} kind={row['kind']} "
            f"production={production['status']}/{production['nearest_integer']} "
            f"independent={independent['status']}/{independent['nearest_integer']} raw={independent['value']}"
        )
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=("controls", "remaining", "all"), default="all")
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    if args.merge_only:
        parts = []
        for name in ("controls", "remaining"):
            path = ROOT / f"finite_size_independent_{name}.json"
            parts.append(json.loads(path.read_text(encoding="utf-8")))
        checks = parts[0]["checks"] + parts[1]["checks"]
        identities = {(row["strength"], row["seed"], row["kind"], row["target"]) for row in checks}
        passed = len(checks) == 7 and len(identities) == 7 and all(row["integer_agreement"] for row in checks)
        output = {
            "schema": "floquet-bdg-tbc-finite-size-independent-v1",
            "selected_count": len(checks), "checks": checks, "passed": passed,
            "part_sha256": {
                name: __import__("hashlib").sha256((ROOT / f"finite_size_independent_{name}.json").read_bytes()).hexdigest()
                for name in ("controls", "remaining")
            },
        }
        (ROOT / "finite_size_independent.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("finite_size_independent", len(checks), "passed", passed)
        return 0 if passed else 1
    data = json.loads((ROOT / "finite_size_zero.json").read_text(encoding="utf-8"))
    controls, remaining = selected_cases(data)
    rows = controls if args.group == "controls" else remaining if args.group == "remaining" else controls + remaining
    expected = 4 if args.group == "controls" else 3 if args.group == "remaining" else 7
    checks = verify(rows, nominal_step=0.05)
    passed = len(checks) == expected and all(row["integer_agreement"] for row in checks)
    output = {
        "schema": "floquet-bdg-tbc-finite-size-independent-part-v1",
        "group": args.group, "nominal_step": 0.05,
        "selected_count": len(checks), "checks": checks, "passed": passed,
    }
    filename = "finite_size_independent.json" if args.group == "all" else f"finite_size_independent_{args.group}.json"
    (ROOT / filename).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("group", args.group, "selected", len(checks), "passed", passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
