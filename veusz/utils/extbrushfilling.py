#    Copyright (C) 2012 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This file is part of Veusz.
#
#    Veusz is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    Veusz is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Veusz. If not, see <https://www.gnu.org/licenses/>.

##############################################################################

"""Paint fills with extended brush class.

Paints solid, hatching, gradient and various qt brushes
"""

import math

import numpy as N

from .. import qtall as qt
from ..helpers.qtloops import plotLinesToPainter, polygonClip
from . import gradient as gradient_module

def dumppath(p):
    i =0
    while i < p.elementCount():
        e = p.elementAt(i)
        if e.isLineTo():
            print(" l(%i,%i)" %( e.x, e.y), end=' ')
            i += 1
        elif e.isMoveTo():
            print(" m(%i,%i)" %(e.x, e.y), end=' ')
            i += 1
        else:
            print(" c(%i,%i,%i,%i,%i,%i)" %(e.x, e.y, p.elementAt(i+1).x, p.elementAt(i+1).y, p.elementAt(i+2).x, p.elementAt(i+2).y), end=' ')
            i += 3
    print()

def _hatcher(painter, pen, painterpath, spacing, hatchlist):
    """Draw hatching on painter path given."""

    painter.save()
    painter.setPen(pen)

    # debugging
    # dumppath(painterpath)

    painter.setClipPath(painterpath, qt.Qt.ClipOperation.IntersectClip)

    # this is the bounding box of the path
    bb = painter.clipPath().boundingRect()

    for params in hatchlist:
        # scale values
        offsetx, offsety, deltax, deltay = [x*spacing for x in params]

        # compute max number of steps
        numsteps = 0
        if deltax != 0:
            numsteps += int(bb.width() / abs(deltax)) + 4
        if deltay != 0:
            numsteps += int(bb.height() / abs(deltay)) + 4

        # calculate repeat position in x and y
        # we start the positions of lines at multiples of these distances
        # to ensure the pattern doesn't shift if the area does

        # distances between lines
        mag = math.sqrt(deltax**2 + deltay**2)
        # angle to x of perpendicular lines
        theta = math.atan2(deltay, deltax)
        s, c = math.sin(theta), math.cos(theta)
        intervalx = intervaly = 1.
        if abs(c) > 1e-4: intervalx = abs(mag / c)
        if abs(s) > 1e-4: intervaly = abs(mag / s)

        startx = int(bb.left() / intervalx) * intervalx + offsetx
        starty = int(bb.top()  / intervaly) * intervaly + offsety

        # normalise line vector
        linedx, linedy = -deltay/mag, deltax/mag
        # scale of lines from start position
        scale = max( bb.width(), bb.height() ) * 4

        # construct points along lines
        # this is scales to ensure the lines are bigger than the box
        idx = N.arange(-numsteps, numsteps)
        x = idx*deltax + startx
        y = idx*deltay + starty
        x1 = x - scale*linedx
        x2 = x + scale*linedx
        y1 = y - scale*linedy
        y2 = y + scale*linedy

        # plot lines, clipping to bb
        plotLinesToPainter(painter, x1, y1, x2, y2, bb)

    painter.restore()

# list of fill styles
extfillstyles = (
    'solid', 'horizontal', 'vertical', 'cross',
    'forward diagonals', 'backward diagonals',
    'diagonal cross',
    'forward 2', 'backward 2', 'forward 3',
    'backward 3', 'forward 4', 'backward 4',
    'forward 5', 'backward 5',
    'diagonal cross 2', 'diagonal cross 3',
    'diagonal cross 4', 'diagonal cross 5',
    'vertical forward', 'vertical backward',
    'horizontal forward', 'horizontal backward',
    'star',
    'triangles 1', 'triangles 2', 'triangles 3', 'triangles 4',
    'horizontal double', 'vertical double',
    'forward double', 'backward double',
    'double cross', 'double diagonal cross',
    '94% dense', '88% dense', '63% dense', '50% dense',
    '37% dense', '12% dense', '6% dense',
)

