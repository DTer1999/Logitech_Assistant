from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QCheckBox, QLineEdit)


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # 驱动软件设置
        driver_group = QWidget()
        driver_layout = QHBoxLayout()

        driver_layout.addWidget(QLabel("驱动软件"))

        driver_combo = QComboBox()
        driver_combo.addItem("通用无适点")
        driver_layout.addWidget(driver_combo)

        download_btn = QPushButton("下载驱动")
        driver_layout.addWidget(download_btn)

        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)

        # 开镜模式
        aim_group = QWidget()
        aim_layout = QHBoxLayout()

        aim_layout.addWidget(QLabel("开镜模式"))

        aim_combo = QComboBox()
        aim_combo.addItem("HOLD")
        aim_layout.addWidget(aim_combo)

        aim_group.setLayout(aim_layout)
        layout.addWidget(aim_group)

        # 其他设置
        layout.addWidget(QLabel("其他设置"))

        debug_cb = QCheckBox("Debug模式")
        layout.addWidget(debug_cb)

        # 各种数值设置
        settings = [
            ("微动值移动", "30"),
            ("开镜灵敏度", "35"),
            ("垂直灵敏度", "1.2"),
            ("压枪倍率补偿", "10")
        ]

        for label, value in settings:
            setting = QWidget()
            setting_layout = QHBoxLayout()
            setting_layout.addWidget(QLabel(label))
            setting_edit = QLineEdit(value)
            setting_layout.addWidget(setting_edit)
            setting.setLayout(setting_layout)
            layout.addWidget(setting)

        # LogiNet设置
        loginet = QCheckBox("LogiNet 6787")
        layout.addWidget(loginet)

        # 应用按钮
        apply_btn = QPushButton("应用")
        layout.addWidget(apply_btn)

        self.setLayout(layout)
