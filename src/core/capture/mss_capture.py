import threading
from typing import List

import cv2
import mss
import numpy as np

from .base_capture import BaseCapture


class MSSCapture(BaseCapture):
    """使用MSS的截图实现"""

    def __init__(self):
        self._local = threading.local()
        super().__init__()
        self.method = 'mss'

    def initialize(self) -> bool:
        """初始化MSS"""
        try:
            if not hasattr(self._local, 'mss') or self._local.mss is None:
                self._local.mss = mss.mss()
            return True
        except Exception as e:
            self.logger.error(f"初始化MSS截图失败: {e}")
            return False

    def capture(self, region: List[int]) -> np.ndarray:
        try:
            # 确保 MSS 实例存在
            if not hasattr(self._local, 'mss') or self._local.mss is None:
                self.initialize()

            monitor = {
                "left": region[0],
                "top": region[1],
                "width": region[2],
                "height": region[3]
            }
            screenshot = np.array(self._local.mss.grab(monitor))
            return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        except Exception as e:
            self.logger.error(f"MSS截图失败: {str(e)}")
            # 尝试重新初始化
            self._local.mss = None
            self.initialize()
            raise

    def cleanup(self):
        """清理MSS资源"""
        try:
            if hasattr(self._local, 'mss') and self._local.mss is not None:
                self._local.mss.close()
                self._local.mss = None
        except Exception as e:
            self.logger.error(f"清理MSS截图资源失败: {e}")
