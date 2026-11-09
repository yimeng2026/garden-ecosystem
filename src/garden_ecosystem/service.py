"""Single-request, whitelisted JSON-over-stdio bridge service."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .bridge import capabilities, health
from .errors import GardenError
from .lean import LeanAdapter
from .proof import LeanProofAdapter
from .receipts import ExternalToolAdapter

ACTIONS = {"capabilities", "health", "lean_health", "lean_receipt", "lean_check"}
MAX_REQUEST_BYTES = 16_384


class Service:
    def __init__(self, lean: ExternalToolAdapter | None = None,
                 proof: LeanProofAdapter | None = None):
        self.lean = lean or LeanAdapter()
        self.proof = proof or LeanProofAdapter(Path.cwd())

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        request_id = request.get("id")
        action = request.get("action")
        params = request.get("params", {})
        if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
            raise ValueError("a short non-empty id is required")
        if action not in ACTIONS or not isinstance(params, dict):
            raise ValueError("unsupported action or params")
        if action == "lean_receipt":
            if set(params) - {"operation"}:
                raise ValueError("unsupported receipt params")
        elif action == "lean_check":
            if set(params) - {"path", "declaration"}:
                raise ValueError("lean_check accepts only path and declaration")
        elif params:
            raise ValueError("this action does not accept params")
        return {"id": request_id, "ok": True, "result": self._dispatch(action, params)}

    def _dispatch(self, action: str, params: dict[str, Any]) -> Any:
        if action == "capabilities":
            return capabilities()
        if action == "health":
            return health([self.lean])
        if action == "lean_health":
            return asdict(self.lean.health())
        if action == "lean_check":
            return asdict(self.proof.execute({
                "operation": "check_file",
                "path": params.get("path"),
                "declaration": params.get("declaration"),
            }))
        return asdict(self.lean.execute({"operation": params.get("operation", "health")}))

    def handle_safely(self, request: Any) -> dict[str, Any]:
        request_id = request.get("id", "") if isinstance(request, dict) else ""
        if not isinstance(request_id, str) or len(request_id) > 128:
            request_id = ""
        try:
            return self.handle(request)
        except (ValueError, GardenError) as error:
            return {"id": request_id, "ok": False,
                    "error": {"type": type(error).__name__, "message": str(error)}}
        except Exception as error:
            return {"id": request_id, "ok": False,
                    "error": {"type": type(error).__name__, "message": "bridge action failed"}}


def main() -> int:
    data = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(data) > MAX_REQUEST_BYTES:
        response = {"id": "", "ok": False,
                    "error": {"type": "ValueError", "message": "request exceeds 16 KiB"}}
    else:
        try:
            request = json.loads(data.decode("utf-8"))
            response = Service().handle_safely(request)
        except (UnicodeDecodeError, json.JSONDecodeError):
            response = {"id": "", "ok": False,
                        "error": {"type": "ValueError", "message": "invalid JSON request"}}
    sys.stdout.write(json.dumps(response, ensure_ascii=False, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
