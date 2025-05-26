import threading
import time
import random
import json
from typing import Dict, List, Set, Any, Optional, Callable

# Will be imported once these modules are created
# from ..node.node import Node
# from .message import Message, MessageType
# from .transport import Transport

class GossipProtocol:
    """
    Implementation of a gossip protocol for efficient message propagation in the network.
    Uses a probabilistic approach to broadcast messages to a subset of peers.
    """
    
    def __init__(self, node):
        """
        Initialize the gossip protocol.
        
        Args:
            node: The node this gossip protocol belongs to
        """
        self.node = node
        self.running = False
        self.seen_messages = set()  # Set of message IDs we've seen
        self.message_cache = {}  # Dict[str, Dict] - Cache of recent messages
        self.lock = threading.RLock()
        
        # Gossip parameters
        self.fanout = 3  # Number of peers to forward messages to
        self.gossip_interval = 1.0  # Seconds between gossip rounds
        self.message_ttl = 10  # Time-to-live for messages (hops)
        self.cache_expiry = 300  # Seconds to keep messages in cache
        
        # Anti-entropy parameters
        self.anti_entropy_interval = 300  # Seconds between anti-entropy sync
        
        # Background threads
        self.gossip_thread = None
        self.anti_entropy_thread = None
        
        # Message handlers
        self.message_handlers = {}
    
    def start(self) -> None:
        """Start the gossip protocol and its background threads."""
        if self.running:
            return
            
        self.running = True
        print(f"GossipProtocol starting for node {self.node.node_id}")
        
        # Start background threads
        self.gossip_thread = threading.Thread(target=self._gossip_loop, daemon=True)
        self.gossip_thread.start()
        
        self.anti_entropy_thread = threading.Thread(target=self._anti_entropy_loop, daemon=True)
        self.anti_entropy_thread.start()
        
        # Register message handlers
        self._register_default_handlers()
    
    def stop(self) -> None:
        """Stop the gossip protocol and its background threads."""
        if not self.running:
            return
            
        self.running = False
        print(f"GossipProtocol stopping for node {self.node.node_id}")
        
        # Threads will exit on their own since they check self.running
        if self.gossip_thread:
            self.gossip_thread.join(timeout=1.0)
        
        if self.anti_entropy_thread:
            self.anti_entropy_thread.join(timeout=1.0)
    
    def broadcast(self, message_type: str, payload: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """
        Broadcast a message to the network using the gossip protocol.
        
        Args:
            message_type: The type of message to broadcast
            payload: The message payload
            ttl: Time-to-live for the message (hops), or None to use default
            
        Returns:
            str: The ID of the broadcast message
        """
        # Create a message
        message_id = f"{self.node.node_id}:{time.time()}:{random.randint(0, 1000000)}"
        message = {
            'id': message_id,
            'type': message_type,
            'sender': self.node.node_id,
            'timestamp': time.time(),
            'ttl': ttl or self.message_ttl,
            'payload': payload
        }
        
        # Add to our seen messages and cache
        with self.lock:
            self.seen_messages.add(message_id)
            self.message_cache[message_id] = {
                'message': message,
                'timestamp': time.time()
            }
        
        # Broadcast to peers
        self._broadcast_to_peers(message)
        
        return message_id
    
    def broadcast_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Broadcast a transaction to the network.
        
        Args:
            transaction: The transaction to broadcast
            
        Returns:
            str: The ID of the broadcast message
        """
        return self.broadcast('TRANSACTION', {'transaction': transaction})
    
    def receive_message(self, message: Dict[str, Any], from_peer: Optional[str] = None) -> bool:
        """
        Process a message received from a peer.
        
        Args:
            message: The received message
            from_peer: The ID of the peer that sent the message
            
        Returns:
            bool: True if the message was processed, False if it was ignored
        """
        message_id = message.get('id')
        if not message_id:
            print(f"Received message without ID from {from_peer}")
            return False
        
        # Check if we've seen this message before
        with self.lock:
            if message_id in self.seen_messages:
                return False  # Already seen this message
            
            # Mark as seen and add to cache
            self.seen_messages.add(message_id)
            self.message_cache[message_id] = {
                'message': message,
                'timestamp': time.time()
            }
        
        # Decrement TTL
        ttl = message.get('ttl', 0) - 1
        if ttl <= 0:
            # TTL expired, don't forward
            print(f"Message {message_id} TTL expired")
            return True
        
        # Update TTL
        message['ttl'] = ttl
        
        # Handle the message based on its type
        message_type = message.get('type')
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type](message, from_peer)
            except Exception as e:
                print(f"Error handling message of type {message_type}: {e}")
        
        # Forward to other peers (gossip)
        self._relay_message(message, from_peer)
        
        return True
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any], Optional[str]], None]) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: The type of message to handle
            handler: The handler function to call when a message of this type is received
        """
        self.message_handlers[message_type] = handler
    
    def _register_default_handlers(self) -> None:
        """
        Register default message handlers.
        """
        self.register_handler('TRANSACTION', self._handle_transaction)
        self.register_handler('BLOCK', self._handle_block)
        self.register_handler('PEER_LIST', self._handle_peer_list)
        self.register_handler('PING', self._handle_ping)
        self.register_handler('PONG', self._handle_pong)
    
    def _handle_transaction(self, message: Dict[str, Any], from_peer: Optional[str]) -> None:
        """
        Handle a transaction message.
        
        Args:
            message: The transaction message
            from_peer: The ID of the peer that sent the message
        """
        transaction = message.get('payload', {}).get('transaction')
        if transaction:
            self.node.receive_transaction(transaction, from_peer)
    
    def _handle_block(self, message: Dict[str, Any], from_peer: Optional[str]) -> None:
        """
        Handle a block message.
        
        Args:
            message: The block message
            from_peer: The ID of the peer that sent the message
        """
        # This will be implemented once the blockchain module is created
        block = message.get('payload', {}).get('block')
        if block:
            print(f"Received block from {from_peer}: {block.get('id', 'unknown')}")
    
    def _handle_peer_list(self, message: Dict[str, Any], from_peer: Optional[str]) -> None:
        """
        Handle a peer list message.
        
        Args:
            message: The peer list message
            from_peer: The ID of the peer that sent the message
        """
        peer_list = message.get('payload', {}).get('peers', [])
        if peer_list and hasattr(self.node, 'peer_manager'):
            self.node.peer_manager.exchange_peer_lists(from_peer, peer_list)
    
    def _handle_ping(self, message: Dict[str, Any], from_peer: Optional[str]) -> None:
        """
        Handle a ping message by responding with a pong.
        
        Args:
            message: The ping message
            from_peer: The ID of the peer that sent the message
        """
        if from_peer:
            # Send a pong response
            pong_payload = {
                'ping_id': message.get('id'),
                'timestamp': time.time()
            }
            self.broadcast('PONG', pong_payload, ttl=1)  # TTL of 1 so it only goes to the sender
    
    def _handle_pong(self, message: Dict[str, Any], from_peer: Optional[str]) -> None:
        """
        Handle a pong message (response to a ping).
        
        Args:
            message: The pong message
            from_peer: The ID of the peer that sent the message
        """
        if from_peer and hasattr(self.node, 'peer_manager'):
            # Mark the peer as active
            self.node.peer_manager.mark_peer_active(from_peer)
    
    def _broadcast_to_peers(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected peers.
        
        Args:
            message: The message to broadcast
        """
        # This will be implemented once the transport module is created
        # For now, we'll just print a message
        print(f"Broadcasting message {message['id']} of type {message['type']}")
    
    def _relay_message(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        """
        Relay a message to a subset of peers (gossip).
        
        Args:
            message: The message to relay
            exclude_peer: The ID of the peer to exclude from relaying
        """
        # Get a list of peers to relay to
        peers_to_relay = self._select_peers_for_relay(exclude_peer)
        
        if not peers_to_relay:
            return
        
        # This will be implemented once the transport module is created
        # For now, we'll just print a message
        peer_ids = [peer.get('id', 'unknown') for peer in peers_to_relay]
        print(f"Relaying message {message['id']} to peers: {', '.join(peer_ids)}")
    
    def _select_peers_for_relay(self, exclude_peer: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select a subset of peers to relay a message to.
        
        Args:
            exclude_peer: The ID of the peer to exclude from selection
            
        Returns:
            List[Dict[str, Any]]: A list of selected peer information dictionaries
        """
        if not hasattr(self.node, 'peer_manager'):
            return []
        
        # Get active peers
        active_peers = self.node.peer_manager.get_active_peers()
        
        # Filter out the excluded peer
        if exclude_peer:
            active_peers = [peer for peer in active_peers if peer.get('id') != exclude_peer]
        
        if not active_peers:
            return []
        
        # Select a random subset of peers
        fanout = min(self.fanout, len(active_peers))
        return random.sample(active_peers, fanout)
    
    def _gossip_loop(self) -> None:
        """
        Background thread that periodically gossips with peers.
        """
        while self.running:
            try:
                self._gossip_round()
            except Exception as e:
                print(f"Error in gossip loop: {e}")
            
            # Sleep until next gossip interval
            time.sleep(self.gossip_interval)
    
    def _gossip_round(self) -> None:
        """
        Perform a round of gossip by sending a random recent message to random peers.
        """
        # Get a random recent message from the cache
        message = self._get_random_recent_message()
        if not message:
            return
        
        # Relay to random peers
        self._relay_message(message)
    
    def _get_random_recent_message(self) -> Optional[Dict[str, Any]]:
        """
        Get a random recent message from the cache.
        
        Returns:
            Optional[Dict[str, Any]]: A random recent message, or None if the cache is empty
        """
        with self.lock:
            if not self.message_cache:
                return None
            
            # Get a random message ID
            message_id = random.choice(list(self.message_cache.keys()))
            return self.message_cache[message_id]['message']
    
    def _anti_entropy_loop(self) -> None:
        """
        Background thread that periodically performs anti-entropy synchronization with peers.
        """
        while self.running:
            try:
                self._anti_entropy_round()
            except Exception as e:
                print(f"Error in anti-entropy loop: {e}")
            
            # Sleep until next anti-entropy interval
            time.sleep(self.anti_entropy_interval)
    
    def _anti_entropy_round(self) -> None:
        """
        Perform a round of anti-entropy synchronization with a random peer.
        """
        if not hasattr(self.node, 'peer_manager'):
            return
        
        # Get a random peer
        peers = self.node.peer_manager.get_random_peers(1)
        if not peers:
            return
        
        peer = peers[0]
        peer_id = peer.get('id')
        
        # Send our message digests to the peer
        with self.lock:
            message_ids = list(self.message_cache.keys())
        
        if not message_ids:
            return
        
        # Create a digest message
        digest_payload = {
            'message_ids': message_ids
        }
        
        # Broadcast the digest to the selected peer
        self.broadcast('DIGEST', digest_payload, ttl=1)  # TTL of 1 so it only goes to the selected peer
        
        print(f"Sent digest with {len(message_ids)} message IDs to peer {peer_id}")
    
    def _clean_message_cache(self) -> None:
        """
        Clean up old messages from the cache.
        """
        current_time = time.time()
        with self.lock:
            # Find expired messages
            expired_ids = []
            for message_id, cache_entry in self.message_cache.items():
                if current_time - cache_entry['timestamp'] > self.cache_expiry:
                    expired_ids.append(message_id)
            
            # Remove expired messages
            for message_id in expired_ids:
                del self.message_cache[message_id]
                self.seen_messages.discard(message_id)
            
            if expired_ids:
                print(f"Cleaned {len(expired_ids)} expired messages from cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the gossip protocol.
        
        Returns:
            Dict[str, Any]: A dictionary of gossip protocol statistics
        """
        with self.lock:
            return {
                'seen_messages': len(self.seen_messages),
                'cached_messages': len(self.message_cache),
                'fanout': self.fanout,
                'message_ttl': self.message_ttl,
                'gossip_interval': self.gossip_interval,
                'anti_entropy_interval': self.anti_entropy_interval
            }