# Veusz Gradient & Fade Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ggpointless-inspired visual enhancements to Veusz: line fade, area fade, point glow, gradient presets, per-point alpha, and SVG gradient export.

**Architecture:** Extend the existing `gradient.py` infrastructure (GradientConfig, QLinearGradient, QRadialGradient) into stroke rendering and per-element alpha modulation. New settings are added via Veusz's `Settings` subclass system, UI controls via existing `GradientFill` widget pattern, and rendering via QPainter segment interpolation.

**Tech Stack:** Python 3.14, PyQt6/Qt6, NumPy, existing veusz `setting`, `utils`, `widgets` modules.

---

## Phase 1: Foundation — Gradient Utilities & Presets

### Task 1.1: Extend gradient.py with fade helpers

**Files:**
- Modify: `veusz/utils/gradient.py`

**Step 1: Add `interpolate_alpha` utility function**

Add after `list_presets()`:

```python
def interpolate_alpha(start_alpha, end_alpha, n_segments):
    """Return array of alpha values linearly interpolated from start to end.
    
    Args:
        start_alpha: Alpha at start (0-1)
        end_alpha: Alpha at end (0-1)
        n_segments: Number of segments
    Returns:
        numpy array of length n_segments + 1
    """
    import numpy as N
    if n_segments < 1:
        return N.array([start_alpha])
    return N.linspace(start_alpha, end_alpha, n_segments + 1)


def create_fade_pen(painter, color, width, alpha_start, alpha_end, n_segments):
    """Create a list of QPen objects with interpolated alpha for line fade.
    
    Returns:
        List of (pen, fraction) tuples where fraction is 0-1 along the line.
    """
    qt = _get_qt()
    alphas = interpolate_alpha(alpha_start, alpha_end, n_segments)
    pens = []
    for i, alpha in enumerate(alphas):
        qcolor = qt.QColor(color)
        qcolor.setAlphaF(max(0.0, min(1.0, alpha)))
        pen = qt.QPen(qcolor, width)
        fraction = i / n_segments if n_segments > 0 else 0.0
        pens.append((pen, fraction))
    return pens


def get_fade_stops(direction, alpha_from, alpha_to):
    """Build gradient stops for a directional fade.
    
    Args:
        direction: 'start' (fade at start), 'end' (fade at end), 
                   'both' (fade at both ends)
        alpha_from: Opaque alpha value
        alpha_to: Transparent alpha value
    Returns:
        List of (offset, alpha) tuples for QLinearGradient
    """
    if direction == 'start':
        return [(0.0, alpha_to), (1.0, alpha_from)]
    elif direction == 'end':
        return [(0.0, alpha_from), (1.0, alpha_to)]
    else:  # 'both'
        return [(0.0, alpha_to), (0.5, alpha_from), (1.0, alpha_to)]
```

**Step 2: Add more preset gradients**

Extend `PRESETS` dict:

```python
'cividis': {
    'name': 'Cividis',
    'type': 'linear', 'angle': 90,
    'stops': [(0.0, '#002051'), (0.25, '#455a6e'), 
              (0.5, '#7f7f7f'), (0.75, '#b8a832'), (1.0, '#fec423')]
},
'turbo': {
    'name': 'Turbo',
    'type': 'linear', 'angle': 90,
    'stops': [(0.0, '#30123b'), (0.25, '#4662d7'), 
              (0.5, '#36aaf9'), (0.75, '#66c646'), (1.0, '#f9fb0d')]
},
'rdbu': {
    'name': 'Red-Blue Diverging',
    'type': 'linear', 'angle': 90,
    'stops': [(0.0, '#0571b0'), (0.25, '#92c5de'), 
              (0.5, '#f7f7f7'), (0.75, '#f4a582'), (1.0, '#ca0020')]
},
'spectral': {
    'name': 'Spectral',
    'type': 'linear', 'angle': 90,
    'stops': [(0.0, '#9e0142'), (0.25, '#fdae61'), 
              (0.5, '#ffffbf'), (0.75, '#66c2a5'), (1.0, '#5e4fa2')]
},
```

