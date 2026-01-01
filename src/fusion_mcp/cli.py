"""CLI entry points for Fusion MCP.

Provides commands for installing the Fusion 360 add-in and starting the MCP server.
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_fusion_addins_path() -> Path:
    """Get the Fusion 360 add-ins directory path for the current platform.

    Returns:
        Path: Platform-specific path to Fusion add-ins directory
            - macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns
            - Windows: %APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns

    Raises:
        RuntimeError: If platform is not supported (not macOS or Windows)
    """
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"
    elif sys.platform == "win32":
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"
    else:
        raise RuntimeError(
            f"Unsupported platform: {sys.platform}. "
            "Only macOS (darwin) and Windows (win32) are supported."
        )


def get_source_path() -> Path:
    """Get the path to the FusionMCPBridge source directory.

    Returns:
        Path: Path to FusionMCPBridge directory in the project root.

    Raises:
        RuntimeError: If FusionMCPBridge directory is not found.
    """
    # Try to find FusionMCPBridge relative to this file's location
    cli_path = Path(__file__).resolve()
    project_root = cli_path.parent.parent.parent  # src/fusion_mcp/cli.py -> project root
    source_path = project_root / "FusionMCPBridge"

    if not source_path.exists():
        raise RuntimeError(
            f"FusionMCPBridge directory not found at {source_path}. "
            "Make sure you're running from the project root."
        )

    return source_path


def install_plugin() -> None:
    """Install the Fusion 360 MCP add-in.

    CLI Arguments:
        --dev: Create symlink instead of copying (for development)

    Behavior:
        - Determines target path based on platform (macOS/Windows)
        - In normal mode: copies FusionMCPBridge to target
        - In dev mode: creates symlink to FusionMCPBridge
        - Creates target directory if it doesn't exist
        - Handles existing symlinks/directories appropriately

    Exit Codes:
        0: Success
        1: Error (directory exists in dev mode, copy failed, etc.)
    """
    parser = argparse.ArgumentParser(
        description="Install the Fusion 360 MCP add-in"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Create symlink instead of copying (for development)"
    )
    args = parser.parse_args()

    try:
        source_path = get_source_path()
        addins_path = get_fusion_addins_path()
        target_path = addins_path / "FusionMCPBridge"

        # Create parent directories if they don't exist
        addins_path.mkdir(parents=True, exist_ok=True)

        if args.dev:
            _install_symlink(source_path, target_path)
        else:
            _install_copy(source_path, target_path)

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Installation failed: {e}", file=sys.stderr)
        sys.exit(1)


def _install_copy(source_path: Path, target_path: Path) -> None:
    """Copy the add-in to the target directory.

    Args:
        source_path: Path to the FusionMCPBridge source directory.
        target_path: Path where the add-in should be installed.
    """
    # Remove existing installation if present
    if target_path.exists():
        if target_path.is_symlink():
            target_path.unlink()
        else:
            shutil.rmtree(target_path)

    # Copy the add-in
    shutil.copytree(source_path, target_path)
    print(f"Fusion MCP add-in installed successfully to: {target_path}")


def _install_symlink(source_path: Path, target_path: Path) -> None:
    """Create a symlink to the add-in for development.

    Args:
        source_path: Path to the FusionMCPBridge source directory.
        target_path: Path where the symlink should be created.

    Raises:
        RuntimeError: If a regular directory exists at the target path.
    """
    if target_path.exists():
        if target_path.is_symlink():
            # Remove existing symlink
            target_path.unlink()
            print(f"Removed existing symlink at: {target_path}")
        else:
            # Regular directory exists - warn and exit
            raise RuntimeError(
                f"A regular directory already exists at {target_path}. "
                "Please remove it manually before installing in development mode."
            )

    # Create symlink
    target_path.symlink_to(source_path.resolve())
    print(f"Development mode: Symlink created at {target_path}")
    print(f"  -> {source_path.resolve()}")
    print("Changes to FusionMCPBridge will be immediately available in Fusion 360.")


def start_server() -> None:
    """Start the MCP server.

    Behavior:
        - Imports and runs the FastMCP server
        - Uses stdio transport by default (for MCP clients like Claude, Kiro)
        - Use --sse flag for HTTP/SSE transport on http://127.0.0.1:8000/sse
        - Blocks until interrupted (Ctrl+C)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the Fusion MCP server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE (HTTP) transport instead of stdio"
    )
    args = parser.parse_args()
    
    try:
        from fusion_mcp.server import mcp
        if args.sse:
            mcp.run(transport="sse")
        else:
            mcp.run(transport="stdio")
    except ImportError as e:
        print(f"Error: Could not import server module: {e}", file=sys.stderr)
        print("Make sure the server module is properly installed.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
