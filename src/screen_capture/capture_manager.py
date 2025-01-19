from typing import Dict, Type

import numpy as np

from src.config.settings import ConfigManager
from src.screen_capture.capture.base_capture import BaseCapture
from src.screen_capture.capture.dxgi_capture import DXGICapture
from src.screen_capture.capture.mss_capture import MSSCapture
from src.screen_capture.capture.win32_capture import Win32Capture
from src.screen_capture.utils.process_logger import ProcessLogger


class CaptureManager:
    """管理不同的截图实现"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CaptureManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not CaptureManager._initialized:
            self.logger = ProcessLogger.get_instance()
            self._capture_classes: Dict[str, Type[BaseCapture]] = {
                'win32': Win32Capture,
                'dxgi': DXGICapture,
                'mss': MSSCapture
            }
            self._current_method = None
            self._current_capture = None
            self.settings = ConfigManager("capture_config")
            CaptureManager._initialized = True
            self.get_capture(self.settings.get('capture', 'method', 'dxgi'))

    @classmethod
    def get_instance(cls) -> 'CaptureManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_capture(self, method: str) -> BaseCapture:
        """获取指定的截图实现，如果切换方式则清理旧实例"""
        try:
            capture_class = self.get_capture_methods().get(method)
            if capture_class:
                self.capture_method = capture_class.get_instance()
                return self.capture_method
        except Exception as e:
            self.logger.error(f"获取截图实现失败: {e}")
            return self.get_capture_methods()['dxgi'].get_instance()

    def get_capture_methods(self) -> Dict[str, Type[BaseCapture]]:
        """获取所有可用的截图方法
        Returns:
            Dict[str, Type[BaseCapture]]: 键为显示名称，值为截图类
        """
        return self._capture_classes.copy()

    def set_fps(self, fps: int):
        """设置FPS"""
        self.capture_method.set_fps(fps)

    def get_fps(self) -> int:
        """获取FPS"""
        return self.settings.get('capture', 'fps', 60)

    def set_method(self, method: str):
        """设置截图方式"""
        self.get_capture(method)
        self.settings.set('capture', 'method', method)
        self.settings.save()

    def get_method(self) -> str:
        """获取截图方式"""
        return self.settings.get('capture', 'method', 'dxgi')

    def get_frame(self) -> np.ndarray:
        """获取帧"""
        return self.capture_method.safe_capture()

    # def get_frame_cache(self) -> np.ndarray:
    #     """获取帧缓存"""
    #     return self.capture_method.frame_cache  

    # def set_frame_cache(self, frame: np.ndarray):
    #     """设置帧缓存"""
    #     self.capture_method.frame_cache = frame
