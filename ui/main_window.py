from PySide6.QtWidgets import QWidget, QApplication, QMenu, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog
from PySide6.QtGui import QPainter, QPixmap, QAction, QDesktopServices
from PySide6.QtCore import Qt, QTimer, QRect, QUrl
from services.timer_service import TimerService

# Copyright (c) 2025 @杰某official
# Released under the Apache License 2.0.
# See LICENSE file for details.

from services.config_service import ConfigService
from services.audio_service import AudioService
from services.stats_service import StatsService
from services.backup_service import BackupService
from skin.loader import load_skin
from render.renderer import Renderer
from ui.settings_dialog import SettingsDialog
from ui.scale_dialog import ScaleDialog
from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtGui import QIcon, QColor
import os
import sys
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class MainWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("番茄钟")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.Tool, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.scale = float(self.config.get("uiScale", 1))
        self.setFixedSize(int(256 * self.scale), int(256 * self.scale))
        
        skin_id = self.config.get("skinId", "default")
        if os.path.isabs(skin_id):
            skin_path = skin_id
        else:
            skin_path = os.path.join(ROOT, "skins", skin_id)
            
        self.renderer = Renderer(skin_path)
        try:
            self.frames, self.is_animated, self.skin_meta = load_skin(skin_id)
        except Exception:
            # Fallback to default if loading fails
            self.config["skinId"] = "default"
            skin_id = "default"
            skin_path = os.path.join(ROOT, "skins", "default")
            self.frames, self.is_animated, self.skin_meta = load_skin(skin_id)
            
        # Apply skin text color if defined
        if "textColor" in self.skin_meta:
            self.config["textColor"] = self.skin_meta["textColor"]

        self.frame_index = 0
        self.text = "{:02d}:{:02d}".format(self.config.get("workMinutes", 25), 0)
        self.show_pause_icon = False
        self.show_setting_icon = True
        self.stats = StatsService()
        self.timer_service = TimerService(self.config, stats_service=self.stats)
        self.audio = AudioService(self.config)
        self.backup_service = BackupService(self.config)
        self.timer_service.ticked.connect(self._on_ticked)
        self.timer_service.phase_changed.connect(self._on_phase)
        self.timer_service.completed.connect(self._on_completed)
        self.anim = QTimer()
        self.anim.setInterval(self.config.get("frameDuration", 100))
        self.anim.timeout.connect(self._next_frame)
        if self.is_animated:
            self.anim.start()
        self.tray = QSystemTrayIcon(self)
        self._setup_tray()
        self._dragging = False
        self._drag_offset = None
        self._composed = None
        self.text_color = QColor(self.config.get("textColor", "#FFFFFF"))
        self.flash_timer = QTimer()
        self.flash_timer.setInterval(150)
        self.flash_timer.timeout.connect(self._flash_step)
        self._flash_remaining = 0

    def _setup_tray(self):
        skin_id = self.config.get("skinId", "default")
        if os.path.isabs(skin_id):
            skin_path = skin_id
        else:
            skin_path = os.path.join(ROOT, "skins", skin_id)

        tray_path_ico = os.path.join(skin_path, "tray.ico")
        tray_path_png = os.path.join(skin_path, "tray.png")
        
        if not os.path.exists(tray_path_ico) and not os.path.exists(tray_path_png):
            tray_path_ico = os.path.join(ROOT, "assets", "tray", "tray.ico")
            tray_path_png = os.path.join(ROOT, "assets", "tray", "tray.png")
            
        icon = QIcon(tray_path_ico) if os.path.exists(tray_path_ico) else QIcon()
        if icon.isNull() and os.path.exists(tray_path_png):
            pm = QPixmap(tray_path_png)
            if not pm.isNull():
                icon = QIcon(pm)
        self.tray.setIcon(icon)
        menu = QMenu()
        act_toggle = QAction("显示/隐藏", self)
        act_skin = QAction("更换皮肤...", self)
        act_scale = QAction("调整缩放倍率...", self)
        act_start = QAction("开始/暂停", self)
        act_reset = QAction("重置", self)
        act_settings = QAction("设置", self)
        act_about = QAction("关于", self)
        
        # Backup Menu
        backup_menu = menu.addMenu("数据备份")
        act_manual_backup = QAction("手动备份", self)
        act_auto_backup = QAction("开启自动备份", self)
        act_auto_backup.setCheckable(True)
        act_auto_backup.setChecked(self.backup_service.is_auto_backup_enabled())
        act_import_backup = QAction("导入备份文件", self)
        act_view_backups = QAction("查看备份文件", self)
        act_clear_history = QAction("清空历史数据", self)
        
        act_manual_backup.triggered.connect(self._manual_backup)
        act_auto_backup.toggled.connect(self._toggle_auto_backup)
        act_import_backup.triggered.connect(self._import_backup)
        act_view_backups.triggered.connect(self._view_backups)
        act_clear_history.triggered.connect(self._clear_history_data)
        
        backup_menu.addAction(act_manual_backup)
        backup_menu.addAction(act_auto_backup)
        backup_menu.addAction(act_import_backup)
        backup_menu.addAction(act_view_backups)
        backup_menu.addSeparator()
        backup_menu.addAction(act_clear_history)

        act_quit = QAction("退出", self)
        act_toggle.triggered.connect(self._toggle_visibility)
        act_skin.triggered.connect(self._change_skin)
        act_scale.triggered.connect(self._adjust_scale)
        act_start.triggered.connect(self._toggle_running)
        act_reset.triggered.connect(self._reset)
        act_settings.triggered.connect(self._open_settings_from_tray)
        act_about.triggered.connect(self._show_about)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_toggle)
        menu.addAction(act_skin)
        menu.addAction(act_scale)
        menu.addAction(act_start)
        menu.addAction(act_reset)
        menu.addAction(act_settings)
        menu.addAction(act_about)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def _manual_backup(self):
        self.stats.flush()
        path = self.backup_service.manual_backup()
        if path:
            self.tray.showMessage("备份成功", f"备份已保存至: {os.path.basename(path)}", QSystemTrayIcon.Information, 2000)

    def _toggle_auto_backup(self, checked):
        self.backup_service.set_auto_backup_enabled(checked)

    def _import_backup(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", self.backup_service.backup_dir, "Zip Files (*.zip)")
        if path:
            success, msg = self.backup_service.import_backup(path, self.stats)
            if success:
                # Reload skin if config was updated during import
                # ConfigService.load() might be needed if config object isn't shared/updated by reference, 
                # but backup_service updates self.config in place.
                
                # Check if skin changed in config vs current UI
                current_skin_id = self.config.get("skinId", "default")
                self._reload_skin()
                
                QMessageBox.information(self, "导入成功", "数据已成功恢复")
            else:
                QMessageBox.warning(self, "导入失败", msg)

    def _view_backups(self):
        self.backup_service.open_backup_folder()

    def _clear_history_data(self):
        ret = QMessageBox.warning(
            self,
            "清空历史数据",
            "确定要清空所有历史统计数据吗？\n此操作不可撤销，但不会删除已备份的文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            self.stats.clear_data()
            QMessageBox.information(self, "操作成功", "历史数据已清空。")

    def _open_settings_from_tray(self):
        self._open_settings()

    def _show_about(self):
        # Create custom dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("关于")
        dlg.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # Software Name
        layout.addWidget(QLabel("软件名：bitomato"))
        
        # Author info
        layout.addWidget(QLabel("制作人：@杰某official"))
        
        # Version
        layout.addWidget(QLabel("当前版本：1.0.0"))
        
        layout.addSpacing(10)

        # Disclaimer Row
        row_disclaimer = QHBoxLayout()
        row_disclaimer.addWidget(QLabel("免责声明"))
        
        btn_read = QPushButton("阅读")
        def open_disclaimer():
            path = os.path.join(ROOT, "免责声明.txt")
            if os.path.exists(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            else:
                QMessageBox.warning(self, "错误", "免责声明文件未找到。")
                
        btn_read.clicked.connect(open_disclaimer)
        row_disclaimer.addWidget(btn_read)
        row_disclaimer.addStretch()
        
        layout.addLayout(row_disclaimer)
        layout.addStretch()
        
        dlg.setLayout(layout)
        dlg.exec()

    def _toggle_visibility(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def showEvent(self, event):
        self._compose()
        if self.is_animated and not self.anim.isActive():
            self.anim.start()
        super().showEvent(event)

    def hideEvent(self, event):
        if self.anim.isActive():
            self.anim.stop()
        super().hideEvent(event)

    def _apply_scale(self):
        self.setFixedSize(int(256 * self.scale), int(256 * self.scale))
        self.update()

    def _adjust_scale(self):
        dlg = ScaleDialog(self.scale, self)
        if dlg.exec():
            self.scale = dlg.value()
            self.config["uiScale"] = self.scale
            ConfigService.save(self.config)
            self._apply_scale()

    def _change_skin(self):
        initial_dir = os.path.join(ROOT, "skins")
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir)
            
        folder = QFileDialog.getExistingDirectory(self, "选择皮肤文件夹", initial_dir)
        if folder:
            try:
                # Test loading skin first
                load_skin(folder)
                # If successful, save and apply
                self.config["skinId"] = folder
                ConfigService.save(self.config)
                self._reload_skin()
            except Exception as e:
                QMessageBox.warning(self, "皮肤加载失败", f"无效的皮肤文件夹：\n{str(e)}\n\n请确保文件夹内包含 256x256 的 skin.png 或序列帧。")

    def _reload_skin(self):
        skin_id = self.config.get("skinId", "default")
        if os.path.isabs(skin_id):
            skin_path = skin_id
        else:
            skin_path = os.path.join(ROOT, "skins", skin_id)
            
        self.frames, self.is_animated, self.skin_meta = load_skin(skin_id)
        
        # Apply skin text color if defined
        if "textColor" in self.skin_meta:
            self.config["textColor"] = self.skin_meta["textColor"]
            self.text_color = QColor(self.config["textColor"])
            
        self.frame_index = 0
        self.renderer.reload(skin_path)
        
        # Update tray icon
        tray_path_ico = os.path.join(skin_path, "tray.ico")
        tray_path_png = os.path.join(skin_path, "tray.png")
        
        if not os.path.exists(tray_path_ico) and not os.path.exists(tray_path_png):
            tray_path_ico = os.path.join(ROOT, "assets", "tray", "tray.ico")
            tray_path_png = os.path.join(ROOT, "assets", "tray", "tray.png")
            
        icon = QIcon(tray_path_ico) if os.path.exists(tray_path_ico) else QIcon()
        if icon.isNull() and os.path.exists(tray_path_png):
            pm = QPixmap(tray_path_png)
            if not pm.isNull():
                icon = QIcon(pm)
        self.tray.setIcon(icon)
        
        # Restart animation if needed
        if self.is_animated:
            self.anim.start()
        else:
            self.anim.stop()
            
        self._compose()
        self.update()

    def _toggle_running(self):
        if self.timer_service.running:
            self.timer_service.pause()
            self.show_pause_icon = False
        else:
            self.timer_service.start()
            self.show_pause_icon = True
        self._compose()
        self.update()

    def _reset(self):
        self.timer_service.reset()
        self.show_pause_icon = False
        self._compose()
        self.update()

    def _on_ticked(self, mm, ss):
        self.text = "{:02d}:{:02d}".format(mm, ss)
        if self.isVisible():
            self._compose()
            self.update()

    def _on_phase(self, phase):
        if self.isVisible():
            self._compose()
            self.update()

    def _on_completed(self):
        # Stop at 00:00 and flash red/white 3 cycles always; sound optional
        self.text = "00:00"
        self.show_pause_icon = False
        self._flash_remaining = 6
        self.flash_timer.start()
        self.stats.flush()
        self.backup_service.auto_backup()
        if self.isVisible():
            self._compose()
            self.update()

    def _flash_step(self):
        normal_color = QColor(self.config.get("textColor", "#FFFFFF"))
        if self._flash_remaining <= 0:
            self.flash_timer.stop()
            self.text_color = normal_color
            if self.isVisible():
                self._compose()
                self.update()
            return
        is_red = (self.text_color == QColor(255, 0, 0))
        self.text_color = normal_color if is_red else QColor(255, 0, 0)
        if not is_red and self.config.get("soundEnabled", False):
            try:
                self.audio.play_end()
            except Exception:
                pass
        self._flash_remaining -= 1
        if self.isVisible():
            self._compose()
            self.update()

    def _next_frame(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        if self.isVisible():
            self._compose()
            self.update()

    def paintEvent(self, event):
        if self._composed is None:
            self._compose()
        composed = self._composed
        p = QPainter(self)
        # Ensure sharp upscaling on High DPI displays
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.drawPixmap(0, 0, composed)
        p.end()

    def _compose(self):
        frame = self.frames[self.frame_index]
        self._composed = self.renderer.compose(
            frame, 
            self.text, 
            self.show_pause_icon, 
            self.show_setting_icon, 
            scale=self.scale, 
            text_color=self.text_color,
            outline_enabled=self.config.get("textOutlineEnabled", False),
            outline_color=QColor(self.config.get("textOutlineColor", "#000000")),
            outline_width=self.config.get("textOutlineWidth", 2)
        )

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        if event.button() == Qt.LeftButton:
            if QRect(int(132 * self.scale), int(230 * self.scale), int(24 * self.scale), int(24 * self.scale)).contains(x, y):
                self._toggle_running()
                return
            if QRect(int(164 * self.scale), int(230 * self.scale), int(24 * self.scale), int(24 * self.scale)).contains(x, y):
                self._reset()
                return
            if QRect(int(196 * self.scale), int(230 * self.scale), int(24 * self.scale), int(24 * self.scale)).contains(x, y):
                self._open_settings()
                return
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._dragging and (event.buttons() & Qt.LeftButton):
            pos = event.globalPosition().toPoint()
            self.move(pos - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def _open_settings(self):
        old_skin = self.config.get("skinId")
        dlg = SettingsDialog(self.config, stats=self.stats, parent=self)
        if dlg.exec():
            ConfigService.save(self.config)
            
            # Update text color immediately
            self.text_color = QColor(self.config.get("textColor", "#FFFFFF"))
            
            # Apply new outline settings to renderer if necessary or handled in _compose via config
            # But renderer.compose needs explicit arguments or we update main window properties
            
            # Check if skin changed
            if self.config.get("skinId") != old_skin:
                self._reload_skin()
            
            # Only update animation interval, don't force pause/reset unless initiated by dialog
            self.anim.setInterval(self.config.get("frameDuration", 100))
            
            # Update UI state if timer service was reset by dialog
            if not self.timer_service.running:
                self.show_pause_icon = False
            else:
                self.show_pause_icon = True
                
            self._compose()
        self.update()
