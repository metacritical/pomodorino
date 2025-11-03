# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pomodoro_pyqt.py'],
    pathex=[],
    binaries=[],
    datas=[('pomodoro.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    # speed up startup: avoid compressed archive
    noarchive=True,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    [],
    [],
    name='Pomodoro Timer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # avoid UPX compression (faster startup)
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pomodoro.png'],
    exclude_binaries=True,
)

# Assemble onedir app contents (faster startup vs onefile)
coll = COLLECT(
    exe,
    a.binaries,
    getattr(a, 'zipfiles', []),
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Pomodoro Timer',
)

app = BUNDLE(
    coll,
    name='PomodoroTimer.app',
    icon='pomodoro.png',
    bundle_identifier='com.pomodorino.timer',
)
