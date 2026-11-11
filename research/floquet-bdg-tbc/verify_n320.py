"""Independent expm+Schur determinant checks for targeted N=320 cases."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from run_disorder import beta_for
from run_n320 import identity, n320_registry
from verify_tbc import determinant_winding

ROOT = Path(__file__).resolve().parent


def output_path(case):
    return ROOT / f"n320_independent_r{case['strength']:.2f}_seed{case['seed']}_{case['kind']}.json".replace(".", "p", 1)


def verify_case(case):
    data = json.loads((ROOT / "n320_zero.json").read_text(encoding="utf-8"))
    row = next(row for row in data["rows"] if identity(row) == identity(case))
    beta = beta_for(case["seed"], 320) if case["kind"] == "disorder" else np.ones(320)
    independent = determinant_winding(
        320, np.full(320, 2.5), case["strength"] * beta, 7.0, 0.0, nominal_step=0.05,
    )
    production = row["zero"]
    agreement = (
        bool(independent["passed"] and independent["nearest_integer"] == production["nearest_integer"])
        if production["status"] == "ok" else None
    )
    output = {
        "schema": "floquet-bdg-tbc-n320-independent-case-v1",
        "case": dict(case), "production_status": production["status"],
        "production_value": production["value"], "production_nearest_integer": production["nearest_integer"],
        "independent": independent, "integer_agreement": agreement,
        "rejection_category_independently_checked": production["status"] != "ok",
    }
    path = output_path(case)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"r={case['strength']} seed={case['seed']} kind={case['kind']} "
        f"production={production['status']}/{production['nearest_integer']} "
        f"independent={independent['status']}/{independent['nearest_integer']} raw={independent['value']}"
    )
    return output, agreement is not False


def merge():
    outputs = [json.loads(output_path(case).read_text(encoding="utf-8")) for case in n320_registry()]
    identities = {identity(row["case"]) for row in outputs}
    passed = len(outputs) == 7 and len(identities) == 7 and all(row["integer_agreement"] is not False for row in outputs)
    data = {
        "schema": "floquet-bdg-tbc-n320-independent-v1", "selected_count": len(outputs),
        "checks": outputs, "passed": passed,
        "case_sha256": {
            output_path(row["case"]).name: hashlib.sha256(output_path(row["case"]).read_bytes()).hexdigest()
            for row in outputs
        },
    }
    (ROOT / "n320_independent.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("n320_independent", len(outputs), "passed", passed)
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("disorder", "uniform_mean"))
    parser.add_argument("--strength", type=float, choices=(0.05, 0.1))
    parser.add_argument("--seed", type=int, choices=range(4))
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    if args.merge_only:
        return merge()
    if args.kind is None or args.strength is None or args.seed is None:
        parser.error("single-case verification requires --kind, --strength, and --seed")
    case = next(
        case for case in n320_registry()
        if case["kind"] == args.kind and case["strength"] == args.strength and case["seed"] == args.seed
    )
    _, passed = verify_case(case)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
