"""Unit tests for gradient fill functionality.

These tests can be run standalone or via runselftest.py
"""

import sys
import os
import unittest
import numpy as N

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
            # keep the app referenced on the class so it is not garbage-collected
            cls.app = qt.QApplication.instance() or qt.QApplication([])
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


class TestFillToEdgeTargets(unittest.TestCase):
    """Test the shared fillToEdgeTargets helper (unified fillto edge logic)."""

    @classmethod
    def setUpClass(cls):
        try:
            from veusz import qtall as qt
            from veusz.utils import extbrushfilling
            cls.qt = qt
            cls.extbrushfilling = extbrushfilling
        except Exception:
            raise unittest.SkipTest("Cannot import Qt stack")

    @classmethod
    def _pts(cls):
        q = cls.qt
        return q.QPolygonF([
            q.QPointF(10, 20), q.QPointF(30, 40), q.QPointF(50, 60)])

    def test_top(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'top')
        self.assertEqual((x1, y1, x2, y2), (10, 5, 50, 5))

    def test_bottom(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'bottom')
        self.assertEqual((x1, y1, x2, y2), (10, 95, 50, 95))

    def test_left(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'left')
        self.assertEqual((x1, y1, x2, y2), (0, 20, 0, 60))

    def test_right(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'right')
        self.assertEqual((x1, y1, x2, y2), (100, 20, 100, 60))

    def test_custom_numeric(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'custom', filltoValue=50.0)
        self.assertEqual((x1, y1, x2, y2), (10, 50, 50, 50))

    def test_custom_auto_falls_back_to_bottom(self):
        # 'Auto' string must not be fed into axis conversion; fall back to bottom
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'custom', filltoValue='Auto')
        self.assertEqual(y1, 95)

    def test_unknown_falls_back_to_bottom(self):
        x1, y1, x2, y2 = self.extbrushfilling.fillToEdgeTargets(
            self._pts(), (0, 5, 100, 95), 'bogus')
        self.assertEqual((y1, y2), (95, 95))


class TestGradientControl(unittest.TestCase):
    """Test the GradientFill editor control + interactive GradientBar."""

    @classmethod
    def setUpClass(cls):
        try:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            from veusz import qtall as qt
            from veusz.setting import controls
            from veusz.setting.setting import GradientFill
            # keep the app referenced on the class so it is not garbage-collected
            cls.app = qt.QApplication.instance() or qt.QApplication([])
            cls.qt = qt
            cls.controls = controls
            cls.GradientFill = GradientFill
        except Exception:
            raise unittest.SkipTest("Cannot import Qt stack for control test")

    def _make_setting(self):
        return self.GradientFill(
            'test',
            {'enabled': True, 'type': 'linear', 'angle': 90,
             'transparency': 30,
             'stops': [(0.0, '#ff0000'), (0.5, '#00ff00'), (1.0, '#0000ff')]})

    def test_control_loads_setting(self):
        s = self._make_setting()
        w = self.controls.GradientFill(s)
        self.assertEqual(w.gradient_bar.stops(),
                         [(0.0, '#ff0000'), (0.5, '#00ff00'), (1.0, '#0000ff')])
        self.assertEqual(w.transparency_spin.value(), 30)

    def test_bar_add_set_remove(self):
        w = self.controls.GradientFill(self._make_setting())
        bar = w.gradient_bar
        # add at occupied 0.5 -> snaps to a free spot
        self.assertTrue(bar.addStopAt(0.5))
        self.assertEqual(len(bar.stops()), 4)
        self.assertGreaterEqual(bar.selectedIndex(), 0)
        # move selected stop
        bar.setStop(bar.selectedIndex(), offset=0.25)
        self.assertIn(0.25, [o for o, _ in bar.stops()])
        # remove selected
        self.assertTrue(bar.removeSelected())
        self.assertEqual(len(bar.stops()), 3)
        # cannot go below two stops
        bar.removeSelected()
        self.assertEqual(len(bar.stops()), 3)

    def test_save_round_trip(self):
        s = self._make_setting()
        w = self.controls.GradientFill(s)
        w.saveToSetting()
        self.assertEqual(s.val['transparency'], 30)
        self.assertEqual(s.val['stops'],
                         [(0.0, '#ff0000'), (0.5, '#00ff00'), (1.0, '#0000ff')])
        self.assertTrue(s.val['enabled'])


