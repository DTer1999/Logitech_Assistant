import threading
from typing import Dict, Type

from .base_capture import BaseCapture
from .mss_capture import MSSCapture
from .nvidia_capture import NvidiaCapture
from .win32_capture import Win32Capture


class CaptureManager:
    """每个线程管理自己的 Capture 实例"""

    def __init__(self):
        self._local = threading.local()
        self._capture_classes: Dict[str, Type[BaseCapture]] = {
            'win32': Win32Capture,
            'mss': MSSCapture,
            'nvidia': NvidiaCapture
        }

    def get_capture(self, method: str) -> BaseCapture:
        """获取当前线程的 Capture 实例"""
        if not hasattr(self._local, 'capture') or \
                not isinstance(self._local.capture, self._capture_classes.get(method)):
            # 如果当前线程没有对应的实例，创建新的
            capture_class = self._capture_classes.get(method)
            if not capture_class:
                raise ValueError(f"Unsupported capture method: {method}")

            # 清理旧的实例（如果存在）
            if hasattr(self._local, 'capture'):
                self._local.capture.cleanup()

            # 创建新实例
            self._local.capture = capture_class()

        return self._local.capture

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
