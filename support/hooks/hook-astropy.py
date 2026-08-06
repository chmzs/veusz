# Custom hooks for Veusz Windows build
# Exclude astropy.wcs to avoid subprocess issues with pyinstaller

from PyInstaller.utils.hooks import exclude_submodules

# Exclude astropy.wcs submodules that cause subprocess issues
excludedimports = ['astropy.wcs', 'astropy.wcs.tests']