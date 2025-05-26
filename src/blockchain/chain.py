import json
import time
import os
from typing import List, Dict, Any, Optional, Tuple

# Will be imported once these modules are created
from .block import Block, create_genesis_block, validate_block
from .transaction import Transaction, validate_transaction

class Blockchain:
    """
    Represents a blockchain that maintains a chain of blocks containing transactions.
    Implements consensus mechanisms and chain validation.
    """
    
    def __init__(self, difficulty: int = 4, target_block_time: int = 60):
        """
        Initialize a new blockchain.
        
        Args:
            difficulty: The initial mining difficulty (number of leading zeros required in block hash)
            target_block_time: The target time between blocks in seconds
        """
        self.chain = [create_genesis_block()]
        self.difficulty = difficulty
        self.target_block_time = target_block_time
        self.pending_transactions = []
        self.last_difficulty_adjustment = time.time()
        self.adjustment_interval = 10  # Number of blocks between difficulty adjustments
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the pending transactions pool.
        
        Args:
            transaction: The transaction to add
            
        Returns:
            bool: True if the transaction was added, False otherwise
        """
        # Validate the transaction
        if not validate_transaction(transaction):
            return False
        
        # Check if the transaction is already in the pending transactions
        for tx in self.pending_transactions:
            if tx.transaction_id == transaction.transaction_id:
                return False  # Already have this transaction
        
        # Add to pending transactions
        self.pending_transactions.append(transaction)
        return True
    
    def mine_pending_transactions(self, miner_address: str) -> Optional[Block]:
        """
        Mine a new block with the pending transactions.
        
        Args:
            miner_address: The address to receive the mining reward
            
        Returns:
            Optional[Block]: The mined block if successful, None otherwise
        """
        if not self.pending_transactions:
            return None
        
        # Create a reward transaction for the miner
        reward_transaction = Transaction(
            sender="0",  # "0" indicates a mining reward
            receiver=miner_address,
            amount=1.0,  # Fixed reward for simplicity
            timestamp=time.time()
        )
        reward_transaction.signature = "SYSTEM"  # Special signature for mining rewards
        
        # Add the reward transaction to the list of transactions to include in the block
        transactions = self.pending_transactions.copy()
        transactions.append(reward_transaction.to_dict())
        
        # Create a new block
        last_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash
        )
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        # Add the block to the chain
        self.chain.append(new_block)
        
        # Clear the pending transactions
        self.pending_transactions = []
        
        # Adjust difficulty if needed
        if len(self.chain) % self.adjustment_interval == 0:
            self._adjust_difficulty()
        
        return new_block
    
    def add_block(self, block: Block) -> bool:
        """
        Add a block to the chain.
        
        Args:
            block: The block to add
            
        Returns:
            bool: True if the block was added, False otherwise
        """
        # Validate the block
        last_block = self.chain[-1]
        if not validate_block(block, last_block, self.difficulty):
            return False
        
        # Add the block to the chain
        self.chain.append(block)
        
        # Remove transactions that are now in the block from pending transactions
        block_tx_ids = [tx.get('id') for tx in block.transactions]
        self.pending_transactions = [tx for tx in self.pending_transactions if tx.transaction_id not in block_tx_ids]
        
        # Adjust difficulty if needed
        if len(self.chain) % self.adjustment_interval == 0:
            self._adjust_difficulty()
        
        return True
    
    def _adjust_difficulty(self) -> None:
        """
        Adjust the mining difficulty based on the time it took to mine the last adjustment_interval blocks.
        """
        if len(self.chain) <= self.adjustment_interval:
            return
        
        # Calculate the time it took to mine the last adjustment_interval blocks
        current_time = time.time()
        time_diff = current_time - self.last_difficulty_adjustment
        expected_time = self.target_block_time * self.adjustment_interval
        
        # Adjust difficulty based on the ratio of actual time to expected time
        if time_diff < expected_time / 2:
            self.difficulty += 1
        elif time_diff > expected_time * 2:
            self.difficulty = max(1, self.difficulty - 1)
        
        self.last_difficulty_adjustment = current_time
    
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain.
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Validate the block
            if not validate_block(current_block, previous_block, self.difficulty):
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        """
        Calculate the balance of an address by going through all transactions in the blockchain.
        
        Args:
            address: The address to calculate the balance for
            
        Returns:
            float: The balance of the address
        """
        balance = 0.0
        
        # Go through all blocks in the chain
        for block in self.chain:
            # Go through all transactions in the block
            for tx_dict in block.transactions:
                # If the address is the receiver, add the amount to the balance
                if tx_dict.get('receiver') == address:
                    balance += tx_dict.get('amount', 0.0)
                
                # If the address is the sender, subtract the amount from the balance
                if tx_dict.get('sender') == address:
                    balance -= tx_dict.get('amount', 0.0)
        
        return balance
    
    def get_transaction_history(self, address: str) -> List[Dict[str, Any]]:
        """
        Get the transaction history of an address.
        
        Args:
            address: The address to get the transaction history for
            
        Returns:
            List[Dict[str, Any]]: A list of transactions involving the address
        """
        transactions = []
        
        # Go through all blocks in the chain
        for block in self.chain:
            # Go through all transactions in the block
            for tx_dict in block.transactions:
                # If the address is involved in the transaction, add it to the list
                if tx_dict.get('sender') == address or tx_dict.get('receiver') == address:
                    tx_copy = tx_dict.copy()
                    tx_copy['block_index'] = block.index
                    tx_copy['block_hash'] = block.hash
                    transactions.append(tx_copy)
        
        return transactions
    
    def get_latest_block(self) -> Block:
        """
        Get the latest block in the chain.
        
        Returns:
            Block: The latest block
        """
        return self.chain[-1]
    
    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Replace the chain with a new one if it's longer and valid.
        
        Args:
            new_chain: The new chain to replace with
            
        Returns:
            bool: True if the chain was replaced, False otherwise
        """
        # Check if the new chain is longer than the current one
        if len(new_chain) <= len(self.chain):
            return False
        
        # Check if the new chain is valid
        for i in range(1, len(new_chain)):
            if not validate_block(new_chain[i], new_chain[i - 1], self.difficulty):
                return False
        
        # Replace the chain
        self.chain = new_chain
        return True
    
    def save_to_file(self, filename: str) -> bool:
        """
        Save the blockchain to a file.
        
        Args:
            filename: The name of the file to save to
            
        Returns:
            bool: True if the blockchain was saved successfully, False otherwise
        """
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Convert the chain to a list of dictionaries
            chain_data = [block.to_dict() for block in self.chain]
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump({
                    'chain': chain_data,
                    'difficulty': self.difficulty,
                    'target_block_time': self.target_block_time,
                    'adjustment_interval': self.adjustment_interval,
                    'last_difficulty_adjustment': self.last_difficulty_adjustment
                }, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error saving blockchain to file: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filename: str) -> Optional['Blockchain']:
        """
        Load a blockchain from a file.
        
        Args:
            filename: The name of the file to load from
            
        Returns:
            Optional[Blockchain]: The loaded blockchain, or None if loading failed
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Create a new blockchain with the loaded parameters
            blockchain = cls(
                difficulty=data.get('difficulty', 4),
                target_block_time=data.get('target_block_time', 60)
            )
            
            # Set other parameters
            blockchain.adjustment_interval = data.get('adjustment_interval', 10)
            blockchain.last_difficulty_adjustment = data.get('last_difficulty_adjustment', time.time())
            
            # Load the chain
            blockchain.chain = [Block.from_dict(block_dict) for block_dict in data.get('chain', [])]
            
            return blockchain
        except Exception as e:
            print(f"Error loading blockchain from file: {e}")
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the blockchain to a dictionary.
        
        Returns:
            Dict[str, Any]: The blockchain as a dictionary
        """
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty,
            'target_block_time': self.target_block_time,
            'adjustment_interval': self.adjustment_interval,
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'last_difficulty_adjustment': self.last_difficulty_adjustment
        }
    
    def __str__(self) -> str:
        """Return a string representation of the blockchain."""
        return f"Blockchain(blocks={len(self.chain)}, difficulty={self.difficulty}, pending_transactions={len(self.pending_transactions)})"