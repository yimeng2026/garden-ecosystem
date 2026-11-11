"""Compute only the preregistered new seed=4..7 profile cells."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_multi_seed import compute_case  # noqa: E402

PROTOCOL = ROOT / "repeated_category_protocol.json"
GRID = [(n, strength, seed) for n in (400, 600) for strength in (0.05, 0.1) for seed in (4, 5, 6, 7)]


def main():
    protocol_hash = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    output = ROOT / "category_new_cells.json"
    if output.exists():
        stored = json.loads(output.read_text(encoding="utf-8"))
        if stored["protocol_sha256"] != protocol_hash or len(stored["cases"]) != 16:
            raise ValueError("Existing new-cell registry does not match the frozen protocol")
        print(json.dumps({"merge_only": True, "cases": 16, "protocol_sha256": protocol_hash}, ensure_ascii=False))
        return 0
    cases = [compute_case(n, strength, seed) for n, strength, seed in GRID]
    data = {
        "schema": "floquet-bdg-category-new-cells-v1",
        "protocol_sha256": protocol_hash,
        "new_seeds": [4, 5, 6, 7],
        "new_winding_computed": False,
        "n640_computed": False,
        "cases": cases,
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"new_cells": len(cases), "new_seeds": data["new_seeds"], "new_winding_computed": False, "n640_computed": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
