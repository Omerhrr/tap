#!/bin/bash
# Run script for Tap & Split Kivy App

cd "$(dirname "$0")"

# Check if dependencies are installed
if ! python3 -c "import kivymd" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the app
python3 main.py
