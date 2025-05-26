# Blockchain Gossip Network

A decentralized peer-to-peer network that implements a simplified blockchain using a custom gossip protocol over TCP/UDP.

## Overview

The Blockchain Gossip Network is a distributed system where nodes communicate using a custom gossip protocol to propagate transactions and blocks across the network. Each node maintains its own copy of the blockchain and participates in the consensus process through Proof-of-Work mining.

## Features

- **Custom Gossip Protocol**: Efficient message propagation across the network
- **Peer Discovery**: Automatic discovery and management of network peers
- **Transaction Creation and Validation**: Create, sign, and validate transactions
- **Blockchain Implementation**: Maintain a chain of blocks with Proof-of-Work consensus
- **Network Visualization**: Real-time visualization of the network topology and blockchain state
- **Multi-Node Support**: Run multiple nodes to simulate a real network

## Project Structure

```
Blockchain Gossip Network/
├── src/
│   ├── blockchain/         # Blockchain implementation
│   │   ├── block.py        # Block structure and validation
│   │   ├── chain.py        # Blockchain management
│   │   ├── pow.py          # Proof-of-Work implementation
│   │   └── transaction.py  # Transaction structure and validation
│   ├── network/            # Network communication
│   │   ├── gossip.py       # Gossip protocol implementation
│   │   ├── message.py      # Network message structure
│   │   └── transport.py    # TCP/UDP transport layer
│   ├── node/               # Node implementation
│   │   ├── config.py       # Node configuration
│   │   ├── node.py         # Main node class
│   │   └── peer_manager.py # Peer discovery and management
│   ├── utils/              # Utility functions
│   │   ├── crypto.py       # Cryptographic utilities
│   │   └── logger.py       # Logging utilities
│   ├── visualization/      # Visualization tools
│   │   ├── blockchain_visualizer.py  # Blockchain visualization
│   │   └── network_visualizer.py     # Network visualization
│   └── main.py             # Main entry point
├── tests/                  # Test suite
│   └── test_basic.py       # Basic functionality tests
├── data/                   # Data storage (created at runtime)
├── requirements.txt        # Project dependencies
├── run_node.py             # Script to run a single node
├── run_network.py          # Script to run multiple nodes
├── README.md               # Project documentation
└── project_proposal.md     # Project proposal
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/jimmyu2foru18/blockchain-gossip-network.git
cd blockchain-gossip-network
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running a Single Node

To start a single node with default settings:

```bash
python run_node.py
```

This will start a node on localhost:5000 and open the visualization interfaces in your web browser.

You can customize the node with command-line arguments:

```bash
python run_node.py --host localhost --port 5001 --difficulty 3 --data-dir ./data/node1
```

### Running a Network of Nodes

To simulate a network with multiple nodes:

```bash
python run_network.py --nodes 3 --base-port 5000 --vis-base-port 8080
```

This will start 3 nodes on ports 5000, 5001, and 5002, with visualization servers on ports 8080/8081, 8082/8083, and 8084/8085 respectively.

### Visualization

The project includes two visualization interfaces:

1. **Network Visualization** (default: http://localhost:8080): Shows the network topology, node status, and message propagation.

2. **Blockchain Visualization** (default: http://localhost:8081): Shows the blockchain structure, blocks, and transactions.

## Testing

To run the test suite:

```bash
python -m unittest discover tests
```

Or run a specific test:

```bash
python -m unittest tests.test_basic
```

## Implementation Details

### Gossip Protocol

The gossip protocol works by having each node periodically share information with a random subset of its peers. This creates an epidemic-like spread of information across the network, ensuring that all nodes eventually receive all messages.

Key features of the gossip protocol implementation:

- **Message Deduplication**: Nodes track which messages they've seen to avoid processing duplicates
- **Anti-Entropy**: Periodic synchronization to ensure all nodes have the same data
- **Peer Health Monitoring**: Nodes monitor their peers and remove unresponsive ones

### Blockchain Implementation

The blockchain implementation includes:

- **Block Structure**: Each block contains a header (previous hash, timestamp, nonce, etc.) and a list of transactions
- **Proof-of-Work**: Miners must find a hash with a certain number of leading zeros
- **Difficulty Adjustment**: The mining difficulty adjusts based on the block generation rate
- **Transaction Validation**: Transactions are validated before being added to blocks

### Network Transport

The network transport layer supports both TCP and UDP:

- **TCP**: Used for reliable communication of transactions and blocks
- **UDP**: Used for peer discovery and network health checks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request