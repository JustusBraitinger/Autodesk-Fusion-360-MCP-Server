# Requirements Document

## Introduction

This feature enhances the Fusion 360 MCP integration to provide comprehensive management of toolpath passes and linking capabilities. In CAM operations, complex machining often requires multiple passes (roughing, semi-finishing, finishing) and coordinated sequences of toolpaths. This enhancement will enable AI assistants to understand, analyze, and manage these multi-pass operations and toolpath relationships through natural language interactions.

## Glossary

- **Toolpath Pass**: A single execution of a toolpath operation with specific parameters (e.g., roughing pass, finishing pass)
- **Pass Sequence**: An ordered series of passes that work together to complete a machining operation
- **Toolpath Linking**: The relationship and coordination between multiple toolpaths in a machining sequence
- **Roughing Pass**: Initial material removal pass with aggressive parameters
- **Finishing Pass**: Final pass with precise parameters for surface quality
- **Semi-Finishing Pass**: Intermediate pass between roughing and finishing
- **Lead-In/Lead-Out**: Entry and exit movements for toolpath operations
- **Pass Dependencies**: Requirements where one pass must complete before another can begin
- **Toolpath Chain**: A sequence of linked toolpaths that execute in a specific order
- **Leads & Transitions**: Dialog section in 2D operations containing lead-in, lead-out, and transition settings
- **Linking Section**: Dialog section in 3D operations containing approach, retract, and clearance settings
- **Multiple Depths**: Pass configuration allowing multiple cutting levels in a single operation
- **Stock to Leave**: Material intentionally left for subsequent finishing operations
- **Spring Pass**: Additional finishing pass at the same depth to improve surface quality
- **Transition Type**: Method of moving between cutting areas (lift, stay down, etc.)
- **Arc Radius**: Radius value for curved lead-in/lead-out movements

## Requirements

### Requirement 1

**User Story:** As a CAM programmer, I want to understand multi-pass toolpath operations, so that I can optimize machining strategies and ensure proper sequencing.

#### Acceptance Criteria

1. WHEN a toolpath has multiple passes defined, THE MCP Server SHALL return information about each pass including pass type, parameters, and sequence order
2. WHEN analyzing toolpath passes, THE MCP Server SHALL identify the relationship between passes (roughing, semi-finishing, finishing)
3. WHEN passes have different tool requirements, THE MCP Server SHALL indicate tool changes and their impact on machining time
4. WHEN passes share common parameters, THE MCP Server SHALL highlight parameter inheritance and overrides
5. THE MCP Server SHALL provide pass execution order and timing information when available

### Requirement 2

**User Story:** As an AI assistant, I want to analyze toolpath linking relationships, so that I can provide intelligent recommendations about machining sequences.

#### Acceptance Criteria

1. WHEN toolpaths are linked in a sequence, THE MCP Server SHALL return the complete chain with execution order
2. WHEN analyzing toolpath dependencies, THE MCP Server SHALL identify which operations must complete before others can begin
3. WHEN toolpath linking affects setup requirements, THE MCP Server SHALL indicate workholding and fixture considerations
4. WHEN linked toolpaths use different tools, THE MCP Server SHALL provide tool change sequence and optimization opportunities
5. THE MCP Server SHALL validate toolpath linking integrity and identify broken or invalid links

### Requirement 3

**User Story:** As a machinist, I want to understand pass parameters and their impact, so that I can verify machining strategies will produce the desired results.

#### Acceptance Criteria

1. WHEN examining roughing passes, THE MCP Server SHALL return aggressive cutting parameters optimized for material removal
2. WHEN examining finishing passes, THE MCP Server SHALL return precision parameters optimized for surface quality
3. WHEN passes have stock-to-leave values, THE MCP Server SHALL calculate remaining material for subsequent passes
4. WHEN analyzing pass efficiency, THE MCP Server SHALL provide estimated machining times and material removal rates
5. THE MCP Server SHALL identify potential conflicts between pass parameters and tool capabilities

### Requirement 4

