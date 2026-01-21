from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSpinBox, QCheckBox, QPushButton, QMessageBox, QGroupBox, QFileDialog, QColorDialog
import os
from ui.stats_dialog import StatsDialog
from ui.scale_dialog import ScaleDialog
from skin.loader import load_skin
from PySide6.QtGui import QColor

class SettingsDialog(QDialog):
    def __init__(self, config, stats=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.config = config
        self.stats = stats
        self._initial = {
            "workMinutes": int(self.config.get("workMinutes", 25)),
            "shortBreakMinutes": int(self.config.get("shortBreakMinutes", 5)),
            "frameDuration": int(self.config.get("frameDuration", 100)),
            "soundEnabled": bool(self.config.get("soundEnabled", False)),
            "customSoundPath": str(self.config.get("customSoundPath", "")),
            "manualBreak": bool(self.config.get("manualBreak", False)),
            "skinId": str(self.config.get("skinId", "default")),
            "textColor": str(self.config.get("textColor", "#FFFFFF")),
            "textOutlineEnabled": bool(self.config.get("textOutlineEnabled", False)),
            "textOutlineColor": str(self.config.get("textOutlineColor", "#000000")),
            "textOutlineWidth": int(self.config.get("textOutlineWidth", 2)),
        }
        self._skin_id = self._initial["skinId"]
        self._text_color = self._initial["textColor"]
        self._outline_enabled = self._initial["textOutlineEnabled"]
        self._outline_color = self._initial["textOutlineColor"]
        self._outline_width = self._initial["textOutlineWidth"]

        main_layout = QVBoxLayout()

        # --- Group 1: 计时设置 ---
        group_timer = QGroupBox("计时设置")
        layout_timer = QGridLayout()
        
        layout_timer.addWidget(QLabel("专注时间:"), 0, 0)
        self.work = QSpinBox()
        self.work.setRange(1, 99)
        self.work.setSingleStep(5)
        self.work.setSuffix(" 分钟")
        self.work.setValue(self.config.get("workMinutes", 25))
        layout_timer.addWidget(self.work, 0, 1)
        
        layout_timer.addWidget(QLabel("休息时间:"), 0, 2)
        self.breakm = QSpinBox()
        self.breakm.setRange(1, 99)
        self.breakm.setSingleStep(5)
        self.breakm.setSuffix(" 分钟")
        self.breakm.setValue(self.config.get("shortBreakMinutes", 5))
        layout_timer.addWidget(self.breakm, 0, 3)
        
        self.countup = QCheckBox("正计时模式")
        self.countup.setChecked(self.config.get("countUpMode", False))
        self.countup.toggled.connect(self._on_countup_toggled)
        layout_timer.addWidget(self.countup, 1, 0, 1, 2)
        
        self.manual_break = QCheckBox("手动开启休息")
        self.manual_break.setChecked(self.config.get("manualBreak", False))
        layout_timer.addWidget(self.manual_break, 1, 2, 1, 2)
        
        group_timer.setLayout(layout_timer)
        main_layout.addWidget(group_timer)

        # --- Group 2: 外观设置 ---
        group_visual = QGroupBox("外观设置")
        layout_visual = QGridLayout()
        
        # Row 0: Skin & Scale
        layout_visual.addWidget(QLabel("当前皮肤:"), 0, 0)
        
        skin_layout = QHBoxLayout()
        self.skin_label = QLabel(self._get_skin_name(self._skin_id))
        self.skin_label.setStyleSheet("color: gray;")
        skin_layout.addWidget(self.skin_label)
        self.skin_btn = QPushButton("更换")
        self.skin_btn.setFixedWidth(60)
        self.skin_btn.clicked.connect(self._change_skin)
        skin_layout.addWidget(self.skin_btn)
        layout_visual.addLayout(skin_layout, 0, 1)
        
        self.scale_btn = QPushButton("缩放倍率")
        self.scale_btn.clicked.connect(self._adjust_scale)
        layout_visual.addWidget(self.scale_btn, 0, 2, 1, 2)
        
        # Row 1: Animation Speed
        layout_visual.addWidget(QLabel("动画速度:"), 1, 0)
        self.duration = QSpinBox()
        self.duration.setRange(100, 1000)
        self.duration.setSingleStep(50)
        self.duration.setSuffix(" ms")
        self.duration.setValue(self.config.get("frameDuration", 100))
        layout_visual.addWidget(self.duration, 1, 1)

        # Row 2: Text Color
        layout_visual.addWidget(QLabel("数字颜色:"), 2, 0)
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(20, 20)
        self.color_preview.setStyleSheet(f"background-color: {self._text_color}; border: 1px solid gray;")
        color_layout.addWidget(self.color_preview)
        self.color_btn = QPushButton("调整")
        self.color_btn.setFixedWidth(60)
        self.color_btn.clicked.connect(self._select_text_color)
        color_layout.addWidget(self.color_btn)
        layout_visual.addLayout(color_layout, 2, 1)

        # Row 3: Outline
        layout_visual.addWidget(QLabel("数字描边:"), 3, 0)
        
        outline_layout = QHBoxLayout()
        
        self.outline_check = QCheckBox("开启")
        self.outline_check.setChecked(self._outline_enabled)
        self.outline_check.toggled.connect(self._toggle_outline)
        outline_layout.addWidget(self.outline_check)
        
        self.outline_group = QGroupBox()
        self.outline_group.setStyleSheet("border: none;")
        o_layout = QHBoxLayout(self.outline_group)
        o_layout.setContentsMargins(0, 0, 0, 0)
        
        self.outline_color_preview = QLabel()
        self.outline_color_preview.setFixedSize(20, 20)
        self.outline_color_preview.setStyleSheet(f"background-color: {self._outline_color}; border: 1px solid gray;")
        o_layout.addWidget(self.outline_color_preview)
        
        self.outline_color_btn = QPushButton("调整")
        self.outline_color_btn.setFixedWidth(60)
        self.outline_color_btn.clicked.connect(self._select_outline_color)
        o_layout.addWidget(self.outline_color_btn)
        
        self.outline_group.setEnabled(self._outline_enabled)
        outline_layout.addWidget(self.outline_group)
        outline_layout.addStretch()
        
        layout_visual.addLayout(outline_layout, 3, 1, 1, 3)
        
        group_visual.setLayout(layout_visual)
        main_layout.addWidget(group_visual)

        # --- Group 3: 声音与数据 ---
        group_sys = QGroupBox("声音与数据")
        layout_sys = QGridLayout()
        
        self.sound = QCheckBox("结束提醒音效")
        self.sound.setChecked(self.config.get("soundEnabled", True))
        layout_sys.addWidget(self.sound, 0, 0)
        
        custom_sound_layout = QHBoxLayout()
        self.custom_sound_label = QLabel(self._get_filename(self.config.get("customSoundPath", "")))
        self.custom_sound_label.setStyleSheet("color: gray;")
        custom_sound_layout.addWidget(self.custom_sound_label)
        
        self.custom_sound_btn = QPushButton("选择")
        self.custom_sound_btn.setFixedWidth(50)
        self.custom_sound_btn.clicked.connect(self._select_custom_sound)
        custom_sound_layout.addWidget(self.custom_sound_btn)
        
        self.reset_sound_btn = QPushButton("重置")
        self.reset_sound_btn.setFixedWidth(50)
        self.reset_sound_btn.clicked.connect(self._reset_custom_sound)
        custom_sound_layout.addWidget(self.reset_sound_btn)
        
        layout_sys.addLayout(custom_sound_layout, 0, 1, 1, 2)
        
        stats_btn = QPushButton("查看统计数据")
        stats_btn.clicked.connect(self._show_stats)
        layout_sys.addWidget(stats_btn, 1, 0, 1, 3)
        
        group_sys.setLayout(layout_sys)
        main_layout.addWidget(group_sys)

        main_layout.addStretch()

        # Bottom Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        
        ok = QPushButton("保存")
        ok.setFixedWidth(80)
        ok.clicked.connect(self._save)
        btns.addWidget(ok)
        
        cancel = QPushButton("取消")
        cancel.setFixedWidth(80)
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        
        main_layout.addLayout(btns)
        self.setLayout(main_layout)

        # Initialize manual break state based on count up mode
        self._on_countup_toggled(self.countup.isChecked())

    def _get_filename(self, path):
        if not path:
            return "默认"
        name = os.path.basename(path)
        if len(name) > 3:
            return name[:3] + "..."
        return name

    def _get_skin_name(self, skin_id):
        if not skin_id or skin_id == "default":
            return "默认"
        name = os.path.basename(skin_id)
        if len(name) > 10:
            return name[:10] + "..."
        return name

    def _select_custom_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择提醒音效", "", "Audio Files (*.mp3 *.wav)")
        if path:
            self.config["customSoundPath"] = path
            self.custom_sound_label.setText(self._get_filename(path))

    def _reset_custom_sound(self):
        self.config["customSoundPath"] = ""
        self.custom_sound_label.setText(self._get_filename(""))

    def _on_countup_toggled(self, checked):
        if checked:
            self.manual_break.setChecked(True)
            self.manual_break.setEnabled(False)
        else:
            self.manual_break.setEnabled(True)
            self.manual_break.setChecked(False)

    def _save(self):
        # Capture new values
        new_work = int(self.work.value())
        new_break = int(self.breakm.value())
        new_countup = bool(self.countup.isChecked())
        
        # Check if timer-critical settings changed
        timer_changed = (
            new_work != self._initial["workMinutes"] or
            new_break != self._initial["shortBreakMinutes"] or
            new_countup != bool(self.config.get("countUpMode", False))
        )

        self.config["workMinutes"] = new_work
        self.config["shortBreakMinutes"] = new_break
        self.config["frameDuration"] = int(self.duration.value())
        self.config["soundEnabled"] = bool(self.sound.isChecked())
        self.config["manualBreak"] = bool(self.manual_break.isChecked())
        self.config["countUpMode"] = new_countup
        self.config["skinId"] = self._skin_id
        self.config["textColor"] = self._text_color
        self.config["textOutlineEnabled"] = self._outline_enabled
        self.config["textOutlineColor"] = self._outline_color
        self.config["textOutlineWidth"] = 1
        
        # Only reset if timer settings changed
        if timer_changed:
            parent = self.parent()
            if hasattr(parent, "_reset"):
                parent._reset()
                    
        self.accept()

    def _show_stats(self):
        dlg = StatsDialog(self.stats, self)
        dlg.exec()

    def _adjust_scale(self):
        current = float(self.config.get("uiScale", 1))
        dlg = ScaleDialog(current, self)
        if dlg.exec():
            val = dlg.value()
            self.config["uiScale"] = val
            parent = self.parent()
            if hasattr(parent, "scale"):
                parent.scale = val
            if hasattr(parent, "_apply_scale"):
                parent._apply_scale()

    def _change_skin(self):
        # Determine initial directory
        initial_dir = os.path.join(os.path.dirname(__file__), os.pardir, "skins")
        if os.path.exists(initial_dir):
            initial_dir = os.path.abspath(initial_dir)
        else:
            initial_dir = os.getcwd()
            
        folder = QFileDialog.getExistingDirectory(self, "选择皮肤文件夹", initial_dir)
        if folder:
            try:
                _, _, meta = load_skin(folder)
                self._skin_id = folder
                self.skin_label.setText(self._get_skin_name(folder))
                
                if "textColor" in meta:
                    self._text_color = meta["textColor"]
                    self.color_preview.setStyleSheet(f"background-color: {self._text_color}; border: 1px solid gray;")
                
                if "textOutlineEnabled" in meta:
                    self._outline_enabled = bool(meta["textOutlineEnabled"])
                    self.outline_check.setChecked(self._outline_enabled)
                    self.outline_group.setEnabled(self._outline_enabled)
                    
                if "textOutlineColor" in meta:
                    self._outline_color = meta["textOutlineColor"]
                    self.outline_color_preview.setStyleSheet(f"background-color: {self._outline_color}; border: 1px solid gray;")
                    
                if "textOutlineWidth" in meta:
                    # Deprecated: width is always 1
                    # self._outline_width = int(meta["textOutlineWidth"])
                    # self.outline_width_spin.setValue(self._outline_width)
                    pass
            except Exception as e:
                QMessageBox.warning(self, "皮肤加载失败", f"无效的皮肤文件夹：\n{str(e)}\n\n请确保文件夹内包含 256×256 的 skin.png 或序列帧。")

    def _select_text_color(self):
        dlg = QColorDialog(QColor(self._text_color), self)
        dlg.setWindowTitle("选择数字显示色")
        dlg.setOption(QColorDialog.DontUseNativeDialog, True)
        
        # Try to hide Basic/Custom colors labels if possible (best effort)
        # This is cosmetic and depends on Qt version
        for label in dlg.findChildren(QLabel):
            if label.text() in ["Basic colors", "Custom colors", "基本颜色", "自定义颜色"]:
                label.hide()

        if dlg.exec():
            color = dlg.selectedColor()
            if color.isValid():
                self._text_color = color.name()
                self.color_preview.setStyleSheet(f"background-color: {self._text_color}; border: 1px solid gray;")

    def _toggle_outline(self, checked):
        self.outline_group.setEnabled(checked)
        self._outline_enabled = checked

    def _select_outline_color(self):
        dlg = QColorDialog(QColor(self._outline_color), self)
        dlg.setWindowTitle("选择描边颜色")
        dlg.setOption(QColorDialog.DontUseNativeDialog, True)
        
        for label in dlg.findChildren(QLabel):
            if label.text() in ["Basic colors", "Custom colors", "基本颜色", "自定义颜色"]:
                label.hide()
                
        if dlg.exec():
            color = dlg.selectedColor()
            if color.isValid():
                self._outline_color = color.name()
                self.outline_color_preview.setStyleSheet(f"background-color: {self._outline_color}; border: 1px solid gray;")

    def reject(self):
        changed = (
            int(self.work.value()) != self._initial["workMinutes"] or
            int(self.breakm.value()) != self._initial["shortBreakMinutes"] or
            int(self.duration.value()) != self._initial["frameDuration"] or
            bool(self.sound.isChecked()) != self._initial["soundEnabled"] or
            bool(self.manual_break.isChecked()) != self._initial["manualBreak"] or
            bool(self.countup.isChecked()) != bool(self.config.get("countUpMode", False)) or
            str(self.config.get("customSoundPath", "")) != self._initial["customSoundPath"] or
            self._skin_id != self._initial["skinId"] or
            self._text_color != self._initial["textColor"] or
            self._outline_enabled != self._initial["textOutlineEnabled"] or
            self._outline_color != self._initial["textOutlineColor"]
        )
        if changed:
            ret = QMessageBox.question(self, "保存设置", "检测到修改，是否保存现有设置？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.Yes:
                self._save()
                return
        super().reject()