# hatching styles
# map names to lists of (offsetx, offsety, gradx, grady)
_hatchmap = {
    'horizontal': ((0, 0, 0, 1), ),
    'vertical': ((0, 0, 1, 0), ),
    'cross': ( (0, 0, 0, 1), (0, 0, 1, 0), ),
    'forward diagonals': ( (0, 0, 0.7071, -0.7071), ),
    'backward diagonals': ( (0, 0, 0.7071, 0.7071), ),
    'diagonal cross': ( (0, 0, 0.7071, 0.7071), (0, 0, 0.7071, -0.7071), ),
    'forward 2': ( (0, 0, 0.8660, -0.5), ),
    'backward 2': ( (0, 0, 0.8660, 0.5), ),
    'forward 3': ( (0, 0, 0.5, -0.8660), ),
    'backward 3': ( (0, 0, 0.5, 0.8660), ),
    'forward 4': ( (0, 0, 0.2588, -0.9659), ),
    'backward 4': ( (0, 0, 0.2588, 0.9659), ),
    'forward 5': ( (0, 0, 0.9659, -0.2588), ),
    'backward 5': ( (0, 0, 0.9659, 0.2588), ),
    'diagonal cross 2': ( (0, 0, 0.8660, -0.5), (0, 0, 0.8660, 0.5), ),
    'diagonal cross 3': ( (0, 0, 0.5, -0.8660), (0, 0, 0.5, 0.8660), ),
    'diagonal cross 4': ( (0, 0, 0.9659, -0.2588), (0, 0, 0.9659, 0.2588), ),
    'diagonal cross 5': ( (0, 0, 0.2588, 0.9659), (0, 0, 0.2588, -0.9659), ),
    'vertical forward': ( (0, 0, 1, 0), (0, 0, 0.7071, -0.7071), ),
    'vertical backward': ( (0, 0, 1, 0), (0, 0, 0.7071, 0.7071), ),
    'horizontal forward': ( (0, 0, 0, 1), (0, 0, 0.7071, -0.7071), ),
    'horizontal backward': ( (0, 0, 0, 1), (0, 0, 0.7071, 0.7071), ),
    'star': ( (0, 0, 2, 0), (0, 0, 0, 2), (0, 0, -1, 1), (0, 0, 1, 1), ),
    'triangles 1': ( (0, 0, 2, 0), (0, 0, 0, 2), (0, 0, -1, 1),),
    'triangles 2': ( (0, 0, 2, 0), (0, 0, 0, 2), (0, 0, 1, 1),),
    'triangles 3': ( (0, 0, 0, 1), (0, 0, -1, 1), (0, 0, 1, 1), ),
    'triangles 4': ( (0, 0, 1, 0), (0, 0, -1, 1), (0, 0, 1, 1), ),
    'horizontal double': ((0, 0, 0, 1), (0, 0.2828, 0, 1), ),
    'vertical double': ((0, 0, 1, 0), (0.2828, 0, 1, 0), ),
    'forward double': ((0, 0, 0.7071, -0.7071), (0.4,0, 0.7071, -0.7071)),
    'backward double': ((0, 0, 0.7071, 0.7071), (0.4,0, 0.7071, 0.7071)),
    'double cross': (
        (0, 0, 0, 1), (0, 0.2828, 0, 1),
        (0, 0, 1, 0), (0.2828, 0, 1, 0),),
    'double diagonal cross': (
        (0, 0, 0.7071, -0.7071), (0.4,0, 0.7071, -0.7071),
        (0, 0, 0.7071, 0.7071), (0.4,0, 0.7071, 0.7071)),
}

# convert qt-specific fill styles into qt styles
_fillcnvt = {
    'solid': qt.Qt.BrushStyle.SolidPattern,
    '94% dense': qt.Qt.BrushStyle.Dense1Pattern,
    '88% dense': qt.Qt.BrushStyle.Dense2Pattern,
    '63% dense': qt.Qt.BrushStyle.Dense3Pattern,
    '50% dense': qt.Qt.BrushStyle.Dense4Pattern,
    '37% dense': qt.Qt.BrushStyle.Dense5Pattern,
    '12% dense': qt.Qt.BrushStyle.Dense6Pattern,
    '6% dense': qt.Qt.BrushStyle.Dense7Pattern
}

