import argparse
import os
import sys
import time
import threading
import json
from typing import Dict, Any, Optional, List

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.node.node import Node
from src.node.config import NodeConfig
from src.utils.logger import get_logger
from src.visualization.network_visualizer import NetworkVisualizer
from src.visualization.blockchain_visualizer import BlockchainVisualizer

# Set up logger
logger = get_logger('main')

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Blockchain Gossip Network')
    
    # Node configuration
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host to bind the node to')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to bind the node to')
    parser.add_argument('--node-id', type=str,
                        help='Unique ID for this node (default: auto-generated)')
    parser.add_argument('--peers', type=str, nargs='*',
                        help='Initial peers to connect to (format: host:port)')
    
    # Blockchain configuration
    parser.add_argument('--difficulty', type=int, default=4,
                        help='Initial mining difficulty')
    parser.add_argument('--block-time', type=int, default=60,
                        help='Target block time in seconds')
    
    # Visualization configuration
    parser.add_argument('--vis-host', type=str, default='localhost',
                        help='Host to bind the visualization server to')
    parser.add_argument('--vis-port', type=int, default=8080,
                        help='Port to bind the network visualization server to')
    parser.add_argument('--blockchain-vis-port', type=int, default=8081,
                        help='Port to bind the blockchain visualization server to')
    parser.add_argument('--no-visualization', action='store_true',
                        help='Disable visualization')
    
    # Other options
    parser.add_argument('--data-dir', type=str, default='./data',
                        help='Directory to store blockchain data')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    return parser.parse_args()

def create_node_config(args) -> NodeConfig:
    """
    Create a node configuration from command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        NodeConfig: The node configuration
    """
    # Create the data directory if it doesn't exist
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Parse peers
    peers = []
    if args.peers:
        for peer in args.peers:
            parts = peer.split(':')
            if len(parts) == 2:
                peers.append({
                    'host': parts[0],
                    'port': int(parts[1])
                })
    
    # Create the configuration
    config = NodeConfig()
    
    # Network configuration
    config.set('network.host', args.host)
    config.set('network.port', args.port)
    config.set('network.node_id', args.node_id)
    config.set('network.initial_peers', peers)
    
    # Blockchain configuration
    config.set('blockchain.difficulty', args.difficulty)
    config.set('blockchain.target_block_time', args.block_time)
    config.set('blockchain.data_dir', args.data_dir)
    
    # Visualization configuration
    config.set('visualization.enabled', not args.no_visualization)
    config.set('visualization.host', args.vis_host)
    config.set('visualization.network_port', args.vis_port)
    config.set('visualization.blockchain_port', args.blockchain_vis_port)
    
    # Logging configuration
    config.set('logging.level', args.log_level)
    config.set('logging.file', os.path.join(args.data_dir, 'node.log'))
    
    return config

def update_visualization(node: Node, network_vis: NetworkVisualizer, blockchain_vis: BlockchainVisualizer) -> None:
    """
    Update the visualization with the latest node state.
    
    Args:
        node: The node to visualize
        network_vis: The network visualizer
        blockchain_vis: The blockchain visualizer
    """
    while True:
        try:
            # Get node status
            status = node.get_status()
            
            # Update network visualization
            network_vis.update_node(
                node_id=status['node_id'],
                status='active' if status['running'] else 'inactive',
                peers=status['peers'],
                transactions=status['transactions_pending'],
                blocks=0  # Placeholder until blockchain is implemented
            )
            
            # Peer connections will be added when peer management is implemented
            # Currently peers count is returned, not the peer list
            
            # Update blockchain visualization with pending transactions
            # Blocks will be added when blockchain is implemented
            # Create a list of pending transactions for visualization
            # Currently we only have the count, so we'll create placeholder transactions
            pending_transactions = [
                {'id': f'pending_{i}', 'status': 'pending'}
                for i in range(status['transactions_pending'])
            ]
            blockchain_vis.update_from_blockchain(
                blocks=[],
                transactions=pending_transactions
            )
            
            # Sleep for a bit
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error updating visualization: {e}")
            time.sleep(5)

def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Create node configuration
    config = create_node_config(args)
    
    # Create and start the node
    node = Node(config)
    node.start()
    
    # Create and start the visualizers if enabled
    if config.get('visualization.enabled'):
        network_vis = NetworkVisualizer(
            host=config.get('visualization.host'),
            port=config.get('visualization.network_port')
        )
        network_vis.start()
        
        blockchain_vis = BlockchainVisualizer(
            host=config.get('visualization.host'),
            port=config.get('visualization.blockchain_port')
        )
        blockchain_vis.start()
        
        # Start a thread to update the visualization
        vis_thread = threading.Thread(
            target=update_visualization,
            args=(node, network_vis, blockchain_vis),
            daemon=True
        )
        vis_thread.start()
        
        # Open the visualizers in the browser
        network_vis.open_in_browser()
        blockchain_vis.open_in_browser()
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        node.stop()
        
        if config.get('visualization.enabled'):
            network_vis.stop()
            blockchain_vis.stop()


if __name__ == '__main__':
    main()