**Step 3: Add unit tests**

Create/update: `tests/selftests/test_gradient_fade.py`

```python
"""Tests for gradient fade utilities."""
import numpy as N
from veusz.utils.gradient import (
    interpolate_alpha, get_fade_stops, list_presets
)


def test_interpolate_alpha_basic():
    result = interpolate_alpha(0.0, 1.0, 10)
    assert len(result) == 11
    assert result[0] == 0.0
    assert result[-1] == 1.0
    assert N.allclose(N.diff(result), 1.0 / 10)


def test_interpolate_alpha_single():
    result = interpolate_alpha(0.5, 0.5, 0)
    assert len(result) == 1
    assert result[0] == 0.5


def test_get_fade_stops_start():
    stops = get_fade_stops('start', 1.0, 0.0)
    assert len(stops) == 2
    assert stops[0] == (0.0, 0.0)
    assert stops[1] == (1.0, 1.0)


def test_get_fade_stops_both():
    stops = get_fade_stops('both', 1.0, 0.0)
    assert len(stops) == 3
    assert stops[1][1] == 1.0


def test_presets_extended():
    presets = list_presets()
    names = [p[0] for p in presets]
    assert 'cividis' in names
    assert 'turbo' in names
    assert 'rdbu' in names
    assert 'spectral' in names
```

**Step 4: Run tests**

Run: `python -m pytest tests/selftests/test_gradient_fade.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add veusz/utils/gradient.py tests/selftests/test_gradient_fade.py
git commit -m "feat: add fade helper utilities and extended gradient presets"
```

---

## Phase 2: Line Fade

### Task 2.1: Add Fade settings to Line widget

**Files:**
- Modify: `veusz/setting/collections.py` (add FadeLine settings class)
- Modify: `veusz/widgets/line.py` (add Fade setting, modify draw method)

**Step 1: Add FadeLine settings class in collections.py**

After the existing `ArrowFill` class, add:

```python
class FadeLine(Settings):
    """Settings for line fade/gradient effect."""
    
    def __init__(self, name, **args):
        Settings.__init__(self, name, **args)
        
        self.add(Bool('hide', True,
            descr=_('Hide fade effect'),
            usertext=_('Enable')))
        self.add(Choice('direction', ('start', 'end', 'both'), 'start',
            descr=_('Direction of fade'),
            usertext=_('Direction')))
        self.add(Float('alphaFrom', 1.0,
            descr=_('Alpha at opaque end (0-1)'),
            usertext=_('Alpha from'),
            minval=0.0, maxval=1.0))
        self.add(Float('alphaTo', 0.0,
            descr=_('Alpha at transparent end (0-1)'),
            usertext=_('Alpha to'),
            minval=0.0, maxval=1.0))
        self.add(Int('segments', 20,
            descr=_('Number of line segments for fade'),
            usertext=_('Segments'),
            minval=2, maxval=200))
```

**Step 2: Add Fade setting to Line.addSettings**

In `veusz/widgets/line.py`, inside `Line.addSettings()`:

```python
s.add( setting.FadeLine(
    'Fade',
    descr=_('Line fade settings'),
    usertext=_('Fade')),
    pixmap='settings_plotline' )
```

**Step 3: Modify Line.draw to support fade rendering**

In `Line.draw()`, after the pen/brush setup and before the line iteration loop, add fade-aware rendering:

