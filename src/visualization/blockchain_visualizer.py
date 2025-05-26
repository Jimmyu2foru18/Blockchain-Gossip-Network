import time
import threading
import json
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import os
import webbrowser

class BlockchainVisualizer:
    """
    Visualizes the blockchain using a web interface.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8081):
        """
        Initialize the blockchain visualizer.
        
        Args:
            host: The host to run the visualization server on
            port: The port to run the visualization server on
        """
        self.host = host
        self.port = port
        self.blocks: List[Dict[str, Any]] = []
        self.transactions: List[Dict[str, Any]] = []
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self) -> None:
        """
        Start the visualization server.
        """
        if self.running:
            print("Blockchain visualization server is already running")
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
                        'blocks': visualizer.blocks,
                        'transactions': visualizer.transactions
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
    <title>Blockchain Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .blockchain-container {
            flex: 1;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 5px;
            padding: 20px;
            overflow-x: auto;
        }
        .transactions-container {
            flex: 0.5;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
            overflow-y: auto;
        }
        h1, h2 {
            color: #333;
        }
        .blockchain {
            display: flex;
            flex-direction: row;
            align-items: center;
            min-height: 200px;
        }
        .block {
            width: 200px;
            min-width: 200px;
            height: 180px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 2px solid #dee2e6;
            padding: 10px;
            margin-right: 20px;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .block.genesis {
            background-color: #d1e7dd;
            border-color: #badbcc;
        }
        .block-header {
            font-weight: bold;
            text-align: center;
            padding-bottom: 5px;
            border-bottom: 1px solid #dee2e6;
        }
        .block-content {
            flex: 1;
            padding: 5px 0;
            overflow: hidden;
        }
        .block-footer {
            font-size: 12px;
            text-align: center;
            padding-top: 5px;
            border-top: 1px solid #dee2e6;
        }
        .arrow {
            width: 30px;
            height: 30px;
            position: absolute;
            right: -25px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 1;
            color: #6c757d;
            font-size: 24px;
        }
        .transaction {
            background-color: #f8f9fa;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #17a2b8;
        }
        .transaction-header {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .transaction-content {
            font-size: 14px;
        }
        .hash {
            font-family: monospace;
            word-break: break-all;
        }
        .timestamp {
            font-size: 12px;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Blockchain Visualization</h1>
        </div>
        <div class="blockchain-container">
            <h2>Blockchain</h2>
            <div class="blockchain" id="blockchain"></div>
        </div>
        <div class="transactions-container">
            <h2>Recent Transactions</h2>
            <div id="transactions"></div>
        </div>
    </div>

    <script>
        // Function to fetch data from the server
        async function fetchData() {
            const response = await fetch('/data');
            return await response.json();
        }

        // Function to update the visualization
        async function updateVisualization() {
            const data = await fetchData();
            
            // Update blockchain visualization
            updateBlockchain(data.blocks);
            
            // Update transactions list
            updateTransactions(data.transactions);
            
            // Schedule the next update
            setTimeout(updateVisualization, 2000);
        }

        // Function to update the blockchain visualization
        function updateBlockchain(blocks) {
            const blockchainElement = document.getElementById('blockchain');
            blockchainElement.innerHTML = '';
            
            blocks.forEach((block, index) => {
                const blockElement = document.createElement('div');
                blockElement.className = `block ${index === 0 ? 'genesis' : ''}`;
                
                const blockHeader = document.createElement('div');
                blockHeader.className = 'block-header';
                blockHeader.textContent = `Block #${block.index}`;
                
                const blockContent = document.createElement('div');
                blockContent.className = 'block-content';
                blockContent.innerHTML = `
                    <div><strong>Hash:</strong> <span class="hash">${block.hash.substring(0, 10)}...</span></div>
                    <div><strong>Prev Hash:</strong> <span class="hash">${block.previous_hash.substring(0, 10)}...</span></div>
                    <div><strong>Transactions:</strong> ${block.transactions}</div>
                    <div><strong>Nonce:</strong> ${block.nonce || 'N/A'}</div>
                    <div><strong>Difficulty:</strong> ${block.difficulty || 'N/A'}</div>
                `;
                
                const blockFooter = document.createElement('div');
                blockFooter.className = 'block-footer';
                blockFooter.innerHTML = `<span class="timestamp">${new Date(block.timestamp * 1000).toLocaleString()}</span>`;
                
                blockElement.appendChild(blockHeader);
                blockElement.appendChild(blockContent);
                blockElement.appendChild(blockFooter);
                
                // Add arrow between blocks
                if (index < blocks.length - 1) {
                    const arrow = document.createElement('div');
                    arrow.className = 'arrow';
                    arrow.innerHTML = '→';
                    blockElement.appendChild(arrow);
                }
                
                blockchainElement.appendChild(blockElement);
            });
            
            // If no blocks, show a message
            if (blocks.length === 0) {
                blockchainElement.innerHTML = '<p>No blocks in the blockchain yet.</p>';
            }
        }

        // Function to update the transactions list
        function updateTransactions(transactions) {
            const transactionsElement = document.getElementById('transactions');
            transactionsElement.innerHTML = '';
            
            transactions.forEach(tx => {
                const txElement = document.createElement('div');
                txElement.className = 'transaction';
                
                const txHeader = document.createElement('div');
                txHeader.className = 'transaction-header';
                txHeader.textContent = `Transaction ${tx.id.substring(0, 8)}`;
                
                const txContent = document.createElement('div');
                txContent.className = 'transaction-content';
                txContent.innerHTML = `
                    <div><strong>From:</strong> ${tx.from.substring(0, 16)}...</div>
                    <div><strong>To:</strong> ${tx.to.substring(0, 16)}...</div>
                    <div><strong>Amount:</strong> ${tx.amount}</div>
                    <div><span class="timestamp">${new Date(tx.timestamp * 1000).toLocaleString()}</span></div>
                `;
                
                txElement.appendChild(txHeader);
                txElement.appendChild(txContent);
                transactionsElement.appendChild(txElement);
            });
            
            // If no transactions, show a message
            if (transactions.length === 0) {
                transactionsElement.innerHTML = '<p>No transactions yet.</p>';
            }
        }

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
        
        print(f"Blockchain visualization server started at http://{self.host}:{self.port}")
    
    def stop(self) -> None:
        """
        Stop the visualization server.
        """
        if not self.running:
            print("Blockchain visualization server is not running")
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("Blockchain visualization server stopped")
    
    def add_block(self, block_data: Dict[str, Any]) -> None:
        """
        Add a block to the visualization.
        
        Args:
            block_data: The block data to add
        """
        # Ensure the block has all required fields
        required_fields = ['index', 'hash', 'previous_hash', 'timestamp']
        for field in required_fields:
            if field not in block_data:
                print(f"Block is missing required field: {field}")
                return
        
        # Add the block to the list
        self.blocks.append(block_data)
        
        # Sort blocks by index
        self.blocks.sort(key=lambda b: b['index'])
    
    def add_transaction(self, tx_data: Dict[str, Any]) -> None:
        """
        Add a transaction to the visualization.
        
        Args:
            tx_data: The transaction data to add
        """
        # Ensure the transaction has all required fields
        required_fields = ['id', 'from', 'to', 'amount', 'timestamp']
        for field in required_fields:
            if field not in tx_data:
                print(f"Transaction is missing required field: {field}")
                return
        
        # Add the transaction to the list
        self.transactions.append(tx_data)
        
        # Sort transactions by timestamp (newest first)
        self.transactions.sort(key=lambda tx: tx['timestamp'], reverse=True)
        
        # Keep only the 10 most recent transactions
        if len(self.transactions) > 10:
            self.transactions = self.transactions[:10]
    
    def update_from_blockchain(self, blocks: List[Dict[str, Any]], transactions: List[Dict[str, Any]]) -> None:
        """
        Update the visualization from blockchain data.
        
        Args:
            blocks: The list of blocks
            transactions: The list of transactions
        """
        # Clear existing data
        self.blocks = []
        self.transactions = []
        
        # Add blocks
        for block in blocks:
            self.add_block(block)
        
        # Add transactions
        for tx in transactions:
            self.add_transaction(tx)
    
    def open_in_browser(self) -> None:
        """
        Open the visualization in a web browser.
        """
        if not self.running:
            print("Blockchain visualization server is not running")
            return
        
        url = f"http://{self.host}:{self.port}"
        webbrowser.open(url)
        print(f"Opening blockchain visualization in browser: {url}")


# Example usage
def main():
    # Create a visualizer
    visualizer = BlockchainVisualizer()
    
    # Start the visualization server
    visualizer.start()
    
    # Add some blocks
    visualizer.add_block({
        'index': 0,
        'hash': 'genesis_hash',
        'previous_hash': '0',
        'timestamp': time.time() - 3600,
        'transactions': 0,
        'nonce': 0,
        'difficulty': 1
    })
    
    visualizer.add_block({
        'index': 1,
        'hash': 'block1_hash',
        'previous_hash': 'genesis_hash',
        'timestamp': time.time() - 2400,
        'transactions': 2,
        'nonce': 12345,
        'difficulty': 2
    })
    
    visualizer.add_block({
        'index': 2,
        'hash': 'block2_hash',
        'previous_hash': 'block1_hash',
        'timestamp': time.time() - 1200,
        'transactions': 1,
        'nonce': 67890,
        'difficulty': 2
    })
    
    # Add some transactions
    visualizer.add_transaction({
        'id': 'tx1',
        'from': 'wallet1',
        'to': 'wallet2',
        'amount': 10.5,
        'timestamp': time.time() - 1800
    })
    
    visualizer.add_transaction({
        'id': 'tx2',
        'from': 'wallet2',
        'to': 'wallet3',
        'amount': 5.2,
        'timestamp': time.time() - 900
    })
    
    visualizer.add_transaction({
        'id': 'tx3',
        'from': 'wallet1',
        'to': 'wallet3',
        'amount': 3.7,
        'timestamp': time.time() - 300
    })
    
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