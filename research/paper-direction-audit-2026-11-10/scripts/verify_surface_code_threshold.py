"""Independently verify every stored surface-code result and summary."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from surface_code_stats import estimate_crossings, protocol_digest, wilson_interval

AUDIT_DIR = Path(__file__).resolve().parents[1]
RESULTS = AUDIT_DIR / "surface-code-threshold" / "results.json"
CSV_RESULTS = AUDIT_DIR / "surface-code-threshold" / "results.csv"
PROTOCOL = AUDIT_DIR / "surface-code-threshold" / "protocol.json"
VERIFICATION = AUDIT_DIR / "surface-code-threshold" / "verification.json"


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)


def verify_payload(payload: dict, protocol_sha256: str) -> dict:
    mismatches = []
    if payload.get("protocol_sha256") != protocol_sha256:
        mismatches.append("protocol_sha256 differs from the frozen protocol")
    points = payload.get("points", [])
    for index, point in enumerate(points):
        expected_rate, low, high = wilson_interval(point["errors"], point["shots"])
        for field, expected in [("rate", expected_rate), ("wilson95_low", low), ("wilson95_high", high)]:
            if not close(point[field], expected):
                mismatches.append(f"point {index}: {field} differs")
        expected_log = math.log10(expected_rate) if expected_rate > 0 else None
        if (point["log10_rate"] is None) != (expected_log is None) or (
                expected_log is not None and not close(point["log10_rate"], expected_log)):
            mismatches.append(f"point {index}: log10_rate differs")
    expected_summary = estimate_crossings(points)
    if payload.get("crossing_summary") != expected_summary:
        mismatches.append("crossing_summary differs from independent recomputation")
    return {"protocol_sha256": protocol_sha256, "point_count": len(points), "mismatches": mismatches}


def verify_csv(path: Path, points: list[dict]) -> list[str]:
    mismatches = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(points):
        return [f"CSV row count {len(rows)} differs from JSON {len(points)}"]
    for index, (row, point) in enumerate(zip(rows, points)):
        for field in ("distance", "shots", "seed", "errors"):
            if int(row[field]) != point[field]:
                mismatches.append(f"CSV row {index}: {field} differs")
        for field in ("p", "rate", "wilson95_low", "wilson95_high", "log10_rate"):
            if row[field] == "" and point[field] is None:
                continue
            if row[field] == "" or point[field] is None or not close(float(row[field]), point[field]):
                mismatches.append(f"CSV row {index}: {field} differs")
    return mismatches


def main() -> int:
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    protocol_sha256 = protocol_digest(PROTOCOL.read_bytes())
    report = verify_payload(payload, protocol_sha256)
    report["csv_mismatches"] = verify_csv(CSV_RESULTS, payload["points"])
    report["status"] = "pass" if not report["mismatches"] and not report["csv_mismatches"] else "fail"
    VERIFICATION.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
