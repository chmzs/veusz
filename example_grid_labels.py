#!/usr/bin/env python
"""
Example: Add sequential labels (a, b, c...) to each Graph inside a Grid
using the "Add labels to grid graphs" tools plugin (GridGraphLabels).

This script:
  1. builds a document with a 2x2 Grid of 4 graphs,
  2. runs the plugin programmatically (same code path the dialog uses),
  3. prints the created labels, and
  4. saves the document to grid_labels_example.vsz.

Run with:  pixi run python example_grid_labels.py
"""

import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import veusz.qtall as qt  # noqa: E402  (must create QApplication first)

app = qt.QApplication([])

import veusz.widgets  # noqa: E402  (register widget types in factory — import side-effect)
from veusz import document  # noqa: E402
from veusz.document import operations  # noqa: E402
from veusz.plugins.toolsplugin import GridGraphLabels  # noqa: E402


def main():
    doc = document.Document()
    root = doc.basewidget

    # 1. Build page > grid (2x2) > 4 graphs
    page = doc.applyOperation(
        operations.OperationWidgetAdd(root, "page", autoadd=True)
    )
    grid = doc.applyOperation(
        operations.OperationWidgetAdd(page, "grid", autoadd=True, name="grid1")
    )
    grid.settings.rows = 2
    grid.settings.columns = 2
    for i in range(4):
        g = doc.applyOperation(
            operations.OperationWidgetAdd(
                grid, "graph", autoadd=True, name=f"graph{i + 1}"
            )
        )
        doc.applyOperation(operations.OperationWidgetAdd(g, "xy", autoadd=True))

    # 2. Run the GridGraphLabels plugin (same fields the dialog produces)
    plugin = GridGraphLabels()
    fields = {
        "grid": grid.path,          # path to the Grid widget
        "label_type": "lowercase",  # lowercase | uppercase | numbers
        "prefix": "(",              # text before the label
        "suffix": ")",              # text after the label
        "x_pos": 0.1,               # x fraction of each graph area (0-1)
        "y_pos": 0.9,               # y fraction of each graph area (0-1)
        "halign": "left",           # left | centre | right
        "valign": "top",            # bottom | centre | top
        "offset": "4pt",            # margin from graph edge
    }
    doc.applyOperation(operations.OperationToolsPlugin(plugin, fields))

    # 3. Show what was created
    for g in grid.children:
        for c in g.children:
            if c.typename == "label":
                print(
                    f"{g.name}: label={c.settings.label!r} "
                    f"positioning={c.settings.get('positioning').get()!r} "
                    f"xPos={c.settings.get('xPos').get()!r} "
                    f"yPos={c.settings.get('yPos').get()!r}"
                )

    # 4. Save
    doc.save("grid_labels_example.vsz")
    print("Saved to grid_labels_example.vsz")
    print("Open it in Veusz to see labels (a), (b), (c), (d) on each graph.")


if __name__ == "__main__":
    main()
