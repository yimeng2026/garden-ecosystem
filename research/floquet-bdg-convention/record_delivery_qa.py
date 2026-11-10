"""Record the actual Word gate and unavailable render-process status without overclaiming."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDER = ROOT / "word-qa" / "report.json"
render = json.loads(RENDER.read_text(encoding="utf-8"))
record = {
    "schema": "floquet-bdg-convention-word-qa-v1",
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "validation": {
        "command": "PATH=/c/Program Files/nodejs:$PATH; DOCX_PY_NO_VENDOR=1; python .../kimi-word/scripts/docx.py build .../build_report.js .../REPORT.docx",
        "exit_code": 0,
        "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docx_sha256": hashlib.sha256((ROOT / "REPORT.docx").read_bytes()).hexdigest(),
        "results_sha256": hashlib.sha256((ROOT / "results.json").read_bytes()).hexdigest(),
    },
    "render_process": {
        "exit_code": 6,
        "error": "E_RENDER_FAILED: EPERM, Permission denied for the temporary doc-k path",
        "status": "unavailable_no_retry",
        "pages_reported_by_partial_output": render.get("pages"),
        "near_blank_pages_reported": render.get("nearBlankPages"),
    },
    "partial_image_observation": {
        "contact_sheet_read": True,
        "reviewed_pages": [1, 2, 3, 4, 5],
        "observations": "Existing page images show the cover/TOC, Fock correction, winding tables, open-chain tables/figure and errata/boundary sections without visible clipping. These images preceded the exit-6 process result and the final exponent-format-only rebuild, so they are not a final-view pass.",
        "visual_pass_claimed": False,
        "libreoffice_fallback_used": False,
        "render_retried": False,
    },
    "scope": {
        "structure_validation_passed": True,
        "final_visual_validation_passed": False,
        "scientific_material_or_experiment_validated": False,
    },
}
(ROOT / "delivery-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
render["processExitCode"] = 6
render["visualQA"] = {
    "status": "unavailable_no_retry",
    "reviewedPages": [1, 2, 3, 4, 5],
    "visualPassClaimed": False,
    "note": "Page images were inspected as partial evidence only; the render process exited 6 and the final document was rebuilt only to normalize exponent formatting. No final-view pass is claimed.",
}
RENDER.write_text(json.dumps(render, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, indent=2))
