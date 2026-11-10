"""Build read-only source and 44-document coverage inventory."""

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from test_project_intro_audit import EXPECTED_HASHES

AUDIT = Path(__file__).resolve().parent
REVIEW_SOURCES = {
    "main_claims_review": "main-claims",
    "theory_review": "theory-breakthrough",
    "validation_review": "validation-materials",
    "isotope_review": "isotope-dft",
    "dmrg_review": "dmrg-qec",
    "data_review": "data-governance",
    "handbook_review": "handbook-chapters",
    "methods_review": "room-temp-methods",
    "technical_review": "technical-docs",
    "magazine_review": "magazine-design",
}
FINAL_DOCS = {
    "directory_index": ("00-目录索引.md", ["coverage_governance"]),
    "project_intro": ("01-封面与介绍/01-项目说明.md", ["conditional_formalization"]),
    "handbook_intro": ("01-封面与介绍/02-手册说明.md", ["handbook_reference_governance"]),
    "magazine_plan": ("01-封面与介绍/03-杂志简介.md", ["public_communication"]),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def roots():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate, candidate / "organized"
    raise FileNotFoundError("room_temp_sc organized root")


def source_paths(paper, organized):
    paths = {key: organized / relative for key, (relative, _) in FINAL_DOCS.items()}
    paths.update({
        "base_bib": organized / "09-参考文献/01-参考文献.bib",
        "enhanced_bib": organized / "09-参考文献/02-增强参考文献.bib",
        "original_readme": paper / "README.md",
        "handbook_task": paper / "HANDBOOK_TASK.md",
        "handbook_docx": paper / "handbook/room_temp_sc_handbook.docx",
    })
    for source_id, batch in REVIEW_SOURCES.items():
        paths[source_id] = AUDIT.parent / batch / "review.json"
    return paths


def display_path(source_id):
    if source_id in FINAL_DOCS:
        return f"toe-sylva-audit/papers/room_temp_sc/organized/{FINAL_DOCS[source_id][0]}"
    special = {
        "base_bib": "toe-sylva-audit/papers/room_temp_sc/organized/09-参考文献/01-参考文献.bib",
        "enhanced_bib": "toe-sylva-audit/papers/room_temp_sc/organized/09-参考文献/02-增强参考文献.bib",
        "original_readme": "toe-sylva-audit/papers/room_temp_sc/README.md",
        "handbook_task": "toe-sylva-audit/papers/room_temp_sc/HANDBOOK_TASK.md",
        "handbook_docx": "toe-sylva-audit/papers/room_temp_sc/handbook/room_temp_sc_handbook.docx",
    }
    if source_id in special:
        return special[source_id]
    return f"{REVIEW_SOURCES[source_id]}/review.json"


def coverage_rows(organized):
    rows = []
    batch_open_false = {}
    batch_direction_counts = {}
    for review_id, batch in REVIEW_SOURCES.items():
        review_path = AUDIT.parent / batch / "review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        direction_ids = [row["id"] for row in review.get("directions", [])]
        batch_direction_counts[batch] = len(direction_ids)
        batch_open_false[batch] = sum(value is False for value in review.get("open_boundaries", {}).values())
        for source in review["sources"]:
            marker = "/organized/"
            if marker not in source["path"] or not source["path"].endswith(".md"):
                continue
            relative = source["path"].split(marker, 1)[1]
            actual = organized / relative
            actual_hash = sha256(actual)
            if actual_hash != source["sha256"]:
                raise ValueError(f"coverage source changed: {relative}: {actual_hash} != {source['sha256']}")
            rows.append({
                "path": relative,
                "source_id": source["id"],
                "source_sha256": actual_hash,
                "batch": batch,
                "review_path": f"{batch}/review.json",
                "review_sha256": sha256(review_path),
                "direction_ids": direction_ids,
                "direction_scope": "shared_batch",
                "represents_new_theory": False,
            })
    for source_id, (relative, direction_ids) in FINAL_DOCS.items():
        rows.append({
            "path": relative,
            "source_id": source_id,
            "source_sha256": sha256(organized / relative),
            "batch": "project-intro",
            "review_path": "project-intro/review.json",
            "review_sha256": None,
            "direction_ids": direction_ids,
            "direction_scope": "current_document",
            "represents_new_theory": False,
        })
    return sorted(rows, key=lambda row: row["path"]), batch_open_false, batch_direction_counts


def handbook_metadata(path):
    with zipfile.ZipFile(path) as package:
        app = ET.fromstring(package.read("docProps/app.xml"))
        properties = {element.tag.split("}")[-1]: element.text for element in app}
        document = package.read("word/document.xml")
        return {
            "exists": True,
            "bytes": path.stat().st_size,
            "app_pages": int(properties.get("Pages", 0)),
            "app_words": int(properties.get("Words", 0)),
            "media_files": len([name for name in package.namelist() if name.startswith("word/media/")]),
            "has_omml": b"<m:oMath" in document,
            "explicit_page_breaks": document.count(b'w:type="page"'),
            "approx_50_pages_verified": False,
        }


def build_inventory():
    paper, organized = roots()
    paths = source_paths(paper, organized)
    sources = []
    for source_id, expected in EXPECTED_HASHES.items():
        actual = sha256(paths[source_id])
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({"id": source_id, "path": display_path(source_id), "sha256": actual, "read_only": True})

    rows, batch_open_false, batch_direction_counts = coverage_rows(organized)
    actual_paths = sorted(path.relative_to(organized).as_posix() for path in organized.rglob("*.md"))
    covered_paths = [row["path"] for row in rows]
    prior_paths = {row["path"] for row in rows if row["batch"] != "project-intro"}
    duplicates = sorted(path for path, count in Counter(covered_paths).items() if count > 1)
    uncovered = sorted(set(actual_paths) - set(covered_paths))
    unexpected = sorted(set(covered_paths) - set(actual_paths))
    if unexpected:
        raise ValueError(f"coverage paths missing from organized tree: {unexpected}")

    index_text = paths["directory_index"].read_text(encoding="utf-8")
    project_text = paths["project_intro"].read_text(encoding="utf-8")
    original_readme = paths["original_readme"].read_text(encoding="utf-8")
    base_bib = paths["base_bib"].read_text(encoding="utf-8")
    enhanced_bytes = paths["enhanced_bib"].read_bytes()
    enhanced_text = enhanced_bytes.decode("utf-8")
    modules = [
        "Superconductivity.SymmetryClassification",
        "Superconductivity.MaterialFamily",
        "Superconductivity.ManyBodyPairing",
        "Superconductivity.MetaTheorems",
        "Superconductivity.Renormalization",
    ]
    handbook = handbook_metadata(paths["handbook_docx"])
    inventory = {
        "schema": "organized-coverage-inventory-v1",
        "sources": sources,
        "coverage": {
            "rows": rows,
            "actual_markdown_count": len(actual_paths),
            "prior_covered_count": len(prior_paths),
            "current_batch_count": len(FINAL_DOCS),
            "covered_count": len(set(covered_paths)),
            "uncovered": uncovered,
            "duplicates": duplicates,
            "unexpected": unexpected,
            "batch_review_count": len(REVIEW_SOURCES),
            "batch_counts": dict(sorted(Counter(row["batch"] for row in rows).items())),
            "batch_direction_counts": batch_direction_counts,
            "batch_open_false": batch_open_false,
            "prior_open_false_items": sum(batch_open_false.values()),
            "organized_44_coverage_complete": len(actual_paths) == 44 and not uncovered and not duplicates,
            "whole_repository_research_complete": False,
        },
        "evidence": {
            "index": {
                "omitted_top_level_groups": [f"{number:02d}" for number in range(12, 22)],
                "prl_claimed": "PRL" in index_text,
                "prl_found": any("prl" in path.stem.lower() for path in (organized / "02-主论文").glob("*.md")),
                "enhanced_bib_recommended": "02-增强参考文献.bib" in index_text,
            },
            "references": {
                "base_entries": len(re.findall(r"(?m)^@", base_bib)),
                "base_placeholders": len(re.findall(r"(?m)^% \[TO_BE_COMPLETED", base_bib)),
                "base_placeholder_token_occurrences": base_bib.count("TO_BE_COMPLETED"),
                "enhanced_bytes": len(enhanced_bytes),
                "enhanced_entries": len(re.findall(r"(?m)^@", enhanced_text)),
                "enhanced_exact_content": enhanced_text.strip(),
                "missing_modern_identifiers": [identifier for identifier in ("2510.01273", "2605.29985", "2401840121") if identifier not in base_bib],
                "enhanced_usable": bool(re.search(r"(?m)^@", enhanced_text)),
            },
            "formalization": {
                "theoretical_framework_found": (paper / "theoretical_framework.md").exists(),
                "expected_lean_found": (paper / "RoomTempSuperconductivity.lean").exists(),
                "m1_m5_modules_found": sum(any(paper.rglob(f"{module}.lean")) for module in modules),
                "m1_m5_todo_present": "实现五个形式化模块" in project_text,
                "sorry_present": "admit/sorry" in project_text,
                "no_error_claim": "不会报错" in project_text,
                "readme_version_mismatch": "v7.33" in original_readme and "0.1-alpha" in project_text,
                "original_readme_lf_equal": paths["original_readme"].read_bytes().replace(b"\r\n", b"\n") == paths["project_intro"].read_bytes().replace(b"\r\n", b"\n"),
            },
            "timeline": {
                "handbook_update": "2025年4月",
                "cited_breakthrough": "2025年10月",
                "handbook_update_precedes_october_breakthrough": "最后更新**：2025年4月" in paths["handbook_intro"].read_text(encoding="utf-8") and "2025年10月" in paths["handbook_intro"].read_text(encoding="utf-8"),
            },
            "handbook_asset": handbook,
        },
    }
    return inventory


def main():
    inventory = build_inventory()
    output = AUDIT / "sources/coverage-inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = inventory["coverage"]
    print(json.dumps({
        "sources": len(inventory["sources"]),
        "actual": coverage["actual_markdown_count"],
        "prior": coverage["prior_covered_count"],
        "current": coverage["current_batch_count"],
        "covered": coverage["covered_count"],
        "uncovered": coverage["uncovered"],
        "duplicates": coverage["duplicates"],
        "prior_open_false_items": coverage["prior_open_false_items"],
        "inventory_sha256": sha256(output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
