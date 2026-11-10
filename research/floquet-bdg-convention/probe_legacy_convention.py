"""Demonstrate the legacy Majorana factor error against independent Fock space."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / "floquet-bdg" / "floquet_bdg.py"
sys.path.insert(0, str(ROOT))
from fock_reference import (  # noqa: E402
    fermion_operators,
    fock_hamiltonian,
    heisenberg_majorana,
    majorana_fock_hamiltonian,
    majorana_operators,
)

spec = importlib.util.spec_from_file_location("legacy_floquet_bdg", LEGACY)
legacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = legacy
spec.loader.exec_module(legacy)


def main():
    mu = 0.37
    time = 0.41
    # The legacy API requires n>=2; use the uncoupled first-site block.
    k1 = legacy.majorana_k(2, mu, gamma=0.0, delta=0.0)[:2, :2]
    actual = expm(-4 * k1 * time)[0, 1]
    expected = np.sin(2 * mu * time)
    print(f"single-site U[0,1]: actual={actual:.16f}, expected={expected:.16f}")
    single_failed = not np.isclose(actual, expected, atol=1e-13)

    c = fermion_operators(2)
    gammas = majorana_operators(c)
    gamma, delta = 0.81, 0.53
    reference = fock_hamiltonian(c, mu, gamma, delta)
    represented = majorana_fock_hamiltonian(legacy.majorana_k(2, mu, gamma, delta), gammas)
    difference = np.max(np.abs(reference - represented))
    print(f"two-site Fock max element difference: {difference:.16e}")
    double_failed = difference > 1e-12

    u = expm(-4 * k1 * time)
    c1 = fermion_operators(1)
    gamma1 = majorana_operators(c1)
    direct = heisenberg_majorana(fock_hamiltonian(c1, mu, 0, 0), gamma1, time)
    evolution_error = 0.0
    for column in range(2):
        transported = sum((u[row, column] * gamma1[row] for row in range(2)), start=np.zeros((2, 2), dtype=complex))
        evolution_error = max(evolution_error, float(np.max(np.abs(direct[column] - transported))))
    print(f"single-site Fock Heisenberg max difference: {evolution_error:.16e}")
    evolution_failed = evolution_error > 1e-12
    failed = single_failed or double_failed or evolution_failed
    print(f"legacy_convention_passed={not failed}")
    print("This is an intentional RED probe of the legacy implementation, not a failure of the Fock reference.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
