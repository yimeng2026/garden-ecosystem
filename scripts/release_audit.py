"""Fail the release on credential-shaped content or disallowed tracked assets."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {"node_modules", "upstream", ".venv", "__pycache__", "word-qa"}
MODEL_SUFFIXES = {".safetensors", ".ckpt", ".gguf", ".pt", ".pth", ".onnx"}
SECRET_PATTERNS = {
    "github_token": re.compile(rb"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "provider_key": re.compile(rb"sk-[A-Za-z0-9]{20,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "google_api_key": re.compile(rb"AIza[0-9A-Za-z_-]{35}"),
}


def main() -> None:
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    failures = []
    text_files = 0
    for name in paths:
        path = ROOT / name
        if set(path.parts) & FORBIDDEN_PARTS or path.suffix.lower() in MODEL_SUFFIXES:
            failures.append(f"disallowed tracked asset: {name}")
        if path.name.startswith(".env") and path.name != ".env.example":
            failures.append(f"credential environment file: {name}")
        if path.suffix.lower() in {".docx", ".png", ".jpg", ".zip", ".pdf"}:
            continue
        data = path.read_bytes()
        text_files += 1
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(data):
                failures.append(f"{kind}: {name}")
    tracked_py = [name for name in paths if name.endswith(".py")]
    expected = {"README.md", "LICENSE", "NOTICE.md", "UPSTREAM.md", "pyproject.toml"}
    missing = sorted(name for name in expected if name not in paths)
    failures.extend(f"missing release file: {name}" for name in missing)
    report = {"tracked_files": len(paths), "python_files": len(tracked_py),
              "text_files_scanned": text_files, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
