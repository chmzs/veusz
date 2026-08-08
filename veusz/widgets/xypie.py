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

"""XY pie scatter plot.

Draws each (x, y) point as a pie / donut / bar shape showing the
proportion of several datasets (e.g. crop shares per site). Point size
is scaled so the shape area is proportional to a dataset (usually the
total sample size), i.e. radius ~ sqrt(n).
"""

import numpy as N

from .. import qtall as qt
from .. import setting
from .. import document
from .. import utils
from . import plotters


def _(text, disambiguation=None, context="XY"):
    """Translate text."""
    return qt.QCoreApplication.translate(context, text, disambiguation)


def _shapeShowfn(val):
    """Show/hide shape-specific settings based on the Shape choice.

    Return (show, hide) lists of setting names, following the
    ChoiceSwitch showfn convention. Error-bar / CI settings only apply
    to the bar shape, so they hide for pie and donut.
    """
    bar_show = [
        "barMode",
        "barDirection",
        "barfill",
        "groupfill",
        "errorstyle",
        "ciMode",
        "ciYMin",
        "ciYMax",
        "ciYError",
        "ciMultiplier",
    ]
    if val == "donut":
        return (("innerRadius",), bar_show)
    if val == "bar":
        return (bar_show, ("innerRadius",))
    return ((), bar_show + ["innerRadius"])


def _ciModeShowfn(val):
    """Show/hide CI error-source settings based on ciMode value."""
    if val == "custom":
        return (("ciYMin", "ciYMax"), ("ciYError", "ciMultiplier"))
    elif val == "std":
        return (("ciYError", "ciMultiplier"), ("ciYMin", "ciYMax"))
    else:
        return ((), ("ciYMin", "ciYMax", "ciYError", "ciMultiplier"))


class SliceFill(setting.Settings):
    """Fill of each slice (cycled per slice)."""

    def __init__(self, name, **args):
        setting.Settings.__init__(self, name, **args)
        self.add(
            setting.FillSet(
                "fills",
                [("solid", "auto", False)],
                descr=_("Fill styles for slices (cycled)"),
                usertext=_("Slice fill"),
            )
        )


class SliceLine(setting.Settings):
    """Outline line for each slice (cycled)."""

    def __init__(self, name, **args):
        setting.Settings.__init__(self, name, **args)
        self.add(
            setting.LineSet(
                "lines",
                [("solid", "0.5pt", "black", False)],
                descr=_("Outline lines for slices (cycled)"),
                usertext=_("Outline line"),
            )
        )


class SliceLabel(setting.PointLabel):
    """Per-slice / per-point label settings plus an extra offset."""

    def __init__(self, name, **args):
        setting.PointLabel.__init__(self, name, **args)
        self.add(
            setting.DistancePt(
                "labelOffset",
                "0pt",
                descr=_("Extra label offset from the shape edge"),
                usertext=_("Label offset"),
            ),
            0,
        )


