from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextBrowser,
                             QSpacerItem, QSizePolicy)

from .... import __version__, __app_name__, __author__, __email__, __github__


class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)  # 增加组件之间的间距
        layout.setContentsMargins(50, 30, 50, 30)  # 设置页面边距

        # 添加顶部空白
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Logo和标题
        title_label = QLabel(f"{__app_name__} v{__version__}")
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # 作者信息
        info_text = f"""
        <div style='text-align: center; font-size: 14px; color: #666666; margin: 20px 0;'>
            <p><b>作者：</b>{__author__}</p>
            <p><b>邮箱：</b><a href="mailto:{__email__}" style='color: #0066cc; text-decoration: none;'>{__email__}</a></p>
            <p><b>项目地址：</b><a href="{__github__}" style='color: #0066cc; text-decoration: none;'>{__github__}</a></p>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #dddddd;")
        layout.addWidget(line)

        # 声明文本
        disclaimer_text = """
        <div style='color: #333333; margin: 20px 0;'>
            <h2 style='color: #2c3e50; text-align: center; margin-bottom: 20px;'>声明</h2>
            <p style='line-height: 1.6; margin: 10px 0;'>
                1. 源码来自于群友 SenLiao 的分享，后通过Cursor软件，调用Claude3.5模型、ChatGPT4o模型、o1模型对代码功能、结构进行优化。
            </p>
            <p style='line-height: 1.6; margin: 10px 0;'>
                2. 相关源码、软件等仅供学习和交流使用。
            </p>
            <p style='line-height: 1.6; margin: 10px 0;'>
                3. 请勿用于商业用途。如进行商业用途，请自行承担相关责任。
            </p>
            <p style='line-height: 1.6; margin: 10px 0;'>
                4. 请勿用于游戏外挂等非法用途。如用于非法用途，请自行承担相关责任。
            </p>

            <h2 style='color: #2c3e50; text-align: center; margin: 30px 0 20px 0;'>许可证</h2>
            <p style='text-align: center;'>
                本项目采用 <a href="https://opensource.org/licenses/MIT" style='color: #0066cc; text-decoration: none;'>MIT 许可证</a>
            </p>
        </div>
        """
        disclaimer_browser = QTextBrowser()
        disclaimer_browser.setHtml(disclaimer_text)
        disclaimer_browser.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
        """)
        disclaimer_browser.setOpenExternalLinks(True)
        layout.addWidget(disclaimer_browser)

        # 添加底部空白
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QLabel {
                padding: 10px;
            }
        """)
