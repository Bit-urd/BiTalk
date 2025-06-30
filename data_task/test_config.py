#!/usr/bin/env python3
"""
Simple test script to verify the configuration system works
"""

import os
import sys
from datetime import datetime

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import config, logger
    print("✓ Config module loaded successfully")
    print(f"✓ Data directory: {config.paths.data_dir}")
    print(f"✓ Content directory: {config.paths.content_dir}")
    print(f"✓ Log directory: {config.paths.log_dir}")
    print(f"✓ Debug mode: {config.debug}")
    print(f"✓ Logger initialized: {logger.name}")
    
    # Test logger
    logger.info("Test log message from config verification")
    print("✓ Logger working correctly")
    
except Exception as e:
    print(f"✗ Error loading config: {e}")
    sys.exit(1)

print("\nConfiguration system test completed successfully!")