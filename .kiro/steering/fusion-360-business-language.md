# Fusion 360 Business Language and Terminology Standards

**Version:** 1.0  
**Last Updated:** January 3, 2025  
**Owner:** CAM Setup Management Team  
**Purpose:** Establish consistent use of Fusion 360's official business terminology throughout the codebase

## Overview

This steering file defines the official Fusion 360 business language and terminology that must be used consistently across all code, documentation, and user interfaces. Using Fusion 360's actual business terminology ensures better user experience and alignment with the official product.

## Core Terminology Standards

### Work Coordinate System (WCS)
- **ALWAYS use:** "WCS" or "Work Coordinate System"
- **NEVER use:** "coordinate_system", "coord_system", "cs"
- **Context:** CAM setup configuration, coordinate system definition
- **Example:** `setup.workCoordinateSystem`, `wcs_configuration`, `WCS origin`

### Design vs CAD Terminology
- **ALWAYS use:** "Design" when referring to the design workspace
- **NEVER use:** "CAD" in user-facing contexts
- **Context:** Workspace references, geometry creation, model preparation
- **Example:** "Design workspace", "design geometry", "design model"
- **Exception:** "CAD" may be used in technical contexts where it's industry standard

### Model Structure and References
- **Model references are ROOT LEVEL entities**
- **NEVER nest:** Model references under WCS or coordinate system objects
- **Structure:** `setup.model_id` (root level), not `setup.wcs.model_id`
- **Context:** CAM setup creation, geometry referencing

### Manufacturing Workspace
- **ALWAYS use:** "MANUFACTURE workspace" (official Fusion 360 name)
- **NEVER use:** "CAM workspace", "manufacturing workspace"
- **Context:** Workspace switching, CAM operations

### Setup vs Operation Terminology
- **Setup:** Container for related machining operations with shared WCS and stock
- **Operation:** Individual machining operation (pocket, contour, drill, etc.)
- **Toolpath:** Generated path for an operation
- **NEVER confuse:** Setup and operation are distinct concepts

## API Naming Conventions

### Property Names
- Use Fusion 360's actual API property names when available
- For custom properties, follow Fusion 360 naming patterns
- Examples:
  - `workCoordinateSystem` (matches Fusion 360 API)
  - `stockDefinition` (follows Fusion 360 patterns)
  - `setupConfiguration` (consistent with Fusion 360 style)

### Function Names
- Use descriptive names that reflect Fusion 360 operations
- Include entity type in function names for clarity
- Examples:
  - `create_cam_setup()` (clear CAM context)
  - `configure_wcs()` (uses official WCS terminology)
  - `define_stock_geometry()` (clear operation purpose)

### Variable Names
- Use full words, not abbreviations, for clarity
- Follow Fusion 360 terminology consistently
- Examples:
  - `work_coordinate_system` not `coord_sys`
  - `setup_configuration` not `setup_config`
  - `model_reference` not `model_ref`

## Documentation Standards

### User-Facing Documentation
- Always use official Fusion 360 terminology
- Explain technical terms using Fusion 360's definitions
- Reference official Fusion 360 documentation when possible

### Code Comments
- Use Fusion 360 terminology in comments
- Explain API usage in context of Fusion 360 workflows
- Reference official API documentation

### Error Messages
- Use terminology that matches Fusion 360 UI
- Provide actionable guidance using Fusion 360 concepts
- Example: "Please switch to the MANUFACTURE workspace to access CAM operations"

## Workspace and UI Terminology

### Workspace Names
- **Design workspace** (for geometry creation and modification)
- **MANUFACTURE workspace** (for CAM operations)
- **SIMULATION workspace** (for analysis)
- Use official capitalization and naming

### UI Elements
- **Browser panel** (not "project browser" or "tree view")
- **Timeline** (for parametric history)
- **Canvas** (for 3D viewport)
- **Toolbar** (for command access)

### CAM-Specific UI Elements
- **Setup** (CAM setup container)
- **Operations** (machining operations)
- **Tool Library** (cutting tool definitions)
- **Post Process** (G-code generation)

## Integration Terminology

### Design-to-CAM Workflow
- **Model preparation** (preparing geometry for CAM)
- **Geometry selection** (selecting bodies/faces for machining)
- **Setup creation** (creating CAM setup with WCS and stock)
- **Operation definition** (defining machining operations)

### Data Flow Terms
- **Model geometry** (source geometry from design workspace)
- **Stock definition** (raw material specification)
- **WCS definition** (work coordinate system setup)
- **Toolpath generation** (creating machining paths)

## Common Mistakes to Avoid

### Incorrect Terminology
- ❌ "coordinate_system" → ✅ "WCS" or "Work Coordinate System"
- ❌ "CAD workspace" → ✅ "Design workspace"
- ❌ "setup.wcs.model_id" → ✅ "setup.model_id" (root level)
- ❌ "CAM workspace" → ✅ "MANUFACTURE workspace"

### Inconsistent Naming
- ❌ Mixed abbreviations and full words
- ❌ Non-standard API property names
- ❌ Generic terms instead of Fusion 360 specific terms

### Technical Debt
- ❌ Using legacy terminology from other CAM systems
- ❌ Inconsistent capitalization
- ❌ Mixing internal and user-facing terminology

## Implementation Guidelines

### Code Reviews
- Verify all new code uses correct Fusion 360 terminology
- Check for consistency with existing terminology standards
- Ensure user-facing strings use official Fusion 360 language

### Refactoring Priorities
1. **High Priority:** User-facing strings and error messages
2. **Medium Priority:** API function and property names
3. **Low Priority:** Internal variable names (unless confusing)

### Documentation Updates
- Update all documentation to use consistent terminology
- Add glossary sections for technical terms
- Reference official Fusion 360 documentation

## Validation and Testing

### Terminology Validation
- Include terminology checks in code reviews
- Test error messages for correct Fusion 360 terminology
- Validate API documentation uses official terms

### User Experience Testing
- Ensure terminology matches user expectations from Fusion 360
- Test with actual Fusion 360 users for terminology clarity
- Validate against official Fusion 360 training materials

## Future Considerations

### API Evolution
- Monitor Fusion 360 API updates for terminology changes
- Update terminology standards as Fusion 360 evolves
- Maintain backward compatibility where possible

### Internationalization
- Consider how terminology translates to other languages
- Follow Fusion 360's internationalization patterns
- Maintain consistency across language versions

## References

- [Autodesk Fusion 360 Official Documentation](https://help.autodesk.com/view/fusion360/)
- [Fusion 360 API Reference](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A)
- [Fusion 360 CAM Programming Guide](https://help.autodesk.com/view/fusion360/ENU/?contextId=CAM-WORKSPACE)

## Change Log

- **v1.0** (January 3, 2025): Initial creation with core terminology standards for CAM setup management - CAM Setup Management Team

---

**Note:** This steering file should be referenced during all CAM setup management development to ensure consistent use of Fusion 360 business terminology. Any deviations should be documented and approved through the standard review process.