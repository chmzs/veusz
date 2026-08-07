# -*- mode: python -*-

# windows pyinstaller file

import glob
import os.path

icon = os.path.abspath('icons\\veusz.ico')

# exclude optional heavy deps that Veusz does not use.
# matplotlib is pulled in transitively by astropy but Veusz has its own
# plotting engine, so exclude it and the astropy.visualization submodules
# that depend on it. Also exclude testing/other heavy libs.
excludes = {
    'matplotlib', 'matplotlib.backends', 'matplotlib.pyplot',
    'astropy.visualization', 'astropy.visualization.wcsaxes', 'astropy.visualization.*',
    'pyarrow', 'pandas', 'scipy', 'sklearn', 'numba', 'llvmlite',
    'IPython', 'jupyter', 'notebook', 'ipykernel', 'sphinx',
    'pytest', 'pytest_asyncio', 'pytest_mock', 'pytest_cov',
    'cryptography', 'cryptography.hazmat', 'cryptography.hazmat.primitives',
    'cffi', 'pycparser',
    'requests', 'urllib3', 'chardet', 'idna', 'certifi',
    'docutils', 'pygments', 'jinja2', 'markupsafe',
}

analysis = Analysis(
    ['..\\veusz\\veusz_main.py'],
    hiddenimports=[
        'multiprocessing', 'multiprocessing.context', 'multiprocessing.reduction',
        'socket', '_socket',
        '_ctypes',
        'h5py.defs', 'h5py.utils', 'h5py.h5ac', 'h5py._proxy',
        'iminuit', 'iminuit.latex', 'iminuit.util',
        'astropy.io.fits', 'astropy.table', 'astropy.units', 'astropy.coordinates',
        'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtPrintSupport',
        'PyQt6.QtSvg', 'PyQt6.QtOpenGLWidgets',
        'veusz.helpers.threed', 'veusz.helpers.qtmml',
        'veusz.helpers.recordpaint', 'veusz.helpers._nc_cntr', 'veusz.helpers.qtloops',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=list(excludes))

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
    contents_directory='.', # do not use _internal
    icon=icon)

# add necessary documentation, licence
data_glob = [
    'VERSION',
    'ChangeLog',
    'AUTHORS',
    'README.md',
    'INSTALL.md',
    'COPYING',
    'icons/*.png',
    'icons/*.ico',
    'icons/*.svg',
    'examples/*.vsz',
    'examples/*.dat',
    'examples/*.csv',
    'examples/*.py',
    'ui/*.ui',
]

datas = analysis.datas
for pattern in data_glob:
    for fn in glob.glob(pattern):
        datas.append((fn, fn, 'DATA'))

# add API files
datas += [
    ('embed.py', 'veusz/embed.py', 'DATA'),
    ('__init__.py', 'veusz/__init__.py', 'DATA'),
]

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    datas,
    strip=False,
    upx=False,
    name='veusz_main'
)