def _brushExtFillPathGradient(painter, extbrush, path, stroke=None,
                               dataindex=0, axes=None, fill_bounds=None):
    """Fill a path with a gradient brush.

    Uses the gradient module for gradient creation.

    gradient_setting contains:
      - type: 'linear' or 'radial'
      - angle: float (0-360) for linear gradient
      - stops: list of (offset, color) tuples
      - enabled: bool
    """
    gradient_setting = extbrush.get('Gradient')
    if not gradient_setting:
        return

    # Get gradient configuration from setting
    config = gradient_module.get_gradient_config(gradient_setting)
    if not config.enabled:
        return

    # Composite brush-level and gradient-level transparency so that the
    # brush's Transparency setting works for gradient fills just as it does
    # for solid fills (extbrushfilling solid path: transparency -> setAlphaF).
    brush_transparency = getattr(extbrush, 'transparency', 0) or 0
    gradient_transparency = getattr(config, 'transparency', 0) or 0
    if brush_transparency >= 100 or gradient_transparency >= 100:
        # fully transparent - skip filling (matches solid path)
        return
    alpha_eff = ((100 - brush_transparency) / 100.0) * \
        ((100 - gradient_transparency) / 100.0)
    eff_transparency = (1.0 - alpha_eff) * 100

    # Get bounding rect of path for gradient coordinates
    bb = path.boundingRect()

    # Handle gradientCenterValue - map data value to gradient offset
    center_value = extbrush.get('gradientCenterValue')
    midpoint = config.midpoint  # visual midpoint override from GradientFill
    if center_value and center_value not in ('Auto', '', None):
        # Convert data value to plotter coordinate, then to 0-1 offset
        if axes is not None and fill_bounds is not None:
            yAxis = axes[1] if len(axes) > 1 else None
            xAxis = axes[0] if len(axes) > 0 else None
            if yAxis is not None:
                try:
                    val = float(center_value)
                    val_arr = yAxis.dataToPlotterCoords(fill_bounds, N.array([val]))
                    plotter_y = val_arr[0]
                    # Map plotter_y to 0-1 offset within fill_bounds
                    y1, y2 = fill_bounds[1], fill_bounds[3]
                    if y2 != y1:
                        midpoint = (plotter_y - y1) / (y2 - y1)
                        # Clamp to [0, 1]
                        midpoint = max(0.0, min(1.0, midpoint))
                except (ValueError, TypeError, AttributeError, IndexError):
                    pass  # fall back to config.midpoint or None

    # Create gradient based on configuration (composited transparency)
    qt_gradient = gradient_module.create_gradient_from_config(
        config, bb, transparency=eff_transparency, midpoint=midpoint)

    # Create brush with gradient
    brush = qt.QBrush(qt_gradient)

    # Apply fill
    if stroke is None:
        painter.fillPath(path, brush)
    else:
        painter.save()
        painter.setPen(stroke)
        painter.setBrush(brush)
        painter.drawPath(path)
        painter.restore()

def brushExtFillPath(painter, extbrush, path, ignorehide=False,
                     stroke=None, dataindex=0, axes=None, fill_bounds=None):
    """Use an BrushExtended settings object to fill a path on painter.
    If ignorehide is True, ignore the hide setting on the brush object.
    stroke is an optional QPen for stroking outline of path
    """

    if extbrush.hide and not ignorehide:
        if stroke is not None:
            painter.strokePath(path, stroke)
        return

    # Check for gradient fill - if enabled, use gradient rendering
    if gradient_module.is_gradient_enabled(extbrush.get('Gradient')):
        _brushExtFillPathGradient(painter, extbrush, path, stroke, dataindex, axes, fill_bounds)
        return

    style = extbrush.style
    if style in _fillcnvt:
        # standard fill: use Qt styles for painting
        color = extbrush.get('color').color(painter, dataindex=dataindex)
        if extbrush.transparency >= 0:
            if extbrush.transparency == 100:
                # skip filling fully transparent areas
                return
            color.setAlphaF((100-extbrush.transparency) / 100.)
        brush = qt.QBrush(color, _fillcnvt[style])
        if stroke is None:
            painter.fillPath(path, brush)
        else:
            painter.save()
            painter.setPen(stroke)
            painter.setBrush(brush)
            painter.drawPath(path)
            painter.restore()

    elif style in _hatchmap:
        # fill with hatching
        if not extbrush.backhide:
            # background brush
            color = extbrush.get('backcolor').color(
                painter, dataindex=dataindex)
            if extbrush.backtransparency > 0:
                color.setAlphaF((100-extbrush.backtransparency) / 100.)
            brush = qt.QBrush(color)
            painter.fillPath(path, brush)

        color = extbrush.get('color').color(painter, dataindex=dataindex)
        if extbrush.transparency >= 0:
            color.setAlphaF((100-extbrush.transparency) / 100.)
        width = extbrush.get('linewidth').convert(painter)
        lstyle, dashpattern = extbrush.get('linestyle')._linecnvt[
            extbrush.linestyle]
        pen = qt.QPen(color, width, lstyle)
        if dashpattern:
            pen.setDashPattern(dashpattern)

        # do hatching with spacing
        spacing = extbrush.get('patternspacing').convert(painter)
        if spacing > 0:
            _hatcher(painter, pen, path, spacing, _hatchmap[style])

        if stroke is not None:
            painter.strokePath(path, stroke)

