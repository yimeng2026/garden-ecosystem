"""Independent finite Fock-space reference; no Majorana-matrix helper is reused."""

import numpy as np
from scipy.linalg import expm


def fermion_operators(n):
    annihilation = np.array([[0, 1], [0, 0]], dtype=complex)
    identity = np.eye(2, dtype=complex)
    parity = np.diag([1, -1]).astype(complex)
    operators = []
    for site in range(n):
        factors = [parity] * site + [annihilation] + [identity] * (n - site - 1)
        operator = factors[0]
        for factor in factors[1:]:
            operator = np.kron(operator, factor)
        operators.append(operator)
    return operators


def majorana_operators(c):
    a = [operator + operator.conj().T for operator in c]
    b = [-1j * (operator - operator.conj().T) for operator in c]
    return [item for pair in zip(a, b) for item in pair]


def fock_hamiltonian(c, mu, gamma, delta):
    n = len(c)
    h = np.zeros((2**n, 2**n), dtype=complex)
    for operator in c:
        number = operator.conj().T @ operator
        h -= mu * (2 * number - np.eye(2**n))
    for left in range(n - 1):
        right = left + 1
        h -= gamma * (c[left].conj().T @ c[right] + c[right].conj().T @ c[left])
        h += delta * (c[left] @ c[right] + c[right].conj().T @ c[left].conj().T)
    return h


def majorana_fock_hamiltonian(k, gammas):
    h = np.zeros_like(gammas[0], dtype=complex)
    for row in range(k.shape[0]):
        for column in range(k.shape[1]):
            h += 1j * k[row, column] * (gammas[row] @ gammas[column])
    return h


def heisenberg_majorana(h, gammas, time):
    evolution = expm(1j * h * time)
    return [evolution @ gamma @ evolution.conj().T for gamma in gammas]
