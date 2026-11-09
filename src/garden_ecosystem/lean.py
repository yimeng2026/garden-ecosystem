"""Real Lean executable health checks; deliberately not a proof runner."""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .receipts import ExternalToolUnavailable, ToolHealth, VerificationLevel, VerificationReceipt
from .security import stable_hash

_VERSION = re.compile(r"Lean \(version ([^,\)]+)")
Runner = Callable[[list[str], float], Any]


def _run(command: list[str], timeout: float) -> Any:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


@dataclass(frozen=True)
class _Probe:
    status: str
    reason: str
    version: str | None = None


class LeanAdapter:
    name = "lean"

    def __init__(self, executable: str | None = None, runner: Runner | None = None,
                 timeout: float = 3.0):
        self.executable = executable or os.environ.get("LEAN_EXECUTABLE", "lean")
        if not self.executable:
            raise ValueError("a Lean executable is required")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) \
                or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = float(timeout)
        self.runner = runner or _run

    def _probe(self) -> _Probe:
        resolved = shutil.which(self.executable)
        if resolved is None:
            return _Probe("unavailable", "Lean executable was not found")
        try:
            result = self.runner([resolved, "--version"], self.timeout)
        except subprocess.TimeoutExpired:
            return _Probe("degraded", "Lean version check timed out")
        except OSError:
            return _Probe("degraded", "Lean executable could not be started")
        if result.returncode != 0:
            return _Probe("degraded", f"Lean version check exited with code {result.returncode}")
        match = _VERSION.search(result.stdout[:200])
        if not match:
            return _Probe("degraded", "Lean version output was empty or unrecognized")
        version = match.group(1)[:80]
        return _Probe("available", f"Lean {version} is available", version)

    def health(self) -> ToolHealth:
        probe = self._probe()
        return ToolHealth(probe.status, probe.reason)

    def execute(self, action: Mapping[str, Any]) -> VerificationReceipt:
        if action.get("operation") != "health":
            raise ValueError("only the Lean health operation is supported")
        probe = self._probe()
        if probe.status != "available" or probe.version is None:
            raise ExternalToolUnavailable(probe.reason)
        evidence = stable_hash({"operation": "version", "version": probe.version, "returncode": 0})
        return VerificationReceipt(VerificationLevel.EXECUTED,
                                   self.name, probe.version, evidence, attested=True)
