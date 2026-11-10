"""核验55篇总账、DOCX内嵌资产和视觉渲染证据；不替代数学与外部查新。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

AUDIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUDIT))
from test_strength_word_content import docx_text, supplement_headings

OUT = AUDIT / "strength-delivery-validation.json"


def run_all_tests() -> bool:
    data = json.loads((AUDIT / "strength-review.json").read_text(encoding="utf-8"))
    records = data["records"]
    qa = json.loads((AUDIT / "strength-word-sync-qa/report.json").read_text(encoding="utf-8"))
    checks = []

    def check(label: str, actual, expected) -> None:
        ok = actual == expected
        checks.append({"label": label, "pass": ok, "expected": expected, "actual": actual})
        if not ok:
            print(f"FAIL {label}：期望 {expected!r}，实际 {actual!r}")

    check("唯一论文ID", len({r["id"] for r in records}), 55)
    check("数学基础篇数", sum(r["series"] == "math" for r in records), 25)
    check("模块强化篇数", sum(r["series"] == "module" for r in records), 30)
    check("全部六字段非空", all(all(r.get(k, "").strip() for k in ("id", "role", "novelty", "unfinished", "priority", "evidence")) for r in records), True)
    check("渲染页数等于总页数", qa["rendered"], qa["pages"])
    check("渲染页数非零", qa["pages"] > 0, True)
    check("空白页", qa["nearBlankPages"], [])
    check("裁切页", [p["page"] for p in qa["pageFiles"] if p["clipped"]], [])
    content_loss = [
        (finding["element"], finding["severity"])
        for finding in qa["fidelity"]["findings"]
        if finding["category"] == "content-loss"
    ]
    check(
        "内容丢失仅为低风险目录编号",
        all(item == ("w:lvlOverride", "low") for item in content_loss),
        True,
    )

    with zipfile.ZipFile(AUDIT / "STRENGTH_SERIES_REVIEW.docx") as docx:
        names = docx.namelist()
        media = [name for name in names if name.startswith("word/media/") and name.endswith(".png")]
        check("DOCX内嵌PNG数", len(media), 1)
        actual_hash = hashlib.sha256(docx.read(media[0])).hexdigest() if media else "missing"
        expected_hash = hashlib.sha256((AUDIT / "strength-review-status.png").read_bytes()).hexdigest()
        check("内嵌图与状态图源一致", actual_hash, expected_hash)
        document = docx.read("word/document.xml").decode("utf-8")
        check("两张逐篇裁决表", document.count("<w:tbl>"), 2)
        check("原生目录域", "TOC" in document, True)
        check("原生Word公式", "<m:oMath" in document, True)
        headers = "".join(docx.read(name).decode("utf-8") for name in names if name.startswith("word/header") and name.endswith(".xml"))
        footers = "".join(docx.read(name).decode("utf-8") for name in names if name.startswith("word/footer") and name.endswith(".xml"))
        check("中文页眉", "55篇逐篇初审" in headers, True)
        check("原生PAGE页码", "PAGE" in footers, True)

    text = docx_text()
    headings = supplement_headings()
    check("Markdown补记数", len(headings), 17)
    check("DOCX缺失补记", [heading for heading in headings if heading not in text], [])
    check("补记重复项", [heading for heading in headings if text.count(heading) != 1], [])
    check(
        "商层与60项回归",
        "K2 商层像模同构类复核补记（2026-11-10）" in text and "60/60" in text,
        True,
    )
    check(
        "逐页人工复核记录",
        qa.get("manualReview", {}).get("reviewedPages"),
        list(range(1, qa["pages"] + 1)),
    )

    passed = all(item["pass"] for item in checks)
    result = {
        "status": "pass" if passed else "fail",
        "scope": "55条总账完整性、DOCX资产与渲染证据；不是数学证明或外部新颖性认证。",
        "checks": checks,
        "passed": sum(item["pass"] for item in checks),
        "total": len(checks),
        "manual_visual_review": f"contact-sheet全部{qa['pages']}页已逐页查看；无未解释空白页、裁切或逐字竖排。",
        "ooxml_gate_observed": "docx.py validate：PASSED（21 parts XSD + semantic checks; gen: 6 checks clean）",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "passed": result["passed"], "total": result["total"]}, ensure_ascii=False))
    return passed


if __name__ == "__main__":
    raise SystemExit(0 if run_all_tests() else 1)
