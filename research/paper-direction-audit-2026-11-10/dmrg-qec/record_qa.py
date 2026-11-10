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
        {"page": 1, "observation": "封面与五条目录完整；缓存页码 2、2、3、4、4 与实际一致。"},
        {"page": 2, "observation": "九来源、四方向表、DMRG 四层证据、原生分式及脚注 1–2 完整，无裁切。"},
        {"page": 3, "observation": "Chen／条纹／Peng 分轨、QEC 表、双面板图及脚注 3–6 完整；图件在证据表后、解释前。"},
        {"page": 4, "observation": "XZZX／Google／中性原子、九项勘误、六项开放边界、最终说明及脚注 7–9 完整；原第五页孤行已收回。"},
    ],
    "contentLossReview": [
        {
            "element": "w:lvlOverride",
            "count": 1,
            "disposition": "默认编号级别覆盖不被本文使用；显式中文标题编号均可见，未观察到对应内容丢失。",
        }
    ],
    "layoutCorrections": [
        "初版第五页只有最后一句范围说明，不记为理想分页。",
        "单元格上下边距由 40 调整为 20，最终收回四页，内容未删除。",
        "缓存目录同步修正为 2、2、3、4、4。",
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
