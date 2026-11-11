"""Resumable theta-chunk winding with scalar checkpoints and bounded block cache."""

import hashlib
import json
from pathlib import Path

import numpy as np

from tbc_model import _parameters, half_chiral_block

CACHE_ROOT = Path("D:/kimi-cache/tbc/large-diagnostic")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def cache_path_for(work_path):
    digest = hashlib.sha256(str(Path(work_path).resolve()).encode("utf-8")).hexdigest()[:24]
    return CACHE_ROOT / digest / "blocks.npz"


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_blocks(path, blocks):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.npz")
    np.savez(temporary, **blocks)
    temporary.replace(path)


def trace_integrand(center, minus, plus, step):
    derivative = (plus - minus) / (2 * step)
    return complex(np.trace(np.linalg.solve(center, derivative)))


def metadata_for(parameters, nominal_step, epsilon, free_method):
    n, mu0, mu1, omega, gamma, delta = _parameters(parameters)
    m = int(round(2 * np.pi / nominal_step))
    if m < 8:
        raise ValueError("theta grid is too coarse")
    return {
        "schema": "resumable-tbc-winding-v1",
        "nominal_step": float(nominal_step),
        "actual_step": float(2 * np.pi / m),
        "points": m,
        "epsilon": float(epsilon),
        "free_method": free_method,
        "n": n,
        "omega": omega,
        "gamma": gamma,
        "delta": delta,
        "mu0_sha256": sha256_bytes(np.asarray(mu0).tobytes()),
        "mu1_sha256": sha256_bytes(np.asarray(mu1).tobytes()),
    }


def winding_from_integrands(rows, metadata):
    """Apply the original central-difference winding formula to scalar rows."""
    ordered = sorted(rows, key=lambda row: row["index"])
    h = metadata["actual_step"]
    values = np.asarray([complex(row["real"], row["imag"]) for row in ordered])
    raw = (1j / (2 * np.pi)) * h * np.sum(values)
    value = float(abs(raw.real))
    closest = int(round(value))
    residual = float(abs(value - closest))
    quantized = residual < 1e-3
    diagnostics = metadata["diagnostics"]
    return {
        "status": "ok" if quantized else "not_converged",
        "reason": None if quantized else "integer_residual_above_tolerance",
        "value": value,
        "raw_real": float(raw.real), "raw_imag": float(raw.imag),
        "nearest_integer": closest if quantized else None,
        "integer_residual": residual,
        "min_bulk_gap": float(min(row["bulk_gap"] for row in diagnostics)),
        "max_block_condition": float(max(row["max_condition"] for row in diagnostics)),
        "max_unitarity_error": float(max(row["unitarity_error"] for row in diagnostics)),
        "max_normality_error": float(max(row["normality_error"] for row in diagnostics)),
        "nominal_step": metadata["nominal_step"], "actual_step": h,
        "points": metadata["points"], "branch": "plus", "epsilon": metadata["epsilon"],
        "free_method": metadata["free_method"], "chunks_completed": metadata["chunks_completed"],
        "cache_file": metadata["cache_file"], "cache_sha256": metadata["cache_sha256"],
    }


def resumable_winding(parameters, nominal_step, epsilon, work_path, free_method="eigh", chunk_size=8, max_chunks=4):
    """Compute or resume one grid without storing the full block history."""
    if chunk_size < 1 or max_chunks < 1:
        raise ValueError("chunk_size and max_chunks must be positive")
    work_path = Path(work_path)
    work_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata_for(parameters, nominal_step, epsilon, free_method)
    if work_path.exists():
        state = json.loads(work_path.read_text(encoding="utf-8"))
        for key, value in metadata.items():
            if state.get(key) != value:
                raise ValueError("resumable winding metadata mismatch")
    else:
        state = dict(
            metadata,
            next_index=0, integrands=[], diagnostics=[], chunks_completed=0,
            cache_file=str(cache_path_for(work_path)), cache_sha256=None,
        )
    m = metadata["points"]
    h = metadata["actual_step"]
    cache_file = Path(state["cache_file"])
    if state["next_index"] > 0:
        if not cache_file.exists():
            raise ValueError("resumable block cache is missing")
        if sha256_bytes(cache_file.read_bytes()) != state["cache_sha256"]:
            raise ValueError("resumable block cache hash mismatch")
        with np.load(cache_file) as cache:
            first0, first1 = cache["first0"].copy(), cache["first1"].copy()
            previous_previous = cache["previous_previous"].copy()
            previous = cache["previous"].copy()
    else:
        first0 = first1 = previous_previous = previous = None
    chunks = 0
    while state["next_index"] < m and chunks < max_chunks:
        stop = min(state["next_index"] + chunk_size, m)
        for index in range(state["next_index"], stop):
            theta = -np.pi + h * index
            point = half_chiral_block(parameters, theta, epsilon, free_method=free_method)
            if point["status"] != "ok":
                state["status"] = point["status"]
                state["reason"] = point["reason"]
                state["failed_theta"] = float(theta)
                state["value"] = None
                state["nearest_integer"] = None
                write_json(work_path, state)
                return dict(state, min_bulk_gap=point.get("bulk_gap"), integrands=state["integrands"])
            block = point["block"]
            if index == 0:
                first0 = block.copy()
            if index == 1:
                first1 = block.copy()
            if index >= 2:
                z = trace_integrand(previous, previous_previous, block, h)
                state["integrands"].append({"index": index - 1, "real": z.real, "imag": z.imag})
            state["diagnostics"].append({
                "index": index, "theta": float(theta), "bulk_gap": point["bulk_gap"],
                "max_condition": point["max_condition"], "unitarity_error": point["unitarity_error"],
                "normality_error": point["normality_error"],
            })
            previous_previous, previous = previous, block
        state["next_index"] = stop
        state["chunks_completed"] += 1
        blocks = {
            "first0": first0 if first0 is not None else np.empty((0, 0)),
            "first1": first1 if first1 is not None else np.empty((0, 0)),
            "previous_previous": previous_previous if previous_previous is not None else np.empty((0, 0)),
            "previous": previous if previous is not None else np.empty((0, 0)),
        }
        write_blocks(cache_file, blocks)
        state["cache_sha256"] = sha256_bytes(cache_file.read_bytes())
        write_json(work_path, state)
        chunks += 1
    if state["next_index"] < m:
        return dict(
            state, status="partial", value=None, nearest_integer=None,
            min_bulk_gap=min(row["bulk_gap"] for row in state["diagnostics"]),
            max_block_condition=max(row["max_condition"] for row in state["diagnostics"]),
        )
    if not state.get("finalized"):
        z0 = trace_integrand(first0, previous, first1, h)
        zlast = trace_integrand(previous, previous_previous, first0, h)
        state["integrands"].append({"index": 0, "real": z0.real, "imag": z0.imag})
        state["integrands"].append({"index": m - 1, "real": zlast.real, "imag": zlast.imag})
        state["finalized"] = True
        result = winding_from_integrands(state["integrands"], state)
        state.update(result)
        write_json(work_path, state)
    return dict(state, next_index=m, integrands=state["integrands"])
