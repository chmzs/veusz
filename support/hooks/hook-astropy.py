# Custom hooks for Veusz Windows build
# Exclude astropy.wcs to avoid subprocess issues with pyinstaller


# Exclude astropy.wcs submodules that cause subprocess issues
excludedimports = ["astropy.wcs", "astropy.wcs.tests"]
