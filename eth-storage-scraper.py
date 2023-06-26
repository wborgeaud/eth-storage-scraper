import os
import pickle
from web3 import Web3, HTTPProvider
from eth_utils import keccak
from rlp import decode
from trie import HexaryTrie
from prefixes import find_prefix, precompute_prefixes
import argparse

NIBBLES = "0123456789abcdef"


def getStorageTrie(address, block, precomputation, w3):
    """
    Compute the storage trie of an Ethereum address at a given block using repeated calls to `eth_getProof`.

    Args:
        address (str): The Ethereum address to compute the storage trie for.
        block (int): The Ethereum block number.
        precomputation (dict): Dictionary mapping prefixes to keys.
                               Satisfies `keccak(precomputation[prefix].to_bytes(32, "big")).hex().startswith(prefix)` for all `prefix in precomputation`.
        w3 (Web3): Web3 instance.

    Returns:
        trie (HexaryTrie): Storage trie.
        storage (dict): Dictionary mapping keys to values. Satisfies `trie = HexaryTrie(storage)`.
    """
    account = w3.eth.get_proof(address, [0], block)
    storageHash = account["storageHash"]
    trie = HexaryTrie({})
    storage = {}
    proof = account["storageProof"][0]
    intkey = 0
    current_key = keccak(intkey.to_bytes(32, "big")).hex()
    prefixes = set()
    seen_prefixes = set()
    while storageHash != trie.root_hash:
        prefix = ""
        for node in proof["proof"]:
            old_prefix = prefix
            prefix = traverse_node(
                node, prefix, current_key, prefixes, seen_prefixes, trie, storage
            )
            seen_prefixes.add(old_prefix)

        if len(prefixes) == 0:
            assert storageHash == trie.root_hash
            break
        new_prefix = prefixes.pop()
        intkey = (
            precomputation[new_prefix]
            if new_prefix in precomputation
            else find_prefix(new_prefix)
        )
        current_key = keccak(intkey.to_bytes(32, "big")).hex()
        account = w3.eth.get_proof(address, [intkey], block)
        proof = account["storageProof"][0]
    return trie, storage


def traverse_node(
    rlp, current_prefix, current_key, prefixes, seen_prefixes, trie, storage
):
    assert current_key.startswith(current_prefix)
    node = decode(rlp)
    if len(node) == 17:  # branch node
        return traverse_branch(
            node, current_prefix, current_key, prefixes, seen_prefixes
        )
    elif len(node) == 2:  # extension or leaf node
        a = node[0].hex()[2:]
        if a[0] == "0":  # extension node with even number of nibbles
            return traverse_extension(
                a[2:], node[1], current_prefix, current_key, prefixes, seen_prefixes
            )
        elif a[0] == "1":  # extension node with odd number of nibbles
            return traverse_extension(
                a[1:], node[1], current_prefix, current_key, prefixes, seen_prefixes
            )
        elif a[0] == "2":  # leaf node with even number of nibbles
            return traverse_leaf(
                a[2:], node[1], current_prefix, seen_prefixes, trie, storage
            )
        elif a[0] == "3":  # leaf node with odd number of nibbles
            return traverse_leaf(
                a[1:], node[1], current_prefix, seen_prefixes, trie, storage
            )
        else:
            raise RuntimeError("This should never happen!")
    else:
        raise RuntimeError("This should never happen!")


def traverse_branch(node, current_prefix, current_key, prefixes, seen_prefixes):
    for nibble in range(16):
        if node[nibble] != b"":
            prefix = current_prefix + NIBBLES[nibble]
            if not current_key.startswith(prefix) and prefix not in seen_prefixes:
                prefixes.add(prefix)
    return current_key[: len(current_prefix) + 1]


def traverse_extension(k, v, current_prefix, current_key, prefixes, seen_prefixes):
    prefix = current_prefix + k
    if not current_key.startswith(prefix) and prefix not in seen_prefixes:
        prefixes.add(prefix)
    return prefix


def traverse_leaf(k, v, current_prefix, seen_prefixes, trie, storage):
    prefix = current_prefix + k
    key_bytes = bytes.fromhex(prefix)
    assert len(key_bytes) == 32
    trie[key_bytes] = v
    storage[key_bytes] = v
    seen_prefixes.add(prefix)


def main():
    parser = argparse.ArgumentParser(
        description="Compute the storage trie of an Ethereum address using only Ethereum JSON-RPC calls."
    )

    parser.add_argument("address", type=str, help="The address to compute the trie for")
    parser.add_argument(
        "--rpc-url", "-u", type=str, required=True, help="Ethereum JSON-RPC URL"
    )
    parser.add_argument(
        "--block", "-b", type=int, required=True, help="Ethereum block number"
    )
    parser.add_argument(
        "--precomputation-size",
        "-p",
        type=int,
        default=1_000_000,
        help="Number of Keccak hashes to precompute",
    )
    parser.add_argument(
        "--save-precomputation",
        "-s",
        action="store_true",
        help="Save the precomputation in a Pickle file and reuse it in later runs",
    )

    args = parser.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc_url))

    if args.save_precomputation and os.path.isfile("precomputation.pkl"):
        with open("precomputation.pkl", "rb") as f:
            precomputation = pickle.load(f)
    else:
        precomputation = precompute_prefixes(args.precomputation_size)
        if args.save_precomputation:
            with open("precomputation.pkl", "wb") as f:
                pickle.dump(precomputation, f)

    _trie, storage = getStorageTrie(args.address, args.block, precomputation, w3)
    print(f"Slot \t Key (None if preimage not found) \t Value")
    for a in storage:
        slot = a.hex()
        key = precomputation.get(slot)
        value = decode(storage[a]).hex()
        print(f"{slot} \t {key} \t {value}")


if __name__ == "__main__":
    main()
