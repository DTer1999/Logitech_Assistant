from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os

from .tabs.auto_tab import AutoTab
from .tabs.weapon_tab import WeaponTab
from .tabs.settings_tab import SettingsTab
from .label import FloatingLabel
from ..config.settings import Settings
from ..utils.logger import Logger

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self, settings: Settings, logger: Logger):
        """初始化主窗口"""
        super().__init__()
        self.settings = settings
        self.logger = logger

        # 初始化组件
        self.label = FloatingLabel(settings)
        self.label.setVisible(False)

        self._init_tabs()

        # 设置窗口属性
        self._setup_window_properties()

        # 设置窗口图标
        icon = QIcon()
        icon_path = str(self.settings.get_path('assets') / '2.png')
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            self.logger.error(f"无法加载图标: {icon_path}")
        else:
            icon.addPixmap(pixmap, QIcon.Normal, QIcon.Off)
            self.setWindowIcon(icon)
            self.logger.info(f"成功加载图标: {icon_path}")

    def _init_tabs(self):
        """初始化标签页"""
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 创建标签页
        # self.weapon_tab = WeaponTab(self.settings)
        self.auto_tab = AutoTab(self.settings, self.logger, self.label)
        
        # 添加标签页
        self.tab_widget.addTab(self.auto_tab, "自动识别")
        # self.tab_widget.addTab(self.weapon_tab, "武器参数")

    def _setup_window_properties(self):
        """设置窗口属性"""
        # 设置窗口标志
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        
        # 设置窗口图标
        # self.setWindowIcon(QIcon("path/to/icon.png"))  # 如果需要图标可以取消注释
        
        # 设置窗口大小策略
        self.setMinimumSize(QSize(400, 400))

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        try:
            # 确保auto_tab正确关闭
            if hasattr(self, 'auto_tab'):
                self.auto_tab.handle_exit()
            
            # 隐藏浮动标签
            if self.label:
                self.label.setVisible(False)
                
            event.accept()
            
        except Exception as e:
            self.logger.error(f"关闭窗口时出错: {e}")
            event.accept()  # 确保窗口能够关闭
