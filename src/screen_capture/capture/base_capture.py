import threading
import time
from abc import ABC, abstractmethod

import numpy as np

from ..utils.process_logger import ProcessLogger
from ...config.settings import ConfigManager


class BaseCapture(ABC):
    """截图基类"""
    _instances = {}  # 用于存储各个子类的实例
    _locks = {}  # 为每个子类存储独立的锁

    @classmethod
    def get_instance(cls) -> 'BaseCapture':
        """获取单例实例"""
        # 为每个子类创建独立的锁
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()

        # 使用子类特定的锁
        if cls not in cls._instances:
            with cls._locks[cls]:
                if cls not in cls._instances:
                    cls._instances[cls] = cls()
                    cls._instances[cls].initialize()
        return cls._instances[cls]

    def __init__(self):
        self.settings = ConfigManager("capture_config")
        self.logger = ProcessLogger.get_instance()
        self.method = 'base'  # 子类需要覆盖这个属性

        # 添加截屏频率控制
        self.min_capture_interval = 1.0 / self.settings.get('capture', 'fps', 60)  # 默认最大60fps
        self._initialized = False

        # 添加帧缓存
        self._frame_cache = None
        self.last_capture_time = 0

    def safe_capture(self) -> np.ndarray:
        """带频率限制和资源管理的安全截图方法，使用缓存而不是sleep
        
        Returns:
            numpy.ndarray: 如果成功，返回图像数组；如果失败，返回None
        """
        current_time = time.time()

        # 使用类的锁确保线程安全
        with self.__class__._locks[self.__class__]:
            if not self._initialized and not self.initialize():
                return None

            try:
                # 检查是否需要进行新的捕获
                if (current_time - self.last_capture_time) >= self.min_capture_interval:
                    # 执行实际的捕获
                    frame = self.capture()
                    if frame is not None:
                        self._frame_cache = frame
                        self.last_capture_time = current_time
                    return frame
                else:
                    # 返回缓存的帧
                    return self._frame_cache

            except Exception as e:
                self.logger.error(f"{self.method} 截图失败: {e}")
                return self._frame_cache  # 发生错误时返回缓存的帧

    def set_fps(self, fps: int):
        """设置FPS"""
        self.min_capture_interval = 1.0 / fps
        self.settings.set('capture', 'fps', fps)
        self.settings.save()

    def get_fps(self) -> int:
        """获取FPS"""
        return int(1.0 / self.min_capture_interval)

    @abstractmethod
    def initialize(self) -> bool:
        """初始化截图方法"""
        pass

    @abstractmethod
    def capture(self) -> np.ndarray:
        """执行截图"""
        pass

    @abstractmethod
    def cleanup(self):
        """清理资源"""
        pass

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            self.cleanup()
        except:
            pass