```python
# Fade rendering path
if not s.Fade.hide and lines:
    fade_dir = s.Fade.direction
    a_from = s.Fade.alphaFrom
    a_to = s.Fade.alphaTo
    n_seg = s.Fade.segments
    
    for index, (x, y, l, a) in enumerate(lines):
        # For single-line mode, fade along the line
        n_pts = max(2, n_seg + 1)
        # Generate sub-segments along the line
        for i in range(n_pts - 1):
            t0 = i / (n_pts - 1)
            t1 = (i + 1) / (n_pts - 1)
            
            # Compute alpha for this sub-segment
            if fade_dir == 'start':
                frac = t0
                seg_alpha = a_from + (a_to - a_from) * frac
            elif fade_dir == 'end':
                frac = t0
                seg_alpha = a_to + (a_from - a_to) * frac
            else:  # both
                frac = t0
                seg_alpha = a_to + (a_from - a_to) * (1 - 2 * abs(frac - 0.5))
            
            seg_alpha = max(0.0, min(1.0, seg_alpha))
            
            # Create pen with computed alpha
            from ..utils.gradient import _get_qt
            qt = _get_qt()
            base_pen = s.get('Line').makeQPen(painter)
            seg_color = qt.QColor(base_pen.color())
            seg_color.setAlphaF(seg_alpha)
            seg_pen = qt.QPen(seg_color, base_pen.widthF())
            seg_pen.setCapStyle(base_pen.capStyle())
            seg_pen.setJoinStyle(base_pen.joinStyle())
            
            # Draw sub-segment
            sx0 = x + l * math.cos(a / 180.0 * math.pi) * t0
            sy0 = y + l * math.sin(a / 180.0 * math.pi) * t0
            sx1 = x + l * math.cos(a / 180.0 * math.pi) * t1
            sy1 = y + l * math.sin(a / 180.0 * math.pi) * t1
            
            painter.setPen(seg_pen)
            qtloops.plotLinesToPainter(painter, 
                N.array([sx0]), N.array([sy0]),
                N.array([sx1]), N.array([sy1]), 
                clip if clip is not None else qt.QRectF())
    
    # Still draw arrows if needed
    utils.plotLineArrow(...)
```

**Step 4: Add UI pixmap for Fade settings**

Ensure `settings_plotfade` pixmap exists or reuse existing `settings_plotline`.

**Step 5: Write test**

Create: `tests/selftests/test_line_fade.py`

```python
"""Test line fade rendering."""
from veusz.utils.gradient import interpolate_alpha, get_fade_stops

def test_fade_stops():
    stops = get_fade_stops('start', 1.0, 0.0)
    assert stops[0][1] == 0.0  # transparent at start
    assert stops[1][1] == 1.0  # opaque at end

def test_alpha_interpolation():
    alphas = interpolate_alpha(1.0, 0.0, 10)
    assert len(alphas) == 11
    assert alphas[0] > alphas[5] > alphas[10]
```

**Step 6: Commit**

```bash
git add veusz/setting/collections.py veusz/widgets/line.py tests/selftests/test_line_fade.py
git commit -m "feat: add line fade with directional alpha interpolation"
```

---

## Phase 3: Point Glow

### Task 3.1: Add glow effect to MarkerFillBrush

**Files:**
- Modify: `veusz/widgets/point.py` (MarkerFillBrush class, _plotPoints method)

**Step 1: Add glow settings to MarkerFillBrush**

In `MarkerFillBrush.__init__()`, after existing settings:

```python
self.add( setting.Bool(
    'glow', False,
    descr=_('Add glow effect around markers'),
    usertext=_('Glow'),
    formatting=True) )
self.add( setting.Float(
    'glowRadius', 2.0,
    descr=_('Glow radius as multiple of marker size'),
    usertext=_('Glow radius'),
    minval=0.5, maxval=10.0) )
self.add( setting.Float(
    'glowAlpha', 0.3,
    descr=_('Glow opacity (0-1)'),
    usertext=_('Glow alpha'),
    minval=0.0, maxval=1.0) )
```

**Step 2: Implement glow drawing in _plotPoints**

In `PointPlotter._plotPoints()`, after drawing each marker, if glow is enabled:

