"""Unit tests for gradient fill functionality.

These tests can be run standalone or via runselftest.py
"""

import sys
import os
import unittest

# Direct import from utils directory (gradient module is standalone)
_utils_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'veusz', 'utils')
if os.path.exists(_utils_dir):
    sys.path.insert(0, _utils_dir)


class TestGradientConfig(unittest.TestCase):
    """Test GradientConfig class."""

    @classmethod
    def setUpClass(cls):
        """Import gradient module."""
        try:
            import gradient
            cls.gradient = gradient
        except ImportError:
            raise unittest.SkipTest("Cannot import gradient module")

    def test_default_init(self):
        """Test default initialization."""
        config = self.gradient.GradientConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.type, 'linear')
        self.assertEqual(config.angle, 90)
        self.assertEqual(len(config.stops), 2)

    def test_from_dict(self):
        """Test creating from dictionary."""
        d = {
            'enabled': True,
            'type': 'radial',
            'angle': 45,
            'stops': [(0.0, '#ff0000'), (0.5, '#00ff00'), (1.0, '#0000ff')]
        }
        config = self.gradient.GradientConfig.from_dict(d)
        self.assertTrue(config.enabled)
        self.assertEqual(config.type, 'radial')
        self.assertEqual(config.angle, 45)
        self.assertEqual(len(config.stops), 3)

    def test_to_dict(self):
        """Test converting to dictionary."""
        config = self.gradient.GradientConfig(
            enabled=True,
            grad_type='linear',
            angle=180,
            stops=[(0.0, '#000000'), (1.0, '#ffffff')]
        )
        d = config.to_dict()
        self.assertTrue(d['enabled'])
        self.assertEqual(d['type'], 'linear')
        self.assertEqual(d['angle'], 180)

    def test_roundtrip(self):
        """Test roundtrip conversion."""
        original = self.gradient.GradientConfig(
            enabled=True,
            grad_type='radial',
            angle=135,
            stops=[(0.0, '#123456'), (1.0, '#abcdef')]
        )
        d = original.to_dict()
        restored = self.gradient.GradientConfig.from_dict(d)
        self.assertEqual(original.enabled, restored.enabled)
        self.assertEqual(original.type, restored.type)
        self.assertEqual(original.angle, restored.angle)


class TestGradientHelpers(unittest.TestCase):
    """Test gradient helper functions."""

    @classmethod
    def setUpClass(cls):
        """Import gradient module."""
        try:
            import gradient
            cls.gradient = gradient
        except ImportError:
            raise unittest.SkipTest("Cannot import gradient module")

    def test_calculate_linear_endpoints(self):
        """Test calculating linear gradient endpoints."""
        # Mock QRectF-like object - gradient.py uses callable methods
        class MockRect:
            def __init__(self, x, y, w, h):
                self._x = x
                self._y = y
                self._w = w
                self._h = h

            def x(self):
                return self._x

            def y(self):
                return self._y

            def width(self):
                return self._w

            def height(self):
                return self._h

        bbox = MockRect(0, 0, 100, 50)  # width=100, height=50

        # Test 0 degrees (horizontal)
        x1, y1, x2, y2 = self.gradient.calculate_linear_endpoints(bbox, 0)
        self.assertAlmostEqual(y1, y2, places=5)  # Should be horizontal

        # Test 90 degrees (vertical)
        x1, y1, x2, y2 = self.gradient.calculate_linear_endpoints(bbox, 90)
        self.assertAlmostEqual(x1, x2, places=5)  # Should be vertical

    def test_gradient_presets(self):
        """Test that presets are available."""
        PRESETS = self.gradient.PRESETS
        get_preset = self.gradient.get_preset
        list_presets = self.gradient.list_presets

        # Check presets exist
        self.assertIn('temperature', PRESETS)
        self.assertIn('elevation', PRESETS)
        self.assertIn('viridis', PRESETS)

        # Check get_preset
        temp = get_preset('temperature')
        self.assertIsNotNone(temp)
        self.assertEqual(temp['type'], 'linear')

        # Check list_presets
        presets = list_presets()
        self.assertGreater(len(presets), 0)
        names = [n for n, _ in presets]
        self.assertIn('temperature', names)

    def test_get_preset_invalid(self):
        """Test getting invalid preset."""
        result = self.gradient.get_preset('nonexistent_preset')
        self.assertIsNone(result)


