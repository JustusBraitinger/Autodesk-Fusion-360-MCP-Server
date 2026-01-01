# Requirements Document

## Introduction

This document specifies the requirements for modernizing the Fusion MCP project to use industry-standard Python tooling and deployment patterns. The modernization will convert the current manual script-based workflow to a unified uv-based workflow with proper pyproject.toml configuration, utility scripts exposed as CLI commands, and standard MCP client integration using FastMCP's installation capabilities.

## Glossary

- **uv**: A fast Python package manager and project tool that replaces pip, virtualenv, and other tools
- **pyproject.toml**: The standard Python project configuration file (PEP 517/518/621)
- **FastMCP**: The MCP server framework used by this project for exposing tools to AI assistants
- **MCP Client**: An AI assistant application (Claude Desktop, VS Code Copilot, etc.) that connects to MCP servers
- **Fusion Add-In**: The Python plugin that runs inside Autodesk Fusion 360 to execute CAD operations
- **Entry Point**: A CLI command defined in pyproject.toml that can be run after package installation

## Requirements

### Requirement 1

**User Story:** As a developer, I want to set up the project with a single command, so that I can quickly get started without manual dependency management.

#### Acceptance Criteria

1. WHEN a developer runs `uv sync` in the project root THEN the Project_Manager SHALL install all required dependencies including fastmcp, uvicorn, and requests
2. WHEN the project is synced THEN the Project_Manager SHALL create a virtual environment automatically if one does not exist
3. WHEN dependencies are installed THEN the Project_Manager SHALL resolve and lock versions in a uv.lock file for reproducible builds

### Requirement 2

**User Story:** As a developer, I want a proper pyproject.toml configuration, so that the project follows Python packaging standards and can be distributed.

#### Acceptance Criteria

1. THE pyproject.toml SHALL define project metadata including name, version, description, and Python version requirement (>=3.10)
2. THE pyproject.toml SHALL specify all runtime dependencies with version constraints matching current requirements.txt
3. THE pyproject.toml SHALL define CLI entry points for utility scripts (install-fusion-plugin, start-mcp-server)
4. THE pyproject.toml SHALL configure the build system using hatchling or similar modern build backend

### Requirement 3

**User Story:** As a developer, I want a CLI command to install the Fusion add-in, so that I can set up the Fusion integration without running standalone Python scripts.

#### Acceptance Criteria

1. WHEN a developer runs `uv run install-fusion-plugin` THEN the Installer SHALL copy the FusionMCPBridge folder to the Fusion 360 add-ins directory
2. WHEN the installer runs on macOS THEN the Installer SHALL use the path `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`
3. WHEN the installer runs on Windows THEN the Installer SHALL use the path `%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns`
4. WHEN the installation completes successfully THEN the Installer SHALL print a confirmation message with the installation path
5. IF the Fusion add-ins directory does not exist THEN the Installer SHALL create the directory structure before copying

### Requirement 4

**User Story:** As a developer, I want a CLI command to install the Fusion add-in as a symlink for development, so that code changes are immediately available without reinstalling.

#### Acceptance Criteria

1. WHEN a developer runs `uv run install-fusion-plugin --dev` THEN the Installer SHALL create a symbolic link instead of copying files
2. WHEN a symlink already exists at the target location THEN the Installer SHALL remove the existing symlink before creating a new one
3. IF a regular directory exists at the target location THEN the Installer SHALL warn the user and exit without modifying the directory
4. WHEN the symlink is created successfully THEN the Installer SHALL print a message indicating development mode is active

### Requirement 5

**User Story:** As a developer, I want a CLI command to start the MCP server, so that I can run the server without navigating to the Server directory.

#### Acceptance Criteria

1. WHEN a developer runs `uv run start-mcp-server` THEN the Server SHALL start the FastMCP server with SSE transport on port 8000
2. WHEN the server starts THEN the Server SHALL be accessible at `http://127.0.0.1:8000/sse`
3. WHEN the server receives a connection THEN the Server SHALL log connection information to the console

### Requirement 6

**User Story:** As a developer, I want to register the MCP server with Claude Desktop using FastMCP's install command, so that I can use standard MCP tooling for client integration.

#### Acceptance Criteria

1. WHEN a developer runs `uv run fastmcp install Server/MCP_Server.py --name Fusion` THEN the MCP_Installer SHALL add the server configuration to Claude Desktop's config file
2. WHEN the installation succeeds THEN the MCP_Installer SHALL print a confirmation message indicating the server was added
3. THE project documentation SHALL include instructions for the FastMCP install command with the correct server path

### Requirement 7

**User Story:** As a developer, I want the project structure reorganized for standard Python packaging, so that the codebase follows conventions and is maintainable.

#### Acceptance Criteria

1. THE Project_Structure SHALL place the MCP server code in a `src/fusion_mcp/` package directory
2. THE Project_Structure SHALL keep the FusionMCPBridge folder at the project root since it must be copied to Fusion's add-ins directory
3. THE Project_Structure SHALL include a `src/fusion_mcp/cli.py` module containing the entry point functions
4. WHEN the package is installed THEN the Server module SHALL be importable as `fusion_mcp.server`

### Requirement 8

**User Story:** As a developer, I want clear documentation for the new workflow, so that I can understand how to use the modernized project.

#### Acceptance Criteria

1. THE README SHALL document the new setup workflow using `uv sync`
2. THE README SHALL document the `uv run install-fusion-plugin` command with both regular and `--dev` options
3. THE README SHALL document the `uv run fastmcp install` command for Claude Desktop integration
4. THE README SHALL document the `uv run start-mcp-server` command for manual server startup
5. THE README SHALL remove references to the old manual Python scripts and pip-based installation
