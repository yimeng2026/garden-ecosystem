"""Benchmark spectral backends without changing validated TBC production code."""

import json
import time
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import eigh, expm, schur

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import beta_sequence  # noqa: E402
from tbc_model import twisted_majorana_k  # noqa: E402


def timed(function, repeats):
    values = []
    for _ in range(repeats):
        started = time.perf_counter()
        result = function()
        values.append(time.perf_counter() - started)
    return result, values


def main():
    output = []
    for n, repeats in ((160, 3), (320, 1)):
        beta = beta_sequence(2, n)
        k0 = twisted_majorana_k(np.full(n, 2.5), 0.037)
        k1 = twisted_majorana_k(0.05 * beta, 0.0, gamma=0.0, delta=0.0)
        period = 2 * np.pi / 7
        free_half, free_times = timed(lambda: expm(-2 * k0 * period), repeats)
        half_kick = expm(-2 * k1)
        u = half_kick @ free_half @ free_half @ half_kick
        (values, vectors), eig_times = timed(lambda: np.linalg.eig(u), repeats)
        (triangular, q), schur_times = timed(lambda: schur(u, output="complex"), repeats)
        (energies, qk), eigh_times = timed(lambda: eigh(1j * k0), repeats)
        free_eigh = (qk * np.exp(2j * energies * period)) @ qk.conj().T
        output.append({
            "n": n,
            "repeats": repeats,
            "expm_seconds": free_times,
            "np_eig_seconds": eig_times,
            "scipy_schur_seconds": schur_times,
            "hermitian_eigh_seconds": eigh_times,
            "np_eig_eigenvector_unitarity": float(np.max(np.abs(vectors.conj().T @ vectors - np.eye(2 * n)))),
            "np_eig_diagonalization_error": float(np.max(np.abs(u @ vectors - vectors * values))),
            "eigh_free_reconstruction_error": float(np.max(np.abs(free_eigh - free_half))),
            "schur_normality_error": float(np.max(np.abs(triangular - np.diag(np.diag(triangular))))),
        })
        print(json.dumps(output[-1], ensure_ascii=False))
    (ROOT / "spectral_benchmark.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
