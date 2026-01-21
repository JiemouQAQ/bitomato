from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class StatsDialog(QDialog):
    def __init__(self, stats_service, parent=None):
        super().__init__(parent)
        self.setWindowTitle("统计数据")
        layout = QVBoxLayout()
        if stats_service is None:
            layout.addWidget(QLabel("统计服务未初始化"))
            self.setLayout(layout)
            return
        summary = stats_service.get_summary()
        sessions = summary.get("total_focus_sessions", 0)
        seconds = summary.get("total_focus_seconds", 0)
        minutes = seconds // 60
        hours = minutes // 60
        mins_rem = minutes % 60
        favorites = summary.get("favorite_slots", [])
        layout.addWidget(QLabel(f"总共专注次数：{sessions}"))
        layout.addWidget(QLabel(f"总共专注时长：{hours}小时{mins_rem}分钟"))
        if favorites:
            zh_map = {
                "midnight": "午夜",
                "morning": "早晨",
                "afternoon": "下午",
                "evening": "晚间"
            }
            labels = [zh_map.get(x, x) for x in favorites]
            layout.addWidget(QLabel("喜好专注时段（>50%）：" + ", ".join(labels)))
        else:
            layout.addWidget(QLabel("喜好专注时段（>50%）：无"))
        self.setLayout(layout)

