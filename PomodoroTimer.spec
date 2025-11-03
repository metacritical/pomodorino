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
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PomodoroTimer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pomodoro.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PomodoroTimer',
)
app = BUNDLE(
    coll,
    name='PomodoroTimer.app',
    icon='pomodoro.png',
    bundle_identifier=None,
)
