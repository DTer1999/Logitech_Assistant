#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.config.settings import Settings
from src.utils.logger import Logger

class Application:
    """应用程序主类"""
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[MainWindow] = None
        self.settings: Optional[Settings] = None
        self.logger: Optional[Logger] = None

    def initialize(self) -> bool:
        """初始化应用程序组件"""
        try:
            # 初始化配置
            self.settings = Settings()

            # 初始化日志
            logs_path = self.settings.get_path('logs')
            self.logger = Logger(logs_path)
            
            # 初始化UI
            self.app = QApplication(sys.argv)

            self.window = MainWindow(self.settings, self.logger)

            self.settings.set('screen', 'width', self._get_screen_width())
            self.settings.set('screen', 'height', self._get_screen_height())

            # 应用窗口设置
            window_settings = self.settings.get_window_settings()
            # 设置窗口标题  
            self.window.setWindowTitle(window_settings['title'])
            # 设置窗口大小
            self.window.resize(
                window_settings['width'],
                window_settings['height']
            )
            # 设置窗口透明度
            self.window.setWindowOpacity(window_settings['opacity'])

            # 设置窗口置顶
            if window_settings['always_on_top']:
                self.window.setWindowFlags(Qt.WindowStaysOnTopHint)
            
            return True
            
        except Exception as e:
            self._show_error("初始化失败", str(e))
            return False

    def run(self) -> int:
        """运行应用程序

        Returns:
            int: 退出码
        """
        try:
            # 初始化
            if not self.initialize():
                return 1

            # 显示主窗口
            if self.window:
                self.window.show()

            # 进入事件循环
            return self.app.exec_()

        except Exception as e:
            self._show_error("运行时错误", str(e))
            return 1

        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        try:
            # 清理日志
            if self.logger:
                self.logger.cleanup()

            # 保存配置
            if self.settings:
                self.settings.save()

        except Exception as e:
            print(f"清理资源失败: {e}")

    def _show_error(self, title: str, message: str):
        """显示错误对话框"""
        if self.app:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setWindowTitle(title)
            error_box.setText(message)
            error_box.setDetailedText(traceback.format_exc())
            error_box.exec_()
        else:
            print(f"错误: {title}\n{message}\n{traceback.format_exc()}")

    def _get_screen_width(self) -> int:
        """获取屏幕宽度"""
        return QApplication.primaryScreen().size().width()

    def _get_screen_height(self) -> int:
        """获取屏幕高度"""
        return QApplication.primaryScreen().size().height()

def main():
    """程序入口点"""
    app = Application()
    sys.exit(app.run())

if __name__ == "__main__":
    main() 