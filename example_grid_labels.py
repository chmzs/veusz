#!/usr/bin/env python
"""
Example: Create a document with a 2x2 grid of graphs.
Then manually run the "Add labels to grid graphs" plugin in Veusz UI.

Run with: pixi run python example_grid_labels.py
"""

import numpy as np
import veusz.embed as veusz

# Create embedded Veusz instance (hidden=True for no GUI)
g = veusz.Embedded("Grid Labels Example", hidden=True, compatlevel=-1)

# Create a page and grid
g.To(g.Add("page"))  # Add page, make it current
page_path = g.CurrentPath()  # Get page path
g.To(g.Add("grid"))  # Add grid, make it current
grid_path = g.CurrentPath()  # Get grid path
g.Set("rows", 2)  # Set grid rows
g.Set("columns", 2)  # Set grid columns

# Add 4 graphs to the grid with data
for i in range(4):
    g.To(g.Add("graph", name=f"graph{i + 1}"))  # Add graph, make it current
    x = np.linspace(0, 10, 100)
    y = np.sin(x + i) * (i + 1)
    g.SetData("x", x)  # Set x data
    g.SetData("y", y)  # Set y data
    g.Add("xy")  # Add xy plot
    g.To("..")  # Back to grid

g.To(page_path)  # Back to page

print("Created document with 2x2 grid containing 4 graphs")
print(f"Grid path: {grid_path}")

# Save to file
g.Save("grid_labels_example.vsz")
print("Saved to grid_labels_example.vsz")
print()
print("=== HOW TO USE THE PLUGIN IN VEUSZ UI ===")
print("1. Open grid_labels_example.vsz in Veusz")
print("2. In the object tree (left panel), CLICK on 'grid1' to SELECT it")
print("3. Menu → General → Add labels to grid graphs")
print("4. Adjust settings:")
print("   - Grid widget: should show /page1/grid1 (auto-selected)")
print("   - Label type: lowercase / uppercase / numbers")
print("   - Prefix/Suffix: e.g. '(' and ')'")
print("   - X position: 0.02 (left), Y position: 0.98 (top)")
print("   - Horizontal text alignment: left / centre / right")
print("   - Vertical text alignment: bottom / centre / top")
print("   - Offset: 4pt (margin from graph edge)")
print("   - Use graph coordinates: Yes (0-1 relative to each graph)")
print("5. Click OK or Apply")
print()
print("Labels (a), (b), (c), (d) will appear on each graph!")
