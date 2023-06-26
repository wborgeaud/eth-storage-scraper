from eth_utils import keccak
import random


def precompute_prefixes(num):
    d = {}
    for n in range(num):
        b = n.to_bytes(32, "big")
        h = keccak(b).hex()
        d[h] = n
        for i in range(1, 8):
            d[h[:i]] = n
    return d


def find_prefix(s):
    """
    Find a key `k` such that `keccak(k.to_bytes(32, "big")).hex().startswith(s)` by repeated random trials.
    Takes a long time for long prefixes.

    Args:
        s (str): Hex prefix.

    Returns:
        k (int): A key `k` such that `keccak(k.to_bytes(32, "big")).hex().startswith(s)` by repeated random trials.
    """
    while True:
        b = random.randbytes(32)
        h = keccak(b).hex()
        if h.startswith(s):
            return int.from_bytes(b, "big")
