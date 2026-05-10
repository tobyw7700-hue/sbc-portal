#!/bin/bash
# SBC Portal launcher — double-click this file to run the app.
# Uses the bundled .venv — no Python install needed.

cd "$(dirname "$0")"
PORTAL_DIR="$(pwd)"

echo "SBC Academic Portal"
echo "==================="
echo ""

# ── Fix hardcoded paths in the bundled .venv ──────────────────────────────────
# The .venv was built on a specific Mac so all shebangs point to the original
# path. We patch them to point to this folder so it works on any Mac.

OLD_PATH=$(head -1 .venv/bin/pip 2>/dev/null | sed 's|#!||' | sed 's|/bin/python.*||')

if [ -n "$OLD_PATH" ] && [ "$OLD_PATH" != "$PORTAL_DIR" ]; then
    echo "Relocating bundled Python environment..."
    find .venv/bin -type f | while read f; do
        if file "$f" 2>/dev/null | grep -q "text"; then
            sed -i '' "s|$OLD_PATH|$PORTAL_DIR|g" "$f" 2>/dev/null
        fi
    done
    if [ -f ".venv/pyvenv.cfg" ]; then
        sed -i '' "s|$OLD_PATH|$PORTAL_DIR|g" .venv/pyvenv.cfg 2>/dev/null
    fi
    echo "Done."
    echo ""
fi

# ── Verify the bundled Python works ───────────────────────────────────────────
if ! .venv/bin/python3 -c "import tkinter; tkinter.Tk().destroy()" 2>/dev/null; then
    echo "ERROR: Bundled Python environment is not working."
    echo ""
    echo "Please re-download the latest version from:"
    echo "  https://github.com/tobyw7700-hue/sbc-portal/releases/latest"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# ── Launch ─────────────────────────────────────────────────────────────────────
echo "Starting SBC Portal..."
echo ""
.venv/bin/python3 main.py
