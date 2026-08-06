#    Copyright (C) 2026 Veusz Contributors
#
#    This file is part of Veusz.
#
#    Veusz is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
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
#
##############################################################################

"""Proportional scatter plot.

Draws each (x, y) point as a pie / donut / bar glyph showing the
proportion of several datasets (e.g. crop shares per site). Point size
is scaled so the glyph area is proportional to a dataset (usually the
total sample size), i.e. radius ~ sqrt(n).
"""

import numpy as N

from .. import qtall as qt
from .. import setting
from .. import document
from .. import utils
from . import plotters


def _(text, disambiguation=None, context='ProportionalScatter'):
    """Translate text."""
    return qt.QCoreApplication.translate(context, text, disambiguation)


class ProportionalScatter(plotters.GenericPlotter):
    """Plot proportional data as pie/donut/bar glyphs at each point."""

    typename = 'proportions'
    description = _('Proportional scatter (pie/donut/bar)')
    allowusercreation = True

    @classmethod
    def addSettings(klass, s):
        """Construct list of settings."""
        plotters.GenericPlotter.addSettings(s)

        s.add(setting.DatasetExtended(
            'xData', '',
            descr=_('Dataset or expression giving x positions'),
            usertext=_('X data')), 1)
        s.add(setting.DatasetExtended(
            'yData', '',
            descr=_('Dataset or expression giving y positions'),
            usertext=_('Y data')), 2)
        s.add(setting.DatasetExtended(
            'scalePoints', '',
            descr=_('Scale glyph area by dataset (radius ~ sqrt(value))'),
            usertext=_('Scale glyphs')), 3)
        s.add(setting.Datasets(
            'wedgeData', (),
            descr=_('Datasets giving the proportions of each slice'),
            usertext=_('Wedge data')), 4)
        s.add(setting.Strings(
            'wedgeLabels', (),
            descr=_('Labels for each wedge (empty = use dataset names)'),
            usertext=_('Wedge labels')), 5)
        s.add(setting.DatasetOrStr(
            'labels', '',
            descr=_('Dataset or string giving axis labels for each point. '
                    'Requires the corresponding axis to be in "labels" mode.'),
            usertext=_('Axis labels')), 6)

        s.add(setting.DistancePt(
            'markerSize', '5pt',
            descr=_('Base size of the largest glyph'),
            usertext=_('Glyph size')), 6)

        s.add(setting.Choice(
            'glyph', ('pie', 'donut', 'bar'), 'pie',
            descr=_('Glyph type: pie, donut (hollow centre) or bar'),
            usertext=_('Glyph')), 7)
        s.add(setting.Float(
            'innerRadius', 0.4, minval=0., maxval=0.95,
            descr=_('Donut inner radius as a fraction of the outer radius'),
            usertext=_('Donut inner radius')), 8)
        s.add(setting.Choice(
            'barDirection', ('horizontal', 'vertical'), 'horizontal',
            descr=_('Direction of the mini bar glyph (stacked mode)'),
            usertext=_('Bar direction')), 9)
        s.add(setting.Choice(
            'barMode', ('stacked', 'grouped'), 'stacked',
            descr=_('Bar glyph mode: stacked (segments in one bar) or '
                    'grouped (separate bars side by side)'),
            usertext=_('Bar mode')), 10)

        s.add(setting.Bool(
            'outline', True,
            descr=_('Draw a border around the glyph'),
            usertext=_('Outline')), 11)

        s.add(setting.FillSet(
            'Fill',
            [('solid', '#1f77b4', False), ('solid', '#ff7f0e', False),
             ('solid', '#2ca02c', False), ('solid', '#d62728', False),
             ('solid', '#9467bd', False), ('solid', '#8c564b', False),
             ('solid', '#e377c2', False), ('solid', '#7f7f7f', False),
             ('solid', '#bcbd22', False), ('solid', '#17becf', False)],
            descr=_('Fill styles per wedge (cycled)'),
            usertext=_('Fill styles')), 12)

        s.add(setting.Line(
            'Line',
            descr=_('Outline line for each wedge'),
            usertext=_('Outline line')), 13)

        s.add(setting.Bool(
            'wedgeLabelShow', False,
            descr=_('Show wedge labels'),
            usertext=_('Show labels')), 14)

        s.add(setting.Choice(
            'labelPosnHorz', ('left', 'centre', 'right'), 'centre',
            descr=_('Horizontal alignment of wedge labels'),
            usertext=_('Label align horiz')), 15)

        s.add(setting.Choice(
            'labelPosnVert', ('top', 'centre', 'bottom'), 'centre',
            descr=_('Vertical alignment of wedge labels'),
            usertext=_('Label align vert')), 16)

        s.add(setting.Text(
            'Font',
            descr=_('Font for wedge labels'),
            usertext=_('Label font')), 17)

    def affectsAxisRange(self):
        """This widget provides range information about these axes."""
        s = self.settings
        return ((s.xAxis, 'sx'), (s.yAxis, 'sy'))

    def getRange(self, axis, depname, axrange):
        """Update axis range from x/y data."""
        dataname = {'sx': 'xData', 'sy': 'yData'}[depname]
        data = self.settings.get(dataname).getData(self.document)
        if data:
            data.updateRangeAuto(axrange, axis.settings.log)

    def getAxisLabels(self, direction):
        """Provide text labels for categorical axis (mode='labels')."""
        s = self.settings
        text = s.get('labels').getData(self.document, checknull=True)
        xv = s.get('xData').getData(self.document)
        yv = s.get('yData').getData(self.document)
        if text is None:
            return (None, None)
        if direction == 'horizontal' and xv is not None:
            return (text, xv.data)
        elif direction == 'vertical' and yv is not None:
            return (text, yv.data)
        return (None, None)

    def _wedgeNames(self):
        """Return the list of non-empty wedge dataset names."""
        return [n for n in self.settings.wedgeData if n]

    def _wedgeLabel(self, idx):
        """Return the label for wedge index idx."""
        labels = self.settings.wedgeLabels
        if idx < len(labels) and labels[idx]:
            return labels[idx]
        names = self._wedgeNames()
        if idx < len(names):
            return names[idx]
        return ''

    def getNumberKeys(self):
        if self.settings.key:
            return len(self._wedgeNames()) or 1
        return 0

    def getKeyText(self, number):
        return self._wedgeLabel(number)

    def drawKeySymbol(self, number, painter, x, y, width, height):
        """Draw a small colored swatch for one wedge in the key."""
        n = len(self._wedgeNames())
        if number >= n:
            return
        swatch = qt.QRectF(x, y + height * 0.1, width, height * 0.8)
        path = qt.QPainterPath()
        path.addRect(swatch)
        self._fillWedge(painter, number, path)

    def _getWedgeData(self):
        """Resolve wedge datasets into a list of numeric arrays (or None).

        Filters out empty-name entries so that a Datasets control that
        contains a trailing empty string does not crash.
        """
        names = self._wedgeNames()
        if not names:
            return None
        out = []
        for name in names:
            ds = self.document.getData(name)
            if ds is None or ds.data is None:
                return None
            out.append(N.asarray(ds.data, dtype=float))
        return out

    def _getRadii(self, npts, markersize):
        """Per-point radii, area proportional to scalePoints (radius~sqrt)."""
        s = self.settings
        scalev = s.get('scalePoints').getData(self.document)
        if scalev is not None and scalev.data is not None:
            scales = N.asarray(scalev.data, dtype=float)[:npts]
            smax = N.nanmax(scales) if len(scales) else 0.0
            if smax > 0:
                radii = markersize * N.sqrt(N.abs(scales)) / N.sqrt(smax)
                return N.where(N.isfinite(radii), radii, markersize)
        return N.full(npts, markersize)

    def dataDraw(self, painter, axes, posn, cliprect):
        """Plot the proportional glyphs."""
        s = self.settings
        d = self.document

        xv = s.get('xData').getData(d)
        yv = s.get('yData').getData(d)
        if xv is None or yv is None or xv.data is None or yv.data is None:
            return
        npts = min(len(xv.data), len(yv.data))
        if npts == 0:
            return

        wedges = self._getWedgeData()
        if wedges is None:
            return

        xplt = axes[0].dataToPlotterCoords(posn, xv.data[:npts])
        yplt = axes[1].dataToPlotterCoords(posn, yv.data[:npts])
        markersize = s.get('markerSize').convert(painter)
        radii = self._getRadii(npts, markersize)

        painter.save()

        for i in range(npts):
            vals = [w[i] if i < len(w) else N.nan for w in wedges]
            if not N.any(N.isfinite(vals)):
                continue
            self._drawGlyph(painter, xplt[i], yplt[i], radii[i], vals)

        painter.restore()

    def _drawGlyph(self, painter, cx, cy, radius, vals):
        """Draw one glyph (pie/donut/bar) centred at (cx, cy)."""
        glyph = self.settings.glyph
        if glyph == 'bar':
            self._drawBarGlyph(painter, cx, cy, radius, vals)
        elif glyph == 'donut':
            self._drawDonutGlyph(painter, cx, cy, radius, vals)
        else:
            self._drawPieGlyph(painter, cx, cy, radius, vals)

    def _wedgeBrush(self, idx):
        """Return the BrushExtended fill for wedge idx (cycles)."""
        return self.settings.get('Fill').returnBrushExtended(idx)

    def _outlinePen(self, painter):
        """QPen for glyph outline (NoPen when hidden)."""
        try:
            return self.settings.Line.makeQPenWHide(painter)
        except setting.ReferenceBase.ResolveException:
            # fall back when not attached to a document tree
            return qt.QPen(qt.QColor('#000000'), 0.5)

    def _fillWedge(self, painter, idx, path):
        """Fill a wedge path with its brush and outline.

        Uses brushExtFillPath when the painter supports docColor (Veusz
        Painter) so gradients/hatching work; falls back to a plain solid
        fill for bare QPainter instances (e.g. unit tests).
        """
        pen = self._outlinePen(painter)
        if hasattr(painter, 'docColor'):
            utils.brushExtFillPath(painter, self._wedgeBrush(idx), path,
                                   stroke=pen)
        else:
            brush = self._wedgeBrush(idx)
            color = qt.QColor(brush.get('color').val)
            if brush.transparency > 0:
                color.setAlphaF((100 - brush.transparency) / 100.)
            painter.setBrush(color)
            painter.setPen(pen)
            painter.drawPath(path)

    def _renderLabel(self, painter, x, y, label):
        """Render a wedge/bar label at (x, y) with the Font settings."""
        pen = self.settings.Font.makeQPen(painter)
        painter.setPen(pen)
        font = self.settings.Font.makeQFont(painter)
        ah = {'left': 1, 'centre': 0, 'right': -1}[self.settings.labelPosnHorz]
        av = {'top': -1, 'centre': 0, 'bottom': 1}[self.settings.labelPosnVert]
        utils.Renderer(painter, font, x, y, label, ah, av, 0.0,
                       doc=self.document).render()

    def _drawWedgeLabel(self, painter, cx, cy, radius, inner_frac,
                        start16, span16, idx):
        """Render the label for a pie/donut wedge at its sector centroid."""
        label = self._wedgeLabel(idx)
        if not (self.settings.wedgeLabelShow and label):
            return
        painter.save()
        try:
            delta = abs(span16 / 16.0) * N.pi / 180.0
            mid = (start16 + span16 / 2.0) / 16.0 * N.pi / 180.0
            ro = radius
            ri = radius * float(inner_frac)
            if delta < 1e-9 or not N.isfinite(delta):
                return
            if ro > ri:
                factor = (ro ** 3 - ri ** 3) / (ro ** 2 - ri ** 2)
            else:
                factor = ro
            rcen = (2.0 / 3.0) * factor * (N.sin(delta / 2.0) / (delta / 2.0))
            lx = cx + rcen * N.cos(mid)
            ly = cy - rcen * N.sin(mid)
            self._renderLabel(painter, lx, ly, label)
        finally:
            painter.restore()

    def _drawBarLabel(self, painter, rect, label):
        """Draw a label centred in a bar segment rectangle."""
        if not (self.settings.wedgeLabelShow and label):
            return
        painter.save()
        try:
            self._renderLabel(painter, rect.center().x(), rect.center().y(), label)
        finally:
            painter.restore()

    def _drawBarGlyph(self, painter, cx, cy, radius, vals):
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        horizontal = self.settings.barDirection == 'horizontal'
        grouped = self.settings.barMode == 'grouped'
        size = radius * 2
        n = len(vals)

        if horizontal:
            # Horizontal bars (stacked or grouped)
            if grouped:
                bar_h = size / max(1, n)
                y0 = cy - size / 2
                for idx, v in enumerate(vals):
                    if not N.isfinite(v) or v == 0:
                        continue
                    frac = abs(v) / total
                    w = size * frac
                    rect = qt.QRectF(cx - w / 2, y0 + idx * bar_h, w, bar_h)
                    path = qt.QPainterPath()
                    path.addRect(rect)
                    self._fillWedge(painter, idx, path)
                    self._drawBarLabel(painter, rect, self._wedgeLabel(idx))
            else:
                # Stacked horizontal
                x0 = cx - size / 2
                y0 = cy - size / 2
                acc = 0.0
                for idx, v in enumerate(vals):
                    if not N.isfinite(v) or v == 0:
                        continue
                    frac = abs(v) / total
                    w = size * frac
                    rect = qt.QRectF(x0 + acc, y0, w, size)
                    path = qt.QPainterPath()
                    path.addRect(rect)
                    self._fillWedge(painter, idx, path)
                    self._drawBarLabel(painter, rect, self._wedgeLabel(idx))
                    acc += w
        else:
            # Vertical bars (stacked or grouped)
            if grouped:
                bar_w = size / max(1, n)
                x0 = cx - size / 2
                for idx, v in enumerate(vals):
                    if not N.isfinite(v) or v == 0:
                        continue
                    frac = abs(v) / total
                    h = size * frac
                    rect = qt.QRectF(x0 + idx * bar_w, cy - h / 2, bar_w, h)
                    path = qt.QPainterPath()
                    path.addRect(rect)
                    self._fillWedge(painter, idx, path)
                    self._drawBarLabel(painter, rect, self._wedgeLabel(idx))
            else:
                # Stacked vertical
                x0 = cx - size / 2
                y0 = cy - size / 2
                acc = 0.0
                for idx, v in enumerate(vals):
                    if not N.isfinite(v) or v == 0:
                        continue
                    frac = abs(v) / total
                    h = size * frac
                    rect = qt.QRectF(x0, y0 + acc, size, h)
                    path = qt.QPainterPath()
                    path.addRect(rect)
                    self._fillWedge(painter, idx, path)
                    self._drawBarLabel(painter, rect, self._wedgeLabel(idx))
                    acc += h

    def _drawPieGlyph(self, painter, cx, cy, radius, vals):
        """Draw a pie glyph (full circle slices)."""
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        start16 = 90 * 16  # Qt starts at 3 o'clock; 90° = 12 o'clock
        for idx, v in enumerate(vals):
            if not N.isfinite(v) or v == 0:
                continue
            frac = abs(v) / total
            span16 = int(-frac * 360 * 16)  # negative = clockwise
            rect = qt.QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            path = qt.QPainterPath()
            path.moveTo(cx, cy)
            path.arcTo(rect, start16 / 16.0, span16 / 16.0)
            path.lineTo(cx, cy)
            self._fillWedge(painter, idx, path)
            self._drawWedgeLabel(painter, cx, cy, radius, 0.0, start16, span16, idx)
            start16 += span16

    def _drawDonutGlyph(self, painter, cx, cy, radius, vals):
        """Draw a donut glyph (pie with hollow centre)."""
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        inner_frac = self.settings.innerRadius
        inner_r = radius * inner_frac
        start16 = 90 * 16
        for idx, v in enumerate(vals):
            if not N.isfinite(v) or v == 0:
                continue
            frac = abs(v) / total
            span16 = int(-frac * 360 * 16)
            outer_rect = qt.QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            inner_rect = qt.QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
            path = qt.QPainterPath()
            path.arcMoveTo(outer_rect, start16 / 16.0)
            path.arcTo(outer_rect, start16 / 16.0, span16 / 16.0)
            path.arcTo(inner_rect, (start16 + span16) / 16.0, -span16 / 16.0)
            path.closeSubpath()
            self._fillWedge(painter, idx, path)
            self._drawWedgeLabel(painter, cx, cy, radius, inner_frac,
                                 start16, span16, idx)
            start16 += span16


document.thefactory.register(ProportionalScatter)
