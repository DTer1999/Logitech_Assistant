from abc import ABC, abstractmethod

import numpy as np

from ...utils.logger_factory import LoggerFactory


class BaseCapture(ABC):
    def __init__(self):
        self.logger = LoggerFactory.get_logger()
        self.initialize()

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
