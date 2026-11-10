"""Independent determinant-phase verification of selected disorder realizations."""

import argparse
import json
from pathlib import Path

import numpy as np

from run_disorder import beta_for
from verify_tbc import determinant_winding

ROOT = Path(__file__).resolve().parent


def select_rows(data):
    selected = []
    for row in data["realizations"]:
        if row["seed"] == 0:
            for target in ("zero", "pi"):
                selected.append((row, target))
        for target in ("zero", "pi"):
            if row[target]["status"] != "ok" and (row, target) not in selected:
                selected.append((row, target))
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nominal-step", type=float, default=0.0125)
    parser.add_argument("--output", default="disorder_independent.json")
    args = parser.parse_args()
    if args.nominal_step <= 0 or Path(args.output).name != args.output:
        raise ValueError("nominal step must be positive and output must be a local filename")
    data = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
    selected = select_rows(data)
    checks = []
    for row, target in selected:
        strength, seed, kind = row["strength"], row["seed"], row["kind"]
        beta = beta_for(seed, row["n"]) if kind == "disorder" else np.ones(row["n"])
        epsilon = 0.0 if target == "zero" else np.pi
        independent = determinant_winding(
            row["n"], np.full(row["n"], 2.5), strength * beta, 7.0, epsilon,
            nominal_step=args.nominal_step,
        )
        production = row[target]
        if production["status"] == "ok":
            agrees = bool(independent["passed"] and independent["nearest_integer"] == production["nearest_integer"])
        else:
            agrees = None
        checks.append({
            "n": row["n"], "strength": strength, "seed": seed, "kind": kind, "target": target,
            "beta_sha256": row["beta_sha256"], "production_status": production["status"],
            "production_value": production["value"], "production_nearest_integer": production["nearest_integer"],
            "independent": independent, "integer_agreement": agrees,
            "rejection_category_independently_checked": production["status"] != "ok",
        })
        print(
            f"r={strength} seed={seed} kind={kind} target={target} "
            f"production={production['status']}/{production['nearest_integer']} "
            f"independent={independent['status']}/{independent['nearest_integer']} raw={independent['value']}"
        )
    valid_agreements = [row["integer_agreement"] for row in checks if row["integer_agreement"] is not None]
    rejection_checks = [row for row in checks if row["rejection_category_independently_checked"]]
    passed = len(checks) == len(selected) and all(valid_agreements) and len(rejection_checks) == 2 and len(checks) == 14
    output = {
        "schema": "floquet-bdg-tbc-disorder-independent-v1",
        "method": "independent vector-mu Schur reconstruction and unwrapped determinant phase",
        "nominal_step": args.nominal_step,
        "selected_count": len(checks), "rejection_category_count": len(rejection_checks),
        "checks": checks, "passed": passed,
        "scope": "selected finite quadratic realizations; does not convert production not_converged rows into ok",
    }
    (ROOT / args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("selected", len(checks), "rejection_categories", len(rejection_checks), "passed", passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
