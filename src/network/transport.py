import socket
import threading
import json
import time
import select
import queue
from typing import Dict, List, Tuple, Optional, Any, Callable, Set

# Will be imported once these modules are created
# from .message import Message

class Transport:
    """
    Handles the network transport layer for the blockchain gossip network.
    Supports both TCP for reliable communication and UDP for discovery.
    """
    
    def __init__(self, host: str, port: int, node=None):
        """
        Initialize the transport layer.
        
        Args:
            host: The hostname or IP address to bind to
            port: The port to listen on
            node: The node this transport layer belongs to
        """
        self.host = host
        self.port = port
        self.node = node
        self.running = False
        
        # TCP socket for reliable communication
        self.tcp_socket = None
        self.tcp_connections = {}  # Dict[str, socket.socket] - Maps peer_id to socket
        self.tcp_lock = threading.RLock()
        
        # UDP socket for discovery and lightweight communication
        self.udp_socket = None
        self.udp_lock = threading.RLock()
        
        # Message handlers
        self.message_handlers = []
        
        # Background threads
        self.tcp_listen_thread = None
        self.udp_listen_thread = None
        
        # Connection parameters
        self.connection_timeout = 5  # seconds
        self.buffer_size = 4096  # bytes
        self.max_connections = 100
        
        # Message queues for async sending
        self.send_queue = queue.Queue()
        self.send_thread = None
    
    def start(self) -> bool:
        """
        Start the transport layer and begin listening for connections.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            return True
            
        try:
            # Initialize TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((self.host, self.port))
            self.tcp_socket.listen(self.max_connections)
            self.tcp_socket.settimeout(0.1)  # Non-blocking with short timeout
            
            # Initialize UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((self.host, self.port))
            self.udp_socket.settimeout(0.1)  # Non-blocking with short timeout
            
            self.running = True
            print(f"Transport layer started on {self.host}:{self.port}")
            
            # Start background threads
            self.tcp_listen_thread = threading.Thread(target=self._tcp_listen_loop, daemon=True)
            self.tcp_listen_thread.start()
            
            self.udp_listen_thread = threading.Thread(target=self._udp_listen_loop, daemon=True)
            self.udp_listen_thread.start()
            
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            self.send_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting transport layer: {e}")
            self.stop()
            return False
    
    def stop(self) -> None:
        """Stop the transport layer and close all connections."""
        if not self.running:
            return
            
        self.running = False
        print(f"Transport layer stopping on {self.host}:{self.port}")
        
        # Close all TCP connections
        with self.tcp_lock:
            for peer_id, conn in self.tcp_connections.items():
                try:
                    conn.close()
                except:
                    pass
            self.tcp_connections.clear()
        
        # Close sockets
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None
        
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
            self.udp_socket = None
        
        # Wait for threads to exit
        if self.tcp_listen_thread:
            self.tcp_listen_thread.join(timeout=1.0)
        
        if self.udp_listen_thread:
            self.udp_listen_thread.join(timeout=1.0)
        
        if self.send_thread:
            self.send_thread.join(timeout=1.0)
    
    def connect(self, host: str, port: int) -> bool:
        """
        Connect to a peer at the given host and port.
        
        Args:
            host: The hostname or IP address of the peer
            port: The port the peer is listening on
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self.running:
            return False
            
        peer_id = f"{host}:{port}"
        
        # Check if already connected
        with self.tcp_lock:
            if peer_id in self.tcp_connections:
                return True
        
        try:
            # Create a new socket for this connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            sock.connect((host, port))
            
            # Add to connections
            with self.tcp_lock:
                self.tcp_connections[peer_id] = sock
            
            # Start a thread to handle incoming messages from this peer
            threading.Thread(target=self._handle_tcp_connection, args=(sock, peer_id), daemon=True).start()
            
            print(f"Connected to peer at {host}:{port}")
            return True
        except Exception as e:
            print(f"Error connecting to peer at {host}:{port}: {e}")
            return False
    
    def disconnect(self, peer_id: str) -> bool:
        """
        Disconnect from a peer.
        
        Args:
            peer_id: The ID of the peer to disconnect from
            
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        with self.tcp_lock:
            if peer_id not in self.tcp_connections:
                return False
                
            try:
                self.tcp_connections[peer_id].close()
            except:
                pass
                
            del self.tcp_connections[peer_id]
            print(f"Disconnected from peer {peer_id}")
            return True
    
    def send_tcp(self, peer_id: str, data: Dict[str, Any]) -> bool:
        """
        Send data to a peer over TCP.
        
        Args:
            peer_id: The ID of the peer to send to
            data: The data to send
            
        Returns:
            bool: True if the data was sent successfully, False otherwise
        """
        # Queue the message for async sending
        self.send_queue.put(('tcp', peer_id, data))
        return True
    
    def send_udp(self, host: str, port: int, data: Dict[str, Any]) -> bool:
        """
        Send data to a peer over UDP.
        
        Args:
            host: The hostname or IP address of the peer
            port: The port the peer is listening on
            data: The data to send
            
        Returns:
            bool: True if the data was sent successfully, False otherwise
        """
        # Queue the message for async sending
        self.send_queue.put(('udp', (host, port), data))
        return True
    
    def broadcast_tcp(self, data: Dict[str, Any], exclude_peers: Optional[Set[str]] = None) -> None:
        """
        Broadcast data to all connected TCP peers.
        
        Args:
            data: The data to broadcast
            exclude_peers: Optional set of peer IDs to exclude from the broadcast
        """
        exclude_peers = exclude_peers or set()
        
        with self.tcp_lock:
            for peer_id in self.tcp_connections:
                if peer_id not in exclude_peers:
                    self.send_queue.put(('tcp', peer_id, data))
    
    def broadcast_udp(self, data: Dict[str, Any], peers: List[Tuple[str, int]]) -> None:
        """
        Broadcast data to a list of peers over UDP.
        
        Args:
            data: The data to broadcast
            peers: List of (host, port) tuples to broadcast to
        """
        for host, port in peers:
            self.send_queue.put(('udp', (host, port), data))
    
    def register_message_handler(self, handler: Callable[[Dict[str, Any], Optional[str]], None]) -> None:
        """
        Register a handler for incoming messages.
        
        Args:
            handler: The handler function to call when a message is received
        """
        self.message_handlers.append(handler)
    
    def _tcp_listen_loop(self) -> None:
        """
        Background thread that listens for incoming TCP connections.
        """
        while self.running and self.tcp_socket:
            try:
                # Accept new connections
                try:
                    client_socket, client_address = self.tcp_socket.accept()
                    client_socket.settimeout(None)  # Set to blocking mode for the handler thread
                    
                    # Get peer ID
                    host, port = client_address
                    peer_id = f"{host}:{port}"
                    
                    # Add to connections
                    with self.tcp_lock:
                        self.tcp_connections[peer_id] = client_socket
                    
                    # Start a thread to handle this connection
                    threading.Thread(target=self._handle_tcp_connection, args=(client_socket, peer_id), daemon=True).start()
                    
                    print(f"Accepted connection from {peer_id}")
                except socket.timeout:
                    # No new connections, continue
                    pass
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        print(f"Error accepting TCP connection: {e}")
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    print(f"Error in TCP listen loop: {e}")
    
    def _udp_listen_loop(self) -> None:
        """
        Background thread that listens for incoming UDP packets.
        """
        while self.running and self.udp_socket:
            try:
                # Receive UDP packets
                try:
                    data, addr = self.udp_socket.recvfrom(self.buffer_size)
                    host, port = addr
                    peer_id = f"{host}:{port}"
                    
                    # Process the received data
                    self._process_udp_data(data, peer_id, addr)
                except socket.timeout:
                    # No data received, continue
                    pass
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        print(f"Error receiving UDP packet: {e}")
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    print(f"Error in UDP listen loop: {e}")
    
    def _handle_tcp_connection(self, sock: socket.socket, peer_id: str) -> None:
        """
        Handle an established TCP connection.
        
        Args:
            sock: The socket for this connection
            peer_id: The ID of the peer
        """
        try:
            # Set socket to non-blocking mode
            sock.setblocking(False)
            
            # Buffer for incomplete data
            buffer = b''
            
            while self.running:
                # Check if the connection is still in our list
                with self.tcp_lock:
                    if peer_id not in self.tcp_connections:
                        break
                
                # Try to receive data
                try:
                    ready_to_read, _, _ = select.select([sock], [], [], 0.1)
                    if ready_to_read:
                        data = sock.recv(self.buffer_size)
                        if not data:  # Connection closed by peer
                            break
                        
                        # Add to buffer
                        buffer += data
                        
                        # Process complete messages in the buffer
                        buffer = self._process_tcp_buffer(buffer, peer_id)
                except ConnectionError:
                    # Connection lost
                    break
                except Exception as e:
                    print(f"Error handling TCP connection from {peer_id}: {e}")
                    break
        finally:
            # Clean up the connection
            with self.tcp_lock:
                if peer_id in self.tcp_connections:
                    try:
                        self.tcp_connections[peer_id].close()
                    except:
                        pass
                    del self.tcp_connections[peer_id]
            
            print(f"Connection with {peer_id} closed")
    
    def _process_tcp_buffer(self, buffer: bytes, peer_id: str) -> bytes:
        """
        Process the TCP receive buffer, extracting and handling complete messages.
        
        Args:
            buffer: The current receive buffer
            peer_id: The ID of the peer that sent the data
            
        Returns:
            bytes: The remaining buffer after processing
        """
        # Simple protocol: each message is a JSON object followed by a newline
        while b'\n' in buffer:
            # Split at the first newline
            message_bytes, buffer = buffer.split(b'\n', 1)
            
            # Process the message
            try:
                message_str = message_bytes.decode('utf-8')
                message = json.loads(message_str)
                self._handle_message(message, peer_id)
            except Exception as e:
                print(f"Error processing message from {peer_id}: {e}")
        
        return buffer
    
    def _process_udp_data(self, data: bytes, peer_id: str, addr: Tuple[str, int]) -> None:
        """
        Process data received over UDP.
        
        Args:
            data: The received data
            peer_id: The ID of the peer that sent the data
            addr: The address (host, port) of the peer
        """
        try:
            message_str = data.decode('utf-8')
            message = json.loads(message_str)
            self._handle_message(message, peer_id)
        except Exception as e:
            print(f"Error processing UDP data from {peer_id}: {e}")
    
    def _handle_message(self, message: Dict[str, Any], peer_id: Optional[str]) -> None:
        """
        Handle a received message by passing it to registered handlers.
        
        Args:
            message: The received message
            peer_id: The ID of the peer that sent the message, or None if unknown
        """
        for handler in self.message_handlers:
            try:
                handler(message, peer_id)
            except Exception as e:
                print(f"Error in message handler: {e}")
    
    def _send_loop(self) -> None:
        """
        Background thread that processes the send queue.
        """
        while self.running:
            try:
                # Get the next message to send (with timeout)
                try:
                    protocol, destination, data = self.send_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Serialize the data
                try:
                    data_str = json.dumps(data)
                    data_bytes = data_str.encode('utf-8')
                    
                    # For TCP, add a newline as message delimiter
                    if protocol == 'tcp':
                        data_bytes += b'\n'
                except Exception as e:
                    print(f"Error serializing message: {e}")
                    continue
                
                # Send the data
                if protocol == 'tcp':
                    self._send_tcp_data(destination, data_bytes)
                elif protocol == 'udp':
                    self._send_udp_data(destination, data_bytes)
                
                # Mark the task as done
                self.send_queue.task_done()
            except Exception as e:
                print(f"Error in send loop: {e}")
    
    def _send_tcp_data(self, peer_id: str, data: bytes) -> bool:
        """
        Send data to a peer over TCP.
        
        Args:
            peer_id: The ID of the peer to send to
            data: The data to send
            
        Returns:
            bool: True if the data was sent successfully, False otherwise
        """
        with self.tcp_lock:
            if peer_id not in self.tcp_connections:
                return False
                
            sock = self.tcp_connections[peer_id]
        
        try:
            sock.sendall(data)
            return True
        except Exception as e:
            print(f"Error sending TCP data to {peer_id}: {e}")
            # Close the connection on error
            self.disconnect(peer_id)
            return False
    
    def _send_udp_data(self, addr: Tuple[str, int], data: bytes) -> bool:
        """
        Send data to a peer over UDP.
        
        Args:
            addr: The address (host, port) of the peer
            data: The data to send
            
        Returns:
            bool: True if the data was sent successfully, False otherwise
        """
        if not self.udp_socket:
            return False
            
        try:
            self.udp_socket.sendto(data, addr)
            return True
        except Exception as e:
            print(f"Error sending UDP data to {addr}: {e}")
            return False
    
    def get_connected_peers(self) -> List[str]:
        """
        Get a list of connected peer IDs.
        
        Returns:
            List[str]: A list of connected peer IDs
        """
        with self.tcp_lock:
            return list(self.tcp_connections.keys())
    
    def is_connected(self, peer_id: str) -> bool:
        """
        Check if we're connected to a peer.
        
        Args:
            peer_id: The ID of the peer to check
            
        Returns:
            bool: True if connected, False otherwise
        """
        with self.tcp_lock:
            return peer_id in self.tcp_connections
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the transport layer.
        
        Returns:
            Dict[str, Any]: A dictionary of transport layer statistics
        """
        with self.tcp_lock:
            tcp_connections = len(self.tcp_connections)
        
        return {
            'tcp_connections': tcp_connections,
            'send_queue_size': self.send_queue.qsize(),
            'running': self.running
        }