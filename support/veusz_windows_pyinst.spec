# -*- mode: python -*-
# Auto-generated Windows PyInstaller spec for Veusz
# DO NOT EDIT MANUALLY - run python support/generate_pyinstaller_spec.py

import glob
import os.path

icon = os.path.abspath('icons\\veusz.ico')

analysis = Analysis(
    ['..\\veusz\\veusz_main.py'],
    hiddenimports=['h5py.defs', 'h5py.utils', 'h5py.h5ac', 'h5py._proxy', 'iminuit', 'iminuit.latex', 'iminuit.util', 'astropy.io.fits', 'astropy.table', 'astropy.units', 'astropy.coordinates', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtOpenGLWidgets', 'veusz.helpers.threed', 'veusz.helpers.qtmml', 'veusz.helpers.recordpaint', 'veusz.helpers._nc_cntr', 'veusz.helpers.qtloops'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['QtWebEngine', 'QtWebEngineCore', 'QtWebEngineWidgets', 'QtWebSockets', 'QtQml', 'QtQmlModels', 'QtQuick', 'QtDBus', 'QtNetwork', 'QtNfc', 'QtPositioning', 'QtRemoteObjects', 'QtScxml', 'QtSensors', 'QtSerialPort', 'QtTextToSpeech', 'QtWebChannel', 'QtWebView', 'QtCharts', 'QtDataVisualization'],
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
data_glob = ['VERSION', 'ChangeLog', 'AUTHORS', 'README.md', 'INSTALL.md', 'COPYING', 'icons/*.png', 'icons/*.svg', 'icons/*.ico', 'icons/*.icns', 'ui/*.ui', 'examples/*.vsz', 'examples/*.dat', 'examples/*.csv', 'examples/*.py']

datas = analysis.datas
for pattern in data_glob:
    for fn in glob.glob(pattern):
        datas.append((fn, fn, 'DATA'))

# add API files
datas += [('veusz/embed.py', 'veusz/embed.py', 'DATA'), ('veusz/__init__.py', 'veusz/__init__.py', 'DATA')]

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
