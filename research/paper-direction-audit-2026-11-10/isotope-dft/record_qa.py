import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa" / "report.json"
DOCX = ROOT / "REVIEW.docx"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 4 or report.get("rendered") != 4:
    raise SystemExit("Expected four final rendered pages")
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
    "reviewedPages": [1, 2, 3, 4],
    "nearBlankPagesReviewed": [],
    "observations": [
        {"page": 1, "observation": "封面与六条目录完整；缓存页码 2、2、3、3、4、4 与实际一致。"},
        {"page": 2, "observation": "六来源、四方向表、原生同位素分式、三组 α 长小数及脚注 1–2 完整，无裁切。"},
        {"page": 3, "observation": "压力表后紧接双面板图和结果解释；Eliashberg／SCDFT 分轨清晰，DFT 表及脚注 3–4 完整。"},
        {"page": 4, "observation": "DFT 表末行、八项勘误、六项开放边界、范围说明及脚注 5–6 完整；原第五页内容已收回，无内容删除。"},
    ],
    "contentLossReview": [
        {
            "element": "w:lvlOverride",
            "count": 1,
            "disposition": "默认编号级别覆盖不被本文使用；显式中文标题编号均可见，未观察到对应内容丢失。",
        }
    ],
    "layoutCorrections": [
        "初版第五页只有开放边界表后三行与两段说明，不记为理想分页。",
        "表格字号由 17 调整为 16、行距由 220 调整为 210、上下边距由 60 调整为 40；最终收回四页，内容未删除。",
        "缓存目录同步修正为 2、2、3、3、4、4。",
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
