#!/usr/bin/env python3

import os
import sys
import argparse

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main module
from src.main import main

if __name__ == '__main__':
    # Run the main function
    main()