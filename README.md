# Pomodorino 🍅

Desktop Pomodoro timer built with Python + PyQt5 for macOS (works cross‑platform for notifications). Comes with a fast macOS .app bundle and a clean system‑theme UI with colorful Start/Pause/Resume/Reset buttons.

## Quick Start (macOS .app)

- Build the app bundle:
  - `bin/build_app`
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
  - `python3 pomodoro_pyqt.py`
- Build a dev bundle from spec:
  - `pyinstaller "Pomodoro Timer.spec"`

## Repo Layout

- `pomodoro_pyqt.py` — main PyQt app
- `bin/build_app` — build script for macOS .app
- `Pomodoro Timer.spec` — PyInstaller config (fast onedir bundle)
- `old_archieve/` — older scripts (bash/ruby/AppleScript) kept for reference

## Git Ignore

- Build outputs are ignored: `build/`, `dist/`
- Python caches: `__pycache__/`, `*.pyc`
- macOS Finder files: `.DS_Store`

---

Made with ❤️ by Pankaj Doharey
