"""Read-only source, lineage and production-asset inventory."""

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

from test_magazine_design_audit import EXPECTED_HASHES

AUDIT = Path(__file__).resolve().parent
ORGANIZED_NAMES = {
    "magazine_readme": "01-杂志说明.md",
    "magazine_intro": "02-杂志简介.md",
    "pixel_system": "03-黑白像素系统.md",
    "vi_design": "04-VI设计.md",
    "layout_system": "05-排版系统.md",
    "content_architecture": "06-内容架构.md",
    "web_layout": "07-网页风格排版.md",
    "chat_culture": "08-网聊文化融入.md",
    "page_designs": "09-页面设计.md",
    "print_guide": "10-印刷指南.md",
    "design_notes": "11-设计笔记.md",
}
ORIGINAL_TO_ORGANIZED = {
    "vi_design.md": "vi_design",
    "layout_system.md": "layout_system",
    "content_architecture.md": "content_architecture",
    "chat_culture_integration.md": "chat_culture",
    "BLACK_WHITE_PIXEL_SYSTEM.md": "pixel_system",
    "web_style_layout.md": "web_layout",
    "page_designs.md": "page_designs",
}


def digest(path, algorithm="sha256", normalized_lf=False):
    data = path.read_bytes()
    if normalized_lf:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.new(algorithm, data).hexdigest()


def source_roots():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate, candidate / "organized/11-杂志设计", candidate / "magazine"
    raise FileNotFoundError("room_temp_sc source root")


def source_paths(paper_root, organized, magazine):
    paths = {key: organized / name for key, name in ORGANIZED_NAMES.items()}
    paths.update({
        "generator": magazine / "generate_pdf.py",
        "delivery_report": magazine / "DELIVERY_REPORT.md",
        "file_index": magazine / "file_index.json",
        "checksums": magazine / "checksums.md5",
        "handbook_review": AUDIT.parent / "handbook-chapters/review.json",
        "technical_review": AUDIT.parent / "technical-docs/review.json",
    })
    return paths


def display_path(source_id):
    if source_id in ORGANIZED_NAMES:
        return f"toe-sylva-audit/papers/room_temp_sc/organized/11-杂志设计/{ORGANIZED_NAMES[source_id]}"
    if source_id in {"generator", "delivery_report", "file_index", "checksums"}:
        filename = {
            "generator": "generate_pdf.py",
            "delivery_report": "DELIVERY_REPORT.md",
            "file_index": "file_index.json",
            "checksums": "checksums.md5",
        }[source_id]
        return f"toe-sylva-audit/papers/room_temp_sc/magazine/{filename}"
    return {"handbook_review": "handbook-chapters/review.json", "technical_review": "technical-docs/review.json"}[source_id]


def pdf_inventory(path):
    row = {"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path)}
    try:
        reader = PdfReader(path, strict=False)
        first = reader.pages[0].mediabox
        row.update({
            "pages": len(reader.pages),
            "first_page_width_mm": round(float(first.width) * 25.4 / 72, 3),
            "first_page_height_mm": round(float(first.height) * 25.4 / 72, 3),
            "metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
            "has_output_intent": "/OutputIntents" in reader.trailer["/Root"],
            "pdf_x_marker_present": False,
        })
        with path.open("rb") as handle:
            row["pdf_x_marker_present"] = any(token in handle.read() for token in (b"GTS_PDFXVersion", b"pdfxid"))
    except Exception as error:
        row["read_error"] = f"{type(error).__name__}: {error}"
    return row


def build_inventory():
    paper_root, organized, magazine = source_roots()
    paths = source_paths(paper_root, organized, magazine)
    sources = []
    for source_id, expected in EXPECTED_HASHES.items():
        actual = digest(paths[source_id])
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({"id": source_id, "path": display_path(source_id), "sha256": actual, "read_only": True})

    expected_md5 = {}
    for line in paths["checksums"].read_text(encoding="utf-8").splitlines():
        value, filename = line.split(maxsplit=1)
        expected_md5[filename] = value
    lineage_rows = []
    for original, source_id in ORIGINAL_TO_ORGANIZED.items():
        organized_path = paths[source_id]
        normalized = digest(organized_path, "md5", normalized_lf=True)
        lineage_rows.append({
            "original_name": original,
            "organized_source_id": source_id,
            "original_path_exists": (magazine / original).exists(),
            "organized_path_exists": organized_path.exists(),
            "expected_md5": expected_md5[original],
            "raw_md5": digest(organized_path, "md5"),
            "normalized_lf_md5": normalized,
            "normalized_lf_matches": normalized == expected_md5[original],
        })

    pdfs = [pdf_inventory(path) for path in sorted(magazine.glob("*.pdf"))]
    generator_text = paths["generator"].read_text(encoding="utf-8")
    archive = paper_root / "Sylva_Magazine_RoomTempSC_COMPLETE.tar.gz"
    vi_candidates = [
        magazine / "assets/logo-kit.zip",
        magazine / "assets/color-palette.zip",
        magazine / "assets/fonts",
        magazine / "assets/textures",
        magazine / "assets/templates",
    ]
    inventory = {
        "schema": "magazine-design-source-inventory-v1",
        "sources": sources,
        "lineage": {
            "rows": lineage_rows,
            "normalized_lf_md5_matches": sum(row["normalized_lf_matches"] for row in lineage_rows),
            "original_markdown_paths_missing": sum(not row["original_path_exists"] for row in lineage_rows),
            "organized_documents_present": sum(path.exists() for path in organized.glob("*.md")),
            "content_loss_inferred_from_raw_md5": False,
        },
        "assets": {
            "pdf_count": len(pdfs),
            "pdfs": pdfs,
            "indd_templates_found": len(list(paper_root.rglob("*.indd"))),
            "vi_asset_pack_found": any(path.exists() for path in vi_candidates),
            "claimed_archive_found": archive.exists(),
            "claimed_archive_path": str(archive),
            "checksum_file_exists": paths["checksums"].exists(),
            "historical_file_index_exists": paths["file_index"].exists(),
        },
        "generator": {
            "missing_design_docs": sum(not (magazine / name).exists() for name in ORIGINAL_TO_ORGANIZED),
            "preview_characters": 500 if "content[:500]" in generator_text else None,
            "overwrites_three_source_docs": all(token in generator_text for token in ("self.create_readme()", "self.create_design_notes()", "self.create_print_guide()")),
            "complete_magazine_generator": "content[:500]" not in generator_text,
            "executed": False,
            "execution_reason": "run() overwrites README.md, DESIGN_NOTES.md and PRINT_GUIDE.md in the read-only source directory",
        },
    }
    return inventory


def main():
    inventory = build_inventory()
    output = AUDIT / "sources/source-inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "sources": len(inventory["sources"]),
        "lf_md5_matches": inventory["lineage"]["normalized_lf_md5_matches"],
        "original_paths_missing": inventory["lineage"]["original_markdown_paths_missing"],
        "pdf_count": inventory["assets"]["pdf_count"],
        "pdf_pages": {row["name"]: row.get("pages") for row in inventory["assets"]["pdfs"]},
        "indd_templates_found": inventory["assets"]["indd_templates_found"],
        "archive_found": inventory["assets"]["claimed_archive_found"],
        "generator_executed": inventory["generator"]["executed"],
        "inventory_sha256": digest(output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
