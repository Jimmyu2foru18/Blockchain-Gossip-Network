import hashlib
import base64
import json
import os
import time
from typing import Tuple, Dict, Any, Optional

def generate_key_pair() -> Tuple[str, str]:
    """
    Generate a simple key pair for signing and verifying transactions.
    
    Note: This is a simplified implementation for demonstration purposes only.
    In a real blockchain, you would use proper cryptographic libraries like RSA or ECDSA.
    
    Returns:
        Tuple[str, str]: A tuple containing (private_key, public_key)
    """
    # Generate a random private key
    private_key = base64.b64encode(os.urandom(32)).decode('utf-8')
    
    # Derive a public key from the private key
    # In a real implementation, this would use proper key derivation
    public_key = hashlib.sha256(private_key.encode()).hexdigest()
    
    return private_key, public_key

def sign_data(data: Dict[str, Any], private_key: str) -> str:
    """
    Sign data with a private key.
    
    Note: This is a simplified implementation for demonstration purposes only.
    In a real blockchain, you would use proper cryptographic libraries.
    
    Args:
        data: The data to sign
        private_key: The private key to sign with
        
    Returns:
        str: The signature
    """
    # Convert the data to a string
    data_string = json.dumps(data, sort_keys=True)
    
    # Create a signature by combining the private key and data
    # In a real implementation, this would use proper signing algorithms
    signature_input = private_key + data_string
    signature = hashlib.sha256(signature_input.encode()).hexdigest()
    
    return signature

def verify_signature(data: Dict[str, Any], signature: str, public_key: str) -> bool:
    """
    Verify a signature with a public key.
    
    Note: This is a simplified implementation for demonstration purposes only.
    In a real blockchain, you would use proper cryptographic libraries.
    
    Args:
        data: The data that was signed
        signature: The signature to verify
        public_key: The public key to verify with
        
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    # In a real implementation, this would use proper verification algorithms
    # For this simplified version, we'll just return True
    # This is just a placeholder for the actual verification logic
    return True

def calculate_hash(data: Dict[str, Any]) -> str:
    """
    Calculate a hash for the given data.
    
    Args:
        data: The data to hash
        
    Returns:
        str: The calculated hash
    """
    # Convert the data to a string
    data_string = json.dumps(data, sort_keys=True)
    
    # Calculate the hash
    return hashlib.sha256(data_string.encode()).hexdigest()

def create_merkle_root(hashes: list) -> str:
    """
    Create a Merkle root from a list of hashes.
    
    Args:
        hashes: A list of hash strings
        
    Returns:
        str: The Merkle root hash
    """
    if not hashes:
        return hashlib.sha256(b'').hexdigest()
    
    if len(hashes) == 1:
        return hashes[0]
    
    # If the number of hashes is odd, duplicate the last one
    if len(hashes) % 2 == 1:
        hashes.append(hashes[-1])
    
    # Pair up hashes and hash each pair
    new_hashes = []
    for i in range(0, len(hashes), 2):
        combined = hashes[i] + hashes[i + 1]
        new_hash = hashlib.sha256(combined.encode()).hexdigest()
        new_hashes.append(new_hash)
    
    # Recursively build the tree
    return create_merkle_root(new_hashes)

def generate_wallet() -> Dict[str, str]:
    """
    Generate a new wallet with a key pair and address.
    
    Returns:
        Dict[str, str]: A dictionary containing the wallet information
    """
    # Generate a key pair
    private_key, public_key = generate_key_pair()
    
    # Generate an address from the public key
    address = hashlib.sha256(public_key.encode()).hexdigest()[:40]
    
    return {
        'private_key': private_key,
        'public_key': public_key,
        'address': address,
        'created_at': time.time()
    }

def validate_address(address: str) -> bool:
    """
    Validate a blockchain address format.
    
    Args:
        address: The address to validate
        
    Returns:
        bool: True if the address is valid, False otherwise
    """
    # In a real implementation, this would check the address format and possibly a checksum
    # For this simplified version, we'll just check the length
    return len(address) == 40 and all(c in '0123456789abcdef' for c in address.lower())