#!/usr/bin/env python3
"""
Create symbolic link for Fusion 360 MCP Add-in for development.
This allows live editing without reinstalling.
"""

import sys
from pathlib import Path

def create_symlink():
    # Source directory (MCP folder in project)
    script_dir = Path(__file__).parent
    source_dir = script_dir / "FusionMCPBridge"
    
    # Target directory (Fusion add-ins folder)
    target_parent = Path.home() / "Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
    target_link = target_parent / "FusionMCPBridge"
    
    # Check if source exists
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return False
    
    # Create target parent directory if needed
    target_parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing link/directory
    if target_link.exists() or target_link.is_symlink():
        if target_link.is_symlink():
            target_link.unlink()
            print(f"Removed existing symlink: {target_link}")
        else:
            print(f"Warning: {target_link} exists and is not a symlink. Please remove manually.")
            return False
    
    # Create symlink
    try:
        target_link.symlink_to(source_dir)
        print(f"Created symlink: {target_link} -> {source_dir}")
        print("Add-in linked successfully for development!")
        return True
    except OSError as e:
        print(f"Error creating symlink: {e}")
        return False

if __name__ == "__main__":
    success = create_symlink()
    sys.exit(0 if success else 1)