```python
if s.MarkerFill.glow and not s.MarkerFill.hide:
    # Draw radial glow behind marker
    qt = utils.gradient._get_qt()
    glow_size = size * s.MarkerFill.glowRadius
    glow_color = qt.QColor(marker_color)
    glow_color.setAlphaF(s.MarkerFill.glowAlpha)
    
    gradient = qt.QRadialGradient(xplt_i, yplt_i, glow_size)
    gradient.setColorAt(0.0, glow_color)
    glow_fade = qt.QColor(glow_color)
    glow_fade.setAlphaF(0.0)
    gradient.setColorAt(1.0, glow_fade)
    
    brush = qt.QBrush(gradient)
    painter.setPen(qt.QPen(qt.Qt.PenStyle.NoPen))
    painter.setBrush(brush)
    painter.drawEllipse(
        qt.QPointF(xplt_i, yplt_i),
        glow_size, glow_size)
```

**Step 3: Commit**

```bash
git add veusz/widgets/point.py
git commit -m "feat: add point glow with radial gradient effect"
```

---

## Phase 4: Area Fill Fade

### Task 4.1: Add data-axis gradient to fill regions

**Files:**
- Modify: `veusz/utils/extbrushfilling.py` (fillToEdgePolygon, brushExtFillPath)

**Step 1: Add gradient direction option to fill**

In `extbrushfilling.py`, modify `brushExtFillPath` to support data-axis gradient:

```python
def brushExtFillPathDataAxis(painter, extbrush, path, fill_y=None, 
                              alpha_from=1.0, alpha_to=0.0, 
                              gradient_direction='vertical'):
    """Fill path with gradient along data axis (fade from baseline)."""
    qt = _get_qt()
    gradient_module = gradient
    
    bb = path.boundingRect()
    
    if gradient_direction == 'vertical':
        x1, y1 = bb.center().x(), bb.top()
        x2, y2 = bb.center().x(), bb.bottom()
    else:
        x1, y1 = bb.left(), bb.center().y()
        x2, y2 = bb.right(), bb.center().y()
    
    grad = qt.QLinearGradient(x1, y1, x2, y2)
    grad.setColorAt(0.0, qt.QColor(extbrush.get('color').color(painter)))
    end_color = qt.QColor(extbrush.get('color').color(painter))
    end_color.setAlphaF(alpha_to)
    grad.setColorAt(1.0, end_color)
    
    brush = qt.QBrush(grad)
    painter.fillPath(path, brush)
```

**Step 2: Integrate into PointFill settings**

Add `alphaFadeTo` setting to `PointFill` class in `collections.py`.

**Step 3: Commit**

```bash
git add veusz/utils/extbrushfilling.py veusz/setting/collections.py
git commit -m "feat: add data-axis gradient fill for area/polygon regions"
```

---

## Phase 5: Per-Point Alpha Dataset

### Task 5.1: Add alpha dataset to MarkerFillBrush

**Files:**
- Modify: `veusz/widgets/point.py` (MarkerFillBrush, _plotPoints)

**Step 1: Add alphaDataset setting**

In `MarkerFillBrush.__init__()`:

```python
self.add( setting.DatasetExtended(
    'alphaDataset', '',
    descr=_('Dataset for per-marker alpha (0-1 or 0-255)'),
    usertext=_('Alpha dataset'),
    formatting=True) )
```

**Step 2: Apply per-point alpha in rendering**

In `_plotPoints()`, before drawing each marker:

```python
# Apply per-point alpha if dataset provided
alpha_ds = s.MarkerFill.get('alphaDataset').getFloatArray(d)
if alpha_ds is not None and len(alpha_ds) > i:
    alpha_val = alpha_ds[i]
    # Normalize 0-255 to 0-1 if needed
    if alpha_val > 1.0:
        alpha_val = alpha_val / 255.0
    qcolor.setAlphaF(max(0.0, min(1.0, alpha_val)))
```

**Step 3: Commit**

```bash
git add veusz/widgets/point.py
git commit -m "feat: add per-point alpha dataset for scatter plots"
```

---

## Phase 6: SVG Export Gradient Support

### Task 6.1: Add gradient serialization to SVG export

