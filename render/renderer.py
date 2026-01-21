from PySide6.QtGui import QFontDatabase, QFont, QPainter, QPixmap, QImage, QColor, QFontMetrics, QPainterPath, QPen
from PySide6.QtCore import QRect, Qt, QPoint
import os
import sys

if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class Renderer:
    def __init__(self, skin_path=None):
        self.font_id = None
        self.font = None
        self._load_font()
        self.reload(skin_path)

    def reload(self, skin_path=None):
        def _get_path(name):
            if skin_path:
                p = os.path.join(skin_path, name)
                if os.path.exists(p):
                    return p
            return os.path.join(ROOT, "assets", "icons", name)

        self.icon_start = self._load_icon(_get_path("start.png"))
        self.icon_pause = self._load_icon(_get_path("pause.png"))
        self.icon_setting = self._load_icon(_get_path("setting.png"))
        self.icon_reset = self._load_icon(_get_path("reset.png"))

    def _load_font(self):
        path = os.path.join(ROOT, "assets", "fonts", "Minecraftia-Regular.ttf")
        if os.path.exists(path):
            self.font_id = QFontDatabase.addApplicationFont(path)
            families = QFontDatabase.applicationFontFamilies(self.font_id)
            if families:
                f = QFont(families[0])
                f.setPixelSize(48)
                f.setStyleStrategy(QFont.NoAntialias)
                self.font = f
        if self.font is None:
            f = QFont("Courier New")
            f.setPixelSize(48)
            f.setStyleStrategy(QFont.NoAntialias)
            self.font = f

    def _load_icon(self, path):
        if os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                return pm
        img = QImage(12, 12, QImage.Format_ARGB32)
        img.fill(QColor(255, 255, 255, 255))
        return QPixmap.fromImage(img)

    def compose(self, base_frame, text, show_pause_icon, show_setting_icon, scale=1, text_color=None, outline_enabled=False, outline_color=None, outline_width=2):
        w = int(base_frame.width() * scale)
        h = int(base_frame.height() * scale)
        canvas = QPixmap(w, h)
        canvas.fill(Qt.transparent)
        p = QPainter(canvas)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.setRenderHint(QPainter.TextAntialiasing, False)
        if text_color is None:
            text_color = QColor(255, 255, 255)
        
        # Auto-scale text to fit
        max_w = 256 - 53 - 5
        fm = QFontMetrics(self.font)
        w_text = fm.horizontalAdvance(text)
        current_font = self.font
        if w_text > max_w:
            factor = max_w / w_text
            new_size = int(48 * factor)
            if new_size < 10: new_size = 10
            f = QFont(self.font)
            f.setPixelSize(new_size)
            current_font = f
            
        p.setFont(current_font)
        p.scale(scale, scale)
        p.drawPixmap(0, 0, base_frame)
        
        # Draw Text with Outline if enabled
        text_rect = QRect(53, 173, 256 - 53, 256 - 173)
        if outline_enabled:
            if outline_color is None:
                outline_color = QColor(0, 0, 0)
            path = QPainterPath()
            # Calculate position manually since drawText uses AlignLeft | AlignTop
            # Default font metric adjustment
            fm = QFontMetrics(current_font)
            # Baseline offset estimation: ascent
            x = text_rect.x()
            y = text_rect.y() + fm.ascent()
            path.addText(x, y, current_font, text)
            
            pen = QPen(outline_color, outline_width)
            p.setPen(pen)
            p.setBrush(text_color)
            p.drawPath(path)
        else:
            p.setPen(text_color)
            p.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, text)

        # Buttons at 24x24
        btn_size = 24
        p.drawPixmap(QRect(132, 230, btn_size, btn_size), self.icon_pause if show_pause_icon else self.icon_start)
        p.drawPixmap(QRect(164, 230, btn_size, btn_size), self.icon_reset)
        if show_setting_icon:
            p.drawPixmap(QRect(196, 230, btn_size, btn_size), self.icon_setting)
        p.end()
        return canvas