**User Story:** As a CAM programmer, I want to modify pass sequences and linking settings, so that I can optimize machining workflows through conversational interaction.

#### Acceptance Criteria

1. WHEN modifying pass parameters, THE MCP Server SHALL validate changes against toolpath constraints and dependencies
2. WHEN reordering passes in a sequence, THE MCP Server SHALL ensure logical machining progression (rough before finish)
3. WHEN adding or removing passes, THE MCP Server SHALL update dependent toolpath parameters automatically
4. WHEN modifying toolpath links, THE MCP Server SHALL validate the new sequence maintains machining integrity
5. THE MCP Server SHALL prevent modifications that would create invalid machining sequences or tool conflicts

### Requirement 5

**User Story:** As an AI assistant, I want to recommend pass optimization strategies, so that I can help users improve machining efficiency and quality.

#### Acceptance Criteria

1. WHEN analyzing multi-pass operations, THE MCP Server SHALL identify opportunities for pass consolidation or splitting
2. WHEN toolpath linking is suboptimal, THE MCP Server SHALL suggest reordering or regrouping strategies
3. WHEN pass parameters are inconsistent, THE MCP Server SHALL recommend parameter harmonization across the sequence
4. WHEN tool changes are excessive, THE MCP Server SHALL suggest toolpath reordering to minimize tool changes
5. THE MCP Server SHALL provide machining time estimates and efficiency metrics for different pass strategies

### Requirement 7

**User Story:** As a CAM programmer, I want to access and modify operation-specific linking settings organized by dialog sections, so that I can configure toolpath behavior exactly as shown in Fusion 360's interface.

#### Acceptance Criteria

1. WHEN querying 2D Pocket operations, THE MCP Server SHALL return linking settings organized under "Leads & Transitions" section including lead-in type, lead-out type, transition type, and arc radius settings
2. WHEN querying Trace operations, THE MCP Server SHALL return linking settings organized under operation-specific sections including contact point, approach/retract distances, and transition settings
3. WHEN querying 3D operations, THE MCP Server SHALL return linking settings organized under "Linking" section including approach type, retract type, and clearance settings
4. WHEN modifying linking settings, THE MCP Server SHALL validate values against operation-specific constraints and available options for that operation type
5. THE MCP Server SHALL present settings grouped by their dialog sections exactly as they appear in Fusion 360's CAM interface

### Requirement 8

**User Story:** As an AI assistant, I want to understand operation-specific pass and linking parameters, so that I can provide accurate recommendations based on the specific machining strategy.

#### Acceptance Criteria

1. WHEN analyzing 2D Pocket operations, THE MCP Server SHALL return pass-specific parameters including multiple depths, stock to leave, and finishing passes with their respective linking settings
2. WHEN analyzing Adaptive Clearing operations, THE MCP Server SHALL return pass parameters including optimal load, stock to leave, and finishing pass settings
3. WHEN analyzing Contour operations, THE MCP Server SHALL return pass parameters including multiple depths, spring passes, and lead-in/lead-out configurations
4. WHEN analyzing Drill operations, THE MCP Server SHALL return cycle-specific parameters including peck depth, dwell time, and retract behavior
5. THE MCP Server SHALL identify which parameters are available for each operation type and indicate operation-specific constraints

### Requirement 6

**User Story:** As a quality engineer, I want to understand pass relationships and their impact on part quality, so that I can ensure machining strategies meet specifications.

#### Acceptance Criteria

1. WHEN analyzing finishing pass relationships, THE MCP Server SHALL identify how roughing passes affect final surface quality
2. WHEN stock-to-leave values are specified, THE MCP Server SHALL validate they provide adequate material for finishing operations
3. WHEN pass sequences affect dimensional accuracy, THE MCP Server SHALL highlight critical relationships and tolerances
4. WHEN toolpath linking affects part distortion, THE MCP Server SHALL identify high-stress sequences and recommend mitigation
5. THE MCP Server SHALL provide quality metrics and predictions based on pass sequencing and parameters