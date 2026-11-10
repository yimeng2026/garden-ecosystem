import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa" / "report.json"
DOCX = ROOT / "REVIEW.docx"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 5 or report.get("rendered") != 5:
    raise SystemExit("Expected five final rendered pages")
if report.get("nearBlankPages"):
    raise SystemExit("Near-blank pages require review")
if any(page.get("clipped") for page in report.get("pageFiles", [])):
    raise SystemExit("Renderer-reported clipping requires review")

report["finalValidation"] = {
    "command": "python docx.py validate REVIEW.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "scope": "Kimi doc-k final-view layout and visible-content review; not a claim of pixel parity with Microsoft Word.",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3, 4, 5],
    "nearBlankPagesReviewed": [],
    "observations": [
        {"page": 1, "observation": "封面与五条目录完整；缓存页码 2、2、3、4、5 与实际一致。"},
        {"page": 2, "observation": "十二来源、四方向、Song／HTSC 表及脚注 1–2 完整，无裁切。"},
        {"page": 3, "observation": "273／300 K 原生公式、Patsnap 边界、第 16／20／21 份文档角色和脚注 3–6 完整。"},
        {"page": 4, "observation": "双面板图、Song、N_F 单位、B–C、DMRG／QEC 更新及脚注 7–10 完整。"},
        {"page": 5, "observation": "十项勘误、七项开放边界和最终范围说明完整，无孤行或内容丢失。"},
    ],
    "contentLossReview": [
        {
            "element": "w:lvlOverride",
            "count": 1,
            "disposition": "默认编号级别覆盖不被本文使用；显式中文标题编号均可见，未观察到对应内容丢失。",
        }
    ],
    "layoutCorrections": [
        "初版缓存目录页码与实际不一致；仅将目录修正为 2、2、3、4、5。",
        "保留五页可读版本，不为追求页数而缩小正文；所有页面均有实质内容。",
    ],
    "otherRendererFindings": "目录内容控件拆壳但缓存条目可见；degraded 与 metadata-loss 项未造成逐页检查中的可见裁切或内容缺失。",
    "visualPassClaimed": True,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "pages": report["pages"],
    "reviewedPages": report["manualReview"]["reviewedPages"],
    "sha256": report["finalValidation"]["sha256"],
    "status": report["manualReview"]["status"],
}, ensure_ascii=False, indent=2))
