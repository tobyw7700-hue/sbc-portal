#!/bin/bash
# Build SBC Portal as a macOS .app bundle
# Run from the sbc_portal_v2 directory: bash build_app.sh

echo "=== SBC Portal — macOS App Builder ==="

# Check for py2app
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "Installing py2app..."
    pip3 install py2app --break-system-packages
fi

# Create setup.py for py2app
cat > setup_app.py << 'EOF'
from setuptools import setup

APP      = ["main.py"]
DATA     = [("assets", ["assets/sbc_crest.png", "assets/sbc_crest.svg"])]
OPTIONS  = {
    "argv_emulation":  False,
    "iconfile":        "assets/sbc_crest.icns" if __import__("os").path.exists("assets/sbc_crest.icns") else None,
    "packages":        ["tkinter","requests","bs4","cryptography","PIL"],
    "includes":        ["scraper","ui","data"],
    "plist": {
        "CFBundleName":             "SBC Portal",
        "CFBundleDisplayName":      "SBC Portal",
        "CFBundleIdentifier":       "au.vic.sbc.portal",
        "CFBundleVersion":          "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "NSHighResolutionCapable":  True,
        "LSMinimumSystemVersion":   "11.0",
        "NSAppTransportSecurity":   {"NSAllowsArbitraryLoads": True},
    },
}

setup(
    name="SBC Portal",
    app=APP,
    data_files=DATA,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
EOF

echo "Building .app bundle..."
python3 setup_app.py py2app --quiet 2>&1 | tail -20

if [ -d "dist/SBC Portal.app" ]; then
    echo ""
    echo "✅ Success! App built at: dist/SBC Portal.app"
    echo ""
    echo "To install: drag 'SBC Portal.app' to your Applications folder"
    echo ""
    echo "Note: On first launch, right-click → Open (to bypass Gatekeeper)"
    open dist/
else
    echo ""
    echo "❌ Build failed. Trying PyInstaller instead..."
    pip3 install pyinstaller --break-system-packages
    pyinstaller --windowed \
        --name "SBC Portal" \
        --add-data "assets:assets" \
        --add-data "scraper:scraper" \
        --add-data "ui:ui" \
        --add-data "data:data" \
        --hidden-import tkinter \
        --hidden-import requests \
        --hidden-import bs4 \
        --hidden-import cryptography \
        --noconfirm \
        main.py
    if [ -d "dist/SBC Portal.app" ]; then
        echo "✅ PyInstaller build succeeded: dist/SBC Portal.app"
        open dist/
    else
        echo "❌ Both builders failed. Use 'python3 main.py' to run directly."
    fi
fi
