#!/bin/bash
echo "Setting up SBC Academic Portal..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -r requirements.txt --quiet
echo "Done! Run with: .venv/bin/python main.py"
