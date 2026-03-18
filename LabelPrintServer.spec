# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['tray_app_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('icons', 'icons'), ('VERSION', '.'), ('README.md', '.'), ('FUNCTIONS.md', '.'), ('db_settings.json', '.'), ('update_config.json', '.')],
    hiddenimports=['flask', 'waitress', 'pyodbc', 'pystray', 'PIL'],
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
    a.binaries,
    a.datas,
    [],
    name='LabelPrintServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\app_icon.ico'],
)
