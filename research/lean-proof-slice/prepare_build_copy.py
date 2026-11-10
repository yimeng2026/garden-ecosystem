"""Create an isolated D: build copy without deleting or modifying the source."""

import json
from pathlib import Path
import shutil

ROOT = Path("C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-isotope-dft-audit/research/lean-proof-slice")
DEST = Path("D:/migration/lean-proof-slice-build")


def metrics(path):
    files = [item for item in path.rglob("*") if item.is_file()]
    return {"files": len(files), "bytes": sum(item.stat().st_size for item in files)}


def main():
    if DEST.exists():
        raise FileExistsError(f"refusing to overwrite existing build copy: {DEST}")
    shutil.copytree(ROOT, DEST, ignore=shutil.ignore_patterns("__pycache__", "node_modules", "word-qa"))
    source_metrics = metrics(ROOT / ".lake")
    dest_metrics = metrics(DEST / ".lake")
    if source_metrics != dest_metrics:
        raise ValueError(f"build copy metrics mismatch: {source_metrics} != {dest_metrics}")
    result = {
        "source": str(ROOT),
        "destination": str(DEST),
        "source_metrics": source_metrics,
        "destination_metrics": dest_metrics,
        "source_deleted": False,
        "acl_modified": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
