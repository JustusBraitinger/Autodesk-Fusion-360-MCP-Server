"""CLI entry points for Fusion MCP.

Provides commands for installing the Fusion 360 add-in and starting the MCP server.
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_fusion_addins_path() -> Path:
    """Get the Fusion 360 add-ins directory path for the current platform."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"
    elif sys.platform == "win32":
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_source_path() -> Path:
    """Get the path to the FusionMCPBridge source directory."""
    cli_path = Path(__file__).resolve()
    project_root = cli_path.parent.parent  # Server/cli.py -> project root
    source_path = project_root / "FusionMCPBridge"

    if not source_path.exists():
        raise RuntimeError(f"FusionMCPBridge directory not found at {source_path}")

    return source_path


def install_plugin() -> None:
    """Install the Fusion 360 MCP add-in."""
    parser = argparse.ArgumentParser(description="Install the Fusion 360 MCP add-in")
    parser.add_argument("--dev", action="store_true", help="Create symlink instead of copying")
    parser.add_argument("--debugger", action="store_true", help="Install debugger add-in instead")
    args = parser.parse_args()

    try:
        if args.debugger:
            _install_debugger(args.dev)
        else:
            _install_main_plugin(args.dev)
    except Exception as e:
        print(f"Installation failed: {e}")
        raise


def _install_main_plugin(dev_mode: bool) -> None:
    """Install the main FusionMCPBridge add-in."""
    source_path = get_source_path()
    addins_path = get_fusion_addins_path()
    target_path = addins_path / "FusionMCPBridge"

    addins_path.mkdir(parents=True, exist_ok=True)

    if dev_mode:
        _install_symlink(source_path, target_path)
    else:
        _install_copy(source_path, target_path)


def _install_debugger(dev_mode: bool) -> None:
    """Install the FusionMCPBridgeDebugger add-in."""
    try:
        source_path = Path(__file__).parent.parent / "FusionMCPBridgeDebugger"
        if not source_path.exists():
            raise RuntimeError(f"FusionMCPBridgeDebugger directory not found at {source_path}")
        
        addins_path = get_fusion_addins_path()
        target_path = addins_path / "FusionMCPBridgeDebugger"

        addins_path.mkdir(parents=True, exist_ok=True)

        if dev_mode:
            _install_symlink(source_path, target_path)
        else:
            _install_copy(source_path, target_path)
        
        print("\nDebugger add-in installed! Available endpoints:")
        print("  GET http://localhost:5002/addon/restart - Restart FusionMCPBridge")
        print("  GET http://localhost:5002/addon/stop    - Stop FusionMCPBridge")
        print("  GET http://localhost:5002/addon/start   - Start FusionMCPBridge")
        print("  GET http://localhost:5002/addon/status  - Get FusionMCPBridge status")

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Installation failed: {e}", file=sys.stderr)
        sys.exit(1)


def _install_copy(source_path: Path, target_path: Path) -> None:
    """Copy the add-in to the target directory."""
    if target_path.exists():
        if target_path.is_symlink():
            target_path.unlink()
        else:
            shutil.rmtree(target_path)

    shutil.copytree(source_path, target_path)
    print(f"Fusion MCP add-in installed successfully to: {target_path}")


def _install_symlink(source_path: Path, target_path: Path) -> None:
    """Create a symlink to the add-in for development."""
    if target_path.exists():
        if target_path.is_symlink():
            target_path.unlink()
            print(f"Removed existing symlink at: {target_path}")
        else:
            raise RuntimeError(f"Directory exists at {target_path}. Remove it manually first.")

    target_path.symlink_to(source_path.resolve())
    print(f"Development mode: Symlink created at {target_path}")
    print(f"  -> {source_path.resolve()}")


def start_server() -> None:
    """Start the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the Fusion MCP server")
    parser.add_argument("--sse", action="store_true", help="Use SSE (HTTP) transport instead of stdio")
    args = parser.parse_args()
    
    try:
        # Import from Server directory
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from MCP_Server import initialize_server
        
        # Initialize the modular server
        mcp = initialize_server()
        
        if args.sse:
            mcp.run(transport="sse")
        else:
            mcp.run(transport="stdio")
    except ImportError as e:
        print(f"Error: Could not import server module: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
