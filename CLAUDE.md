# Veusz Development Guide

## Project Overview
Veusz is a scientific plotting package (forked from https://github.com/veusz/veusz). Written in Python with C++ extensions (SIP/PyQt6).

## Current Version & Environment (v4.2.1.1-fork)
- **Veusz version**: 4.2.1.1-fork (upstream 4.2.1)
- **Python**: 3.13.12 (pixi geo env uses 3.13+)
- **Numpy**: 2.4.4
- **Qt**: 6.10.2
- **PyQt**: 6.11.0
- **SIP**: 6.15.2

## Source Code Structure

```
veusz/              # Main Python package (source code)
├── __init__.py
├── embed.py              # Embedding Veusz in other programs
├── embed_remote.py       # Remote embedding
├── veusz_main.py         # Main entry point
├── veusz_listen.py       # DBUS/SAMP listener
├── dataimport/           # Data import plugins
├── datasets/             # Dataset handling
├── dialogs/              # UI dialogs
├── document/             # Document model
├── helpers/              # C++ extensions (built from src/)
├── plugins/              # Plugin system
├── qtwidgets/            # Qt widgets
├── setting/              # Settings/preferences
├── utils/                # Utility functions
├── widgets/              # Plotting widgets
└── windows/              # Main window UI

src/                # C++ extension source (compiled to veusz/helpers/)
├── nc_cntr/         # Contour plotting (C)
├── qtloops/         # Qt helper loops (C++)
├── qtmml/           # MathML widget (C++)
├── recordpaint/     # Paint recording device (C++)
└── threed/          # 3D rendering (C++)

support/            # Build/packaging scripts
├── build/         # PyInstaller build artifacts (gitignored)
├── dist/          # PyInstaller dist output (gitignored)
├── hooks/         # PyInstaller hooks (hook-astropy.py)
├── ci/            # CI scripts
├── veusz_windows_pyinst.spec  # Windows PyInstaller spec
├── veusz_linux_pyinst.spec    # Linux PyInstaller spec
├── veusz_mac_pyinst.spec      # macOS PyInstaller spec
└── zi/            # ZIP installer helpers

Documents/              # Documentation source (upstream)
├── api/                #   API doc generation
├── manual-source/      #   Manual source (reST)
├── manual/             #   Built manual (gitignored)
└── man-page/           #   Man pages

dev-docs/               # Fork development docs (your additions)
├── dev_docs.md         #   Development成果文档
└── plans/              #   Development plans

tests/              # Test suite
├── selftests/      # Self-tests (run with pixi task)

examples/           # Example .vsz files
icons/              # Application icons
ui/                 # Qt .ui files
translation/        # Translation files (.ts/.qm)
scripts/            # Utility scripts
```

## Local Dev Files (Gitignored)
- `bug_log/` - Development debug logs
- `_edit_gradient.py` - Temp script
- `*.log` - Log files
- `.pixi/` - Pixi virtual environment
- `.pytest_cache/`, `__pycache__/` - Python cache

## Build Artifacts (Gitignored)
- `support/build/` - PyInstaller build intermediates
- `support/dist/` - PyInstaller final executables
- `veusz/helpers/*.pyd` / `*.so` - Compiled C++ extensions
- `veusz.egg-info/` - Package metadata
- `Documents/manual/` - Built documentation (upstream)
- `.pytest_cache/`, `__pycache__/` - Python cache
- `.pixi/` - Pixi virtual environment
- `bug_log/` - Development debug logs
- `_edit_gradient.py` - Temp script
- `aqtinstall.log` - Install log

## Development Commands

### Using pixi (recommended)
```bash
# Run tests
pixi run test

# Run Veusz
pixi run veusz

# Install in editable mode
pixi run install
```

### Manual Python
```bash
# Run from source
python -m veusz.veusz_main

# Run tests
python tests/selftests/test_gradient_fill.py

# Build C++ extensions
python setup.py build_ext --inplace

# Install editable
pip install -e .
```

## Key Files
- `pixi.toml` - Pixi project config (dependencies, tasks)
- `pixi.lock` - Locked dependencies (commit this)
- `setup.py` - setuptools build config (C++ extensions via SIP)
- `pyproject.toml` - Modern Python packaging config
- `VERSION` - Version number
- `support/veusz_windows_pyinst.spec` - Windows installer spec

## Architecture Notes
- **Main package**: `veusz/` (pure Python + imported C++ extensions)
- **C++ extensions**: Built from `src/` into `veusz/helpers/`
- **SIP**: Used for PyQt6 bindings (via `pyqt_setuptools`)
- **Entry point**: `veusz.veusz_main:main`
- **GUI**: PyQt6 (Qt6)

## Key Architecture Components (Fork Additions)

### Gradient System (`veusz/utils/gradient.py`)
- `GradientConfig` - enabled/type/angle/stops/transparency/midpoint
- `create_linear/radial_gradient` - Create Qt gradients
- `_add_gradient_stops` - Apply transparency to stops
- `remap_stops_for_midpoint` - Midpoint remapping for diverging colormaps
- `create_gradient_from_config` - Supports `midpoint` override (for `gradientCenterValue`)
- `PRESETS` - 35 presets: 9 diverging (rdbu, brbg, spectral, piyg, prgn, puor, rdgy, rdylbu, rdylgn) + 22 sequential (viridis, plasma, inferno, magma, cividis, turbo + 16 ColorBrewer) + 4 legacy

### Rendering Entry (`veusz/utils/extbrushfilling.py`)
- `brushExtFillPath` - Single fill entry point (gradient/solid/hatch)
- `_brushExtFillPathGradient` - Gradient path with transparency compositing + `gradientCenterValue` support
- `fillToEdgePolygon` / `fillToEdgeTargets` - Unified fillto edge computation

### Settings System (`veusz/setting/setting.py`, `controls.py`)
- `GradientFill` - Gradient settings (enabled, type, angle, stops, transparency, midpoint)
- `Color` - Supports `@axis:x:Line/color` etc. references (14 paths)
- `Color` control - Dropdown (▼) with axis reference menu + clear option
- `GradientFill` control - Interactive `GradientBar` editor + midpoint spinbox
- `GradientBar` - Interactive gradient editor (click/drag/dblclick/drag-out stops)

### Widgets Added
- `veusz/widgets/proportions.py` - `ProportionalScatter` (pie/donut/bar glyphs, scalePoints ∝ √n, wedgeData, barMode stacked/grouped)
- Donut glyph fix: `arcMoveTo` prevents line from origin

### Plugins (`veusz/plugins/toolsplugin.py`)
- `GridGraphLabels` - Batch add sequential labels (a/b/c, A/B/C, 1/2/3) to Grid graphs with prefix/suffix/position/offset

### Settings Persistence
- `FillSet` supports 3/10/11 elements (11th = Gradient)
- `BrushExtended` has `Gradient` sub-setting + `gradientCenterValue` (String, 'Auto'/'zero'/numeric)

## Development Commands

### Using pixi (recommended)
```bash
# Run tests
pixi run test

# Run Veusz
pixi run veusz

# Install in editable mode
pixi run install
```

### Manual Python
```bash
# Run from source
python -m veusz.veusz_main

# Run tests
python tests/selftests/test_gradient_fill.py

# Build C++ extensions
python setup.py build_ext --inplace

# Install editable
pip install -e .
```

## Key Files
- `pixi.toml` - Pixi project config (dependencies, tasks)
- `pixi.lock` - Locked dependencies (commit this)
- `setup.py` - setuptools build config (C++ extensions via SIP)
- `pyproject.toml` - Modern Python packaging config
- `VERSION` - Version number
- `support/veusz_windows_pyinst.spec` - Windows installer spec

## Architecture Notes
- **Main package**: `veusz/` (pure Python + imported C++ extensions)
- **C++ extensions**: Built from `src/` into `veusz/helpers/`
- **SIP**: Used for PyQt6 bindings (via `pyqt_setuptools`)
- **Entry point**: `veusz.veusz_main:main`
- **GUI**: PyQt6 (Qt6)

## Testing
```bash
# Gradient fill tests (pixi task)
pixi run test
# or directly:
python tests/selftests/test_gradient_fill.py
```

## Building Installers (Windows)

All build artifacts go to `support/build/` and `support/dist/` (gitignored).
The fork builds into `support/dist/`, unlike upstream which uses root `dist/`.

```bash
# 1. Run tests first
pixi run test                                    # gradient unit tests
VEUSZ_INPLACE_TEST=1 pixi run python tests/runselftest.py   # full selftests

# 2. PyInstaller build (from project root, outputs to support/dist + support/build)
pixi run python -m PyInstaller support/veusz_windows_pyinst.spec \
  --distpath support/dist --workpath support/build

# 3. Portable zip (optional, no NSIS needed)
cd support/dist
powershell -Command "Compress-Archive -Path 'veusz_main' -DestinationPath 'veusz-<VER>-windows-x64-portable.zip' -Force"

# 4. NSIS installer (requires NSIS, e.g. D:\Program Files (x86)\NSIS)
cd support
python veusz_windows_make_nsi.py veusz_windows_setup.nsi   # generate .nsi from template
mkdir -p installer_out
MSYS_NO_PATHCONV=1 "/d/Program Files (x86)/NSIS/makensis.exe" veusz_windows_setup.nsi
# Output: support/installer_out/veusz-<VER>-windows-x64-setup.exe
```

Requirements: PyInstaller (pixi env), NSIS 3.x, pre-built `veusz/helpers/*.pyd`
(compile once with `python setup.py build_ext --inplace`). VS2022 only needed
for recompiling C++ extensions, not for packaging.

## Git Workflow
- `dev` branch: Active development
- `master` branch: Stable releases
- Commit `pixi.lock` with dependency changes
- Build artifacts in `support/build/`, `support/dist/` are gitignored

## Common Tasks

### Add a C++ extension
1. Add source files to `src/<name>/`
2. Add Extension to `setup.py` ext_modules
3. Run `python setup.py build_ext --inplace`

### Update dependencies
1. Edit `pixi.toml` dependencies
2. Run `pixi install` to update `pixi.lock`
3. Commit both files

### Run with custom Python env
The project uses pixi's `geo` environment (Python 3.13+). See `.pixi/` for env.

## Key Development Learnings & Patterns

### Gradient System
- **Transparency compositing**: `alpha_eff = (100-t_brush)/100 × (100-t_grad)/100` — applies to both solid and gradient paths; 100% either side → skip fill
- **Midpoint remapping**: `remap_stops_for_midpoint(stops, midpoint)` shifts middle color to target offset (0-1); used by `gradientCenterValue` (data value → offset mapping)
- **GradientCenterValue**: Maps data value (e.g., 0) to gradient offset via axis conversion; used for diverging colormaps (white at 0)
- **GradientBar**: Interactive editor — click empty=add stop, drag=move, dblclick=color, drag out=delete; preview 32px with checkerboard

### Color Axis References
- Format: `@axis:x:Line/color`, `@axis:y:MajorTicks/color`, etc. (14 paths: x/y × Line/MajorTicks/MinorTicks/GridLines/MinorGridLines/Label/TickLabels)
- UI: Color control has ▼ button with menu listing all 14 refs + "Clear axis reference"
- Resolution: At paint time, traverses axis settings path, returns resolved QColor

### ProportionalScatter
- Glyphs: `pie` (drawPie), `donut` (arcMoveTo + arcTo for hole), `bar` (stacked/grouped)
- `barMode`: `stacked` (default, segments in one bar) vs `grouped` (side-by-side bars)
- `scalePoints`: radius ∝ √(value/max) × markerSize (area ∝ value)
- Key symbol: uses first row of wedge data (avoids `int(numpy_array)` crash)
- Key symbol draws single pie per wedge, not full dataset

### Bar CI Fill Bands
- `drawCIBand` called from `barDrawGroup`, `barDrawStacked`, `areaDrawStacked`
- `grouped`: each bar gets its own CI band anchored at base
- `stacked`: each segment gets band anchored at its cumulative base
- Length guard: `n = min(len(posns1), len(mincoord), len(maxcoord))` prevents IndexError

### Color Axis Reference Resolution
```python
# In extbrushfilling.py:_brushExtFillPathGradient
center_value = extbrush.get('gradientCenterValue')
if center_value and center_value not in ('Auto', '', None):
    # data value → plotter coord → 0-1 offset → midpoint
```

### Testing Patterns
```bash
# Unit tests (fast)
pixi run python -m pytest tests/selftests/test_gradient_fill.py -q

# Full selftest (78 SVG comparisons)
VEUSZ_INPLACE_TEST=1 pixi run python tests/runselftest.py

# Known issue: test_gradient_fill.py fails in runselftest due to Qt clipboard env
# Run separately via pytest for clean results
```

### CI/CD Patterns
- Three workflows: `github-ubuntu-pip.yml`, `github-windows-pip.yml`, `build-binary-windows.yml`
- All now include `pytest tests/selftests/test_gradient_fill.py` step
- Windows uses `QT_QPA_PLATFORM=minimal` for selftest, `offscreen` for pytest

### Debugging Tips
- **Donut glyph lines to origin**: Use `arcMoveTo` for first segment instead of `arcTo`
- **Key symbol crashes**: Pass single row `[w[0] for w in wedges]` not full arrays
- **Custom CI IndexError**: Guard with `min(len(posns), len(mincoord), len(maxcoord))`
- **Save As checkbox crash**: Capture state via closure before dialog destroys widget

## Common Tasks

### Add a C++ extension
1. Add source files to `src/<name>/`
2. Add Extension to `setup.py` ext_modules
3. Run `python setup.py build_ext --inplace`

### Update dependencies
1. Edit `pixi.toml` dependencies
2. Run `pixi install` to update `pixi.lock`
3. Commit both files

### Run with custom Python env
The project uses pixi's `geo` environment (Python 3.13+). See `.pixi/` for env.