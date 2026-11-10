"""Read-only text and repository checks for the theory/breakthrough audit."""

import json
import re
from pathlib import Path

MODULES = [
    "Superconductivity.SymmetryClassification",
    "Superconductivity.MaterialFamily",
    "Superconductivity.ManyBodyPairing",
    "Superconductivity.MetaTheorems",
    "Superconductivity.Renormalization",
]
CORE_THEOREMS = [
    "room_temperature_superconductivity_necessity",
    "constructive_room_temp_sc_exists",
    "pairing_temperature_mapping",
]


def find_source_root():
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("toe-sylva-audit room_temp_sc root")


def scan_theory():
    root = find_source_root()
    path = root / "organized/03-理论框架/01-理论框架.md"
    text = path.read_text(encoding="utf-8")
    admit_count = len(re.findall(r"^\s*admit\b", text, flags=re.MULTILINE))
    sorry_count = len(re.findall(r"^\s*sorry\b", text, flags=re.MULTILINE))
    repository = root.parents[1]
    lean_files = list(repository.rglob("*.lean"))
    lean_text = {}
    for lean_path in lean_files:
        lean_text[lean_path] = lean_path.read_text(encoding="utf-8", errors="replace")
    module_matches = {
        module: [path.relative_to(repository).as_posix() for path, content in lean_text.items() if module in content]
        for module in MODULES
    }
    theorem_matches = {
        theorem: [path.relative_to(repository).as_posix() for path, content in lean_text.items() if theorem in content]
        for theorem in CORE_THEOREMS
    }
    return {
        "path": path,
        "admit_count": admit_count,
        "sorry_count": sorry_count,
        "proof_debt_total": admit_count + sorry_count,
        "module_references": MODULES,
        "module_matches": module_matches,
        "repository_module_match_count": sum(bool(paths) for paths in module_matches.values()),
        "core_theorem_matches": theorem_matches,
        "lean_file_count_searched": len(lean_files),
        "search_scope": "toe-sylva-audit/**/*.lean",
    }


def scan_breakthrough():
    root = find_source_root()
    path = root / "organized/06-突破详解/01-2025年10月突破.md"
    text = path.read_text(encoding="utf-8")
    date_match = re.search(r"文档生成时间\*{0,2}:\s*(\d{4}-\d{2}-\d{2})", text)
    if not date_match:
        raise ValueError("breakthrough document date not found")
    return {
        "path": path,
        "document_date": date_match.group(1),
        "cited_preprint_month": "2025-10",
        "metadata_date_precedes_cited_preprint": date_match.group(1) < "2025-10-01",
        "contains_298_316_range": "298-316" in text,
        "contains_13_independent_experiments": "13次独立实验" in text,
        "contains_p6mmm_quasi_2d_claim": "P6/mmm (准二维" in text,
        "contains_perfect_theorem_verification": "完美验证论文核心定理" in text,
        "contains_first_room_temperature_claim": "人类历史上首次实现室温超导" in text,
    }


if __name__ == "__main__":
    theory = scan_theory()
    breakthrough = scan_breakthrough()
    printable = {
        "theory": {key: value for key, value in theory.items() if key != "path"},
        "breakthrough": {key: value for key, value in breakthrough.items() if key != "path"},
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2, default=str))
