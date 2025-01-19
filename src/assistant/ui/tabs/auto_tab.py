from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QCheckBox, QPushButton, QTextBrowser, QGroupBox, QProgressDialog,
                             QComboBox, QMessageBox, QSlider)

from ...core.worker_thread import WorkerThread
from ...ui.label import FloatingLabel
from ...utils.logger_factory import LoggerFactory
from ....config.settings import ConfigManager
from ....screen_capture.capture_manager import CaptureManager


class AutoTab(QWidget):
    def __init__(self, label: FloatingLabel):
        super().__init__()
        self.settings = ConfigManager("config")
        self.logger = LoggerFactory.get_logger()
        self.label = label

        self.worker_thread = WorkerThread()

        self.is_processing = False
        self.is_switching = False

        # 2. 日志信号 -> log_message
        self.logger.log_signal.connect(self.log_message)

        # 3. 统一的UI更新信号 -> on_ui_update
        self.logger.ui_update_signal.connect(self.on_ui_update)

        # 4. 关闭进度信号 -> update_close_progress
        self.logger.close_progress_signal.connect(self.update_close_progress)

        self.capture_manager = CaptureManager()

        self.weapon1_labels = []  # “1号”武器的5个标签
        self.weapon2_labels = []  # “2号”武器的5个标签
        self.current_weapon_label = None
        self.shoot_status_label = None
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QGridLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 右上角的控制区域
        top_right = QHBoxLayout()
        top_right.setContentsMargins(0, 0, 0, 0)
        top_right.addStretch()
        
        self.show_cb = QCheckBox("开启Label")
        self.always_on_top_cb = QCheckBox("置顶")

        # 设置复选框的固定高度
        self.show_cb.setFixedHeight(20)
        self.always_on_top_cb.setFixedHeight(20)

        # 连接信号
        self.show_cb.stateChanged.connect(self.show_hide_label)
        self.always_on_top_cb.stateChanged.connect(self.toggle_always_on_top)
        self.show_cb.setChecked(True)
        # self.label.setVisible(True)

        top_right.addWidget(self.always_on_top_cb)
        top_right.addWidget(self.show_cb)
        # top_right.addSpacing(10)

        top_right_widget = QWidget()
        top_right_widget.setLayout(top_right)
        top_right_widget.setFixedHeight(20)
        top_right_widget.setContentsMargins(0, 0, 0, 0)

        # 将容器添加到主布局的右上角
        main_layout.addWidget(top_right_widget, 0, 0, 1, 3, Qt.AlignRight)
        main_layout.setRowMinimumHeight(0, 20)

        # 创建1号区域
        group1, self.weapon1_labels = self.create_weapon_group("1号")
        group1.setFixedHeight(150)
        main_layout.addWidget(group1, 1, 0, 1, 2)
        main_layout.setRowStretch(1, 0)

        # 日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.text_browser = QTextBrowser()
        log_layout.addWidget(self.text_browser)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1, 2, 3, 1)  # 日志区域跨3行

        # 创建2号区域
        group2, self.weapon2_labels = self.create_weapon_group("2号")
        group2.setFixedHeight(150)
        main_layout.addWidget(group2, 2, 0, 1, 2)

        # 创建录制控制
        self.recording_control = self.setup_recording_control()
        self.recording_control.setFixedHeight(120)
        main_layout.addWidget(self.recording_control, 3, 0, 1, 2)
        

        # 当前武器区域
        weapon_widget = QWidget()
        weapon_layout = QHBoxLayout()
        weapon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.shoot_status_label = QLabel("未开火")
        self.shoot_status_label.setFixedWidth(60)
        weapon_layout.addWidget(self.shoot_status_label)

        weapon_layout.addWidget(QLabel("当前武器:"))
        self.current_weapon_label = QLabel("无")
        self.current_weapon_label.setAlignment(Qt.AlignCenter)
        weapon_layout.addWidget(self.current_weapon_label)
        weapon_widget.setLayout(weapon_layout)
        main_layout.addWidget(weapon_widget, 4, 0, 1, 2)

        # 控制按钮组（独立的框）
        control_group = QGroupBox()
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 5, 10, 5)

        self.switch_button = QPushButton('开启')
        self.switch_button.setCheckable(True)
        self.switch_button.setChecked(False)
        self.switch_button.clicked.connect(self.switch_button_clicked)

        self.exit_button = QPushButton("退出")
        self.exit_button.clicked.connect(self.handle_exit)

        control_layout.addWidget(self.switch_button)
        control_layout.addWidget(self.exit_button)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group, 4, 2, 1, 1)  # 按钮组放在日志区域下方

        # 设置列的拉伸因子
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 1)

        self.setLayout(main_layout)

    def setup_recording_control(self):
        control_widget = QWidget()
        control_bar = QHBoxLayout()
        control_bar.setSpacing(20)
        control_widget.setLayout(control_bar)

        # 左侧截图方式选择
        method_layout = QHBoxLayout()
        method_layout.setContentsMargins(0, 0, 0, 0)
        capture_label = QLabel("方式:")

        self.capture_combo = QComboBox()
        self.capture_combo.setFixedSize(80, 25)

        # 获取所有可用的截图方式
        capture_methods = self.capture_manager.get_capture_methods()
        for method_id, method_class in capture_methods.items():
            self.capture_combo.addItem(method_id, method_id)
        # 设置当前选中的截图方式
        current_method = self.capture_manager.get_method()
        index = self.capture_combo.findData(current_method)
        if index >= 0:
            self.capture_combo.setCurrentIndex(index)

        # 连接信号
        self.capture_combo.currentIndexChanged.connect(self.on_capture_method_changed)

        method_layout.addWidget(capture_label)
        method_layout.addWidget(self.capture_combo)

        # 右侧FPS设置
        fps_layout = QHBoxLayout()
        fps_layout.setContentsMargins(0, 0, 0, 0)
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("margin-left: 20px;")

        # FPS值显示标签
        self.fps_value_label = QLabel("60")
        self.fps_value_label.setStyleSheet("margin-left: 5px;")

        # FPS滑动条
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setFixedWidth(120)
        self.fps_slider.setMinimum(1)
        self.fps_slider.setMaximum(60)
        self.fps_slider.setPageStep(5)

        # 设置当前FPS值
        current_fps = self.capture_manager.get_fps()
        self.fps_slider.setValue(current_fps)
        self.fps_value_label.setText(str(current_fps))

        # 连接滑动条信号
        self.fps_slider.valueChanged.connect(self.on_fps_value_display)
        self.fps_slider.sliderReleased.connect(self.on_fps_changed)

        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_value_label)

        # 添加到控制栏
        left_container = QWidget()
        left_container.setLayout(method_layout)
        right_container = QWidget()
        right_container.setLayout(fps_layout)

        control_bar.addWidget(left_container, 0, Qt.AlignLeft)
        control_bar.addStretch(1)
        control_bar.addWidget(right_container, 0, Qt.AlignRight)

        return control_widget
    

    def create_weapon_group(self, title):
        group = QGroupBox(title)
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(10, 10, 10, 10)
        
        labels = []
        top_attrs_layout = QHBoxLayout()
        for _ in range(2):
            label = QLabel("无")
            label.setAlignment(Qt.AlignCenter)
            labels.append(label)
            top_attrs_layout.addWidget(label)
        top_attrs_widget = QWidget()
        top_attrs_widget.setLayout(top_attrs_layout)
        group_layout.addWidget(top_attrs_widget)
        
        bottom_attrs_layout = QHBoxLayout()
        for _ in range(3):
            label = QLabel("无")
            label.setAlignment(Qt.AlignCenter)
            labels.append(label)
            bottom_attrs_layout.addWidget(label)
        bottom_attrs_widget = QWidget()
        bottom_attrs_widget.setLayout(bottom_attrs_layout)
        group_layout.addWidget(bottom_attrs_widget)
        
        group.setLayout(group_layout)
        return group, labels

    def on_ui_update(self, data: dict):
        """由 logger.ui_update_signal 发射的单个信号，统一更新UI"""
        if "label" in data:
            self.label.setText(data["label"])  # 顶部浮动窗的显示文字
        
        if "results" in data and "current_weapon" in data:
            self.update_results(data["results"], data["current_weapon"])

    def update_results(self, results, current_weapon):
        """更新界面显示的识别结果（这里的 results 是翻译完的）"""
        # 1. 更新当前武器
        current_weapon_name = results.get(f"weapons_name_{current_weapon}", "无")
        self.current_weapon_label.setText(current_weapon_name)

        # 2. 更新开火状态
        shoot_value = results.get("shoot", "无")
        is_shooting = (shoot_value == "shoot" or shoot_value == "开火中")
        self.shoot_status_label.setText("开火中" if is_shooting else "未开火")
        self.shoot_status_label.setStyleSheet("color: red;" if is_shooting else "color: black;")

        # 3. 更新1号和2号武器信息
        self.update_weapon_info("rifle", self.weapon1_labels, results)
        self.update_weapon_info("sniper", self.weapon2_labels, results)

    def update_weapon_info(self, weapon_type, labels, results):
        """更新武器信息，使用翻译后的 results"""
        # 定义需要检查的属性名
        attributes = ["weapons_name", "scopes", "muzzles", "grips", "stocks"]

        for label, attribute in zip(labels, attributes):
            # 构建完整的属性名
            full_attribute_name = f"{attribute}_{weapon_type}"
            # 从 results 中获取对应的值，如果为空或者None，则设置“无”

            value = results.get(full_attribute_name, "无")
            # 更新 label 的文本，如果为空或者None，则设置为“无”
            if value is None:
                value = "无"
            label.setText(value)


    def switch_button_clicked(self, checked: bool):
        """处理开关按钮点击"""
        if self.is_switching:  # 如果正在切换中，忽略点击
            self.switch_button.setChecked(not checked)  # 恢复按钮状态
            return
        
        self.is_switching = True  # 设置切换标志
        self.switch_button.setEnabled(False)  # 禁用按钮
        
        # 使用 QTimer 延迟执行，避免界面卡顿
        QTimer.singleShot(0, lambda: self.execute_switch_steps(checked))

    def execute_switch_steps(self, checked: bool):
        """执行开关步骤"""
        try:
            if checked:
                self.capture_combo.setDisabled(True)
                self.fps_slider.setDisabled(True)
                # 直接启动工作线程
                if not self.worker_thread.is_alive():
                    self.worker_thread.start()
                # self.process_manager.start()
                # self.start_capture_thread()
                self.switch_button.setText("关闭")
            else:
                self.capture_combo.setDisabled(False)
                self.fps_slider.setDisabled(False)
                if self.worker_thread.is_alive():
                    # 创建关闭进度对话框
                    self.close_progress = QProgressDialog("正在关闭...", None, 0, 7, self)
                    # 设置进度条窗口名字
                    self.close_progress.setWindowTitle("关闭进度")
                    # 设置进度条窗口模式
                    self.close_progress.setWindowModality(Qt.WindowModal)
                    # 设置进度条自动关闭
                    self.close_progress.setAutoClose(True)
                    # 设置进度条初始值
                    self.close_progress.setValue(0)

                    self.worker_thread.stop_signal.emit()
                # self.process_manager.stop()

                # self.stop_capture_thread()
                self.switch_button.setText("开启")
        except Exception as e:
            print(f"执行开关步骤失败: {e}")
            self.switch_button.setChecked(not checked)
        finally:
            self.is_switching = False
            self.switch_button.setEnabled(True)

    def update_close_progress(self, stage: int):
        """更新关闭进度
        Args:
            stage: 关闭阶段（0-4）
        """
        if hasattr(self, 'close_progress'):
            self.close_progress.setValue(stage)
            if stage >= 7:  # 最后一个阶段
                # 确保UI状态更新
                self.switch_button.setChecked(False)
                self.reset_displays()

    def show_hide_label(self, checked: bool):
        """显示/隐藏标签"""
        self.label.setVisible(checked)

    def handle_exit(self):
        """处理退出"""
        try:
            # 如果线程正在运行，先停止它
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop_signal.emit()
            # self.process_manager.stop()
        except Exception as e:
            self.logger.error(f"退出处理失败: {e}")
        finally:
            # 确保程序能够退出
            QCoreApplication.instance().quit()

    def reset_displays(self):
        """重置所有显示"""
        # 重置1号和2号武器标签
        for label in self.weapon1_labels + self.weapon2_labels:
            if label:
                label.setText("无")
        
        # 重置当前武器标签
        if hasattr(self, 'current_weapon_label'):
            self.current_weapon_label.setText("无")
        
        # 重置开火状态标签
        if hasattr(self, 'shoot_status_label'):
            self.shoot_status_label.setText("未开火")
            self.shoot_status_label.setStyleSheet("color: black;")

    def log_message(self, message: str):
        """处理日志消息"""
        # 普通日志显示
        if hasattr(self, 'text_browser'):
            self.text_browser.append(message)
            self.text_browser.moveCursor(QTextCursor.End)

    def toggle_always_on_top(self, checked: bool):
        """控制主窗口置顶"""
        window = self.window()  # 获取主窗口
        # 保存当前窗口位置
        pos = window.pos()

        if checked:
            window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)

        # 恢复窗口位置并显示
        window.move(pos)
        window.show()

    def handle_capture_error(self, error_msg: str):
        """处理捕获错误"""
        self.logger.error(f"屏幕捕获错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"屏幕捕获错误: {error_msg}")

    def on_capture_method_changed(self, index: int):
        """截图方式改变时的处理"""
        try:
            method = self.capture_combo.currentData()
            self.capture_manager.set_method(method)
            self.logger.info(f"截图方式已更改为: {method}")
        except Exception as e:
            self.logger.error(f"更改截图方式时出错: {e}")

    def on_fps_value_display(self, value: int):
        """FPS值实时显示"""
        self.fps_value_label.setText(str(value))

    def on_fps_changed(self):
        """FPS改变时的处理（滑动结束时）"""
        try:
            value = self.fps_slider.value()
            self.capture_manager.set_fps(value)
            self.logger.info(f"FPS已更改为: {value}")
        except Exception as e:
            self.logger.error(f"更改FPS时出错: {e}")