**Files:**
- Modify: `veusz/document/svg_export.py`

**Step 1: Add gradient definition tracking**

```python
self._gradient_defs = {}
self._gradient_counter = 0
```

**Step 2: Add gradient SVG element generation**

```python
def _write_gradient_def(self, gradient_obj, bbox):
    """Write QLinearGradient/QRadialGradient to SVG <defs>."""
    self._gradient_counter += 1
    grad_id = f"vg{self._gradient_counter}"
    
    if hasattr(gradient_obj, 'type') and gradient_obj.type() == qt.QGradient.LinearGradient:
        x1, y1 = gradient_obj.start().x(), gradient_obj.start().y()
        x2, y2 = gradient_obj.finalStop().x(), gradient_obj.finalStop().y()
        # Normalize to viewBox coordinates
        self._defs_xml.append(
            f'<linearGradient id="{grad_id}" '
            f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
        )
        for offset, color in gradient_obj.stops():
            self._defs_xml.append(
                f'<stop offset="{offset}" '
                f'stop-color="{color.name()}" '
                f'stop-opacity="{color.alphaF():.3f}"/>'
            )
        self._defs_xml.append('</linearGradient>')
    
    return f'url(#{grad_id})'
```

**Step 3: Commit**

```bash
git add veusz/document/svg_export.py
git commit -m "feat: add gradient serialization to SVG export"
```

---

## Phase 7: Grid Layer Control

### Task 7.1: Add z-order setting to Grid widget

**Files:**
- Modify: `veusz/widgets/grid.py`

**Step 1: Add layer setting**

```python
s.add( setting.Choice(
    'layer', ('background', 'foreground'), 'background',
    descr=_('Draw grid lines above or below data'),
    usertext=_('Layer'),
    formatting=True) )
```

**Step 2: Implement foreground drawing**

In `Grid.draw()`, if `layer == 'foreground'`, register for post-data rendering.

**Step 3: Commit**

```bash
git add veusz/widgets/grid.py
git commit -m "feat: add grid z-order control (foreground/background)"
```

---

## Phase 8: Gradient Key/Legend Rendering

### Task 8.1: Support gradient in Key widget

**Files:**
- Modify: `veusz/widgets/key.py`

**Step 1: Detect gradient-enabled plotters**

When drawing key symbols, check if the source plotter has gradient fill enabled and render accordingly.

**Step 2: Commit**

```bash
git add veusz/widgets/key.py
git commit -m "feat: render gradient fills in key/legend symbols"
```

---

## Implementation Order & Dependencies

```
Phase 1 (Foundation)          ← No dependencies
    ↓
Phase 2 (Line Fade)           ← Depends on Phase 1
Phase 3 (Point Glow)          ← Depends on Phase 1
Phase 4 (Area Fade)           ← Depends on Phase 1
Phase 5 (Per-Point Alpha)     ← Independent of Phase 1
    ↓
Phase 6 (SVG Export)          ← Depends on Phases 2-4
Phase 7 (Grid Layer)          ← Independent
Phase 8 (Key Rendering)       ← Depends on Phases 2-4
```

Phases 2, 3, 4, 5, 7 can be developed in parallel after Phase 1.
Phase 6 requires working gradient rendering to export.
Phase 8 is polish that depends on visible gradient effects.

---

## Assumptions

1. Qt6 QLinearGradient and QRadialGradient are available (confirmed in `gradient.py`)
2. The existing `BrushExtended.Gradient` setting infrastructure is reused for fill gradients
3. Line fade uses QPainter segment interpolation (not SVG filter chains) for cross-backend compatibility
4. Glow uses QRadialGradient centered on each marker position
5. Per-point alpha dataset expects values in [0, 1] or [0, 255] range
6. SVG gradient export targets SVG 1.1 with embedded `<linearGradient>` elements
7. Grid foreground mode reuses the existing draw method with a modified paint order
8. Default values for all new settings match the "no effect" behavior (glow off, fade off) to maintain backward compatibility
