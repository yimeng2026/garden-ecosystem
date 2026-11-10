"""Independent full-Fock DEE check for an eight-site Kitaev chain."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from fock_reference import fermion_operators, fock_hamiltonian


def site_entropy(psi, n, indices):
    indices = list(indices)
    if not indices:
        return 0.0
    remaining = [site for site in range(n) if site not in indices]
    order = indices + remaining
    tensor = psi.reshape([2] * n).transpose(order).reshape(2 ** len(indices), -1)
    singular = np.linalg.svd(tensor, compute_uv=False) ** 2
    singular = singular[singular > 1e-14]
    return float(-np.sum(singular * np.log(singular)))


def dee(psi, n):
    a = np.arange(n // 2)
    overlap = np.arange(n // 4, n // 2)
    right = np.arange(3 * n // 4, n)
    b = np.r_[overlap, right]
    union = np.unique(np.r_[a, b])
    return site_entropy(psi, n, a) + site_entropy(psi, n, b) - site_entropy(psi, n, union) - site_entropy(psi, n, overlap)


def main():
    n = 8
    c = fermion_operators(n)
    for mu in (0.5, 2.5):
        h = fock_hamiltonian(c, mu, 1.0, 1.0)
        values, vectors = np.linalg.eigh(h)
        psi = vectors[:, 0]
        print(f"N={n} mu={mu}: full-Fock DEE={dee(psi, n):.12f}")


if __name__ == "__main__":
    main()
