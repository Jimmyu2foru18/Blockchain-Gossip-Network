import os
import sys
import unittest
import time
import threading

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.node.node import Node
from src.node.config import NodeConfig
from src.blockchain.transaction import Transaction
from src.blockchain.block import Block
from src.utils.crypto import generate_wallet


class TestBasicFunctionality(unittest.TestCase):
    """
    Test basic functionality of the blockchain gossip network.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        # Create a test data directory
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create node configurations
        self.config1 = NodeConfig()
        self.config1.set('network.host', 'localhost')
        self.config1.set('network.port', 5001)
        self.config1.set('network.node_id', 'node1')
        self.config1.set('blockchain.data_dir', os.path.join(self.test_data_dir, 'node1'))
        self.config1.set('visualization.enabled', False)
        
        self.config2 = NodeConfig()
        self.config2.set('network.host', 'localhost')
        self.config2.set('network.port', 5002)
        self.config2.set('network.node_id', 'node2')
        self.config2.set('network.initial_peers', [{'host': 'localhost', 'port': 5001}])
        self.config2.set('blockchain.data_dir', os.path.join(self.test_data_dir, 'node2'))
        self.config2.set('visualization.enabled', False)
        
        # Create nodes
        self.node1 = Node(self.config1)
        self.node2 = Node(self.config2)
        
        # Create test wallets
        self.wallet1 = generate_wallet()
        self.wallet2 = generate_wallet()
    
    def tearDown(self):
        """
        Clean up after the test.
        """
        # Stop the nodes
        if hasattr(self, 'node1') and self.node1:
            self.node1.stop()
        
        if hasattr(self, 'node2') and self.node2:
            self.node2.stop()
        
        # Remove the test data directory
        # Commented out for debugging purposes
        # import shutil
        # if os.path.exists(self.test_data_dir):
        #     shutil.rmtree(self.test_data_dir)
    
    def test_node_startup(self):
        """
        Test that nodes can start up and connect to each other.
        """
        # Start the nodes
        self.node1.start()
        self.node2.start()
        
        # Wait for the nodes to connect
        time.sleep(2)
        
        # Check that the nodes are connected
        node1_status = self.node1.get_status()
        node2_status = self.node2.get_status()
        
        self.assertTrue(node1_status['is_running'])
        self.assertTrue(node2_status['is_running'])
        
        # Node 2 should have Node 1 as a peer
        node2_peers = [peer['id'] for peer in node2_status['peers']]
        self.assertIn('node1', node2_peers)
    
    def test_transaction_creation(self):
        """
        Test that transactions can be created and added to the pending transactions.
        """
        # Start the first node
        self.node1.start()
        
        # Create a transaction
        tx = self.node1.create_transaction(
            sender=self.wallet1['address'],
            recipient=self.wallet2['address'],
            amount=10.0,
            private_key=self.wallet1['private_key']
        )
        
        # Check that the transaction was created
        self.assertIsNotNone(tx)
        self.assertEqual(tx['from'], self.wallet1['address'])
        self.assertEqual(tx['to'], self.wallet2['address'])
        self.assertEqual(tx['amount'], 10.0)
        
        # Check that the transaction was added to the pending transactions
        node1_status = self.node1.get_status()
        pending_tx_ids = [tx['id'] for tx in node1_status['pending_transactions']]
        self.assertIn(tx['id'], pending_tx_ids)
    
    def test_transaction_propagation(self):
        """
        Test that transactions are propagated between nodes.
        """
        # Start the nodes
        self.node1.start()
        self.node2.start()
        
        # Wait for the nodes to connect
        time.sleep(2)
        
        # Create a transaction on node 1
        tx = self.node1.create_transaction(
            sender=self.wallet1['address'],
            recipient=self.wallet2['address'],
            amount=10.0,
            private_key=self.wallet1['private_key']
        )
        
        # Wait for the transaction to propagate
        time.sleep(2)
        
        # Check that the transaction was propagated to node 2
        node2_status = self.node2.get_status()
        pending_tx_ids = [tx['id'] for tx in node2_status['pending_transactions']]
        self.assertIn(tx['id'], pending_tx_ids)
    
    def test_block_mining(self):
        """
        Test that blocks can be mined.
        """
        # Start the first node
        self.node1.start()
        
        # Create a transaction
        tx = self.node1.create_transaction(
            sender=self.wallet1['address'],
            recipient=self.wallet2['address'],
            amount=10.0,
            private_key=self.wallet1['private_key']
        )
        
        # Mine a block
        block = self.node1.mine_block()
        
        # Check that the block was mined
        self.assertIsNotNone(block)
        self.assertEqual(block['index'], 1)  # Index 0 is the genesis block
        
        # Check that the transaction was included in the block
        self.assertEqual(len(block['transactions']), 1)
        self.assertEqual(block['transactions'][0]['id'], tx['id'])
        
        # Check that the pending transactions were cleared
        node1_status = self.node1.get_status()
        self.assertEqual(len(node1_status['pending_transactions']), 0)
        
        # Check that the block was added to the blockchain
        self.assertEqual(node1_status['blockchain']['length'], 2)  # Genesis block + new block
    
    def test_block_propagation(self):
        """
        Test that blocks are propagated between nodes.
        """
        # Start the nodes
        self.node1.start()
        self.node2.start()
        
        # Wait for the nodes to connect
        time.sleep(2)
        
        # Create a transaction on node 1
        tx = self.node1.create_transaction(
            sender=self.wallet1['address'],
            recipient=self.wallet2['address'],
            amount=10.0,
            private_key=self.wallet1['private_key']
        )
        
        # Mine a block on node 1
        block = self.node1.mine_block()
        
        # Wait for the block to propagate
        time.sleep(2)
        
        # Check that the block was propagated to node 2
        node2_status = self.node2.get_status()
        self.assertEqual(node2_status['blockchain']['length'], 2)  # Genesis block + new block
        
        # Check that the transaction was included in the block on node 2
        self.assertEqual(len(node2_status['blockchain']['blocks'][1]['transactions']), 1)
        self.assertEqual(node2_status['blockchain']['blocks'][1]['transactions'][0]['id'], tx['id'])


if __name__ == '__main__':
    unittest.main()