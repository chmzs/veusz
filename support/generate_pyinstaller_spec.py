#!/usr/bin/env python3
"""
Auto-generate PyInstaller spec files for Veusz.
Analyzes the codebase to determine hidden imports, data files, and binaries.
"""

import ast
from pathlib import Path

VEUSZ_ROOT = Path(__file__).parent.parent
VEUSZ_PKG = VEUSZ_ROOT / "veuzz" / "veusz"
SUPPORT_DIR = VEUSZ_ROOT / "support"

# Known patterns
ICON_EXTS = (".png", ".svg", ".ico", ".icns")
UI_EXTS = (".ui",)
EXAMPLE_EXTS = (".vsz", ".dat", ".csv", ".py")
DOC_FILES = ["VERSION", "ChangeLog", "AUTHORS", "README.md", "INSTALL.md", "COPYING"]

# Modules that need explicit hidden imports (from common issues)
KNOWN_HIDDEN_IMPORTS = [
    # h5py
    "h5py.defs",
    "h5py.utils",
    "h5py.h5ac",
    "h5py._proxy",
    # iminuit
    "iminuit",
    "iminuit.latex",
    "iminuit.util",
    # astropy
    "astropy.io.fits",
    "astropy.table",
    "astropy.units",
    "astropy.coordinates",
    # PyQt6
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtPrintSupport",
    "PyQt6.QtSvg",
    "PyQt6.QtOpenGLWidgets",
    # veusz internal
    "veusz.helpers.threed",
    "veusz.helpers.qtmml",
    "veusz.helpers.recordpaint",
    "veusz.helpers._nc_cntr",
    "veusz.helpers.qtloops",
]

# Qt modules to exclude (reduce size)
EXCLUDE_QT_MODULES = [
    "QtWebEngine",
    "QtWebEngineCore",
    "QtWebEngineWidgets",
    "QtWebSockets",
    "QtQml",
    "QtQmlModels",
    "QtQuick",
    "QtDBus",
    "QtNetwork",
    "QtNfc",
    "QtPositioning",
    "QtRemoteObjects",
    "QtScxml",
    "QtSensors",
    "QtSerialPort",
    "QtTextToSpeech",
    "QtWebChannel",
    "QtWebView",
    "QtCharts",
    "QtDataVisualization",
]


def find_python_imports(root_dir):
    """Scan Python files for import statements."""
    imports = set()
    for py_file in root_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except Exception:
            pass
    return imports


def get_data_files():
    """Collect data files to include."""
    data_glob = []

    # Documentation
    for f in DOC_FILES:
        if (VEUSZ_ROOT / f).exists():
            data_glob.append(f)

    # Icons
    data_glob.extend(["icons/*.png", "icons/*.svg", "icons/*.ico", "icons/*.icns"])

    # UI files
    data_glob.append("ui/*.ui")

    # Examples
    for ext in EXAMPLE_EXTS:
        data_glob.append(f"examples/*{ext}")

    return data_glob


def get_api_files():
    """API files needed for embedding."""
    return [
        ("veusz/embed.py", "veusz/embed.py", "DATA"),
        ("veusz/__init__.py", "veusz/__init__.py", "DATA"),
    ]


def generate_windows_spec():
    """Generate Windows PyInstaller spec."""

    spec = f"""# -*- mode: python -*-
# Auto-generated Windows PyInstaller spec for Veusz
# DO NOT EDIT MANUALLY - run python support/generate_pyinstaller_spec.py

import glob
import os.path

icon = os.path.abspath('icons\\\\veusz.ico')

analysis = Analysis(
    ['..\\\\veusz\\\\veusz_main.py'],
    hiddenimports={KNOWN_HIDDEN_IMPORTS!r},
    hookspath=[],
    runtime_hooks=[],
    excludes={EXCLUDE_QT_MODULES!r},
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    exclude_binaries=True,
    name='veusz.exe',
    debug=False,
    strip=None,
    upx=False,
    console=False,
    contents_directory='.',  # do not use _internal
    icon=icon,
)

# add necessary documentation, licence
data_glob = {get_data_files()!r}

datas = analysis.datas
for pattern in data_glob:
    for fn in glob.glob(pattern):
        datas.append((fn, fn, 'DATA'))

# add API files
datas += {get_api_files()!r}

# exclude files listed (currently unused)
excludes = set()
analysis.binaries[:] = [b for b in analysis.binaries if b[0] not in excludes]

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    datas,
    strip=False,
    upx=False,
    name='veusz_main'
)
"""
    return spec


