#!/usr/bin/env python3
"""
ILG nine-gate schedule over the 1024-tick breath.
Computes blocked ticks |B| by brute force and via analytic inclusion–exclusion.
The canonical schedule yields |B|=46 ⇒ S = 489/512 ≈ 0.955078125.
"""

MASKS = [
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
    0b1111111000,
]
PATTERNS = [
    0b0000011000,
    0b0010001000,
    0b0011101000,
    0b0101010000,
    0b0110111000,
    0b1000100000,
    0b1010011000,
    0b1100000000,
    0b1101111000,
]
# Allowed 8-beat phases per gate (canonical; finalized)
PHASES = [
    {0,1,2,3,4},
    {1,2,3,4,5},
    {2,3,4,5,6},
    {3,4,5,6,7},
    {0,2,3,5,7},
    {0,1,3,5,6},
    {1,3,4,6,7},
    {0,2,4,6,7},
    {0,1,2,4,5,7},
]

def compute_blocked_bruteforce():
    blocked = set()
    for t in range(1024):
        phi = t & 0b111  # t mod 8
        for j in range(9):
            if ((t & MASKS[j]) == PATTERNS[j]) and (phi in PHASES[j]):
                blocked.add(t)
                break
    return blocked

def popcount(x: int) -> int:
    # Portable popcount for Python versions without int.bit_count()
    return bin(x).count('1')

def intersection_phase_size(idxs) -> int:
    inter = set(range(8))
    for j in idxs:
        inter &= PHASES[j]
        if not inter:
            return 0
    return len(inter)

def patterns_compatible(idxs) -> bool:
    # Check that masked high-bit requirements across gates do not conflict
    forced1 = 0
    forced0 = 0
    for j in idxs:
        m = MASKS[j]
        p = PATTERNS[j]
        # bits forced to 1 under this mask
        ones = p & m
        zeros = (~p) & m
        if (forced1 & zeros) or (forced0 & ones):
            return False
        forced1 |= ones
        forced0 |= zeros
    return True

def forced_high_bits_count(idxs) -> int:
    # Count distinct high bits (3..9) forced by the union of masks in idxs
    m_union = 0
    for j in idxs:
        m_union |= MASKS[j]
    return popcount(m_union)

def analytic_intersection_count(idxs) -> int:
    # N(S) = 2^(10 - rank(M_S)) * |∩Φ_j| / 8, if patterns are compatible; else 0
    if not patterns_compatible(idxs):
        return 0
    rank = forced_high_bits_count(idxs)
    phase_sz = intersection_phase_size(idxs)
    return (1 << (10 - rank)) * phase_sz // 8

def analytic_union_size() -> int:
    # Inclusion–exclusion over all non-empty subsets of the 9 gates
    n = 9
    total = 0
    from itertools import combinations
    for r in range(1, n+1):
        sgn = -1 if (r % 2 == 0) else 1
        for idxs in combinations(range(n), r):
            total += sgn * analytic_intersection_count(idxs)
    return total

if __name__ == "__main__":
    B = compute_blocked_bruteforce()
    S = 1.0 - len(B)/1024.0
    print(f"|B| (brute)   = {len(B)}")
    print(f"S   (brute)   = 1 - {len(B)}/1024 -> {S:.9f}")
    U = analytic_union_size()
    S2 = 1.0 - U/1024.0
    print(f"|B| (analytic)= {U}")
    print(f"S   (analytic)= 1 - {U}/1024 -> {S2:.9f}")
