"""
Laster datastrukturer fra data/Instance_PDP.py og beregner BigM konservativt.
"""

from data.Instance_PDP import Nv, Np, Nd, A, D, Q, K, CS, o, d

try:
    from data.Instance_PDP import BigM as explicit_BigM
    BigM = explicit_BigM
except ImportError:
    def _maxD():
        m = 0.0
        for (i, j) in A:
            v = D[i][j]
            if v > m:
                m = v
        return m
    
    BigM = _maxD() * max(1, len(Nv))

n = len(Np)


__all__ = ["Nv", "Np", "Nd", "A", "D", "Q", "K", "CS", "o", "d", "n", "BigM"]

