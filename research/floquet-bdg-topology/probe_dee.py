"""Read-only feasibility probe for Gaussian disconnected entanglement entropy."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from convention_model import majorana_k


def inverse_sqrt(matrix):
    values, vectors = np.linalg.eigh(matrix)
    if values.min() <= 0:
        raise ValueError("singular covariance")
    return (vectors / np.sqrt(values)) @ vectors.T


def correlation(k):
    values, vectors = np.linalg.eigh(1j * k)
    signs = np.where(np.abs(values) > 1e-12, np.sign(values), 0.0)
    return np.eye(k.shape[0]) + (vectors * signs) @ vectors.conj().T


def entropy(correlation_matrix, indices):
    if len(indices) == 0:
        return 0.0
    alpha = np.linalg.eigvalsh(correlation_matrix[np.ix_(indices, indices)])
    alpha = alpha[np.abs(alpha) > 1e-13]
    return float(-np.sum((alpha / 2) * np.log(np.abs(alpha / 2))))


def dee(k):
    n = k.shape[0] // 2
    a = np.arange(n // 2)
    overlap = np.arange(n // 4, n // 2)
    right = np.arange(3 * n // 4, n)
    b = np.r_[overlap, right]
    union = np.unique(np.r_[a, b])
    assert np.array_equal(overlap, np.intersect1d(a, b))
    assert np.array_equal(np.setdiff1d(np.arange(n), union), np.arange(n // 2, 3 * n // 4))
    matrix = correlation(k)
    return entropy(matrix, a) + entropy(matrix, b) - entropy(matrix, union) - entropy(matrix, overlap)


def main():
    for n in (8, 40, 80):
        for mu in (0.5, 2.5):
            value = dee(majorana_k(n, mu))
            print(f"N={n} mu={mu}: DEE={value:.12f}, DEE/ln2={value / np.log(2):.12f}")


if __name__ == "__main__":
    main()
