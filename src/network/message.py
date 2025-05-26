import json
import time
import uuid
from enum import Enum, auto
from typing import Dict, Any, Optional, Union, List

class MessageType(Enum):
    """Enumeration of message types used in the network protocol."""
    TRANSACTION = auto()  # A new transaction
    BLOCK = auto()        # A new block
    PING = auto()         # Heartbeat ping
    PONG = auto()         # Heartbeat response
    PEER_LIST = auto()    # List of peers
    DIGEST = auto()       # Message digest for anti-entropy
    SYNC_REQ = auto()     # Request for missing messages
    SYNC_RESP = auto()    # Response with requested messages

class Message:
    """
    Represents a message in the network protocol.
    Messages are serialized to JSON for transmission over the network.
    """
    
    def __init__(self, 
                 message_type: Union[MessageType, str], 
                 payload: Dict[str, Any], 
                 sender: Optional[str] = None,
                 message_id: Optional[str] = None,
                 ttl: int = 10):
        """
        Initialize a new message.
        
        Args:
            message_type: The type of message
            payload: The message payload
            sender: The ID of the sender node
            message_id: Optional unique identifier for this message
            ttl: Time-to-live for the message (hops)
        """
        self.id = message_id or str(uuid.uuid4())
        
        # Convert MessageType enum to string if needed
        if isinstance(message_type, MessageType):
            self.type = message_type.name
        else:
            self.type = message_type
            
        self.sender = sender
        self.timestamp = time.time()
        self.ttl = ttl
        self.payload = payload
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dict[str, Any]: The message as a dictionary
        """
        return {
            'id': self.id,
            'type': self.type,
            'sender': self.sender,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'payload': self.payload
        }
    
    def to_json(self) -> str:
        """
        Convert the message to a JSON string.
        
        Returns:
            str: The message as a JSON string
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: The dictionary to create the message from
            
        Returns:
            Message: The created message
        """
        return cls(
            message_type=data.get('type'),
            payload=data.get('payload', {}),
            sender=data.get('sender'),
            message_id=data.get('id'),
            ttl=data.get('ttl', 10)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Create a message from a JSON string.
        
        Args:
            json_str: The JSON string to create the message from
            
        Returns:
            Message: The created message
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def decrement_ttl(self) -> bool:
        """
        Decrement the TTL of the message.
        
        Returns:
            bool: True if the message is still alive, False if TTL reached zero
        """
        self.ttl -= 1
        return self.ttl > 0
    
    def __str__(self) -> str:
        """Return a string representation of the message."""
        return f"Message(id={self.id}, type={self.type}, sender={self.sender}, ttl={self.ttl})"

# Helper functions for creating specific message types

def create_transaction_message(transaction: Dict[str, Any], sender: str, ttl: int = 10) -> Message:
    """
    Create a transaction message.
    
    Args:
        transaction: The transaction to include in the message
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created transaction message
    """
    return Message(
        message_type=MessageType.TRANSACTION,
        payload={'transaction': transaction},
        sender=sender,
        ttl=ttl
    )

def create_block_message(block: Dict[str, Any], sender: str, ttl: int = 10) -> Message:
    """
    Create a block message.
    
    Args:
        block: The block to include in the message
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created block message
    """
    return Message(
        message_type=MessageType.BLOCK,
        payload={'block': block},
        sender=sender,
        ttl=ttl
    )

def create_ping_message(sender: str, ttl: int = 1) -> Message:
    """
    Create a ping message for heartbeat.
    
    Args:
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created ping message
    """
    return Message(
        message_type=MessageType.PING,
        payload={'timestamp': time.time()},
        sender=sender,
        ttl=ttl
    )

def create_pong_message(ping_id: str, sender: str, ttl: int = 1) -> Message:
    """
    Create a pong message in response to a ping.
    
    Args:
        ping_id: The ID of the ping message being responded to
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created pong message
    """
    return Message(
        message_type=MessageType.PONG,
        payload={'ping_id': ping_id, 'timestamp': time.time()},
        sender=sender,
        ttl=ttl
    )

def create_peer_list_message(peers: List[Dict[str, Any]], sender: str, ttl: int = 1) -> Message:
    """
    Create a peer list message.
    
    Args:
        peers: The list of peers to include in the message
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created peer list message
    """
    return Message(
        message_type=MessageType.PEER_LIST,
        payload={'peers': peers},
        sender=sender,
        ttl=ttl
    )

def create_digest_message(message_ids: List[str], sender: str, ttl: int = 1) -> Message:
    """
    Create a digest message for anti-entropy.
    
    Args:
        message_ids: The list of message IDs to include in the digest
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created digest message
    """
    return Message(
        message_type=MessageType.DIGEST,
        payload={'message_ids': message_ids},
        sender=sender,
        ttl=ttl
    )

def create_sync_request_message(missing_ids: List[str], sender: str, ttl: int = 1) -> Message:
    """
    Create a sync request message.
    
    Args:
        missing_ids: The list of message IDs to request
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created sync request message
    """
    return Message(
        message_type=MessageType.SYNC_REQ,
        payload={'missing_ids': missing_ids},
        sender=sender,
        ttl=ttl
    )

def create_sync_response_message(messages: List[Dict[str, Any]], sender: str, ttl: int = 1) -> Message:
    """
    Create a sync response message.
    
    Args:
        messages: The list of messages to include in the response
        sender: The ID of the sender node
        ttl: Time-to-live for the message
        
    Returns:
        Message: The created sync response message
    """
    return Message(
        message_type=MessageType.SYNC_RESP,
        payload={'messages': messages},
        sender=sender,
        ttl=ttl
    )