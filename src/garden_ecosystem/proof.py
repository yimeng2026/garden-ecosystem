"""Conservative Lean compilation for self-contained, non-executable source files."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .lean import LeanAdapter, Runner, _run
from .receipts import ExternalToolUnavailable, ToolHealth, VerificationLevel, VerificationReceipt
from .security import stable_hash

MAX_SOURCE_BYTES = 65_536
MAX_SOURCE_LINES = 2_000
MAX_STDOUT = 65_536
MAX_STDERR = 16_384
MAX_LOG_CHARS = 2_000
DECLARATION = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]{0,127}\Z")
BANNED = [
    re.compile(r"(?m)^\s*import\b"),
    re.compile(r"(?m)^\s*#"),
    *[re.compile(rf"\b{word}\b")
      for word in ("sorry", "admit", "axiom", "unsafe", "postulate", "partial",
                   "opaque", "extern", "noncomputable", "macro", "elab",
                   "run_cmd", "run_elab", "run_tac", "set_option")],
]


def _code_only(source: str) -> str:
    """Mask nested comments and string contents, retaining structural newlines."""
    result: list[str] = []
    state = "code"
    depth = 0
    escaped = False
    index = 0
    while index < len(source):
        pair = source[index:index + 2]
        char = source[index]
        if state == "code":
            if pair == "--":
                state = "line_comment"
                result.append("  ")
                index += 2
                continue
            if pair == "/-":
                state = "block_comment"
                depth = 1
                result.append("  ")
                index += 2
                continue
            if char == '"':
                state = "string"
                escaped = False
                result.append(char)
            else:
                result.append(char)
        elif state == "line_comment":
            if char == "\n":
                state = "code"
                result.append(char)
            else:
                result.append(" ")
        elif state == "block_comment":
            if pair == "/-":
                depth += 1
                result.append("  ")
                index += 2
                continue
            if pair == "-/":
                depth -= 1
                result.append("  ")
                index += 2
                if depth == 0:
                    state = "code"
                continue
            result.append("\n" if char == "\n" else " ")
        else:  # string
            if char == "\n":
                result.append(char)
                escaped = False
            elif char == '"' and not escaped:
                state = "code"
                result.append(char)
            else:
                result.append(" ")
            if char == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
        index += 1
    if depth:
        raise ValueError("unterminated Lean block comment")
    return "".join(result)


def _bounded(text: str, workspace: Path) -> str:
    return text.replace(str(workspace), "<workspace>")[:MAX_LOG_CHARS]


@dataclass(frozen=True)
class ProofReport:
    ok: bool
    receipt: VerificationReceipt
    declaration: str
    path: str
    depends_on_axioms: bool | None
    axioms: tuple[str, ...]
    stdout: str
    stderr: str
    source_hash: str


class _OutputLimit(Exception):
    pass


class LeanProofAdapter:
    name = "lean_proof"

    def __init__(self, workspace: str | Path, executable: str | None = None,
                 runner: Runner | None = None, timeout: float = 10.0, resolver=None):
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError("proof workspace must be an existing directory")
        self.executable = executable or os.environ.get("LEAN_EXECUTABLE", "lean")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) \
                or not 0 < timeout <= 60:
            raise ValueError("proof timeout must be between 0 and 60 seconds")
        self.timeout = float(timeout)
        self.runner = runner or _run
        self.mock = runner is not None
        self.resolver = resolver
        self.lean = LeanAdapter(self.executable, self.runner, timeout=min(3.0, self.timeout),
                                resolver=self.resolver)

    def health(self) -> ToolHealth:
        return self.lean.health()

    def _prepare(self, action: Mapping[str, Any]) -> tuple[Path, str, str]:
        if set(action) != {"operation", "path", "declaration"}:
            raise ValueError("check_file accepts only operation, path and declaration")
        if action["operation"] != "check_file":
            raise ValueError("only check_file is supported")
        relative = action["path"]
        declaration = action["declaration"]
        if not isinstance(relative, str) or not relative:
            raise ValueError("a relative .lean path is required")
        if not isinstance(declaration, str) or not DECLARATION.fullmatch(declaration):
            raise ValueError("declaration must be a bounded ASCII Lean identifier")
        candidate = Path(relative)
        if (candidate.is_absolute() or relative.startswith(("/", "\\"))
                or ".." in candidate.parts or candidate.suffix != ".lean"):
            raise ValueError("only a relative .lean path inside the workspace is allowed")
        try:
            path = (self.workspace / candidate).resolve(strict=True)
        except OSError as error:
            raise ValueError("proof file does not exist") from error
        if not path.is_relative_to(self.workspace) or not path.is_file():
            raise ValueError("proof file must stay a regular file inside the workspace")
        raw = path.read_bytes()
        if len(raw) > MAX_SOURCE_BYTES:
            raise ValueError("proof file exceeds 64 KiB")
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("proof file must be UTF-8") from error
        if source.count("\n") + 1 > MAX_SOURCE_LINES:
            raise ValueError("proof file exceeds 2000 lines")
        code = _code_only(source)
        if any(pattern.search(code) for pattern in BANNED):
            raise ValueError("source contains a forbidden import, directive or declaration")
        return path, source, declaration

    def _report(self, *, path: Path, source: str, declaration: str, version: str,
                returncode: int, stdout: str, stderr: str) -> ProofReport:
        stdout = _bounded(stdout, self.workspace)
        stderr = _bounded(stderr, self.workspace)
        source_hash = stable_hash(source)
        combined = stdout + "\n" + stderr
        depends: bool | None = None
        axioms: tuple[str, ...] = ()
        if "does not depend on any axioms" in combined:
            depends = False
        else:
            match = re.search(r"depends on axioms:\s*\[([^\]]+)\]", combined)
            if match:
                depends = True
                axioms = tuple(item.strip() for item in match.group(1).split(",") if item.strip())
        ok = returncode == 0 and depends is not None
        evidence = stable_hash({"source": source_hash, "declaration": declaration,
                                "version": version, "returncode": returncode,
                                "stdout": stdout, "stderr": stderr, "mock": self.mock})
        receipt = VerificationReceipt(
            VerificationLevel.MACHINE_CHECKED if ok else VerificationLevel.EXECUTED,
            self.lean.name, version, evidence, mock=self.mock, attested=not self.mock,
        )
        return ProofReport(ok, receipt, declaration, path.relative_to(self.workspace).as_posix(),
                           depends, axioms, stdout, stderr, source_hash)

    def execute(self, action: Mapping[str, Any]) -> ProofReport:
        path, source, declaration = self._prepare(action)
        health = self.lean._probe()
        if health.status != "available" or health.version is None:
            raise ExternalToolUnavailable(health.reason)
        executable = (self.resolver or shutil.which)(self.executable)
        if executable is None:
            raise ExternalToolUnavailable("Lean executable was not found")
        temporary_root = self.workspace / ".garden_tmp"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="proof-", dir=temporary_root) as directory:
            wrapper = Path(directory) / "Check.lean"
            wrapper.write_text(source + f"\n#print axioms {declaration}\n", encoding="utf-8",
                               newline="\n")
            try:
                result = self.runner([executable, str(wrapper)], self.timeout)
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                if len(stdout) > MAX_STDOUT or len(stderr) > MAX_STDERR:
                    raise _OutputLimit("compiler output exceeds the configured limit")
                return self._report(path=path, source=source, declaration=declaration,
                                    version=health.version, returncode=result.returncode,
                                    stdout=stdout, stderr=stderr)
            except subprocess.TimeoutExpired:
                return self._report(path=path, source=source, declaration=declaration,
                                    version=health.version, returncode=124,
                                    stdout="", stderr="Lean compilation timed out")
            except _OutputLimit:
                return self._report(path=path, source=source, declaration=declaration,
                                    version=health.version, returncode=125,
                                    stdout="", stderr="Lean output limit exceeded")
            except OSError as error:
                return self._report(path=path, source=source, declaration=declaration,
                                    version=health.version, returncode=126,
                                    stdout="", stderr=f"Lean could not start: {type(error).__name__}")
