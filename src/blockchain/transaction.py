import time
import json
import hashlib
import uuid
from typing import Dict, Any, Optional, List

class Transaction:
    """
    Represents a transaction in the blockchain.
    A transaction transfers value from a sender to a receiver.
    """
    
    def __init__(self, 
                 sender: str, 
                 receiver: str, 
                 amount: float, 
                 timestamp: Optional[float] = None, 
                 transaction_id: Optional[str] = None, 
                 signature: Optional[str] = None):
        """
        Initialize a new transaction.
        
        Args:
            sender: The identifier of the sender
            receiver: The identifier of the receiver
            amount: The amount to transfer
            timestamp: The time the transaction was created (defaults to current time)
            transaction_id: Optional unique identifier for this transaction
            signature: Optional cryptographic signature for the transaction
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.signature = signature
    
    def calculate_hash(self) -> str:
        """
        Calculate the hash of the transaction.
        
        Returns:
            str: The SHA-256 hash of the transaction
        """
        # Convert the transaction to a string and hash it
        tx_string = json.dumps(self.to_dict(include_signature=False), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def sign(self, private_key: str) -> None:
        """
        Sign the transaction with a private key.
        
        Args:
            private_key: The private key to sign with
        """
        # In a real implementation, this would use proper cryptographic signing
        # For this simplified version, we'll just create a dummy signature
        tx_hash = self.calculate_hash()
        self.signature = f"{private_key}:{tx_hash}"
    
    def verify_signature(self, public_key: str) -> bool:
        """
        Verify the transaction's signature with a public key.
        
        Args:
            public_key: The public key to verify with
            
        Returns:
            bool: True if the signature is valid, False otherwise
        """
        # In a real implementation, this would use proper cryptographic verification
        # For this simplified version, we'll just check if the signature exists
        return self.signature is not None
    
    def to_dict(self, include_signature: bool = True) -> Dict[str, Any]:
        """
        Convert the transaction to a dictionary.
        
        Args:
            include_signature: Whether to include the signature in the dictionary
            
        Returns:
            Dict[str, Any]: The transaction as a dictionary
        """
        tx_dict = {
            'id': self.transaction_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp
        }
        
        if include_signature and self.signature:
            tx_dict['signature'] = self.signature
            
        return tx_dict
    
    @classmethod
    def from_dict(cls, tx_dict: Dict[str, Any]) -> 'Transaction':
        """
        Create a transaction from a dictionary.
        
        Args:
            tx_dict: The dictionary to create the transaction from
            
        Returns:
            Transaction: The created transaction
        """
        return cls(
            sender=tx_dict['sender'],
            receiver=tx_dict['receiver'],
            amount=tx_dict['amount'],
            timestamp=tx_dict.get('timestamp', time.time()),
            transaction_id=tx_dict.get('id', str(uuid.uuid4())),
            signature=tx_dict.get('signature')
        )
    
    def is_valid(self) -> bool:
        """
        Check if the transaction is valid.
        
        Returns:
            bool: True if the transaction is valid, False otherwise
        """
        # Check that the amount is positive
        if self.amount <= 0:
            return False
        
        # Check that the sender and receiver are not the same
        if self.sender == self.receiver:
            return False
        
        # In a real implementation, we would also verify the signature here
        # For this simplified version, we'll just check if the signature exists
        if not self.signature:
            return False
        
        return True
    
    def __str__(self) -> str:
        """Return a string representation of the transaction."""
        return f"Transaction(id={self.transaction_id[:8]}..., sender={self.sender}, receiver={self.receiver}, amount={self.amount})"

# Helper functions

def create_transaction(sender: str, receiver: str, amount: float, private_key: Optional[str] = None) -> Transaction:
    """
    Create a new transaction and optionally sign it.
    
    Args:
        sender: The identifier of the sender
        receiver: The identifier of the receiver
        amount: The amount to transfer
        private_key: Optional private key to sign the transaction with
        
    Returns:
        Transaction: The created transaction
    """
    transaction = Transaction(sender, receiver, amount)
    
    if private_key:
        transaction.sign(private_key)
        
    return transaction

def validate_transaction(transaction: Transaction, public_key: Optional[str] = None) -> bool:
    """
    Validate a transaction.
    
    Args:
        transaction: The transaction to validate
        public_key: Optional public key to verify the signature with
        
    Returns:
        bool: True if the transaction is valid, False otherwise
    """
    # Check basic validity
    if not transaction.is_valid():
        return False
    
    # Verify signature if public key is provided
    if public_key and not transaction.verify_signature(public_key):
        return False
    
    return True

def validate_transactions(transactions: List[Transaction]) -> bool:
    """
    Validate a list of transactions.
    
    Args:
        transactions: The list of transactions to validate
        
    Returns:
        bool: True if all transactions are valid, False otherwise
    """
    return all(validate_transaction(tx) for tx in transactions)