def brushExtFillPolygon(painter, extbrush, cliprect, polygon, ignorehide=False):
    """Fill a polygon with an extended brush."""
    clipped = qt.QPolygonF()
    polygonClip(polygon, cliprect, clipped)
    path = qt.QPainterPath()
    path.addPolygon(clipped)
    brushExtFillPath(painter, extbrush, path, ignorehide=ignorehide)

def fillToEdgeTargets(pts, bounds, fillto, filltoValue=None, axes=None):
    """Return the two closing points (x1, y1, x2, y2) that fill a line to an edge.

    This is the single source of truth for fillto edge computation, shared by
    fillToEdgePolygon (polygon fills) and bezier/line fills in the widgets.

    Args:
        pts: QPolygonF of data points
        bounds: tuple (x1, y1, x2, y2) defining plot boundaries
        fillto: 'top', 'bottom', 'left', 'right', 'custom', 'mean' or 'auto'
        filltoValue: numeric value when fillto='custom', or None for default edge
        axes: (xAxis, yAxis) tuple for coordinate conversion, or None

    Returns:
        (x1, y1, x2, y2): the start-edge and end-edge closing points
    """
    x1, y1, x2, y2 = bounds

    # Determine the fill boundary y/x coordinate
    if fillto == 'mean':
        # fill to the mean of the plotted y values (plotter coords)
        if len(pts) > 0:
            fill_y = sum(p.y() for p in pts) / len(pts)
        else:
            fill_y = y2
        fill_x = None  # horizontal fill
    elif fillto == 'top':
        fill_y = y1
        fill_x = None  # horizontal fill
    elif fillto == 'bottom':
        fill_y = y2
        fill_x = None
    elif fillto == 'left':
        fill_x = x1
        fill_y = None  # vertical fill
    elif fillto == 'right':
        fill_x = x2
        fill_y = None
    elif fillto in ('custom', 'mean') or filltoValue is not None:
        # Use provided filltoValue (from 'mean' or 'custom') or explicit filltoValue
        if filltoValue is not None and filltoValue != 'Auto' and filltoValue != 'zero':
            if axes is not None:
                # Convert data value to plotter coordinates
                yAxis = axes[1] if len(axes) > 1 else None
                if yAxis is not None:
                    try:
                        val_arr = yAxis.dataToPlotterCoords(bounds, N.array([filltoValue]))
                        fill_y = val_arr[0]  # y-axis value in plotter coords
                        fill_x = None
                    except (AttributeError, TypeError, IndexError):
                        # Fallback to default edge
                        fill_y = y2
                        fill_x = None
                else:
                    # No axes available, use data value directly (assumes plotter coords)
                    fill_y = filltoValue
                    fill_x = None
            else:
                fill_y = filltoValue
                fill_x = None
        else:
            # 'Auto' or 'zero': fallback to bottom edge
            fill_y = y2
            fill_x = None
    else:
        # 'auto' (or unknown): fallback to bottom edge
        fill_y = y2
        fill_x = None

    if fill_x is not None:
        # Vertical fill (left/right)
        return (fill_x, pts[0].y(), fill_x, pts[-1].y())
    # Horizontal fill (top/bottom/custom)
    return (pts[0].x(), fill_y, pts[-1].x(), fill_y)


def fillToEdgePolygon(pts, bounds, fillto, filltoValue=None, axes=None):
    """Create a polygon that fills points to a boundary edge.

    Args:
        pts: QPolygonF of data points
        bounds: tuple (x1, y1, x2, y2) defining plot boundaries
        fillto: 'top', 'bottom', 'left', 'right', 'custom', 'mean'
        filltoValue: numeric value when fillto='custom', or None for default edge
        axes: (xAxis, yAxis) tuple for coordinate conversion, or None

    Returns:
        QPolygonF: polygon ready for filling (includes edge points)
    """
    x1, y1, x2, y2 = fillToEdgeTargets(pts, bounds, fillto, filltoValue, axes)

    # Build the polygon with fill boundary
    polypts = qt.QPolygonF()
    polypts.append(qt.QPointF(x1, y1))
    for pt in pts:
        polypts.append(pt)
    polypts.append(qt.QPointF(x2, y2))
    return polypts

    return polypts