class TestFillToDefaults(unittest.TestCase):
    """Regression test: fillto defaults must preserve FillBelow/FillAbove
    semantics (see functions.vsz failure where 'bottom' default broke FillAbove).

    Requires full veusz package (PyQt6 + helpers) - skipped otherwise.
    """

    @classmethod
    def setUpClass(cls):
        """Import veusz settings - needs PyQt6 stack."""
        try:
            from veusz.setting import collections
            cls.collections = collections
        except ImportError:
            raise unittest.SkipTest("Cannot import veusz.setting.collections")

    def test_plotter_fill_default_is_auto(self):
        """Function-plot fills must default to 'auto' (preserve belowleft
        semantics) so FillAbove fills to top and FillBelow fills to bottom."""
        f = self.collections.PlotterFill('TestPlotterFill')
        self.assertEqual(f.fillto, 'auto')

    def test_plotter_fill_choices_include_auto(self):
        """'auto' must be a selectable fillto choice for function plots."""
        f = self.collections.PlotterFill('TestPlotterFill')
        choices = f.get('fillto').vallist
        self.assertIn('auto', choices)

    def test_point_fill_default_is_top(self):
        """PointPlotter fill class default must stay 'top' so FillAbove
        (which overrides to 'bottom' via newDefault) keeps upstream behavior."""
        f = self.collections.PointFill('TestPointFill')
        self.assertEqual(f.fillto, 'top')


class TestGradientUtils(unittest.TestCase):
    """Test gradient utility functions."""

    @classmethod
    def setUpClass(cls):
        """Import gradient module."""
        try:
            import gradient
            cls.gradient = gradient
        except ImportError:
            raise unittest.SkipTest("Cannot import gradient module")

    def test_is_gradient_enabled_none(self):
        """Test is_gradient_enabled with None."""
        self.assertFalse(self.gradient.is_gradient_enabled(None))

    def test_is_gradient_enabled_dict(self):
        """Test is_gradient_enabled with dict."""
        self.assertFalse(self.gradient.is_gradient_enabled({'enabled': False}))
        self.assertTrue(self.gradient.is_gradient_enabled({'enabled': True}))

    def test_is_gradient_enabled_config(self):
        """Test is_gradient_enabled with GradientConfig."""
        config = self.gradient.GradientConfig(enabled=False)
        self.assertFalse(self.gradient.is_gradient_enabled(config))

        config = self.gradient.GradientConfig(enabled=True)
        self.assertTrue(self.gradient.is_gradient_enabled(config))


class TestGradientRendering(unittest.TestCase):
    """Render gradient fills to a QImage and verify transparency behaviour.

    Guards the transparency regression where the gradient render path
    (extbrushfilling._brushExtFillPathGradient) ignored the brush-level
    transparency setting, unlike the solid-fill path.
    """

    @classmethod
    def setUpClass(cls):
        try:
            # need a QGuiApplication to paint; use offscreen platform
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            from veusz import qtall as qt
            from veusz.utils import extbrushfilling
            from veusz.setting import collections
            app = qt.QApplication.instance()
            if app is None:
                app = qt.QApplication([])
            cls.qt = qt
            cls.extbrushfilling = extbrushfilling
            cls.collections = collections
        except Exception:
            raise unittest.SkipTest("Cannot import Qt stack for rendering")

    def _render_center_alpha(self, brush_transparency, grad_transparency):
        """Fill a 60x60 rect with a red->blue vertical gradient and return
        the alpha of the center pixel (0-255)."""
        qt = self.qt
        img = qt.QImage(60, 60, qt.QImage.Format.Format_ARGB32)
        img.fill(qt.QColor(0, 0, 0, 0))
        painter = qt.QPainter(img)
        try:
            brush = self.collections.BrushExtended('testbrush')
            brush.hide = False
            brush.transparency = brush_transparency
            brush.Gradient = {
                'enabled': True,
                'type': 'linear',
                'angle': 90,
                'stops': [(0.0, '#ff0000'), (1.0, '#0000ff')],
                'transparency': grad_transparency,
            }
            path = qt.QPainterPath()
            path.addRect(qt.QRectF(5, 5, 50, 50))
            self.extbrushfilling.brushExtFillPath(painter, brush, path)
        finally:
            painter.end()
        return img.pixelColor(30, 30).alpha()

    def test_opaque_gradient(self):
        self.assertEqual(self._render_center_alpha(0, 0), 255)

    def test_brush_transparency_applied(self):
        alpha = self._render_center_alpha(50, 0)
        self.assertAlmostEqual(alpha / 255., 0.5, delta=0.15)

    def test_gradient_transparency_applied(self):
        alpha = self._render_center_alpha(0, 50)
        self.assertAlmostEqual(alpha / 255., 0.5, delta=0.15)

    def test_composited_transparency(self):
        # brush 50 * gradient 50 -> effective 75 -> alpha 0.25
        alpha = self._render_center_alpha(50, 50)
        self.assertAlmostEqual(alpha / 255., 0.25, delta=0.15)

    def test_full_transparency_skips_fill(self):
        self.assertEqual(self._render_center_alpha(100, 0), 0)


def main(outfile):
    """Run tests and write success marker to outfile."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Write success marker to outfile
    with open(outfile, 'w') as f:
        if result.wasSuccessful():
            f.write('OK')
        else:
            f.write('FAILED')

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Called by runselftest.py with outfile argument
        main(sys.argv[1])
    else:
        # Standalone run
        unittest.main(argv=[''], exit=False)