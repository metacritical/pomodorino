# Pomodorino 🍅

Desktop Pomodoro timer built with Python + PyQt5 for macOS (works cross‑platform for notifications). Clean, focused UI:
- Main window uses a single toggle button (Start/Pause/Resume) plus Reset.
- Fullscreen session view shows large time with Pause and Reset.

## Quick Start (macOS .app)

- Download prebuilt app:
  - Direct zip (0.0.1): https://github.com/metacritical/pomodorino/releases/download/0.0.1/PomodoroTimer-0.0.1.zip
  - All releases: https://github.com/metacritical/pomodorino/releases
- Build the app bundle:
  - `./build_app`
- Launch the app:
  - `open dist/PomodoroTimer.app`

Notes
- The app runs with a menu‑bar tray icon. Close hides to tray; use the tray to Show or Quit.
- No external dependencies required for the bundled app.

## Cross‑Platform Notifications

- macOS: `osascript` notifications
- Linux: `notify-send`
- Windows: `win10toast`

If a notifier is not available, the app logs a fallback message.

## Development

- Run the Python app directly:
  - `python3 src/pomodoro_pyqt.py`
  - Or in fullscreen after Start from the main window.

## Repo Layout

- `src/pomodoro_pyqt.py` — main PyQt app
- `build_app` — root build script (cleans and builds)
- `pomodoro.png` — app icon
- `dist/` and `build/` — build outputs

## Dependencies

- PyInstaller and PyQt5 for building from source.
- Install with:
  - `pip install -r requirements.txt`

## Git Ignore

- Build outputs are ignored: `build/`, `dist/`
- Python caches: `__pycache__/`, `*.pyc`
- macOS Finder files: `.DS_Store`

---

Made with ❤️ by Pankaj Doharey
