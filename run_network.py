#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import signal
import argparse

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Run a Blockchain Gossip Network with multiple nodes')
    parser.add_argument('--nodes', type=int, default=3, help='Number of nodes to run')
    parser.add_argument('--base-port', type=int, default=5000, help='Base port for the nodes')
    parser.add_argument('--vis-base-port', type=int, default=8080, help='Base port for the visualization servers')
    parser.add_argument('--data-dir', type=str, default='./data', help='Directory to store blockchain data')
    parser.add_argument('--difficulty', type=int, default=4, help='Initial mining difficulty')
    
    return parser.parse_args()

def main():
    """
    Run multiple nodes to form a blockchain gossip network.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Create the data directory if it doesn't exist
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Start the nodes
    processes = []
    try:
        for i in range(args.nodes):
            # Calculate ports for this node
            port = args.base_port + i
            vis_port = args.vis_base_port + (i * 2)
            blockchain_vis_port = args.vis_base_port + (i * 2) + 1
            
            # Create the node's data directory
            node_data_dir = os.path.join(args.data_dir, f'node{i}')
            os.makedirs(node_data_dir, exist_ok=True)
            
            # Build the command to run the node
            cmd = [
                sys.executable,
                'run_node.py',
                '--host', 'localhost',
                '--port', str(port),
                '--node-id', f'node{i}',
                '--data-dir', node_data_dir,
                '--vis-host', 'localhost',
                '--vis-port', str(vis_port),
                '--blockchain-vis-port', str(blockchain_vis_port),
                '--difficulty', str(args.difficulty)
            ]
            
            # Add peers for nodes after the first one
            if i > 0:
                # Connect to the first node
                cmd.extend(['--peers', f'localhost:{args.base_port}'])
            
            # Start the node process
            print(f"Starting node {i} on port {port}...")
            process = subprocess.Popen(cmd)
            processes.append(process)
            
            # Wait a bit before starting the next node
            time.sleep(2)
        
        print(f"Started {args.nodes} nodes. Press Ctrl+C to stop.")
        
        # Wait for Ctrl+C
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Stopping nodes...")
    
    finally:
        # Stop all node processes
        for process in processes:
            process.send_signal(signal.SIGINT)
        
        # Wait for all processes to terminate
        for process in processes:
            process.wait()
        
        print("All nodes stopped.")

if __name__ == '__main__':
    main()