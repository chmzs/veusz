# -*- mode: python -*-
# Auto-generated macOS PyInstaller spec for Veusz
# DO NOT EDIT MANUALLY - run python support/generate_pyinstaller_spec.py

import glob

block_cipher = None

badqt = ['QtWebEngine', 'QtWebEngineCore', 'QtWebEngineWidgets', 'QtWebSockets', 'QtQml', 'QtQmlModels', 'QtQuick', 'QtDBus', 'QtNetwork', 'QtNfc', 'QtPositioning', 'QtRemoteObjects', 'QtScxml', 'QtSensors', 'QtSerialPort', 'QtTextToSpeech', 'QtWebChannel', 'QtWebView', 'QtCharts', 'QtDataVisualization']

a = Analysis(
    ['../veusz/veusz_main.py'],
    binaries=[],
    datas=[],
    hiddenimports=['h5py.defs', 'h5py.utils', 'h5py.h5ac', 'h5py._proxy', 'iminuit', 'iminuit.latex', 'iminuit.util', 'astropy.io.fits', 'astropy.table', 'astropy.units', 'astropy.coordinates', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtOpenGLWidgets', 'veusz.helpers.threed', 'veusz.helpers.qtmml', 'veusz.helpers.recordpaint', 'veusz.helpers._nc_cntr', 'veusz.helpers.qtloops'],
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

binaries += [('veusz/embed.py', 'veusz/embed.py', 'DATA'), ('veusz/__init__.py', 'veusz/__init__.py', 'DATA')]

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
    info_plist={
        'CFBundleShortVersionString': version,
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',

        'CFBundleDocumentTypes': [{
                'CFBundleTypeIconFile': 'veusz.icns',
                'CFBundleTypeName': 'Veusz document',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['org.veusz.document', 'org.veusz.document_hdf5'],
                'LSHandlerRank': 'Owner',
            }],
        'UTExportedTypeDeclarations': [
            {
                'UTTypeConformsTo': ['public.data'],
                'UTTypeDescription': 'Veusz document',
                'UTTypeIconFile': 'veusz.icns',
                'UTTypeIdentifier': 'org.veusz.document',
                'UTTypeTagSpecification': {
                    'public.filename-extension': 'vsz',
                    'public.mime-type': 'application/vnd.veusz.document',
                }
            },
            {
                'UTTypeConformsTo': ['public.data'],
                'UTTypeDescription': 'Veusz HDF5 document',
                'UTTypeIconFile': 'veusz.icns',
                'UTTypeIdentifier': 'org.veusz.document_hdf5',
                'UTTypeTagSpecification': {
                    'public.filename-extension': 'vszh5',
                    'public.mime-type': 'application/vnd.veusz.document_hdf5',
                }
            },
        ]
    }
)
