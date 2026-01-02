#!/usr/bin/env python3
"""
Cleanup script for development environment.

This script removes Python bytecode cache files and other temporary files
that can accumulate during development.
"""

import os
import shutil
from pathlib import Path


def cleanup_pycache(root_dir: Path):
    """Remove all __pycache__ directories recursively."""
    removed_count = 0
    
    for pycache_dir in root_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                print(f"Removed: {pycache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"Failed to remove {pycache_dir}: {e}")
    
    return removed_count


def cleanup_pyc_files(root_dir: Path):
    """Remove all .pyc files recursively."""
    removed_count = 0
    
    for pyc_file in root_dir.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"Removed: {pyc_file}")
            removed_count += 1
        except Exception as e:
            print(f"Failed to remove {pyc_file}: {e}")
    
    return removed_count


def main():
    """Main cleanup function."""
    server_dir = Path(__file__).parent
    
    print("Starting cleanup of development files...")
    print(f"Root directory: {server_dir}")
    
    # Skip venv directory to avoid cleaning up installed packages
    exclude_dirs = {"venv"}
    
    total_pycache = 0
    total_pyc = 0
    
    for item in server_dir.iterdir():
        if item.is_dir() and item.name not in exclude_dirs:
            print(f"\nCleaning directory: {item.name}")
            pycache_count = cleanup_pycache(item)
            pyc_count = cleanup_pyc_files(item)
            
            total_pycache += pycache_count
            total_pyc += pyc_count
            
            if pycache_count == 0 and pyc_count == 0:
                print(f"  No files to clean in {item.name}")
    
    print(f"\nCleanup complete!")
    print(f"Removed {total_pycache} __pycache__ directories")
    print(f"Removed {total_pyc} .pyc files")


if __name__ == "__main__":
    main()