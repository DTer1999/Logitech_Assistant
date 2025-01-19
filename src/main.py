#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import multiprocessing
import sys
import traceback
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox

from src.assistant.ui.main_window import MainWindow
from src.assistant.utils.logger_factory import LoggerFactory
from src.config.settings import ConfigManager


class Application:
    """应用程序主类"""
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[MainWindow] = None
        self.capture_daemon = None  # 添加 capture_daemon 属性
        # 1. 初始化配置（全局单例）
        self.settings = ConfigManager("config")
        # 2. 初始化日志（全局单例）
        self.logger = LoggerFactory.get_logger()

    def initialize(self) -> bool:
        """初始化应用程序组件"""
        try:

            # 4. 初始化UI
            self.app = QApplication(sys.argv)
            self.window = MainWindow()
            width = self._get_screen_width()
            height = self._get_screen_height()
            self.settings.set('screen', 'width', width)
            self.settings.set('screen', 'height', height)

            capture_config = ConfigManager('capture_config')
            capture_config.set('frame_shape', 'width', width)
            capture_config.set('frame_shape', 'height', height)
            capture_config.save()

            # 应用窗口设置
            window_settings = self.settings.get('window')
            
            # 设置窗口大小
            self.window.resize(
                window_settings['width'],
                window_settings['height']
            )
            # 设置窗口透明度
            self.window.setWindowOpacity(window_settings['opacity'])
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
        if self.app:
            screen = self.app.primaryScreen()
            return screen.size().width()
        return 2560  # 默认宽度

    def _get_screen_height(self) -> int:
        """获取屏幕高度"""
        if self.app:
            screen = self.app.primaryScreen()
            return screen.size().height()
        return 1080  # 默认高度


def main():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的程序，确保multiprocessing正常工作
        multiprocessing.freeze_support()
    
    app = Application()

    try:
        sys.exit(app.run())
    except KeyboardInterrupt:
        # 处理 Ctrl+C
        print("\n正在关闭程序...")
        app.cleanup()
    except Exception as e:
        print(f"程序异常退出: {e}")
        app.cleanup()
    finally:
        # 确保所有子进程都被终止
        for p in multiprocessing.active_children():
            try:
                p.terminate()
                p.join(timeout=0.5)
                if p.is_alive():
                    p.kill()
            except Exception:
                pass

if __name__ == "__main__":
    main()
