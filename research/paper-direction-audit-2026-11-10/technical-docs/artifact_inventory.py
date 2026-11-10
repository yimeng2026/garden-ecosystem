"""Read-only inventory of claimed delivery artifacts."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = next(
    parent / "toe-sylva-audit/papers/room_temp_sc"
    for parent in ROOT.parents
    if (parent / "toe-sylva-audit/papers/room_temp_sc").is_dir()
)


def exists(relative):
    return (SOURCE_ROOT / relative).exists()


def main():
    tex_variants = [
        "manuscript.tex",
        "versions/manuscript_nature.tex",
        "versions/manuscript_science.tex",
        "versions/manuscript_arxiv.tex",
    ]
    methods = json.loads((ROOT.parent / "room-temp-methods/review.json").read_text(encoding="utf-8"))
    inventory = {
        "scope": "current papers/room_temp_sc workspace; absence means not verified here, not proof of historical nonexistence",
        "tar_exists": exists("room_temp_sc_paper_FINAL_v2.tar.gz"),
        "md5_verifiable": exists("room_temp_sc_paper_FINAL_v2.tar.gz"),
        "claimed_md5": "6147303abc3ec02cfea5f75ee1fe4b45",
        "figures_found": len(list(SOURCE_ROOT.rglob("figure*.png"))),
        "references_enhanced_found": int(exists("references_enhanced.bib")),
        "prl_tex_exists": exists("versions/manuscript_prl.tex"),
        "claimed_markdown_missing": not exists("manuscript.md"),
        "tex_variants_present": sum(exists(path) for path in tex_variants),
        "tex_variant_paths": {path: exists(path) for path in tex_variants},
        "expected_lean_exists": exists("RoomTempSuperconductivity.lean"),
        "alternate_lean_exists": exists("room_temp_sc_Formalization.lean"),
        "expected_si_exists": exists("supplementary/supplementary_info.md"),
        "alternate_si_exists": exists("organized/10-技术文档/06-补充信息.md"),
        "si_placeholder_count": methods["evidence"]["si"]["placeholder_count"],
        "negative_result_scope_limited": True,
    }
    output = ROOT / "sources/artifact-inventory.json"
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory, ensure_ascii=False, indent=2))
    print("SHA-256:", hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
