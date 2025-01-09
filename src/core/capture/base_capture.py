import threading
from abc import ABC, abstractmethod

import numpy as np

from ...config.settings import Settings
from ...utils.logger_factory import LoggerFactory


class BaseCapture(ABC):
    """截图基类"""
    _instances = {}  # 用于存储各个子类的实例
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'BaseCapture':
        """获取单例实例"""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = cls()
        return cls._instances[cls]

    def __init__(self):
        self.settings = Settings.get_instance()
        self.logger = LoggerFactory.get_logger()
        self.method = 'base'  # 子类需要覆盖这个属性

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
