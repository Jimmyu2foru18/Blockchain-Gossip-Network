import os
import json
from typing import Dict, Any, Optional

class NodeConfig:
    """
    Configuration manager for blockchain nodes.
    Handles loading, saving, and accessing node configuration settings.
    """
    
    DEFAULT_CONFIG = {
        # Network settings
        'host': 'localhost',
        'port': 8000,
        'max_peers': 10,
        'heartbeat_interval': 30,  # seconds
        'discovery_interval': 60,  # seconds
        'connection_timeout': 5,   # seconds
        
        # Gossip protocol settings
        'gossip_fanout': 3,        # number of peers to forward messages to
        'gossip_interval': 1,      # seconds between gossip rounds
        'anti_entropy_interval': 300,  # seconds between anti-entropy sync
        
        # Blockchain settings
        'target_block_time': 60,   # seconds
        'initial_difficulty': 4,   # leading zeros for PoW
        'difficulty_adjustment_interval': 10,  # blocks
        'max_transactions_per_block': 100,
        
        # Storage settings
        'data_dir': './data',
        'blockchain_file': 'blockchain.json',
        'peers_file': 'peers.json',
        
        # Logging settings
        'log_level': 'INFO',
        'log_file': 'node.log',
        
        # Visualization settings
        'visualization_enabled': True,
        'visualization_port': 5000
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file, or None to use default settings
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file
        
        if config_file and os.path.exists(config_file):
            self.load(config_file)
    
    def load(self, config_file: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            bool: True if the configuration was loaded successfully, False otherwise
        """
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
                self.config_file = config_file
                return True
        except Exception as e:
            print(f"Error loading configuration from {config_file}: {e}")
            return False
    
    def save(self, config_file: Optional[str] = None) -> bool:
        """
        Save the current configuration to a file.
        
        Args:
            config_file: Path to the configuration file, or None to use the current file
            
        Returns:
            bool: True if the configuration was saved successfully, False otherwise
        """
        config_file = config_file or self.config_file
        if not config_file:
            print("No configuration file specified")
            return False
            
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                return True
        except Exception as e:
            print(f"Error saving configuration to {config_file}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            Any: The configuration value, or the default if not found
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update multiple configuration values at once.
        
        Args:
            config_dict: A dictionary of configuration keys and values
        """
        self.config.update(config_dict)
    
    def reset(self) -> None:
        """Reset the configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access to configuration values."""
        return self.config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-like setting of configuration values."""
        self.config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator to check if a key exists."""
        return key in self.config
    
    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return json.dumps(self.config, indent=4)