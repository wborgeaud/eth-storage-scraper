# eth-storage-scraper.py

The Ethereum JSON-RPC protocol can only be used to query the storage of a contract at a given slot (using `eth_getStorageAt`). In particular, there is no method to get every slot with non-empty storage value.

This small Python script solves this particular issue by repeatedly calling `eth_getProof` in order to compute the storage trie of an Ethereum account at a given block.

It can be used as a CLI

```bash
$ python eth-storage-scraper.py -h
usage: eth-storage-scraper.py [-h] --rpc-url RPC_URL --block BLOCK [--precomputation-size PRECOMPUTATION_SIZE] [--save-precomputation] address

Compute the storage trie of an Ethereum address using only Ethereum JSON-RPC calls.

positional arguments:
  address               The address to compute the trie for

options:
  -h, --help            show this help message and exit
  --rpc-url RPC_URL, -u RPC_URL
                        Ethereum JSON-RPC URL
  --block BLOCK, -b BLOCK
                        Ethereum block number
  --precomputation-size PRECOMPUTATION_SIZE, -p PRECOMPUTATION_SIZE
                        Number of Keccak hashes to precompute
  --save-precomputation, -s
                        Save the precomputation in a Pickle file and reuse it in later runs
```

or as a Python library

```python
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
```

## Example on the _Uniswap: Universal Router_

```bash
$ python eth-storage-scraper.py 0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD  -b 17562051 -u RPC_URL
Slot     Key (None if preimage not found)        Value
290decd9548b62a8d60345a988386fc84ba6bc95484008f6362f93160ef3e563         0       0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
b10e2d527612073b26eecdfd717e6a320cf44b4afac2b0732d9fcbe2b7fa0cf6         1       0x01
```

## Warning

This script will take a very long time on accounts with a lot of non-empty storage slots (e.g. token contracts).
