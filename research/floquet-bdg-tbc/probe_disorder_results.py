"""Print concise raw diagnostics; no result modification."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
for row in data["realizations"]:
    if row["strength"] != 0.2:
        continue
    print(f"seed={row['seed']} kind={row['kind']}")
    for target in ("zero", "pi"):
        w = row[target]
        endpoint = row["endpoint"][target]
        print(target, json.dumps({
            "status": w["status"], "reason": w["reason"], "raw": w["value"],
            "integer": w["nearest_integer"], "mesh": w["mesh_difference"],
            "residual": w["integer_residual"], "gap": w["min_bulk_gap"],
            "grid_statuses": [item["status"] for item in w["rows"]],
            "grid_raw": [item["value"] for item in w["rows"]],
            "grid_residual": [item["integer_residual"] for item in w["rows"]],
            "endpoint_joint_pass": endpoint["joint_pass"],
            "endpoint_distances": endpoint["distances"],
            "endpoint_separation": endpoint["separation_ratios"],
            "endpoint_edge_weight": endpoint["edge_weight"],
        }, ensure_ascii=False))
