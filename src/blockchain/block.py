import time
import json
import hashlib
from typing import Dict, List, Any, Optional

class Block:
    """
    Represents a block in the blockchain.
    Each block contains a list of transactions and links to the previous block.
    """
    
    def __init__(self, 
                 index: int, 
                 transactions: List[Dict[str, Any]], 
                 timestamp: Optional[float] = None, 
                 previous_hash: str = '', 
                 nonce: int = 0):
        """
        Initialize a new block.
        
        Args:
            index: The position of the block in the chain
            transactions: List of transactions included in the block
            timestamp: The time the block was created (defaults to current time)
            previous_hash: Hash of the previous block in the chain
            nonce: Nonce value used for mining (Proof-of-Work)
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp or time.time()
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate the hash of the block.
        
        Returns:
            str: The SHA-256 hash of the block
        """
        # Convert the block to a string and hash it
        block_string = json.dumps(self.to_dict(include_hash=False), sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self, include_hash: bool = True) -> Dict[str, Any]:
        """
        Convert the block to a dictionary.
        
        Args:
            include_hash: Whether to include the hash in the dictionary
            
        Returns:
            Dict[str, Any]: The block as a dictionary
        """
        block_dict = {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
        
        if include_hash:
            block_dict['hash'] = self.hash
            
        return block_dict
    
    @classmethod
    def from_dict(cls, block_dict: Dict[str, Any]) -> 'Block':
        """
        Create a block from a dictionary.
        
        Args:
            block_dict: The dictionary to create the block from
            
        Returns:
            Block: The created block
        """
        block = cls(
            index=block_dict['index'],
            transactions=block_dict['transactions'],
            timestamp=block_dict['timestamp'],
            previous_hash=block_dict['previous_hash'],
            nonce=block_dict['nonce']
        )
        
        # Set the hash directly if it's in the dictionary
        if 'hash' in block_dict:
            block.hash = block_dict['hash']
            
        return block
    
    def mine_block(self, difficulty: int) -> None:
        """
        Mine the block by finding a hash with the specified difficulty.
        
        Args:
            difficulty: The number of leading zeros required in the hash
        """
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def is_valid(self) -> bool:
        """
        Check if the block's hash is valid.
        
        Returns:
            bool: True if the hash is valid, False otherwise
        """
        return self.hash == self.calculate_hash()
    
    def __str__(self) -> str:
        """Return a string representation of the block."""
        return f"Block(index={self.index}, hash={self.hash[:10]}..., transactions={len(self.transactions)}, nonce={self.nonce})"

# Helper functions

def create_genesis_block() -> Block:
    """
    Create the genesis block (first block in the chain).
    
    Returns:
        Block: The genesis block
    """
    return Block(
        index=0,
        transactions=[],
        timestamp=time.time(),
        previous_hash="0"
    )

def create_block(index: int, transactions: List[Dict[str, Any]], previous_hash: str) -> Block:
    """
    Create a new block with the given parameters.
    
    Args:
        index: The position of the block in the chain
        transactions: List of transactions to include in the block
        previous_hash: Hash of the previous block in the chain
        
    Returns:
        Block: The created block
    """
    return Block(
        index=index,
        transactions=transactions,
        timestamp=time.time(),
        previous_hash=previous_hash
    )

def validate_block(block: Block, previous_block: Block, difficulty: int) -> bool:
    """
    Validate a block against the previous block and difficulty.
    
    Args:
        block: The block to validate
        previous_block: The previous block in the chain
        difficulty: The current mining difficulty
        
    Returns:
        bool: True if the block is valid, False otherwise
    """
    # Check that the block's index is one more than the previous block
    if block.index != previous_block.index + 1:
        return False
    
    # Check that the block's previous_hash matches the hash of the previous block
    if block.previous_hash != previous_block.hash:
        return False
    
    # Check that the block's hash is valid
    if not block.is_valid():
        return False
    
    # Check that the block's hash meets the difficulty requirement
    if block.hash[:difficulty] != '0' * difficulty:
        return False
    
    return True