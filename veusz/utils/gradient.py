#    Copyright (C) 2025 Veusz Contributors
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
#
##############################################################################

"""Gradient fill utilities for Veusz.

This module provides gradient fill functionality for various plot elements.
Gradients can be linear or radial with configurable color stops.
"""

import math

# Import Qt - use lazy import to avoid circular dependencies
_qt = None


def _get_qt():
    """Lazy import of Qt modules."""
    global _qt
    if _qt is None:
        from .. import qtall as qt

        _qt = qt
    return _qt


class GradientConfig:
    """Configuration for a gradient fill.

    Attributes:
        enabled: Whether gradient is enabled
        type: 'linear' or 'radial'
        angle: Angle in degrees for linear gradient (0-360)
        stops: List of (offset, color) tuples, offset is 0-1
        transparency: Transparency percentage (0-100)
        midpoint: Optional float (0-1) or None, gradient offset where the
            central color should appear. When set, stops are remapped so
            the middle stop aligns to this position.
    """

    def __init__(
        self,
        enabled=False,
        grad_type="linear",
        angle=90,
        stops=None,
        transparency=0,
        midpoint=None,
    ):
        """Initialize gradient configuration.

        Args:
            enabled: Whether gradient is enabled
            grad_type: 'linear' or 'radial'
            angle: Angle in degrees for linear gradient
            stops: List of (offset, color) tuples
            transparency: Transparency percentage
            midpoint: Optional float 0-1 for gradient midpoint position
        """
        self.enabled = enabled
        self.type = grad_type
        self.angle = angle
        self.stops = stops or [(0.0, "#ff0000"), (1.0, "#0000ff")]
        self.transparency = transparency
        self.midpoint = midpoint

    @classmethod
    def from_dict(cls, d):
        """Create GradientConfig from a dictionary.

        Args:
            d: Dictionary with gradient configuration.
                Keys: 'enabled', 'type' (or 'grad_type'), 'angle', 'stops', 'transparency', 'midpoint'

        Returns:
            GradientConfig instance
        """
        # Support both 'type' and 'grad_type' keys for backward compatibility
        grad_type = d.get("type") or d.get("grad_type", "linear")
        return cls(
            enabled=d.get("enabled", False),
            grad_type=grad_type,
            angle=d.get("angle", 90),
            stops=d.get("stops", [(0.0, "#ff0000"), (1.0, "#0000ff")]),
            transparency=d.get("transparency", 0),
            midpoint=d.get("midpoint"),
        )

    def to_dict(self):
        """Convert to dictionary.

        Returns:
            Dictionary with gradient configuration
        """
        result = {
            "enabled": self.enabled,
            "type": self.type,
            "angle": self.angle,
            "stops": self.stops,
            "transparency": self.transparency,
        }
        if self.midpoint is not None:
            result["midpoint"] = self.midpoint
        return result


def remap_stops_for_midpoint(stops, midpoint):
    """Remap gradient stops so the central color aligns with midpoint.

    Args:
        stops: List of (offset, color) tuples, offsets in [0, 1]
        midpoint: Target offset (0-1) where the middle stop should land

    Returns:
        New list of stops with remapped offsets
    """
    if midpoint is None or midpoint <= 0 or midpoint >= 1:
        return stops
    if len(stops) < 3:
        return stops

    # Find the stop closest to 0.5 (the "middle" color)
    mid_idx = min(range(len(stops)), key=lambda i: abs(stops[i][0] - 0.5))

    # Split stops into left and right of middle
    left_stops = stops[: mid_idx + 1]
    right_stops = stops[mid_idx:]

    # Remap left side to [0, midpoint], right side to [midpoint, 1]
    new_stops = []

    # Left side
    if len(left_stops) > 1:
        left_offsets = [s[0] for s in left_stops]
        left_min, left_max = left_offsets[0], left_offsets[-1]
        if left_max > left_min:
            for offset, color in left_stops:
                norm = (offset - left_min) / (left_max - left_min)
                new_offset = norm * midpoint
                new_stops.append((new_offset, color))
        else:
            new_stops.append((0.0, left_stops[0][1]))

    # Right side (skip the middle stop to avoid duplicate)
    if len(right_stops) > 1:
        right_offsets = [s[0] for s in right_stops]
        right_min, right_max = right_offsets[0], right_offsets[-1]
        if right_max > right_min:
            for offset, color in right_stops[1:]:  # skip middle
                norm = (offset - right_min) / (right_max - right_min)
                new_offset = midpoint + (1.0 - midpoint) * norm
                new_stops.append((new_offset, color))
        else:
            new_stops.append((1.0, right_stops[-1][1]))

    # Ensure endpoints exactly 0 and 1
    if new_stops:
        new_stops[0] = (0.0, new_stops[0][1])
        new_stops[-1] = (1.0, new_stops[-1][1])

    return new_stops


