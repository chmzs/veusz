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
    """

    def __init__(self, enabled=False, grad_type='linear', angle=90,
                 stops=None, transparency=0):
        """Initialize gradient configuration.

        Args:
            enabled: Whether gradient is enabled
            grad_type: 'linear' or 'radial'
            angle: Angle in degrees for linear gradient
            stops: List of (offset, color) tuples
            transparency: Transparency percentage
        """
        self.enabled = enabled
        self.type = grad_type
        self.angle = angle
        self.stops = stops or [(0.0, '#ff0000'), (1.0, '#0000ff')]
        self.transparency = transparency

    @classmethod
    def from_dict(cls, d):
        """Create GradientConfig from a dictionary.

        Args:
            d: Dictionary with gradient configuration.
                Keys: 'enabled', 'type' (or 'grad_type'), 'angle', 'stops', 'transparency'

        Returns:
            GradientConfig instance
        """
        # Support both 'type' and 'grad_type' keys for backward compatibility
        grad_type = d.get('type') or d.get('grad_type', 'linear')
        return cls(
            enabled=d.get('enabled', False),
            grad_type=grad_type,
            angle=d.get('angle', 90),
            stops=d.get('stops', [(0.0, '#ff0000'), (1.0, '#0000ff')]),
            transparency=d.get('transparency', 0)
        )

    def to_dict(self):
        """Convert to dictionary.

        Returns:
            Dictionary with gradient configuration
        """
        return {
            'enabled': self.enabled,
            'type': self.type,
            'angle': self.angle,
            'stops': self.stops,
            'transparency': self.transparency
        }


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


def create_gradient_from_config(config, bbox):
    """Create a Qt gradient from GradientConfig.

    Args:
        config: GradientConfig object
        bbox: QRectF with bounding box

    Returns:
        Qt gradient object (QLinearGradient or QRadialGradient)
    """
    if config.type == 'linear':
        x1, y1, x2, y2 = calculate_linear_endpoints(bbox, config.angle)
        return create_linear_gradient(x1, y1, x2, y2,
                                      config.stops, config.transparency)
    else:  # radial
        cx = bbox.x() + bbox.width() / 2
        cy = bbox.y() + bbox.height() / 2
        radius = max(bbox.width(), bbox.height()) / 2
        return create_radial_gradient(cx, cy, radius,
                                       config.stops, config.transparency)


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
        return gradient_setting.get('enabled', False)

    # Assume it's a setting object with val attribute
    try:
        return gradient_setting.val.get('enabled', False)
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
PRESETS = {
    'temperature': {
        'name': 'Temperature (Blue-White-Red)',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#0066ff'), (0.5, '#ffffff'), (1.0, '#ff3300')]
    },
    'elevation': {
        'name': 'Elevation (Green-Yellow-Red)',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#00aa00'), (0.5, '#ffff00'), (1.0, '#ff0000')]
    },
    'grayscale': {
        'name': 'Grayscale',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#000000'), (1.0, '#ffffff')]
    },
    'viridis': {
        'name': 'Viridis',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#440154'), (0.25, '#3b528b'), (0.5, '#21918c'),
                  (0.75, '#5ec962'), (1.0, '#fde725')]
    },
    'plasma': {
        'name': 'Plasma',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#0d0887'), (0.25, '#7e03a8'), (0.5, '#cc4778'),
                  (0.75, '#f89540'), (1.0, '#f0f921')]
    },
    'inferno': {
        'name': 'Inferno',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#000004'), (0.25, '#51127c'), (0.5, '#b73779'),
                  (0.75, '#fb8861'), (1.0, '#fcffa4')]
    },
    'drywet': {
        'name': 'Dry-Wet (BrBG)',
        'type': 'linear',
        'angle': 90,
        'stops': [(0.0, '#543005'), (0.25, '#cfa255'), (0.5, '#f4f4f4'),
                  (0.75, '#58b0a6'), (1.0, '#003c30')]
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
    return [(name, data['name']) for name, data in PRESETS.items()]