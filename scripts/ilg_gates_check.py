#!/usr/bin/env python3
# Draft verification of ILG nine-gate schedule over 1024-tick breath
# Computes blocked ticks |B| and suppression S = 1 - |B|/1024.

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
# Allowed 8-beat phases per gate (draft, pending finalization)
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

def compute_blocked():
    blocked = set()
    for t in range(1024):
        phi = t & 0b111  # t mod 8
        for j in range(9):
            if ((t & MASKS[j]) == PATTERNS[j]) and (phi in PHASES[j]):
                blocked.add(t)
                break
    return blocked

if __name__ == "__main__":
    B = compute_blocked()
    S = 1.0 - len(B)/1024.0
    print(f"|B| = {len(B)}")
    print(f"S   = {len(B)}/1024 -> {S:.9f}")
