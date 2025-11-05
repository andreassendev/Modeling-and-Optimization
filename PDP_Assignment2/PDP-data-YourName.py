"""
Laster datastrukturer fra data/Instance_PDP.py og beregner BigM konservativt.

Forventet i Instance_PDP.py:
  Nv (sett/list), Np (sett/list med pickups indeksert 1..n),
  Nd (sett/list med deliveries {n+1,..,n+n} eller mapping),
  A (sett av buer (i,j), i != j), D (dict-of-dict: D[i][j]),
  Q (dict med Q[i] for i in Np), K (kapasitet), CS (spot charter-kost),
  o (origin), d (destination).
"""

from data.Instance_PDP import Nv, Np, Nd, A, D, Q, K, CS, o, d

# Check if BigM is explicitly provided in Instance_PDP
try:
    from data.Instance_PDP import BigM as explicit_BigM
    BigM = explicit_BigM
except ImportError:
    # Calculate BigM conservatively if not provided
    def _maxD():
        """Find maximum distance in the distance matrix"""
        m = 0.0
        for (i, j) in A:
            v = D[i][j]
            if v > m:
                m = v
        return m
    
    BigM = _maxD() * max(1, len(Nv))

n = len(Np)


__all__ = ["Nv", "Np", "Nd", "A", "D", "Q", "K", "CS", "o", "d", "n", "BigM"]

