#!/usr/bin/env bash
set -euo pipefail

# Build a proper macOS .app with PyInstaller

APP_NAME="PomodoroTimer"
ICON="pomodoro.png"
ENTRY="pomodoro_pyqt.py"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "pyinstaller not found. Please install it (e.g. pip install pyinstaller)." >&2
  exit 1
fi

# Ensure icon exists
if [ ! -f "$ICON" ]; then
  echo "Icon $ICON not found next to $0" >&2
  exit 1
fi

echo "Building $APP_NAME.app..."

pyinstaller \
  --windowed \
  --name "$APP_NAME" \
  --icon "$ICON" \
  --add-data "$ICON:." \
  "$ENTRY"

echo "Build complete. Find the app under dist/$APP_NAME.app"

