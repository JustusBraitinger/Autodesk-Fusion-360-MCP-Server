# Reference: Fusion 360 Add-in Testing with Pytest
**Strategy:** The Humble Object Pattern (Logic Separation)
**Goal:** Enable standard unit testing without mocks or running Fusion 360.

## 1. The Core Constraint
The Autodesk API (`adsk`) is embedded in Fusion 360. It cannot be installed via pip and does not run in a standard terminal.
* **Result:** Any file containing `import adsk` will crash `pytest`.
* **Solution:** We isolate "Logic" from "API Interactions" completely.

## 2. The Architecture: "Green Zone" vs. "Red Zone"
We split the codebase into two distinct layers.

![Architecture Diagram](https://mermaid.ink/img/pako:eNp1ksFOwzAMhl_F8gl14bTdeIB24oA4cOIwCW6TNhZNEjvFClT13UlarYGEDi6R49_2b_85oYw1QoE8FttHVEg_zSg0eF9yS-fLhaT8kC5y-Pz8Ch8fH9dGSQZt0Hjwy4y2Cg10oR20g3FwAdoq0C8O_A7WwR0Y4N466IEP8A3s4BEM0M-l1kgrdOQyF-WzUsqC8kVaQkX5VbJ2K-2sLCSXlaRaS9k2yYtS6oKysyTdtU1H-VlS3qR104b9_m-8y1iW5FpW5L3k4mF3X0uR7yXlG2l3d5eWp_xH0j5Kyi-S9kVSfpO0b1e_4wU44A144P94P96PD-PD-DA-jI_jw_g4PoxP4MP4BD6MT-DD-AQ-nI_z43w4P86P8-P8OD_OT_KT_CQ_yU_yk_wkP8lP8rP8LD_Lz_Kz_Cw_y8_yC_kFf8k)

| Zone | Layer Name | Dependencies | Testable? | Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| 🟢 | **Green Zone** (Logic) | Standard Python only (`math`, `json`, etc.) | **YES** (Pytest) | Math, Algorithms, Data Parsing, State Logic. |
| 🔴 | **Red Zone** (Interface) | `adsk.core`, `adsk.fusion` | **NO** (Manual) | Reading Fusion inputs, Calling Green Zone, Creating Fusion geometry. |

## 3. Implementation

### Directory Structure
```text
my_addin/
├── logic.py         # 🟢 PURE PYTHON (No adsk imports)
├── commands.py      # 🔴 FUSION API (Imports adsk & logic)
└── tests/
    └── test_logic.py # 🟢 STANDARD PYTEST
```

### Code Example A: The Green Zone (`logic.py`)
*This file contains the "brains." It is safe for Pytest because it knows nothing about Fusion.*

```python
# logic.py
# STRICT RULE: Do not import adsk here.

def calculate_grid_coordinates(width: float, height: float, count: int) -> list:
    \"\"\"
    Pure math logic.
    Returns standard Python tuples: [(0,0), (10,0), (20,0)...]
    \"\"\"
    step_x = width / (count - 1)
    points = []
    for i in range(count):
        points.append((i * step_x, 0.0))
    return points
```

### Code Example B: The Red Zone (`commands.py`)
*This file is the "Humble Object." It is a thin wrapper that bridges Fusion to the logic.*

```python
# commands.py
import adsk.core, adsk.fusion
from .logic import calculate_grid_coordinates  # Import logic

def run_grid_command(width, height, count):
    # 1. DELEGATE: Get raw data from the Green Zone
    raw_points = calculate_grid_coordinates(width, height, count)
    
    # 2. EXECUTE: Use Fusion API to draw the result
    app = adsk.core.Application.get()
    sketch = app.activeProduct.rootComponent.sketches.add(
        app.activeProduct.rootComponent.xYConstructionPlane
    )
    
    for x, y in raw_points:
        # Convert standard tuple to Fusion Point3D here
        pt = adsk.core.Point3D.create(x, y, 0)
        sketch.sketchPoints.add(pt)
```

### Code Example C: The Test (`test_logic.py`)
*Runs instantly in CI/CD or local terminal.*

```python
# test_logic.py
import pytest
from my_addin.logic import calculate_grid_coordinates

def test_grid_math():
    # Tests the algorithm without launching Fusion 360
    points = calculate_grid_coordinates(width=100.0, height=50.0, count=3)
    
    assert len(points) == 3
    assert points[0] == (0.0, 0.0)
    assert points[1] == (50.0, 0.0)
    assert points[2] == (100.0, 0.0)
```

## 4. The Golden Rule of Dependencies
To ensure `pytest` never crashes:
1.  **Red** may import **Green**.
2.  **Green** must **NEVER** import **Red**.
3.  Tests only import **Green**.