class TestRectangleBounds(unittest.TestCase):
    """Regression tests for Rectangle explicit-bounds mode (shape.py)."""

    @classmethod
    def setUpClass(cls):
        try:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            import veusz.widgets  # populate the widget registry
            from veusz.widgets.shape import Rectangle
            from veusz import qtall as qt
            app = qt.QApplication.instance() or qt.QApplication([])
            cls.qt = qt
            cls.app = app
            cls.Rectangle = Rectangle
        except Exception:
            raise unittest.SkipTest("Cannot import Qt stack for shape test")

    @staticmethod
    def _make_mock_doc():
        class MockDoc:
            def getData(self, name):
                return None
        return MockDoc()

    def _make_rect(self, parent=None):
        r = self.Rectangle(parent, name='rect1')
        r.document = self._make_mock_doc()
        r.settings.rectPosition = 'bounds'
        return r

    def test_fractional_fallback_no_axes(self):
        """Rect on a page (no graph axes) uses fractional bounds (S4)."""
        r = self._make_rect()  # parent None -> no getAxes
        r.settings.xmin = [0.1]
        r.settings.xmax = [0.6]
        r.settings.ymin = [0.2]
        r.settings.ymax = [0.8]
        xmin, ymin, xmax, ymax = r._getBoundsCoords((0, 0, 300, 200))
        self.assertAlmostEqual(xmin[0], 30.0)
        self.assertAlmostEqual(ymin[0], 160.0)
        self.assertAlmostEqual(xmax[0], 180.0)
        self.assertAlmostEqual(ymax[0], 40.0)

    def test_data_conversion_with_axes(self):
        """Rect inside a graph converts data bounds to plotter coords."""
        r = self._make_rect()

        class MockAxis:
            def dataToPlotterCoords(self, posn, vals):
                return N.asarray(vals) * 100

        class MockParent:
            def getAxes(self, names):
                return (MockAxis(), MockAxis())

        r.parent = MockParent()
        r.settings.xmin = [0.1]
        r.settings.xmax = [0.6]
        r.settings.ymin = [0.2]
        r.settings.ymax = [0.8]
        xmin, ymin, xmax, ymax = r._getBoundsCoords((0, 0, 300, 200))
        self.assertAlmostEqual(xmin[0], 10.0)
        self.assertAlmostEqual(ymin[0], 20.0)
        self.assertAlmostEqual(xmax[0], 60.0)
        self.assertAlmostEqual(ymax[0], 80.0)

    def test_mismatched_lengths_no_crash(self):
        """Bounds arrays of different lengths must not raise (S1)."""
        r = self._make_rect()
        r.settings.xmin = [0.1, 0.3, 0.5]
        r.settings.xmax = [0.4, 0.6, 0.8]
        r.settings.ymin = [0.2]
        r.settings.ymax = [0.7]
        xmin, ymin, xmax, ymax = r._getBoundsCoords((0, 0, 300, 200))
        self.assertEqual(len(xmin), 3)
        self.assertEqual(len(ymin), 1)


class TestBarCI(unittest.TestCase):
    """Test bar-chart confidence-interval error computation (bar.py)."""

    @classmethod
    def setUpClass(cls):
        try:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            import veusz.widgets
            from veusz.widgets.bar import BarPlotter
            from veusz import qtall as qt
            app = qt.QApplication.instance() or qt.QApplication([])
            cls.qt = qt
            cls.app = app
            cls.BarPlotter = BarPlotter
        except Exception:
            raise unittest.SkipTest("Cannot import Qt stack for bar test")

    @staticmethod
    def _make_plotter():
        class DS:
            def __init__(self, data):
                self.data = N.array(data, dtype=float)

        class MockDoc:
            def __init__(self):
                self.data = {'errds': DS([1.0, 2.0, 3.0]),
                             'mind': DS([0.5, 0.6]),
                             'maxd': DS([1.5, 1.6])}

            def getData(self, name):
                return self.data.get(name)

        bp = TestBarCI.BarPlotter(None, name='bar1')
        bp.document = MockDoc()
        return bp

    def test_std_mode(self):
        bp = self._make_plotter()
        vals = N.array([10.0, 20.0, 30.0])
        mn, mx = bp.calculateErrorBars(
            {}, vals, ciMode='std', ciYError='errds', ciMultiplier=2.0)
        self.assertEqual(mn.tolist(), [8.0, 16.0, 24.0])
        self.assertEqual(mx.tolist(), [12.0, 24.0, 36.0])

    def test_custom_mode(self):
        bp = self._make_plotter()
        vals = N.array([10.0, 20.0, 30.0])
        mn, mx = bp.calculateErrorBars(
            {}, vals, ciMode='custom', ciYMin='mind', ciYMax='maxd')
        self.assertEqual(mn.tolist(), [0.5, 0.6])
        self.assertEqual(mx.tolist(), [1.5, 1.6])

    def test_default_serr(self):
        bp = self._make_plotter()
        vals = N.array([10.0, 20.0, 30.0])
        dset = {'serr': N.array([1.0, 1.0, 1.0])}
        mn, mx = bp.calculateErrorBars(dset, vals)
        self.assertEqual(mn.tolist(), [9.0, 19.0, 29.0])
        self.assertEqual(mx.tolist(), [11.0, 21.0, 31.0])

    def test_fillci_default_hidden(self):
        """The CI fill band must be hidden unless the user enables it."""
        bp = self._make_plotter()
        self.assertTrue(bp.settings.FillCI.hide)

    def test_calc_ci_std(self):
        """_calcCI wires the bar's ciMode settings into the bounds."""
        bp = self._make_plotter()
        bp.settings.ciMode = 'std'
        bp.settings.ciYError = 'errds'
        bp.settings.ciMultiplier = 2.0
        vals = N.array([10.0, 20.0, 30.0])
        mn, mx = bp._calcCI({}, vals)
        self.assertEqual(mn.tolist(), [8.0, 16.0, 24.0])
        self.assertEqual(mx.tolist(), [12.0, 24.0, 36.0])

    def test_calc_ci_default_serr(self):
        """_calcCI falls back to dataset serr columns when no ciMode."""
        bp = self._make_plotter()
        vals = N.array([10.0, 20.0, 30.0])
        dset = {'serr': N.array([1.0, 1.0, 1.0])}
        mn, mx = bp._calcCI(dset, vals)
        self.assertIsNotNone(mn)
        self.assertEqual(mn.tolist(), [9.0, 19.0, 29.0])


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