def create_linear_gradient(x1, y1, x2, y2, stops, transparency=0):
    """Create a Qt linear gradient.

    Args:
        x1, y1: Start point
        x2, y2: End point
        stops: List of (offset, color) tuples
        transparency: Transparency percentage (0-100)

    Returns:
        QLinearGradient object
    """
    qt = _get_qt()
    gradient = qt.QLinearGradient(x1, y1, x2, y2)
    _add_gradient_stops(gradient, stops, transparency)
    return gradient


def create_radial_gradient(cx, cy, radius, stops, transparency=0):
    """Create a Qt radial gradient.

    Args:
        cx, cy: Center point
        radius: Radius of gradient
        stops: List of (offset, color) tuples
        transparency: Transparency percentage (0-100)

    Returns:
        QRadialGradient object
    """
    qt = _get_qt()
    gradient = qt.QRadialGradient(cx, cy, radius)
    _add_gradient_stops(gradient, stops, transparency)
    return gradient


def _add_gradient_stops(gradient, stops, transparency=0):
    """Add color stops to a gradient with transparency support.

    Args:
        gradient: Qt gradient object
        stops: List of (offset, color) tuples
        transparency: Transparency percentage (0-100)
    """
    qt = _get_qt()
    alpha = 1.0 if transparency >= 100 else (100 - transparency) / 100.0

    for offset, color in stops:
        qcolor = qt.QColor(color)
        if alpha < 1.0:
            qcolor.setAlphaF(alpha)
        gradient.setColorAt(offset, qcolor)


def calculate_linear_endpoints(bbox, angle):
    """Calculate start and end points for a linear gradient.

    Args:
        bbox: QRectF with bounding box
        angle: Angle in degrees

    Returns:
        Tuple of (x1, y1, x2, y2)
    """
    # Calculate gradient direction from angle
    rad = math.radians(angle)
    cx = bbox.x() + bbox.width() / 2
    cy = bbox.y() + bbox.height() / 2

    # Use the larger dimension to ensure gradient covers the entire area
    max_dim = max(bbox.width(), bbox.height())

    x1 = cx - math.cos(rad) * max_dim
    y1 = cy - math.sin(rad) * max_dim
    x2 = cx + math.cos(rad) * max_dim
    y2 = cy + math.sin(rad) * max_dim

    return x1, y1, x2, y2


def create_gradient_from_config(config, bbox, transparency=None, midpoint=None):
    """Create a Qt gradient from GradientConfig.

    Args:
        config: GradientConfig object
        bbox: QRectF with bounding box
        transparency: Optional transparency percentage (0-100) to override
            config.transparency. Used to composite brush-level transparency.
        midpoint: Optional midpoint override (0-1). When provided, this takes
            precedence over config.midpoint. Used for gradientCenterValue mapping.

    Returns:
        Qt gradient object (QLinearGradient or QRadialGradient)
    """
    if transparency is None:
        transparency = config.transparency

    # Apply midpoint remapping if configured (runtime midpoint takes precedence)
    stops = config.stops
    effective_midpoint = midpoint if midpoint is not None else config.midpoint
    if effective_midpoint is not None:
        stops = remap_stops_for_midpoint(stops, effective_midpoint)

    if config.type == "linear":
        x1, y1, x2, y2 = calculate_linear_endpoints(bbox, config.angle)
        return create_linear_gradient(x1, y1, x2, y2, stops, transparency)
    else:  # radial
        cx = bbox.x() + bbox.width() / 2
        cy = bbox.y() + bbox.height() / 2
        radius = max(bbox.width(), bbox.height()) / 2
        return create_radial_gradient(cx, cy, radius, stops, transparency)


def is_gradient_enabled(gradient_setting):
    """Check if gradient is enabled from a setting object.

    Args:
        gradient_setting: Setting object with 'enabled' key or GradientConfig

    Returns:
        True if gradient is enabled
    """
    if gradient_setting is None:
        return False

    if isinstance(gradient_setting, GradientConfig):
        return gradient_setting.enabled

    if isinstance(gradient_setting, dict):
        return gradient_setting.get("enabled", False)

    # Assume it's a setting object with val attribute
    try:
        return gradient_setting.val.get("enabled", False)
    except AttributeError:
        return False


