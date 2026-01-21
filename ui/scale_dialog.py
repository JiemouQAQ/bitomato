from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton

class ScaleDialog(QDialog):
    def __init__(self, current_scale: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("调整缩放倍率")
        layout = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("输入缩放倍数（0.5 - 3.0）："))
        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.5, 3.0)
        self.spin.setDecimals(2)
        self.spin.setSingleStep(0.1)
        self.spin.setValue(current_scale)
        row.addWidget(self.spin)
        layout.addLayout(row)
        layout.addWidget(QLabel("调整倍率可能影响像素显示效果"))
        btns = QHBoxLayout()
        ok = QPushButton("确定")
        cancel = QPushButton("取消")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def value(self) -> float:
        return float(self.spin.value())

