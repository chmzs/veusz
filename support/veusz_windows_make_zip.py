#!/usr/bin/env python3
"""Package the PyInstaller build output (support/dist/veusz_main) into a
portable zip whose top level is the app itself (veusz.exe etc.) -- no
extra 'veusz_main' wrapper directory -- matching the upstream release zip.

Usage: pixi run python support/veusz_windows_make_zip.py
Output: support/installer_out/veusz-<VERSION>-windows-x64.zip
"""

import os
import sys
import zipfile


def getVersion():
    with open(os.path.join(os.path.dirname(__file__), "..", "VERSION")) as f:
        return f.read().strip()


def main(argv):
    thisdir = os.path.dirname(os.path.abspath(__file__))
    distdir = os.path.join(thisdir, "dist", "veusz_main")
    outdir = os.path.join(thisdir, "installer_out")
    version = getVersion()

    outname = os.path.join(outdir, f"veusz-{version}-windows-x64.zip")
    os.makedirs(outdir, exist_ok=True)

    if not os.path.isdir(distdir):
        print(f"ERROR: build output not found at {distdir}")
        print("Run PyInstaller first: pixi run python -m PyInstaller "
              "support/veusz_windows_pyinst.spec --distpath support/dist "
              "--workpath support/build")
        return 1

    # Strip the 'veusz_main' root dir so the zip unpacks to veusz.exe etc.
    with zipfile.ZipFile(outname, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(distdir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, distdir)
                z.write(full, rel)

    print(f"Wrote {outname} ({os.path.getsize(outname)} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))