class XYPie(plotters.GenericPlotter):
    """Plot proportional data as pie/donut/bar shapes at each point."""

    typename = "xypie"
    description = _("X/Y pie scatter (pie/donut/bar)")
    allowusercreation = True

    @classmethod
    def addSettings(klass, s):
        """Construct list of settings."""
        plotters.GenericPlotter.addSettings(s)

        # --- properties: data ---
        s.add(
            setting.DatasetExtended(
                "xData",
                "",
                descr=_("Dataset or expression giving x positions"),
                usertext=_("X data"),
            ),
            0,
        )
        s.add(
            setting.DatasetExtended(
                "yData",
                "",
                descr=_("Dataset or expression giving y positions"),
                usertext=_("Y data"),
            ),
            1,
        )
        s.add(
            setting.DatasetExtended(
                "scalePoints",
                "",
                descr=_(
                    "Dataset giving total sample size per point "
                    "(shape area scales with it)"
                ),
                usertext=_("Scale shapes"),
            ),
            2,
        )
        s.add(
            setting.Datasets(
                "sliceData",
                ("",),
                descr=_("Datasets giving the proportions of each slice"),
                usertext=_("Slice data"),
            ),
            3,
        )
        s.add(
            setting.Strings(
                "sliceKeyTexts",
                ("",),
                descr=_("Key text for each slice (empty = use dataset names)"),
                usertext=_("Slice key text"),
            ),
            4,
        )
        s.add(
            setting.DatasetOrStr(
                "axisLabels",
                "",
                descr=_(
                    "Dataset or string giving text labels for axis tick labels. "
                    'Requires the corresponding axis to be in "labels" mode.'
                ),
                usertext=_("Axis labels"),
            ),
            5,
        )
        s.add(
            setting.DatasetOrStr(
                "labels",
                "",
                descr=_("Dataset or string giving text to label each point"),
                usertext=_("Labels"),
            ),
            6,
        )

        # remove single key text from base class; use per-slice key texts
        s.remove("key")

        # --- format main: shape structure ---
        s.add(
            setting.ChoiceSwitch(
                "shape",
                ("pie", "donut", "bar"),
                "pie",
                showfn=_shapeShowfn,
                descr=_("Shape to draw at each point"),
                usertext=_("Shape"),
                formatting=True,
            ),
            0,
        )
        s.add(
            setting.Float(
                "innerRadius",
                0.4,
                minval=0.0,
                maxval=0.95,
                descr=_("Donut inner radius as a fraction of the outer radius"),
                usertext=_("Donut inner radius"),
                formatting=True,
            ),
            1,
        )
        s.add(
            setting.Choice(
                "barMode",
                ("grouped", "stacked"),
                "grouped",
                descr=_(
                    "Bar mode: grouped (separate bars) or stacked (segments in one bar)"
                ),
                usertext=_("Mode"),
                formatting=True,
            ),
            2,
        )
        s.add(
            setting.Choice(
                "barDirection",
                ("vertical", "horizontal"),
                "vertical",
                descr=_("Direction of the mini bar shape"),
                usertext=_("Direction"),
                formatting=True,
            ),
            3,
        )
        s.add(
            setting.Float(
                "barfill",
                0.75,
                minval=0.0,
                maxval=1.0,
                descr=_("Filling fraction of each bar (between 0 and 1)"),
                usertext=_("Bar fill"),
                formatting=True,
            ),
            4,
        )
        s.add(
            setting.Float(
                "groupfill",
                0.9,
                minval=0.0,
                maxval=1.0,
                descr=_("Filling fraction of the group of bars (between 0 and 1)"),
                usertext=_("Group fill"),
                formatting=True,
            ),
            5,
        )
        s.add(
            setting.DistancePt(
                "shapeSize",
                "5pt",
                descr=_("Base size of the largest shape"),
                usertext=_("Shape size"),
                formatting=True,
            ),
            11,
        )
        s.add(
            setting.Choice(
                "errorstyle",
                ("none", "bar", "barends"),
                "bar",
                descr=_("Error bar style to show on bar shapes"),
                usertext=_("Error style"),
                formatting=True,
            ),
            12,
        )

        # CI mode: choose the error source for each slice's error bar
        s.add(
            setting.ChoiceSwitch(
                "ciMode",
                ["", "custom", "std"],
                "",
                showfn=_ciModeShowfn,
                descr=_("Confidence interval mode for slice error bars"),
                usertext=_("CI mode"),
                formatting=True,
            ),
            13,
        )
        s.add(
            setting.Datasets(
                "ciYMin",
                ("",),
                descr=_("Datasets for minimum y of each slice's error bar"),
                usertext=_("CI Y min"),
                formatting=True,
            ),
            14,
        )
        s.add(
            setting.Datasets(
                "ciYMax",
                ("",),
                descr=_("Datasets for maximum y of each slice's error bar"),
                usertext=_("CI Y max"),
                formatting=True,
            ),
            15,
        )
        s.add(
            setting.Datasets(
                "ciYError",
                ("",),
                descr=_(
                    "Datasets for y error of each slice (y +/- error * multiplier)"
                ),
                usertext=_("CI Y error"),
                formatting=True,
            ),
            16,
        )
        s.add(
            setting.Float(
                "ciMultiplier",
                1.0,
                descr=_("Multiplier for error values (e.g. 2 for 2*std)"),
                usertext=_("CI multiplier"),
                formatting=True,
            ),
            17,
        )

        # --- format pages: fill, line, label, error bars ---
        s.add(
            SliceFill("Fill", descr=_("Fill of each slice"), usertext=_("Fill")),
            pixmap="settings_bgfill",
        )
        s.add(
            SliceLine("Line", descr=_("Outline lines"), usertext=_("Line")),
            pixmap="settings_border",
        )
        s.add(
            SliceLabel("Label", descr=_("Point labels"), usertext=_("Label")),
            pixmap="settings_axislabel",
        )
        s.add(
            setting.ErrorBarLine(
                "ErrorBarLine",
                descr=_("Error bar line settings"),
                usertext=_("Error bar line"),
            ),
            pixmap="settings_ploterrorline",
        )

    def affectsAxisRange(self):
        """This widget provides range information about these axes."""
        s = self.settings
        return ((s.xAxis, "sx"), (s.yAxis, "sy"))

    def getRange(self, axis, depname, axrange):
        """Update axis range from x/y data."""
        dataname = {"sx": "xData", "sy": "yData"}[depname]
        data = self.settings.get(dataname).getData(self.document)
        if data:
            data.updateRangeAuto(axrange, axis.settings.log)

    def getAxisLabels(self, direction):
        """Provide text labels for categorical axis (mode='labels')."""
        s = self.settings
        text = s.get("axisLabels").getData(self.document, checknull=True)
        xv = s.get("xData").getData(self.document)
        yv = s.get("yData").getData(self.document)
        if text is None:
            return (None, None)
        if direction == "horizontal" and xv is not None:
            return (text, xv.data)
        elif direction == "vertical" and yv is not None:
            return (text, yv.data)
        return (None, None)

    def _sliceNames(self):
        """Return the list of non-empty slice dataset names."""
        return [n for n in self.settings.get("sliceData").val if n]

    def _sliceKeyText(self, idx):
        """Return the key text for slice idx (falls back to dataset name)."""
        keys = self.settings.get("sliceKeyTexts").val
        if idx < len(keys) and keys[idx]:
            return keys[idx]
        names = self._sliceNames()
        if idx < len(names):
            return names[idx]
        return ""

    def getNumberKeys(self):
        """Key shows one entry per slice."""
        return len(self._sliceNames())

    def getKeyText(self, number):
        """Return key entry text for the slice index given."""
        return self._sliceKeyText(number)

    def drawKeySymbol(self, number, painter, x, y, width, height):
        """Draw a small colored swatch for one slice in the key."""
        n = len(self._sliceNames())
        if number >= n:
            return
        swatch = qt.QRectF(x, y + height * 0.1, width, height * 0.8)
        path = qt.QPainterPath()
        path.addRect(swatch)
        self._fillSlice(painter, number, path, dataindex=number)

    def _getSliceData(self):
        """Resolve slice datasets into a list of numeric arrays (or None).

        Missing or empty-name datasets are skipped silently; None is only
        returned when every slice dataset is missing or empty.
        """
        names = self._sliceNames()
        if not names:
            return None
        out = []
        for name in names:
            ds = self.document.getData(name)
            if ds is None or ds.data is None:
                continue
            out.append((name, N.asarray(ds.data, dtype=float), ds))
        return out or None

    def _getRadii(self, npts, shapesize):
        """Per-point radii, area proportional to scalePoints (radius~sqrt)."""
        s = self.settings
        scalev = s.get("scalePoints").getData(self.document)
        if scalev is not None and scalev.data is not None and len(scalev.data) > 0:
            scales = N.asarray(scalev.data, dtype=float)[:npts]
            if len(scales) < npts:
                scales = N.concatenate([scales, N.full(npts - len(scales), N.nan)])
            smax = N.nanmax(scales) if len(scales) else 0.0
            if smax > 0:
                radii = shapesize * N.sqrt(N.abs(scales)) / N.sqrt(smax)
                return N.where(N.isfinite(radii), radii, shapesize)
        return N.full(npts, shapesize)

    def dataDraw(self, painter, axes, posn, cliprect):
        """Plot the shapes."""
        s = self.settings
        d = self.document

        xv = s.get("xData").getData(d)
        yv = s.get("yData").getData(d)
        if xv is None or yv is None or xv.data is None or yv.data is None:
            return
        npts = min(len(xv.data), len(yv.data))
        if npts == 0:
            return

        slices = self._getSliceData()
        if slices is None:
            return

        xplt = axes[0].dataToPlotterCoords(posn, xv.data[:npts])
        yplt = axes[1].dataToPlotterCoords(posn, yv.data[:npts])
        shapesize = s.get("shapeSize").convert(painter)
        radii = self._getRadii(npts, shapesize)

        painter.save()

        for i in range(npts):
            # slice values in plotter coords for this point
            vals = [
                dataslice[i] if i < len(dataslice) else N.nan
                for _, dataslice, _ in slices
            ]
            if not N.any(N.isfinite(vals)):
                continue
            self._drawShape(
                painter, xplt[i], yplt[i], radii[i], vals, slices, i, axes, posn
            )

        # per-point labels (independent content) drawn beside each shape
        textvals = s.get("labels").getData(d, checknull=True)
        if textvals:
            self._drawLabels(painter, xplt, yplt, textvals, shapesize, radii)

        painter.restore()

    def _drawShape(
        self, painter, cx, cy, radius, vals, slices, pointidx, axes, widgetposn
    ):
        """Draw one shape (pie/donut/bar) centred at (cx, cy)."""
        shape = self.settings.get("shape").val
        if shape == "bar":
            self._drawBar(
                painter, cx, cy, radius, vals, slices, pointidx, axes, widgetposn
            )
        elif shape == "donut":
            self._drawDonut(painter, cx, cy, radius, vals)
        else:
            self._drawPie(painter, cx, cy, radius, vals)

    def _sliceBrush(self, idx):
        """Return the BrushExtended fill for slice idx (cycles)."""
        return self.settings.get("Fill").get("fills").returnBrushExtended(idx)

    def _outlinePen(self, painter, idx):
        """QPen for slice outline (per-slice LineSet)."""
        return self.settings.get("Line").get("lines").makePen(painter, idx)

    def _fillSlice(self, painter, idx, path, dataindex=0):
        """Fill a slice path with its brush and outline.

        Uses brushExtFillPath when the painter supports docColor (Veusz
        Painter) so gradients / 'auto' colouring work; falls back to a
        plain solid fill for bare QPainter instances (unit tests).
        """
        try:
            pen = self._outlinePen(painter, idx)
        except (setting.ReferenceBase.ResolveException, AttributeError):
            pen = qt.QPen(qt.QColor("#000000"), 0.5)
        if hasattr(painter, "docColor"):
            utils.brushExtFillPath(
                painter, self._sliceBrush(idx), path, stroke=pen, dataindex=dataindex
            )
        else:
            brush = self._sliceBrush(idx)
            color = qt.QColor(brush.get("color").val)
            if brush.transparency > 0:
                color.setAlphaF((100 - brush.transparency) / 100.0)
            painter.setBrush(color)
            painter.setPen(pen)
            painter.drawPath(path)

    def _drawLabels(self, painter, xplotter, yplotter, textvals, shapesize, radius):
        """Draw per-point labels around each shape (port of point.drawLabels)."""
        s = self.settings
        lab = s.get("Label")
        if lab.hide:
            return

        labeloffset = lab.get("labelOffset").convert(painter)
        offset = shapesize * 1.5 + labeloffset

        deltax = offset * {"left": -1, "centre": 0, "right": 1}[lab.posnHorz]
        deltay = offset * {"top": -1, "centre": 0, "bottom": 1}[lab.posnVert]
        alignhorz = {"left": 1, "centre": 0, "right": -1}[lab.posnHorz]
        alignvert = {"top": -1, "centre": 0, "bottom": 1}[lab.posnVert]

        textpen = lab.makeQPen(painter)
        painter.setPen(textpen)
        font = lab.makeQFont(painter)
        angle = lab.angle

        for x, y, t in zip(xplotter + deltax, yplotter + deltay, textvals):
            utils.Renderer(
                painter, font, x, y, t, alignhorz, alignvert, angle, doc=self.document
            ).render()

    def _drawBar(self, painter, cx, cy, radius, vals, slices, i, axes, widgetposn):
        """Draw mini bars (one per slice), grouped or stacked.

        In grouped mode bars are aligned to the baseline (cy for vertical
        bars, cx for horizontal). barfill/groupfill control bar thickness.
        """
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        s = self.settings
        size = radius * 2
        n = len(vals)
        ishorz = s.get("barDirection").val == "horizontal"
        grouped = s.get("barMode").val == "grouped"
        barfill = s.get("barfill").val
        groupfill = s.get("groupfill").val

        # usable extent perpendicular to bars / along the bars
        groupsize = size * groupfill
        barthick = (size / max(1, n)) * barfill

        if grouped:
            # bars side by side, baseline-aligned, thickness = barfill of slot
            for idx, v in enumerate(vals):
                if not N.isfinite(v) or v == 0:
                    continue
                frac = float(abs(v)) / total
                if ishorz:
                    # horizontal bars: extend right from the centre-left line
                    y0 = cy - groupsize / 2 + idx * (groupsize / n)
                    rect = qt.QRectF(cx - size / 2, y0, size * frac, barthick)
                else:
                    # vertical bars: extend upward from the baseline (cy)
                    x0 = cx - groupsize / 2 + idx * (groupsize / n)
                    rect = qt.QRectF(x0, cy - size * frac, barthick, size * frac)
                path = qt.QPainterPath()
                path.addRect(rect)
                self._fillSlice(painter, idx, path, dataindex=idx)
        else:
            # stacked bars: segments laid end-to-end along one length
            posn = -size / 2
            for idx, v in enumerate(vals):
                if not N.isfinite(v) or v == 0:
                    continue
                frac = float(abs(v)) / total
                if ishorz:
                    # horizontal segments stacked from the left centre
                    rect = qt.QRectF(
                        cx - size / 2 + posn, cy - barthick / 2, size * frac, barthick
                    )
                else:
                    rect = qt.QRectF(
                        cx - barthick / 2, cy + posn, barthick, size * frac
                    )
                path = qt.QPainterPath()
                path.addRect(rect)
                self._fillSlice(painter, idx, path, dataindex=idx)
                posn += size * frac

        # per-slice error bars (each slice dataset has its own error)
        if s.get("errorstyle").val != "none":
            self._drawBarErrorBars(painter, cx, cy, radius, vals, slices, i, n, total)

    def _sliceMediaDataset(self, setting, sliceidx, ptidx):
        """Return the value at ptidx of sliceidx-th dataset in a Datasets setting.

        Returns None if the dataset is missing or the index is out of range.
        """
        names = [n for n in setting.val if n]
        if not (0 <= sliceidx < len(names)):
            return None
        ds = self.document.getData(names[sliceidx])
        if ds is None or ds.data is None:
            return None
        if not (0 <= ptidx < len(ds.data)):
            return None
        return float(ds.data[ptidx])

    def _drawBarErrorBars(self, painter, cx, cy, radius, vals, slices, i, n, total):
        """Draw one error bar per slice on bar shapes.

        Each slice dataset supplies its own perr/nerr/serr error columns;
        the error bar sits on top of that slice's bar.
        """
        s = self.settings
        ishorz = s.get("barDirection").val == "horizontal"
        grouped = s.get("barMode").val == "grouped"
        ebl = s.get("ErrorBarLine")
        try:
            pen = ebl.makeQPenWHide(painter)
        except (setting.ReferenceBase.ResolveException, AttributeError):
            # not attached to a document tree (unit tests): no error bars
            return
        painter.setPen(pen)
        size = radius * 2
        groupfill = s.get("groupfill").val
        barfill = s.get("barfill").val
        style = s.get("errorstyle").val
        ends = style == "barends"
        w = ebl.endsize

        for idx, (_name, _data, ds) in enumerate(slices):
            if idx >= len(vals):
                break
            if not N.isfinite(vals[idx]) or vals[idx] == 0:
                continue
            frac = float(abs(vals[idx])) / total if total else 0.0
            # error source depends on ciMode; each slice gets its own
            err_low = err_high = 0.0
            ci = s.get("ciMode").val
            if ci == "custom":
                # use explicit per-slice min/max datasets
                mn = self._sliceMediaDataset(s.get("ciYMin"), idx, i)
                mx = self._sliceMediaDataset(s.get("ciYMax"), idx, i)
                if mn is not None:
                    err_low = (
                        max(0.0, abs(vals[idx]) * (1 - mn / vals[idx]))
                        if vals[idx]
                        else 0.0
                    )
                if mx is not None:
                    err_high = max(0.0, (mx - vals[idx])) if vals[idx] else 0.0
            elif ci == "std":
                # std mode: y +/- error * multiplier
                err = self._sliceMediaDataset(s.get("ciYError"), idx, i)
                if err is not None:
                    mult = s.get("ciMultiplier").val
                    err_low = err_high = abs(err) * mult
            else:
                # default: use the slice dataset's own error columns
                if ds.serr is not None:
                    err = float(ds.serr[i]) if i < len(ds.serr) else 0.0
                    err_low = err_high = err
                else:
                    if ds.nerr is not None:
                        err_low = float(ds.nerr[i]) if i < len(ds.nerr) else 0.0
                    if ds.perr is not None:
                        err_high = float(ds.perr[i]) if i < len(ds.perr) else 0.0
            lowfrac = err_low / total if total else 0.0
            highfrac = err_high / total if total else 0.0

            # perpendicular position of this bar (x for vertical bars,
            # y for horizontal bars). grouped bars sit in slots of width
            # size*groupfill/n (matches _drawBar), centred in each slot.
            if grouped:
                groupsize = size * groupfill
                slot = groupsize / max(1, n)
                barthick = (size / max(1, n)) * barfill
                base = cx if not ishorz else cy
                # bars are left-aligned in their slots with width barthick;
                # put the error bar on the bar centre (slot centre would be
                # offset towards the right whenever barfill < 1)
                barpos = base - groupsize / 2 + idx * slot + barthick / 2
            else:
                # stacked bars occupy the whole extent, centred
                barpos = cx if not ishorz else cy

            if ishorz:
                # horizontal: error along the value (x) axis from the bar tip
                xb = cx - size / 2 + size * frac
                y = barpos
                x_high = xb + size * highfrac
                x_low = xb - size * lowfrac
                painter.drawLine(qt.QPointF(x_low, y), qt.QPointF(x_high, y))
                if ends:
                    painter.drawLine(
                        qt.QPointF(x_high, y - w), qt.QPointF(x_high, y + w)
                    )
                    painter.drawLine(qt.QPointF(x_low, y - w), qt.QPointF(x_low, y + w))
            else:
                # vertical: error above the bar tip
                x = barpos
                yb = cy - size * frac  # bar tip (value end)
                y_high = yb - size * highfrac
                y_low = yb + size * lowfrac
                painter.drawLine(qt.QPointF(x, y_low), qt.QPointF(x, y_high))
                if ends:
                    painter.drawLine(
                        qt.QPointF(x - w, y_high), qt.QPointF(x + w, y_high)
                    )
                    painter.drawLine(qt.QPointF(x - w, y_low), qt.QPointF(x + w, y_low))

    def _drawPie(self, painter, cx, cy, radius, vals):
        """Draw a pie shape (full circle slices)."""
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        start16 = 90 * 16  # Qt starts at 3 o'clock; 90deg = 12 o'clock
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
            self._fillSlice(painter, idx, path, dataindex=idx)
            start16 += span16

    def _drawDonut(self, painter, cx, cy, radius, vals):
        """Draw a donut shape (pie with hollow centre)."""
        total = float(N.nansum(N.abs(vals)))
        if total <= 0:
            return
        inner_frac = self.settings.get("innerRadius").val
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
            self._fillSlice(painter, idx, path, dataindex=idx)
            start16 += span16


document.thefactory.register(XYPie)
