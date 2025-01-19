import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QDoubleSpinBox
)

from ....config.settings import Settings


class WeaponTab(QWidget):
    """武器参数配置标签页"""

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.weapons_data = {}

        # 使用配置的路径
        config_path = self.settings.get_path('config')
        self.weapons_file = config_path / 'weapons.json'

        self._load_weapons_data()
        self._init_ui()

    def _load_weapons_data(self):
        """加载武器配置数据"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))  # tabs目录
            src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # src的父目录

            config_path = os.path.join(
                src_dir,
                'resources',
                'config',
                'weapons.json'
            )

            # 如果文件不存在，尝试创建目录
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            if not os.path.exists(config_path):
                print(f"配置文件不存在: {config_path}")
                # 可以在这里添加创建默认配置文件的逻辑
                self.weapons_data = {}
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                self.weapons_data = json.load(f)

        except Exception as e:
            print(f"加载武器数据失败: {e}")
            print(f"尝试加载的路径: {config_path}")  # 添加路径调试信息
            self.weapons_data = {}

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 添加武器选择区域
        self._setup_weapon_selector(main_layout)

        # 添加参数配置区域
        self._setup_params_area(main_layout)

        # 添加控制按钮
        self._setup_control_buttons(main_layout)

        self.setLayout(main_layout)

    def _setup_weapon_selector(self, layout: QVBoxLayout):
        """设置武器选择区域"""
        selector_group = QGroupBox("武器选择")
        selector_layout = QHBoxLayout()

        # 武器类型选择
        self.weapon_combo = QComboBox()
        self.weapon_combo.addItems(self.weapons_data.keys())
        self.weapon_combo.currentTextChanged.connect(self._on_weapon_changed)

        selector_layout.addWidget(QLabel("武器:"))
        selector_layout.addWidget(self.weapon_combo)
        selector_layout.addStretch()

        selector_group.setLayout(selector_layout)
        layout.addWidget(selector_group)

    def _setup_params_area(self, layout: QVBoxLayout):
        """设置参数配置区域"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建参数容器
        params_container = QWidget()
        self.params_layout = QGridLayout()
        self.params_layout.setAlignment(Qt.AlignTop)
        params_container.setLayout(self.params_layout)

        scroll.setWidget(params_container)
        layout.addWidget(scroll)

        # 初始化参数控件
        if self.weapon_combo.count() > 0:
            self._on_weapon_changed(self.weapon_combo.currentText())

    def _setup_control_buttons(self, layout: QVBoxLayout):
        """设置控制按钮"""
        button_layout = QHBoxLayout()

        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_weapon_params)

        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset_weapon_params)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)

        layout.addLayout(button_layout)

    def _create_param_spinbox(self, value):
        """创建参数调节框"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(0, 100)
        spinbox.setDecimals(2)
        spinbox.setSingleStep(0.1)

        # 处理不同类型的值
        if isinstance(value, (int, float)):
            spinbox.setValue(float(value))
        elif isinstance(value, dict):
            # 如果是字典，使用默认值或第一个值
            if 'default' in value:
                spinbox.setValue(float(value['default']))
            elif len(value) > 0:
                first_value = next(iter(value.values()))
                spinbox.setValue(float(first_value))
            else:
                spinbox.setValue(0.0)
        else:
            # 其他情况使用默认值
            spinbox.setValue(0.0)
            print(f"未知的参数值类型: {type(value)}, 值: {value}")

        return spinbox

    def _on_weapon_changed(self, weapon_name: str):
        """处理武器选择变化"""
        try:
            # 清除现有参数
            self._clear_params_layout()

            # 获取武器参数
            weapon_params = self.weapons_data.get(weapon_name, {})
            if not weapon_params:
                print(f"未找到武器参数: {weapon_name}")
                return

            # 创建参数控件
            row = 0
            for param_name, param_value in weapon_params.items():
                # 跳过特殊参数
                if param_name in ['default', 'burst']:
                    continue

                # 创建标签
                label = QLabel(param_name)
                self.params_layout.addWidget(label, row, 0)

                # 创建并配置SpinBox
                spinbox = self._create_param_spinbox(param_value)
                spinbox.valueChanged.connect(
                    lambda value, name=param_name: self._on_param_changed(name, value)
                )
                self.params_layout.addWidget(spinbox, row, 1)

                row += 1

        except Exception as e:
            print(f"处理武器变化失败: {e}")

    def _clear_params_layout(self):
        """清除参数布局"""
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _save_weapon_params(self):
        """保存武器参数"""
        if not self.current_weapon:
            return

        try:
            # 更新数据
            weapon_params = self.weapons_data[self.current_weapon]
            for param_name, spinbox in self.param_widgets.items():
                weapon_params[param_name] = spinbox.value()

            # 写入文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(
                current_dir,
                '../../../resources/config/weapons.json'
            )

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.weapons_data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"保存武器参数失败: {e}")

    def _reset_weapon_params(self):
        """重置武器参数"""
        if not self.current_weapon:
            return

        # 重新加载数据
        self._load_weapons_data()

        # 更新显示
        self._on_weapon_changed(self.current_weapon)
