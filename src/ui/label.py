from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

from src.config.settings import Settings


class FloatingLabel(QWidget):
    """浮动标签类，用于显示游戏状态信息"""

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化浮动标签"""
        super().__init__(parent)
        self.settings = Settings.get_instance()
        self.label_settings = self.settings.get('label')
        # 设置窗口属性
        self._setup_window()
        
        # 创建标签
        self._create_label()
        
        # 初始化布局
        self._init_layout()
        
        # 设置样式
        self._apply_styles()

    def _setup_window(self):
        """设置窗口属性"""
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # 窗口置顶
            Qt.FramelessWindowHint |    # 无边框
            Qt.Tool                     # 工具窗口
        )
        
        # 设置窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置默认位置和大小
        screen_geometry = self.screen().geometry()
        # 设置窗口位置和大小
        self.setGeometry(
            screen_geometry.width() // 2 - self.label_settings['min_width'] // 2,  # 居中距离
            1, # 顶部距离
            self.label_settings['min_width'],
            self.label_settings['height']
        )

    def _create_label(self):
        """创建标签组件"""
        self.label = QLabel("无")

        # 设置字体
        font = QFont(
            self.label_settings['font_family'],
            self.label_settings['font_size'],
            QFont.Bold
        )
        self.label.setFont(font)
        
        # 设置对齐方式
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 设置自动换行
        self.label.setWordWrap(True)

    def _init_layout(self):
        """初始化布局"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)  # 设置边距
        layout.addWidget(self.label)
        self.setLayout(layout)

    def _apply_styles(self):
        """应用样式"""
        

        # 设置窗口透明度
        self.setWindowOpacity(self.label_settings['opacity'])
        
        # 设置标签样式
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.label_settings['background']};
                color: {self.label_settings['text_color']};
                padding: {self.label_settings['padding']};
                border-radius: {self.label_settings['border_radius']};
            }}
        """)

    def setText(self, text: str):
        """设置标签文本"""
        if not text or text.isspace():
            text = "无"
        self.label.setText(text)
        
        # 调整大小以适应内容
        self._adjust_size()

    def _adjust_size(self):
        """调整窗口大小以适应内容"""
        # 获取文本大小
        text_width = self.label.fontMetrics().boundingRect(
            self.label.text()
        ).width()
        
        # 计算新的窗口宽度
        new_width = max(
            text_width + 40,  # 文本宽度加上边距
            self.label_settings['min_width']  # 最小宽度
        )
        # 保持当前位置，只更新大小
        current_pos = self.pos()
        self.setGeometry(
            current_pos.x(),
            current_pos.y(),
            new_width,
            self.label_settings['height']
        )

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 记录鼠标位置和窗口位置的差值
            self._drag_position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() & Qt.LeftButton and hasattr(self, '_drag_position'):
            # 计算新位置
            new_pos = event.globalPos() - self._drag_position
            
            # 确保窗口不会移出屏幕
            screen_geometry = self.screen().geometry()
            new_pos.setX(max(0, min(new_pos.x(), 
                screen_geometry.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), 
                screen_geometry.height() - self.height())))
            
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 清除拖动位置
            self._drag_position = None
            event.accept()

    def enterEvent(self, event):
        """鼠标进入事件"""
        # 可以在这里添加鼠标悬停效果
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 恢复默认透明度
        self.setWindowOpacity(self.label_settings['opacity'])
        super().leaveEvent(event)
