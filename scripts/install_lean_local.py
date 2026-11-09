"""Install an official Lean release into this repository's ignored .tools directory."""
from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"
RELEASE_URL = "https://api.github.com/repos/leanprover/lean4/releases/tags/v4.35.0"
USER_AGENT = "garden-ecosystem-lean-bootstrap/1.0"


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> None:
    release = get_json(RELEASE_URL)
    version = release["tag_name"].lstrip("v")
    asset = next(item for item in release["assets"] if item["name"] == f"lean-{version}-windows.zip")
    expected_hash = asset["digest"].removeprefix("sha256:")
    if len(expected_hash) != 64:
        raise RuntimeError("official SHA-256 is missing")
    download_dir = TOOLS / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    archive = download_dir / asset["name"]
    digest = hashlib.sha256()
    request = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": USER_AGENT})
    print(f"Downloading official Lean {version}: {asset['size']} bytes", flush=True)
    with urllib.request.urlopen(request, timeout=90) as response, archive.open("wb") as output:
        while chunk := response.read(8 * 1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
    actual_hash = digest.hexdigest()
    if actual_hash != expected_hash:
        archive.unlink()
        raise RuntimeError("SHA-256 mismatch; downloaded file was not executed")
    if archive.stat().st_size != asset["size"]:
        raise RuntimeError("release size mismatch")

    target = TOOLS / f"lean-{version}"
    if target.exists():
        raise RuntimeError(f"refusing to overwrite existing directory: {target}")
    target.mkdir(parents=True)
    try:
        with zipfile.ZipFile(archive) as package:
            if sum(info.file_size for info in package.infolist()) > 6_000_000_000:
                raise RuntimeError("expanded release exceeds safety limit")
            for info in package.infolist():
                relative = Path(info.filename)
                if relative.is_absolute() or ".." in relative.parts or ":" in relative.parts[0]:
                    raise RuntimeError("unsafe path in release archive")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise RuntimeError("symbolic links are not accepted in this installer")
                destination = (target / relative).resolve()
                if not destination.is_relative_to(target):
                    raise RuntimeError("release path escapes the local toolchain directory")
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with package.open(info) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
    except Exception:
        shutil.rmtree(target)
        raise
    executables = list(target.rglob("lean.exe"))
    if len(executables) != 1:
        raise RuntimeError("expected exactly one lean.exe in the official package")
    executable = executables[0]
    result = subprocess.run([str(executable), "--version"], capture_output=True, text=True,
                            timeout=20, check=False)
    if result.returncode != 0 or not result.stdout.startswith("Lean (version "):
        raise RuntimeError("downloaded Lean did not pass its own version check")
    report = {
        "version": version,
        "asset": asset["name"],
        "official_sha256": expected_hash,
        "verified_sha256": actual_hash,
        "bytes": archive.stat().st_size,
        "executable": str(executable),
        "version_output": result.stdout.strip(),
        "source_release": release["html_url"],
    }
    (TOOLS / "install-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
    archive.unlink()
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
