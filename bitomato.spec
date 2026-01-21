# -*- mode: python ; coding: utf-8 -*-
import os
from PySide6.QtCore import QLibraryInfo

try:
    # Try new enum location
    location = QLibraryInfo.LibraryLocation.TranslationsPath
except AttributeError:
    # Fallback to old location
    location = QLibraryInfo.TranslationsPath

trans_path = QLibraryInfo.path(location)
trans_datas = []
# Include common Chinese translation files
for f in ['qt_zh_CN.qm', 'qtbase_zh_CN.qm', 'widgets_zh_CN.qm']:
    p = os.path.join(trans_path, f)
    if os.path.exists(p):
        trans_datas.append((p, 'PySide6/translations'))

a = Analysis(
    ['src\\app.py'],
    pathex=['D:\\PyCharm\\tomato2'],
    binaries=[],
    datas=[('assets', 'assets'), ('skins', 'skins'), ('LICENSE', '.'), ('免责声明.txt', '.'), ('使用说明.txt', '.')] + trans_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtXml', 'PySide6.QtSvg', 'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtRemoteObjects', 'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtWebChannel', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets', 'PySide6.Qt3DCore', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender', 'PySide6.Qt3DExtras', 'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'cv2', 'numpy', 'PIL', 'matplotlib', 'pandas', 'scipy', 'tkinter', 'unittest', 'pydoc', 'email', 'html', 'http', 'xml', 'multiprocessing', 'distutils', 'lib2to3', 'test', 'concurrent'],
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
    name='bitomato',
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
    icon='assets\\tray\\tray.ico',
)
