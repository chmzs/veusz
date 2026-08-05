# Veusz Development Guide

## Project Overview
Veusz is a scientific plotting package (forked from https://github.com/veusz/veusz). Written in Python with C++ extensions (SIP/PyQt6).

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

## Testing
```bash
# Gradient fill tests (pixi task)
pixi run test
# or directly:
python tests/selftests/test_gradient_fill.py
```

## Building Installers
Windows:
```bash
# Requires NSIS and PyInstaller
cd support
pyinstaller veusz_windows_pyinst.spec
# Then run veusz_windows_make_nsi.py
```

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
The project uses pixi's `geo` environment (Python 3.14+). See `.pixi/` for env.