def generate_linux_spec():
    """Generate Linux PyInstaller spec."""
    spec = f"""# -*- mode: python -*-
# Auto-generated Linux PyInstaller spec for Veusz
# DO NOT EDIT MANUALLY - run python support/generate_pyinstaller_spec.py

import glob
import os

# get version
with open('VERSION') as fin:
    version = fin.read().strip()

analysis = Analysis(
    ['../veusz/veusz_main.py'],
    pathex=[],
    hiddenimports={KNOWN_HIDDEN_IMPORTS!r},
    hookspath=None,
    runtime_hooks=None,
    excludes={EXCLUDE_QT_MODULES!r},
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    exclude_binaries=True,
    name='veusz',
    debug=False,
    strip=True,
    upx=False,
    console=True,
)

# add necessary documentation, licence
data_glob = {get_data_files()!r}

datas = analysis.datas
for pattern in data_glob:
    for fn in glob.glob(pattern):
        datas.append((fn, fn, 'DATA'))

# add API files
datas += {get_api_files()!r}

# exclude files listed (currently unused)
excludes = set()
analysis.binaries[:] = [b for b in analysis.binaries if b[0] not in excludes]

# collect together results
outdir = f'veusz-{{version}}'
coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    datas,
    strip=True,
    upx=False,
    name=outdir,
)

# make symlinks to make it easier to find files
print('Making symlinks')
symlink = [
    'ChangeLog', 'AUTHORS', 'README.md', 'INSTALL.md',
    'embed.py', 'COPYING', 'examples',
]
for fn in symlink:
    os.symlink(f'_internal/{{fn}}', f'dist/{{outdir}}/{{fn}}')

# make a highly compressed tar file
print(f'Creating tar file')
tardir = 'tar'
tarfn = f'{{tardir}}/veusz-{{version}}-linux-x86_64.tar.xz'
os.makedirs(tardir, exist_ok=True)
cmd = f'tar -C dist/ --owner=0 --group=0 -cf - veusz-{{version}} | xz -9 -c - > {{tarfn}}'
print(cmd)
retn = os.system(cmd)
if retn != 0:
    raise RuntimeError('tar failed')
"""
    return spec


def generate_macos_spec():
    """Generate macOS PyInstaller spec."""
    spec = f"""# -*- mode: python -*-
# Auto-generated macOS PyInstaller spec for Veusz
# DO NOT EDIT MANUALLY - run python support/generate_pyinstaller_spec.py

import glob

block_cipher = None

badqt = {EXCLUDE_QT_MODULES!r}

a = Analysis(
    ['../veusz/veusz_main.py'],
    binaries=[],
    datas=[],
    hiddenimports={KNOWN_HIDDEN_IMPORTS!r},
    hookspath=[],
    runtime_hooks=[],
    excludes=[('PyQt6.'+mod) for mod in badqt],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)

# add necessary documentation, licence
binaries = a.binaries
for bin in ('VERSION', 'ChangeLog', 'AUTHORS', 'README.md', 'INSTALL.md', 'COPYING'):
    binaries += [ (bin, bin, 'DATA') ]

binaries += {get_api_files()!r}

# remove not needed qt
# binaries[:] = [b for b in binaries if b[0] not in set(badqt)]

# add various required files to distribution
for f in (
        glob.glob('icons/*.png')  + glob.glob('icons/*.ico') +
        glob.glob('icons/*.svg') + glob.glob('icons/*.icns') +
        glob.glob('examples/*.vsz') +
        glob.glob('examples/*.dat') + glob.glob('examples/*.csv') +
        glob.glob('examples/*.py') +
        glob.glob('ui/*.ui')
):
    binaries.append( (f, f, 'DATA') )

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='veusz',
    debug=False,
    strip=True,
    upx=False,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    name='veusz'
)

version = open('VERSION').read().strip()

app = BUNDLE(
    coll,
    name='Veusz.app',
    icon='../icons/veusz.icns',
    bundle_identifier='org.veusz',
    info_plist={{
        'CFBundleShortVersionString': version,
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',

        'CFBundleDocumentTypes': [{{
                'CFBundleTypeIconFile': 'veusz.icns',
                'CFBundleTypeName': 'Veusz document',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['org.veusz.document', 'org.veusz.document_hdf5'],
                'LSHandlerRank': 'Owner',
            }}],
        'UTExportedTypeDeclarations': [
            {{
                'UTTypeConformsTo': ['public.data'],
                'UTTypeDescription': 'Veusz document',
                'UTTypeIconFile': 'veusz.icns',
                'UTTypeIdentifier': 'org.veusz.document',
                'UTTypeTagSpecification': {{
                    'public.filename-extension': 'vsz',
                    'public.mime-type': 'application/vnd.veusz.document',
                }}
            }},
            {{
                'UTTypeConformsTo': ['public.data'],
                'UTTypeDescription': 'Veusz HDF5 document',
                'UTTypeIconFile': 'veusz.icns',
                'UTTypeIdentifier': 'org.veusz.document_hdf5',
                'UTTypeTagSpecification': {{
                    'public.filename-extension': 'vszh5',
                    'public.mime-type': 'application/vnd.veusz.document_hdf5',
                }}
            }},
        ]
    }}
)
"""
    return spec


def main():
    """Generate all spec files."""
    specs = {
        "veusz_windows_pyinst.spec": generate_windows_spec(),
        "veusz_linux_pyinst.spec": generate_linux_spec(),
        "veusz_mac_pyinst.spec": generate_macos_spec(),
    }

    for filename, content in specs.items():
        path = SUPPORT_DIR / filename
        path.write_text(content, encoding="utf-8")
        print(f"Generated {path}")

    print("\nDone! Review and test the generated specs.")


if __name__ == "__main__":
    main()
