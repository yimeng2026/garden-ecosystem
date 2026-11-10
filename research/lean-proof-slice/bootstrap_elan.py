"""Download, verify and bootstrap the official elan/Lean toolchain on D:."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
URL = "https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-pc-windows-msvc.zip"
EXPECTED_BYTES = 2508099
EXPECTED_SHA256 = "fad2e980a191c15884cc1d80d170ffc5fa84f3774541020145b66d1a644c6111"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.35.0"
BASE = Path("D:/migration/toolchains/elan")
ARCHIVE = BASE / "downloads/elan-x86_64-pc-windows-msvc.zip"
EXTRACT_DIR = BASE / "bootstrap"
ELAN_HOME = BASE / "home"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_and_verify():
    BASE.mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists() or ARCHIVE.stat().st_size != EXPECTED_BYTES or sha256(ARCHIVE) != EXPECTED_SHA256:
        temporary = ARCHIVE.with_suffix(".part")
        with urllib.request.urlopen(URL, timeout=90) as response, temporary.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        if temporary.stat().st_size != EXPECTED_BYTES or sha256(temporary) != EXPECTED_SHA256:
            raise ValueError("official elan asset size or SHA-256 mismatch")
        temporary.replace(ARCHIVE)
    if ARCHIVE.stat().st_size != EXPECTED_BYTES or sha256(ARCHIVE) != EXPECTED_SHA256:
        raise ValueError("cached elan asset size or SHA-256 mismatch")


def extract_verified_asset():
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as package:
        for member in package.infolist():
            relative = Path(member.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe archive member: {member.filename}")
        package.extractall(EXTRACT_DIR)
    files = sorted(path.name for path in EXTRACT_DIR.iterdir() if path.is_file())
    if "elan-init.exe" not in files and "elan.exe" not in files:
        raise FileNotFoundError(f"elan executable not found in verified archive: {files}")
    return files


def run(command, timeout=240):
    env = os.environ.copy()
    env["ELAN_HOME"] = str(ELAN_HOME)
    env["PATH"] = str(ELAN_HOME / "bin") + os.pathsep + env.get("PATH", "")
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    download_and_verify()
    files = extract_verified_asset()
    initializer = EXTRACT_DIR / ("elan-init.exe" if "elan-init.exe" in files else "elan.exe")
    version = run([str(initializer), "--version"])
    if version["exit_code"] != 0:
        raise RuntimeError(f"elan --version failed: {version}")
    if initializer.name == "elan-init.exe":
        command = [str(initializer), "-y", "--no-modify-path", "--default-toolchain", LEAN_TOOLCHAIN]
    else:
        command = [str(initializer), "toolchain", "install", LEAN_TOOLCHAIN]
    install = run(command)
    if install["exit_code"] != 0:
        raise RuntimeError(f"Lean toolchain installation failed: {install}")
    lean = ELAN_HOME / "bin/lean.exe"
    lake = ELAN_HOME / "bin/lake.exe"
    lean_version = run([str(lean), "--version"])
    lake_version = run([str(lake), "--version"])
    if lean_version["exit_code"] != 0 or lake_version["exit_code"] != 0:
        raise RuntimeError(f"installed Lean/Lake unavailable: {lean_version} {lake_version}")
    result = {
        "status": "passed",
        "archive": str(ARCHIVE),
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": sha256(ARCHIVE),
        "extracted_files": files,
        "elan_home": str(ELAN_HOME),
        "lean_home": str(ELAN_HOME),
        "lean_executable": str(lean),
        "lake_executable": str(lake),
        "path_modified": False,
        "elan_version": version,
        "install": install,
        "lean_version": lean_version,
        "lake_version": lake_version,
    }
    (ROOT / "bootstrap-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "archive_sha256": result["archive_sha256"],
        "elan_home": result["elan_home"],
        "lean_version": lean_version["stdout"].strip() or lean_version["stderr"].strip(),
        "lake_version": lake_version["stdout"].strip() or lake_version["stderr"].strip(),
        "path_modified": result["path_modified"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
