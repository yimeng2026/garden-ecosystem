"""Independent original expm+Schur determinant checks for scale diagnostics."""

import argparse
import json
from pathlib import Path

import numpy as np

from run_disorder import beta_for
from verify_tbc import determinant_winding

ROOT = Path(__file__).resolve().parent


def verify(n, step):
    if not 0 < step < np.pi:
        raise ValueError("independent step must be positive and less than pi")
    data = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
    row = next(row for row in data["rows"] if row["n"] == n)
    beta = beta_for(row["seed"], n)
    independent = determinant_winding(
        n, np.full(n, 2.5), row["strength"] * beta, 7.0, 0.0, nominal_step=step,
    )
    production = row["zero"]
    agreement = bool(independent["passed"] and independent["nearest_integer"] == production["nearest_integer"])
    output = {
        "schema": "floquet-bdg-scale-independent-v1",
        "n": n, "strength": row["strength"], "seed": row["seed"], "target": "zero",
        "method": "original expm+Schur determinant phase",
        "independent_nominal_step": step,
        "production_status": production["status"], "production_nearest_integer": production["nearest_integer"],
        "production_value": production["value"], "production_min_bulk_gap": production["min_bulk_gap"],
        "endpoint_joint_pass": row["endpoint"]["zero"]["joint_pass"],
        "independent": independent, "integer_agreement": agreement,
    }
    (ROOT / f"scale_independent_n{n}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in output.items() if key != "independent"}, ensure_ascii=False))
    print("independent", json.dumps(independent, ensure_ascii=False))
    return 0 if agreement else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, choices=(400, 600), required=True)
    parser.add_argument("--step", type=float, default=0.1)
    args = parser.parse_args()
    return verify(args.n, args.step)


if __name__ == "__main__":
    raise SystemExit(main())
