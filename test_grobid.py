#!/usr/bin/env python3
"""
Test script for GROBID integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from grobid_manager import grobid_manager
import logging

logging.basicConfig(level=logging.INFO)

def test_grobid_manager():
    """Test GROBID manager functionality"""
    print("Testing GROBID Manager...")

    # Test server status
    print(f"Server running: {grobid_manager.is_server_running()}")

    # Test server start (this will take time)
    print("Attempting to start GROBID server...")
    success = grobid_manager.start_server()
    print(f"Server start result: {success}")

    if success:
        print(f"Server running after start: {grobid_manager.is_server_running()}")

        # Test server stop
        print("Stopping GROBID server...")
        stop_result = grobid_manager.stop_server()
        print(f"Server stop result: {stop_result}")

    print("GROBID Manager test completed")

if __name__ == "__main__":
    test_grobid_manager()