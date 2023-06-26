# eth-storage-scraper.py

The Ethereum JSON-RPC protocol can only be used to query the storage of a contract at a given index (using `eth_getStorageAt`). In particulat, there is no method to get every index with non-empty storage value.

This small Python scipt solves this particular issue by repeatedly calling `eth_getProof` in order to compute the storage trie of an Ethereum account at a given block.

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
