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

# default categorical palette, cycled across wedges
_CATEGORICAL = (
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
)


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

        s.add(setting.DistancePt(
            'markerSize', '5pt',
            descr=_('Base size of the largest glyph'),
            usertext=_('Glyph size')), 5)

        s.add(setting.Choice(
            'glyph', ('pie', 'donut', 'bar'), 'pie',
            descr=_('Glyph type: pie, donut (hollow centre) or bar'),
            usertext=_('Glyph')), 6)
        s.add(setting.Float(
            'innerRadius', 0.4, minval=0., maxval=0.95,
            descr=_('Donut inner radius as a fraction of the outer radius'),
            usertext=_('Donut inner radius')), 7)
        s.add(setting.Choice(
            'barDirection', ('horizontal', 'vertical'), 'horizontal',
            descr=_('Direction of the mini bar glyph'),
            usertext=_('Bar direction')), 8)

        s.add(setting.Bool(
            'outline', True,
            descr=_('Draw a border around the glyph'),
            usertext=_('Outline')), 9)

    def getRange(self, axis, depname, axrange):
        """Update axis range from x/y data."""
        dataname = {'sx': 'xData', 'sy': 'yData'}[depname]
        data = self.settings.get(dataname).getData(self.document)
        if data:
            data.updateRangeAuto(axrange, axis.settings.log)

    def requiresAxisRange(self):
        """The x and y axes need ranges from these datasets."""
        return (('sx', 'xData'), ('sy', 'yData'))

    def getNumberKeys(self):
        if self.settings.key:
            return 1
        return 0

    def getKeyText(self, number):
        return self.settings.key

    def drawKeySymbol(self, number, painter, x, y, width, height):
        """Draw a small pie as the key symbol."""
        s = self.settings
        wedges = self._getWedgeData()
        if wedges is None:
            return
        cx = x + width / 2
        cy = y + height / 2
        r = min(width, height) * 0.45
        self._drawGlyph(painter, cx, cy, r, wedges)

    def _getWedgeData(self):
        """Resolve wedge datasets into a list of numeric arrays (or None)."""
        names = list(self.settings.wedgeData)
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
        pen = qt.QPen(qt.QColor('#000000'), 0.5)
        if not s.outline:
            pen.setStyle(qt.Qt.PenStyle.NoPen)
        painter.setPen(pen)

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

    def _wedgeColors(self, n):
        """Return n distinct colours (cycled categorical palette)."""
        return [qt.QColor(_CATEGORICAL[i % len(_CATEGORICAL)])
                for i in range(n)]

    def _drawPieGlyph(self, painter, cx, cy, radius, vals):
        rect = qt.QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        start = 90 * 16  # 12 o'clock; Qt angles in 1/16 degree
        for color, v in zip(self._wedgeColors(len(vals)), vals):
            if not N.isfinite(v) or v == 0:
                continue
            span = int(-360.0 * abs(v) / total * 16)
            painter.setBrush(color)
            painter.drawPie(rect, start, span)
            start += span

    def _drawDonutGlyph(self, painter, cx, cy, radius, vals):
        outer = qt.QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        ir = radius * float(self.settings.innerRadius)
        inner = qt.QRectF(cx - ir, cy - ir, 2 * ir, 2 * ir)
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        start = 90 * 16
        for color, v in zip(self._wedgeColors(len(vals)), vals):
            if not N.isfinite(v) or v == 0:
                continue
            span = int(-360.0 * abs(v) / total * 16)
            path = qt.QPainterPath()
            path.arcTo(outer, start / 16.0, span / 16.0)
            path.arcTo(inner, (start + span) / 16.0, -span / 16.0)
            path.closeSubpath()
            painter.setBrush(color)
            painter.drawPath(path)
            start += span

    def _drawBarGlyph(self, painter, cx, cy, radius, vals):
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        horizontal = self.settings.barDirection == 'horizontal'
        size = radius * 2
        x0 = cx - size / 2
        y0 = cy - size / 2
        acc = 0.0
        for color, v in zip(self._wedgeColors(len(vals)), vals):
            if not N.isfinite(v) or v == 0:
                continue
            frac = abs(v) / total
            painter.setBrush(color)
            if horizontal:
                w = size * frac
                rect = qt.QRectF(x0 + acc, y0, w, size)
                acc += w
            else:
                h = size * frac
                rect = qt.QRectF(x0, y0 + acc, size, h)
                acc += h
            painter.drawRect(rect)


document.thefactory.register(ProportionalScatter)
