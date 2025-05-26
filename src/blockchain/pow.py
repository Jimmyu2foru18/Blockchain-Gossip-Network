import hashlib
import time
from typing import Dict, Any, Optional

class ProofOfWork:
    """
    Implements the Proof-of-Work consensus algorithm.
    Miners must find a hash with a certain number of leading zeros.
    """
    
    def __init__(self, difficulty: int = 4, target_block_time: int = 60):
        """
        Initialize the Proof-of-Work system.
        
        Args:
            difficulty: The initial mining difficulty (number of leading zeros required in hash)
            target_block_time: The target time between blocks in seconds
        """
        self.difficulty = difficulty
        self.target_block_time = target_block_time
        self.last_adjustment_time = time.time()
        self.blocks_since_adjustment = 0
        self.adjustment_interval = 10  # Number of blocks between difficulty adjustments
    
    def get_target(self) -> str:
        """
        Get the current target hash pattern.
        
        Returns:
            str: A string of zeros representing the target difficulty
        """
        return '0' * self.difficulty
    
    def calculate_hash(self, data: Dict[str, Any], nonce: int) -> str:
        """
        Calculate a hash for the given data and nonce.
        
        Args:
            data: The data to hash
            nonce: The nonce value to include in the hash
            
        Returns:
            str: The calculated hash
        """
        # Convert the data to a string and add the nonce
        data_string = str(data) + str(nonce)
        
        # Calculate the hash
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def mine(self, data: Dict[str, Any], max_nonce: int = 1000000) -> Optional[Dict[str, Any]]:
        """
        Mine a block by finding a hash that meets the difficulty requirement.
        
        Args:
            data: The data to include in the block
            max_nonce: The maximum nonce value to try
            
        Returns:
            Optional[Dict[str, Any]]: The mined block with nonce and hash, or None if mining failed
        """
        target = self.get_target()
        nonce = 0
        start_time = time.time()
        
        while nonce < max_nonce:
            hash_result = self.calculate_hash(data, nonce)
            
            if hash_result.startswith(target):
                # Found a valid hash
                end_time = time.time()
                mining_time = end_time - start_time
                
                print(f"Block mined in {mining_time:.2f} seconds with nonce {nonce}")
                print(f"Hash: {hash_result}")
                
                # Update block data with the nonce and hash
                result = data.copy()
                result['nonce'] = nonce
                result['hash'] = hash_result
                
                # Update difficulty if needed
                self.blocks_since_adjustment += 1
                if self.blocks_since_adjustment >= self.adjustment_interval:
                    self._adjust_difficulty(end_time)
                
                return result
            
            nonce += 1
        
        print(f"Failed to mine block after trying {max_nonce} nonces")
        return None
    
    def verify(self, data: Dict[str, Any], nonce: int, hash_value: str) -> bool:
        """
        Verify that a hash is valid for the given data and nonce.
        
        Args:
            data: The data that was hashed
            nonce: The nonce that was used
            hash_value: The hash to verify
            
        Returns:
            bool: True if the hash is valid, False otherwise
        """
        # Calculate the hash for the data and nonce
        calculated_hash = self.calculate_hash(data, nonce)
        
        # Check that the calculated hash matches the provided hash
        if calculated_hash != hash_value:
            return False
        
        # Check that the hash meets the difficulty requirement
        target = self.get_target()
        return hash_value.startswith(target)
    
    def _adjust_difficulty(self, current_time: float) -> None:
        """
        Adjust the mining difficulty based on the time it took to mine the last adjustment_interval blocks.
        
        Args:
            current_time: The current time
        """
        time_diff = current_time - self.last_adjustment_time
        expected_time = self.target_block_time * self.adjustment_interval
        
        # Adjust difficulty based on the ratio of actual time to expected time
        if time_diff < expected_time / 2:
            # Blocks are being mined too quickly, increase difficulty
            self.difficulty += 1
            print(f"Increased difficulty to {self.difficulty}")
        elif time_diff > expected_time * 2:
            # Blocks are being mined too slowly, decrease difficulty
            self.difficulty = max(1, self.difficulty - 1)
            print(f"Decreased difficulty to {self.difficulty}")
        
        # Reset counters
        self.last_adjustment_time = current_time
        self.blocks_since_adjustment = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Proof-of-Work system.
        
        Returns:
            Dict[str, Any]: A dictionary of Proof-of-Work statistics
        """
        return {
            'difficulty': self.difficulty,
            'target': self.get_target(),
            'target_block_time': self.target_block_time,
            'adjustment_interval': self.adjustment_interval,
            'blocks_since_adjustment': self.blocks_since_adjustment
        }