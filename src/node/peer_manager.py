import threading
import time
import random
from typing import Dict, List, Set, Tuple, Optional, Any

class PeerManager:
    """
    Manages peer connections for a node in the blockchain gossip network.
    Handles peer discovery, connection maintenance, and peer list synchronization.
    """
    
    def __init__(self, node):
        """
        Initialize the peer manager.
        
        Args:
            node: The node this peer manager belongs to
        """
        self.node = node
        self.peers = {}  # Dict[str, Dict[str, Any]] - Maps peer_id to peer info
        self.active_peers = set()  # Set[str] - Set of active peer IDs
        self.dead_peers = set()  # Set[str] - Set of peers marked as dead/unreachable
        self.lock = threading.RLock()
        self.running = False
        self.heartbeat_interval = 30  # Seconds between heartbeats
        self.discovery_interval = 60  # Seconds between peer discovery attempts
        self.max_peers = 10  # Maximum number of peers to maintain
        
        # Background threads
        self.heartbeat_thread = None
        self.discovery_thread = None
    
    def start(self) -> None:
        """Start the peer manager and its background threads."""
        if self.running:
            return
            
        self.running = True
        print(f"PeerManager starting for node {self.node.node_id}")
        
        # Start background threads
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
    
    def stop(self) -> None:
        """Stop the peer manager and its background threads."""
        if not self.running:
            return
            
        self.running = False
        print(f"PeerManager stopping for node {self.node.node_id}")
        
        # Threads will exit on their own since they check self.running
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1.0)
        
        if self.discovery_thread:
            self.discovery_thread.join(timeout=1.0)
    
    def add_peer(self, peer_id: str, host: str, port: int) -> bool:
        """
        Add a new peer to the peer list.
        
        Args:
            peer_id: The unique identifier of the peer
            host: The hostname or IP address of the peer
            port: The port the peer is listening on
            
        Returns:
            bool: True if the peer was added, False otherwise
        """
        with self.lock:
            # Don't add ourselves
            if peer_id == self.node.node_id:
                return False
                
            # Don't add if we're at max capacity and this isn't a known peer
            if len(self.active_peers) >= self.max_peers and peer_id not in self.peers:
                return False
                
            # Add or update the peer
            self.peers[peer_id] = {
                'id': peer_id,
                'host': host,
                'port': port,
                'last_seen': time.time(),
                'active': True
            }
            
            self.active_peers.add(peer_id)
            if peer_id in self.dead_peers:
                self.dead_peers.remove(peer_id)
                
            print(f"Added peer {peer_id} at {host}:{port}")
            return True
    
    def remove_peer(self, peer_id: str) -> bool:
        """
        Remove a peer from the peer list.
        
        Args:
            peer_id: The unique identifier of the peer to remove
            
        Returns:
            bool: True if the peer was removed, False if it wasn't in the list
        """
        with self.lock:
            if peer_id not in self.peers:
                return False
                
            del self.peers[peer_id]
            self.active_peers.discard(peer_id)
            self.dead_peers.discard(peer_id)
            
            print(f"Removed peer {peer_id}")
            return True
    
    def mark_peer_active(self, peer_id: str) -> None:
        """
        Mark a peer as active and update its last seen timestamp.
        
        Args:
            peer_id: The unique identifier of the peer
        """
        with self.lock:
            if peer_id in self.peers:
                self.peers[peer_id]['last_seen'] = time.time()
                self.peers[peer_id]['active'] = True
                self.active_peers.add(peer_id)
                self.dead_peers.discard(peer_id)
    
    def mark_peer_dead(self, peer_id: str) -> None:
        """
        Mark a peer as dead/unreachable.
        
        Args:
            peer_id: The unique identifier of the peer
        """
        with self.lock:
            if peer_id in self.peers:
                self.peers[peer_id]['active'] = False
                self.active_peers.discard(peer_id)
                self.dead_peers.add(peer_id)
                print(f"Marked peer {peer_id} as dead")
    
    def get_active_peers(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active peers.
        
        Returns:
            List[Dict[str, Any]]: A list of active peer information dictionaries
        """
        with self.lock:
            return [self.peers[peer_id] for peer_id in self.active_peers]
    
    def get_random_peers(self, count: int) -> List[Dict[str, Any]]:
        """
        Get a random subset of active peers.
        
        Args:
            count: The number of random peers to return
            
        Returns:
            List[Dict[str, Any]]: A list of random peer information dictionaries
        """
        with self.lock:
            if not self.active_peers:
                return []
                
            # Get a random sample of peer IDs
            sample_size = min(count, len(self.active_peers))
            sampled_ids = random.sample(list(self.active_peers), sample_size)
            
            # Return the peer info for each sampled ID
            return [self.peers[peer_id] for peer_id in sampled_ids]
    
    def _heartbeat_loop(self) -> None:
        """
        Background thread that periodically sends heartbeats to peers
        and checks for unresponsive peers.
        """
        while self.running:
            try:
                self._send_heartbeats()
                self._check_unresponsive_peers()
            except Exception as e:
                print(f"Error in heartbeat loop: {e}")
            
            # Sleep until next heartbeat interval
            time.sleep(self.heartbeat_interval)
    
    def _send_heartbeats(self) -> None:
        """
        Send heartbeat messages to all active peers.
        """
        # This will be implemented once the gossip protocol is created
        # For now, we'll just print a message
        with self.lock:
            if self.active_peers:
                print(f"Sending heartbeats to {len(self.active_peers)} peers")
    
    def _check_unresponsive_peers(self) -> None:
        """
        Check for peers that haven't been seen recently and mark them as dead.
        """
        current_time = time.time()
        timeout = self.heartbeat_interval * 3  # Consider a peer dead after missing 3 heartbeats
        
        with self.lock:
            for peer_id in list(self.active_peers):
                last_seen = self.peers[peer_id]['last_seen']
                if current_time - last_seen > timeout:
                    self.mark_peer_dead(peer_id)
    
    def _discovery_loop(self) -> None:
        """
        Background thread that periodically attempts to discover new peers.
        """
        while self.running:
            try:
                self._discover_peers()
            except Exception as e:
                print(f"Error in discovery loop: {e}")
            
            # Sleep until next discovery interval
            time.sleep(self.discovery_interval)
    
    def _discover_peers(self) -> None:
        """
        Attempt to discover new peers by asking existing peers for their peer lists.
        """
        # This will be implemented once the gossip protocol is created
        # For now, we'll just print a message
        with self.lock:
            if self.active_peers:
                print(f"Attempting peer discovery with {len(self.active_peers)} active peers")
    
    def exchange_peer_lists(self, peer_id: str, peer_list: List[Dict[str, Any]]) -> None:
        """
        Process a peer list received from another peer during peer exchange.
        
        Args:
            peer_id: The ID of the peer that sent the list
            peer_list: A list of peer information dictionaries
        """
        # Mark the sending peer as active
        self.mark_peer_active(peer_id)
        
        # Process each peer in the received list
        for peer_info in peer_list:
            if 'id' in peer_info and 'host' in peer_info and 'port' in peer_info:
                # Add the peer if we don't have too many already
                if len(self.active_peers) < self.max_peers or peer_info['id'] in self.peers:
                    self.add_peer(peer_info['id'], peer_info['host'], peer_info['port'])
    
    def get_peer_info(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific peer.
        
        Args:
            peer_id: The unique identifier of the peer
            
        Returns:
            Optional[Dict[str, Any]]: The peer's information, or None if not found
        """
        with self.lock:
            return self.peers.get(peer_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the peer manager.
        
        Returns:
            Dict[str, Any]: A dictionary of peer manager statistics
        """
        with self.lock:
            return {
                'total_peers': len(self.peers),
                'active_peers': len(self.active_peers),
                'dead_peers': len(self.dead_peers),
                'max_peers': self.max_peers
            }