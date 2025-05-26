import time
import threading
import json
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import os
import webbrowser

class NetworkVisualizer:
    """
    Visualizes the blockchain gossip network using a web interface.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        """
        Initialize the network visualizer.
        
        Args:
            host: The host to run the visualization server on
            port: The port to run the visualization server on
        """
        self.host = host
        self.port = port
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, str]] = []
        self.transactions: List[Dict[str, Any]] = []
        self.blocks: List[Dict[str, Any]] = []
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self) -> None:
        """
        Start the visualization server.
        """
        if self.running:
            print("Visualization server is already running")
            return
        
        # Create a custom HTTP request handler
        visualizer = self
        
        class VisualizerHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(self._get_html().encode())
                elif self.path == '/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    data = {
                        'nodes': list(visualizer.nodes.values()),
                        'connections': visualizer.connections,
                        'transactions': visualizer.transactions,
                        'blocks': visualizer.blocks
                    }
                    self.wfile.write(json.dumps(data).encode())
                elif self.path.startswith('/static/'):
                    # Serve static files (CSS, JS)
                    file_path = os.path.join(os.path.dirname(__file__), 'static', self.path[8:])
                    if os.path.exists(file_path):
                        self.send_response(200)
                        if file_path.endswith('.css'):
                            self.send_header('Content-type', 'text/css')
                        elif file_path.endswith('.js'):
                            self.send_header('Content-type', 'application/javascript')
                        self.end_headers()
                        with open(file_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def _get_html(self):
                # Return the HTML for the visualization
                return '''
<!DOCTYPE html>
<html>
<head>
    <title>Blockchain Gossip Network Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .network-container {
            flex: 2;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            margin: 20px;
            border-radius: 5px;
            overflow: hidden;
        }
        .info-container {
            flex: 1;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            margin: 20px;
            border-radius: 5px;
            overflow-y: auto;
        }
        h1, h2 {
            color: #333;
        }
        .node {
            fill: #69b3a2;
            stroke: #fff;
            stroke-width: 2px;
        }
        .node.active {
            fill: #28a745;
        }
        .node.inactive {
            fill: #dc3545;
        }
        .link {
            stroke: #999;
            stroke-opacity: 0.6;
        }
        .node-label {
            font-size: 12px;
            text-anchor: middle;
        }
        .transaction {
            background-color: #f8f9fa;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #17a2b8;
        }
        .block {
            background-color: #f8f9fa;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background-color: #f8f9fa;
            cursor: pointer;
            border: 1px solid #dee2e6;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background-color: white;
            border-bottom: 2px solid white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="network-container">
            <h1>Network Visualization</h1>
            <svg id="network" width="100%" height="500"></svg>
        </div>
        <div class="info-container">
            <h1>Network Information</h1>
            <div class="tabs">
                <div class="tab active" data-tab="nodes">Nodes</div>
                <div class="tab" data-tab="transactions">Transactions</div>
                <div class="tab" data-tab="blocks">Blocks</div>
            </div>
            <div class="tab-content active" id="nodes-content">
                <h2>Nodes</h2>
                <div id="nodes-list"></div>
            </div>
            <div class="tab-content" id="transactions-content">
                <h2>Recent Transactions</h2>
                <div id="transactions-list"></div>
            </div>
            <div class="tab-content" id="blocks-content">
                <h2>Blockchain</h2>
                <div id="blocks-list"></div>
            </div>
        </div>
    </div>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Function to fetch data from the server
        async function fetchData() {
            const response = await fetch('/data');
            return await response.json();
        }

        // Function to update the visualization
        async function updateVisualization() {
            const data = await fetchData();
            
            // Update network graph
            updateNetworkGraph(data.nodes, data.connections);
            
            // Update nodes list
            updateNodesList(data.nodes);
            
            // Update transactions list
            updateTransactionsList(data.transactions);
            
            // Update blocks list
            updateBlocksList(data.blocks);
            
            // Schedule the next update
            setTimeout(updateVisualization, 2000);
        }

        // Function to update the network graph
        function updateNetworkGraph(nodes, connections) {
            const svg = d3.select('#network');
            const width = svg.node().getBoundingClientRect().width;
            const height = svg.node().getBoundingClientRect().height;
            
            svg.selectAll('*').remove();
            
            const simulation = d3.forceSimulation(nodes)
                .force('link', d3.forceLink(connections).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append('g')
                .selectAll('line')
                .data(connections)
                .enter().append('line')
                .attr('class', 'link');
            
            const node = svg.append('g')
                .selectAll('circle')
                .data(nodes)
                .enter().append('circle')
                .attr('class', d => `node ${d.status}`)
                .attr('r', 10)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            const label = svg.append('g')
                .selectAll('text')
                .data(nodes)
                .enter().append('text')
                .attr('class', 'node-label')
                .attr('dy', '0.35em')
                .text(d => d.id.substring(0, 8));
            
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y + 20);
            });
            
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        }

        // Function to update the nodes list
        function updateNodesList(nodes) {
            const nodesList = document.getElementById('nodes-list');
            nodesList.innerHTML = '';
            
            nodes.forEach(node => {
                const nodeElement = document.createElement('div');
                nodeElement.className = 'node-info';
                nodeElement.innerHTML = `
                    <h3>Node ${node.id.substring(0, 8)}</h3>
                    <p>Status: ${node.status}</p>
                    <p>Peers: ${node.peers}</p>
                    <p>Transactions: ${node.transactions}</p>
                    <p>Blocks: ${node.blocks}</p>
                `;
                nodesList.appendChild(nodeElement);
            });
        }

        // Function to update the transactions list
        function updateTransactionsList(transactions) {
            const transactionsList = document.getElementById('transactions-list');
            transactionsList.innerHTML = '';
            
            transactions.forEach(tx => {
                const txElement = document.createElement('div');
                txElement.className = 'transaction';
                txElement.innerHTML = `
                    <h3>Transaction ${tx.id.substring(0, 8)}</h3>
                    <p>From: ${tx.from.substring(0, 8)}</p>
                    <p>To: ${tx.to.substring(0, 8)}</p>
                    <p>Amount: ${tx.amount}</p>
                    <p>Time: ${new Date(tx.timestamp * 1000).toLocaleString()}</p>
                `;
                transactionsList.appendChild(txElement);
            });
        }

        // Function to update the blocks list
        function updateBlocksList(blocks) {
            const blocksList = document.getElementById('blocks-list');
            blocksList.innerHTML = '';
            
            blocks.forEach(block => {
                const blockElement = document.createElement('div');
                blockElement.className = 'block';
                blockElement.innerHTML = `
                    <h3>Block ${block.index}</h3>
                    <p>Hash: ${block.hash.substring(0, 16)}...</p>
                    <p>Previous Hash: ${block.previous_hash.substring(0, 16)}...</p>
                    <p>Transactions: ${block.transactions}</p>
                    <p>Time: ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                `;
                blocksList.appendChild(blockElement);
            });
        }

        // Tab switching functionality
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and tab contents
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                document.getElementById(`${tab.dataset.tab}-content`).classList.add('active');
            });
        });

        // Start the visualization update loop
        updateVisualization();
    </script>
</body>
</html>
'''
        
        # Create and start the server
        self.server = socketserver.TCPServer((self.host, self.port), VisualizerHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True
        
        print(f"Visualization server started at http://{self.host}:{self.port}")
    
    def stop(self) -> None:
        """
        Stop the visualization server.
        """
        if not self.running:
            print("Visualization server is not running")
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("Visualization server stopped")
    
    def add_node(self, node_id: str, status: str = 'active', peers: int = 0, transactions: int = 0, blocks: int = 0) -> None:
        """
        Add a node to the visualization.
        
        Args:
            node_id: The ID of the node
            status: The status of the node ('active' or 'inactive')
            peers: The number of peers the node has
            transactions: The number of transactions the node has
            blocks: The number of blocks the node has
        """
        self.nodes[node_id] = {
            'id': node_id,
            'status': status,
            'peers': peers,
            'transactions': transactions,
            'blocks': blocks
        }
    
    def update_node(self, node_id: str, status: Optional[str] = None, peers: Optional[int] = None, 
                   transactions: Optional[int] = None, blocks: Optional[int] = None) -> None:
        """
        Update a node in the visualization.
        
        Args:
            node_id: The ID of the node
            status: The status of the node ('active' or 'inactive')
            peers: The number of peers the node has
            transactions: The number of transactions the node has
            blocks: The number of blocks the node has
        """
        if node_id not in self.nodes:
            self.add_node(node_id)
        
        if status is not None:
            self.nodes[node_id]['status'] = status
        
        if peers is not None:
            self.nodes[node_id]['peers'] = peers
        
        if transactions is not None:
            self.nodes[node_id]['transactions'] = transactions
        
        if blocks is not None:
            self.nodes[node_id]['blocks'] = blocks
    
    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the visualization.
        
        Args:
            node_id: The ID of the node
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            
            # Remove any connections involving this node
            self.connections = [c for c in self.connections if c['source'] != node_id and c['target'] != node_id]
    
    def add_connection(self, source_id: str, target_id: str) -> None:
        """
        Add a connection between two nodes.
        
        Args:
            source_id: The ID of the source node
            target_id: The ID of the target node
        """
        # Make sure both nodes exist
        if source_id not in self.nodes:
            self.add_node(source_id)
        
        if target_id not in self.nodes:
            self.add_node(target_id)
        
        # Add the connection if it doesn't already exist
        connection = {'source': source_id, 'target': target_id}
        if connection not in self.connections:
            self.connections.append(connection)
    
    def remove_connection(self, source_id: str, target_id: str) -> None:
        """
        Remove a connection between two nodes.
        
        Args:
            source_id: The ID of the source node
            target_id: The ID of the target node
        """
        self.connections = [c for c in self.connections if not (c['source'] == source_id and c['target'] == target_id)]
    
    def add_transaction(self, tx_id: str, from_addr: str, to_addr: str, amount: float, timestamp: Optional[float] = None) -> None:
        """
        Add a transaction to the visualization.
        
        Args:
            tx_id: The ID of the transaction
            from_addr: The address of the sender
            to_addr: The address of the recipient
            amount: The amount of the transaction
            timestamp: The timestamp of the transaction (default: current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.transactions.append({
            'id': tx_id,
            'from': from_addr,
            'to': to_addr,
            'amount': amount,
            'timestamp': timestamp
        })
        
        # Keep only the 10 most recent transactions
        if len(self.transactions) > 10:
            self.transactions = self.transactions[-10:]
    
    def add_block(self, index: int, hash_val: str, prev_hash: str, transactions: int, timestamp: Optional[float] = None) -> None:
        """
        Add a block to the visualization.
        
        Args:
            index: The index of the block
            hash_val: The hash of the block
            prev_hash: The hash of the previous block
            transactions: The number of transactions in the block
            timestamp: The timestamp of the block (default: current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.blocks.append({
            'index': index,
            'hash': hash_val,
            'previous_hash': prev_hash,
            'transactions': transactions,
            'timestamp': timestamp
        })
        
        # Keep only the 10 most recent blocks
        if len(self.blocks) > 10:
            self.blocks = self.blocks[-10:]
    
    def open_in_browser(self) -> None:
        """
        Open the visualization in a web browser.
        """
        if not self.running:
            print("Visualization server is not running")
            return
        
        url = f"http://{self.host}:{self.port}"
        webbrowser.open(url)
        print(f"Opening visualization in browser: {url}")


# Example usage
def main():
    # Create a visualizer
    visualizer = NetworkVisualizer()
    
    # Start the visualization server
    visualizer.start()
    
    # Add some nodes
    visualizer.add_node('node1', 'active', 3, 5, 2)
    visualizer.add_node('node2', 'active', 2, 3, 2)
    visualizer.add_node('node3', 'inactive', 1, 0, 1)
    
    # Add some connections
    visualizer.add_connection('node1', 'node2')
    visualizer.add_connection('node1', 'node3')
    
    # Add some transactions
    visualizer.add_transaction('tx1', 'addr1', 'addr2', 10.5)
    visualizer.add_transaction('tx2', 'addr2', 'addr3', 5.2)
    
    # Add some blocks
    visualizer.add_block(1, 'hash1', 'genesis', 2)
    visualizer.add_block(2, 'hash2', 'hash1', 1)
    
    # Open the visualization in a browser
    visualizer.open_in_browser()
    
    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        visualizer.stop()


if __name__ == '__main__':
    main()