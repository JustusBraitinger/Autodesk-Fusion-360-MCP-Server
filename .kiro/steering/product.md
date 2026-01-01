# Fusion MCP Integration

## Overview
Fusion MCP Integration bridges AI assistants (Claude, VS Code Copilot) with Autodesk Fusion 360 through the Model Context Protocol (MCP). It enables conversational CAD - creating and manipulating 3D models using natural language.

## Purpose
- Conversational CAD: Create 3D models via natural language commands
- AI-Driven Automation: Automate repetitive modeling tasks
- Parametric Control: Dynamically modify design parameters
- Accessible CAD: Lower barrier for non-CAD users

## Status
Proof-of-concept / Educational project - not production software.

## Key Capabilities
- 2D Sketching: circles, rectangles, lines, arcs, splines, ellipses, text
- 3D Operations: extrude, revolve, sweep, loft, boolean operations
- Features: fillet, shell, holes, threads, patterns (circular/rectangular)
- Export: STEP and STL file formats
- CAM: Toolpath listing and parameter inspection

## Architecture
Two-component system:
1. **MCP Server** (`src/fusion_mcp/`): FastMCP server exposing tools to AI assistants
2. **Fusion Add-In** (`FusionMCPBridge/`): HTTP server running inside Fusion 360, executing CAD operations

Communication flow: AI Assistant → MCP Server → HTTP → Fusion Add-In → Fusion 360 API
