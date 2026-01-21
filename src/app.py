from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QLocale, Qt
import sys, os

# Copyright (c) 2025 @杰某official
# Released under the Apache License 2.0.
# See LICENSE file for details.

# ensure project root is on sys.path when running as script
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.config_service import ConfigService
from ui.main_window import MainWindow

def main():
    # Force integer scale factors to ensure sharp pixel art
    # This prevents fractional scaling (e.g. 125% -> 1x, 150% -> 2x)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.Round
    )

    app = QApplication(sys.argv)
    
    # Load translations
    from PySide6.QtCore import QTranslator, QLibraryInfo
    try:
        location = QLibraryInfo.LibraryLocation.TranslationsPath
    except AttributeError:
        location = QLibraryInfo.TranslationsPath
        
    path = QLibraryInfo.path(location)
    translator = QTranslator(app)
    if translator.load("qt_zh_CN", path):
        app.installTranslator(translator)
        
    ConfigService.ensure_defaults()
    cfg = ConfigService.load()
    if cfg.get("language") == "zh-CN":
        QLocale.setDefault(QLocale(QLocale.Chinese, QLocale.China))
    win = MainWindow(cfg)
    tray_ico = os.path.join(ROOT, "assets", "tray", "tray.ico")
    tray_png = os.path.join(ROOT, "assets", "tray", "tray.png")
    icon = QIcon(tray_ico) if os.path.exists(tray_ico) else (QIcon(tray_png) if os.path.exists(tray_png) else QIcon())
    app.setWindowIcon(icon)
    win.setWindowIcon(icon)
    def _flush_stats():
        try:
            if hasattr(win, "stats") and win.stats:
                win.stats.flush()
        except Exception:
            pass
    app.aboutToQuit.connect(_flush_stats)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
