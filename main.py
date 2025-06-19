#!/usr/bin/env python3
"""
STPA Tool - Main Entry Point
Systems-Theoretic Process Analysis Tool

This is the main entry point for the STPA Tool application.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the application
if __name__ == "__main__":
    from src.app import main
    main()