def get_gradient_config(gradient_setting):
    """Get GradientConfig from a setting object or dict.

    Args:
        gradient_setting: Setting object, dict, or GradientConfig

    Returns:
        GradientConfig object
    """
    if gradient_setting is None:
        return GradientConfig()

    if isinstance(gradient_setting, GradientConfig):
        return gradient_setting

    if isinstance(gradient_setting, dict):
        return GradientConfig.from_dict(gradient_setting)

    # Assume it's a setting object with val attribute
    try:
        return GradientConfig.from_dict(gradient_setting.val)
    except (AttributeError, TypeError):
        return GradientConfig()


# Preset gradient configurations
# Organized by category following RColorBrewer conventions:
# - Diverging (发散型): 中间中性/白色，两端对比 —— 适配 gradientCenterValue
# - Sequential (顺序型): 单向渐变，低→高
# - Qualitative (定性型): 分类离散色，不适合连续渐变（不在此列）

PRESETS = {
    # ===== Diverging (发散型) =====
    # 中间白/浅灰，两端强对比，专用 gradientCenterValue 映射
    "rdbu": {
        "name": "RdBu (Red-Blue Diverging)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#053061"),
            (0.1, "#2166ac"),
            (0.2, "#4393c3"),
            (0.3, "#92c5de"),
            (0.4, "#d1e5f0"),
            (0.5, "#f7f7f7"),
            (0.6, "#fddbc7"),
            (0.7, "#f4a582"),
            (0.8, "#d6604d"),
            (0.9, "#b2182b"),
            (1.0, "#67001f"),
        ],
    },
    "rdylbu": {
        "name": "RdYlBu (Red-Yellow-Blue)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#313695"),
            (0.1, "#4575b4"),
            (0.2, "#74add1"),
            (0.3, "#abd9e9"),
            (0.4, "#e0f3f8"),
            (0.5, "#ffffbf"),
            (0.6, "#fee090"),
            (0.7, "#fdae61"),
            (0.8, "#f46d43"),
            (0.9, "#d73027"),
            (1.0, "#a50026"),
        ],
    },
    "spectral": {
        "name": "Spectral (Full Spectrum)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#9e0142"),
            (0.1, "#d53e4f"),
            (0.2, "#f46d43"),
            (0.3, "#fdae61"),
            (0.4, "#fee08b"),
            (0.5, "#ffffbf"),
            (0.6, "#e6f598"),
            (0.7, "#abdda4"),
            (0.8, "#66c2a5"),
            (0.9, "#3288bd"),
            (1.0, "#5e4fa2"),
        ],
    },
    "brbg": {
        "name": "BrBG (Brown-Blue-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#543005"),
            (0.1, "#8c510a"),
            (0.2, "#bf812d"),
            (0.3, "#dfc27d"),
            (0.4, "#f6e8c3"),
            (0.5, "#f5f5f5"),
            (0.6, "#c7eae5"),
            (0.7, "#80cdc1"),
            (0.8, "#35978f"),
            (0.9, "#01665e"),
            (1.0, "#003c30"),
        ],
    },
    "piyg": {
        "name": "PiYG (Pink-Yellow-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#8e0152"),
            (0.1, "#c51b7d"),
            (0.2, "#de77ae"),
            (0.3, "#f1b6da"),
            (0.4, "#fde0ef"),
            (0.5, "#f7f7f7"),
            (0.6, "#e6f5d0"),
            (0.7, "#b8e186"),
            (0.8, "#7fbc41"),
            (0.9, "#4d9221"),
            (1.0, "#276419"),
        ],
    },
    "prgn": {
        "name": "PRGn (Purple-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#40004b"),
            (0.1, "#762a83"),
            (0.2, "#9970ab"),
            (0.3, "#c2a5cf"),
            (0.4, "#e7d4e8"),
            (0.5, "#f7f7f7"),
            (0.6, "#d9f0d3"),
            (0.7, "#a6dba0"),
            (0.8, "#5aae61"),
            (0.9, "#1b7837"),
            (1.0, "#00441b"),
        ],
    },
    "puor": {
        "name": "PuOr (Purple-Orange)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#7f3b08"),
            (0.1, "#b35806"),
            (0.2, "#e08214"),
            (0.3, "#fdb863"),
            (0.4, "#fee0b6"),
            (0.5, "#f7f7f7"),
            (0.6, "#fdb863"),
            (0.7, "#e08214"),
            (0.8, "#b35806"),
            (0.9, "#7f3b08"),
            (1.0, "#542788"),
        ],
    },
    "rdgy": {
        "name": "RdGy (Red-Grey)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#67001f"),
            (0.1, "#b2182b"),
            (0.2, "#d6604d"),
            (0.3, "#f4a582"),
            (0.4, "#fddbc7"),
            (0.5, "#f7f7f7"),
            (0.6, "#d9d9d9"),
            (0.7, "#bababa"),
            (0.8, "#878787"),
            (0.9, "#4d4d4d"),
            (1.0, "#1a1a1a"),
        ],
    },
    "rdylgn": {
        "name": "RdYlGn (Red-Yellow-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#a50026"),
            (0.1, "#d73027"),
            (0.2, "#f46d43"),
            (0.3, "#fdae61"),
            (0.4, "#fee08b"),
            (0.5, "#ffffbf"),
            (0.6, "#d9ef8b"),
            (0.7, "#a6d96a"),
            (0.8, "#66bd63"),
            (0.9, "#1a9850"),
            (1.0, "#006837"),
        ],
    },
    # ===== Sequential (顺序型) =====
    "viridis": {
        "name": "Viridis",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#440154"),
            (0.25, "#3b528b"),
            (0.5, "#21918c"),
            (0.75, "#5ec962"),
            (1.0, "#fde725"),
        ],
    },
    "plasma": {
        "name": "Plasma",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#0d0887"),
            (0.25, "#7e03a8"),
            (0.5, "#cc4778"),
            (0.75, "#f89540"),
            (1.0, "#f0f921"),
        ],
    },
    "inferno": {
        "name": "Inferno",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#000004"),
            (0.25, "#51127c"),
            (0.5, "#b73779"),
            (0.75, "#fb8861"),
            (1.0, "#fcffa4"),
        ],
    },
    "magma": {
        "name": "Magma",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#000004"),
            (0.25, "#490c6c"),
            (0.5, "#a8336e"),
            (0.75, "#f1605d"),
            (1.0, "#fcfdbf"),
        ],
    },
    "cividis": {
        "name": "Cividis",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#00204d"),
            (0.2, "#3e496c"),
            (0.4, "#6c5b7d"),
            (0.6, "#a2705f"),
            (0.8, "#d79038"),
            (1.0, "#fef287"),
        ],
    },
    "turbo": {
        "name": "Turbo",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#30123b"),
            (0.1, "#4150a8"),
            (0.2, "#3882d5"),
            (0.3, "#33b7e5"),
            (0.4, "#2cb877"),
            (0.5, "#65d63b"),
            (0.6, "#a9db21"),
            (0.7, "#eef214"),
            (0.8, "#fcad06"),
            (0.9, "#f5670a"),
            (1.0, "#f9fb0d"),
        ],
    },
    "blues": {
        "name": "Blues",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7fbff"),
            (0.2, "#deebf7"),
            (0.4, "#c6dbef"),
            (0.6, "#9ecae1"),
            (0.8, "#6baed6"),
            (1.0, "#08306b"),
        ],
    },
    "greens": {
        "name": "Greens",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7fcf5"),
            (0.2, "#e5f5e0"),
            (0.4, "#c7e9c0"),
            (0.6, "#a1d99b"),
            (0.8, "#74c476"),
            (1.0, "#00441b"),
        ],
    },
    "greys": {
        "name": "Greys",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#ffffff"),
            (0.2, "#f0f0f0"),
            (0.4, "#d9d9d9"),
            (0.6, "#bdbdbd"),
            (0.8, "#969696"),
            (1.0, "#000000"),
        ],
    },
    "oranges": {
        "name": "Oranges",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff5eb"),
            (0.2, "#fee6ce"),
            (0.4, "#fdd0a2"),
            (0.6, "#fdae6b"),
            (0.8, "#fd8d3c"),
            (1.0, "#7f2704"),
        ],
    },
    "reds": {
        "name": "Reds",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff5f0"),
            (0.2, "#fee0d2"),
            (0.4, "#fcbba1"),
            (0.6, "#fc9272"),
            (0.8, "#de2d26"),
            (1.0, "#67000d"),
        ],
    },
    "purples": {
        "name": "Purples",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fcfbfd"),
            (0.2, "#efedf5"),
            (0.4, "#dadaeb"),
            (0.6, "#bcbddc"),
            (0.8, "#9e9ac8"),
            (1.0, "#3f007d"),
        ],
    },
    "bugn": {
        "name": "BuGn (Blue-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7fcfd"),
            (0.2, "#e5f5f9"),
            (0.4, "#ccece6"),
            (0.6, "#99d8c9"),
            (0.8, "#66c2a4"),
            (1.0, "#00441b"),
        ],
    },
    "bupu": {
        "name": "BuPu (Blue-Purple)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7fcfd"),
            (0.2, "#e0ecf4"),
            (0.4, "#bfd3e6"),
            (0.6, "#9ebcda"),
            (0.8, "#8856a7"),
            (1.0, "#4d004b"),
        ],
    },
    "gnbu": {
        "name": "GnBu (Green-Blue)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7fcf0"),
            (0.2, "#e0f3db"),
            (0.4, "#ccebc5"),
            (0.6, "#a8ddb5"),
            (0.8, "#7bccc4"),
            (1.0, "#084081"),
        ],
    },
    "orrd": {
        "name": "OrRd (Orange-Red)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff7ec"),
            (0.2, "#fee8c8"),
            (0.4, "#fdd49e"),
            (0.6, "#fdbb84"),
            (0.8, "#fc8d59"),
            (1.0, "#7f0000"),
        ],
    },
    "pubu": {
        "name": "PuBu (Purple-Blue)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff7fb"),
            (0.2, "#ece7f2"),
            (0.4, "#d0d1e6"),
            (0.6, "#a6bddb"),
            (0.8, "#74a9cf"),
            (1.0, "#08306b"),
        ],
    },
    "pubugn": {
        "name": "PuBuGn (Purple-Blue-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff7fb"),
            (0.2, "#ece2f0"),
            (0.4, "#d0d1e6"),
            (0.6, "#9ebcda"),
            (0.8, "#74a9cf"),
            (1.0, "#002b73"),
        ],
    },
    "purd": {
        "name": "PuRd (Purple-Red)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#f7f4f9"),
            (0.2, "#e7e1ef"),
            (0.4, "#d4b9da"),
            (0.6, "#c994c7"),
            (0.8, "#df65b0"),
            (1.0, "#67001f"),
        ],
    },
    "rdpu": {
        "name": "RdPu (Red-Purple)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#fff7f3"),
            (0.2, "#fde0dd"),
            (0.4, "#fcc5c0"),
            (0.6, "#fa9fb5"),
            (0.8, "#f768a1"),
            (1.0, "#7a0177"),
        ],
    },
    "ylgn": {
        "name": "YlGn (Yellow-Green)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#ffffe5"),
            (0.2, "#f7fcb9"),
            (0.4, "#d9f0a3"),
            (0.6, "#addd8e"),
            (0.8, "#78c679"),
            (1.0, "#004529"),
        ],
    },
    "ylgnbu": {
        "name": "YlGnBu (Yellow-Green-Blue)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#ffffd9"),
            (0.2, "#edf8b1"),
            (0.4, "#c7e9b4"),
            (0.6, "#7fcdbb"),
            (0.8, "#41b6c4"),
            (1.0, "#081d58"),
        ],
    },
    "ylorbr": {
        "name": "YlOrBr (Yellow-Orange-Brown)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#ffffe5"),
            (0.2, "#fff7bc"),
            (0.4, "#fee391"),
            (0.6, "#fec44f"),
            (0.8, "#fe9929"),
            (1.0, "#8c2d04"),
        ],
    },
    "ylorrd": {
        "name": "YlOrRd (Yellow-Orange-Red)",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#ffffcc"),
            (0.2, "#ffeda0"),
            (0.4, "#fed976"),
            (0.6, "#feb24c"),
            (0.8, "#fd8d3c"),
            (1.0, "#800026"),
        ],
    },
    # ===== Legacy (兼容旧预设) =====
    "temperature": {
        "name": "Temperature (Blue-White-Red) [legacy]",
        "type": "linear",
        "angle": 90,
        "stops": [(0.0, "#0066ff"), (0.5, "#ffffff"), (1.0, "#ff3300")],
    },
    "elevation": {
        "name": "Elevation (Green-Yellow-Red) [legacy]",
        "type": "linear",
        "angle": 90,
        "stops": [(0.0, "#00aa00"), (0.5, "#ffff00"), (1.0, "#ff0000")],
    },
    "grayscale": {
        "name": "Grayscale",
        "type": "linear",
        "angle": 90,
        "stops": [(0.0, "#000000"), (1.0, "#ffffff")],
    },
    "drywet": {
        "name": "Dry-Wet (BrBG) [legacy]",
        "type": "linear",
        "angle": 90,
        "stops": [
            (0.0, "#543005"),
            (0.25, "#cfa255"),
            (0.5, "#f4f4f4"),
            (0.75, "#58b0a6"),
            (1.0, "#003c30"),
        ],
    },
}


def get_preset(name):
    """Get a preset gradient configuration.

    Args:
        name: Name of the preset

    Returns:
        Dictionary with preset configuration, or None if not found
    """
    return PRESETS.get(name)


def list_presets():
    """Get a list of available presets.

    Returns:
        List of (name, display_name) tuples
    """
    return [(name, data["name"]) for name, data in PRESETS.items()]
