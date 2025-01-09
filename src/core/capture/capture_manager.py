import threading
from typing import Dict, Type

from .base_capture import BaseCapture
from .dxgi_capture import DXGICapture
from .win32_capture import Win32Capture
from ...utils.logger_factory import LoggerFactory


class CaptureManager:
    """每个线程管理自己的 Capture 实例"""

    def __init__(self):
        self._local = threading.local()
        self.logger = LoggerFactory.get_logger()
        self._capture_classes: Dict[str, Type[BaseCapture]] = {
            'win32': Win32Capture,
            'dxgi': DXGICapture
        }

    def get_capture(self, method: str) -> BaseCapture:
        """获取指定的截图实现"""
        try:
            capture_class = self.get_capture_methods().get(method)
            if capture_class:
                return capture_class.get_instance()  # 使用单例方法
            else:
                self.logger.error(f"未找到截图方式: {method}")
                # 返回默认的截图方式
                return self.get_capture_methods()['win32'].get_instance()
        except Exception as e:
            self.logger.error(f"获取截图实现失败: {e}")
            return self.get_capture_methods()['win32'].get_instance()

    def get_capture_methods(self) -> Dict[str, str]:
        """获取所有可用的截图方法
        Returns:
            Dict[str, str]: 键为显示名称，值为方法ID
        """
        return self._capture_classes.copy()

    def cleanup(self):
        """清理当前线程的资源"""
        if hasattr(self._local, 'capture'):
            self._local.capture.cleanup()
            del self._local.capture
