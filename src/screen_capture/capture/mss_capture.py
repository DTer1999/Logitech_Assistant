import mss
import numpy as np

from .base_capture import BaseCapture


class MSSCapture(BaseCapture):
    """使用MSS的截图实现"""

    def __init__(self):
        super().__init__()
        self.method = 'mss'
        self.mss = None
        self.monitor = None
        self.initialize()

    def initialize(self) -> bool:
        """初始化MSS"""
        try:
            # 每次初始化都创建新的 mss 实例
            if self.mss is not None:
                self.cleanup()

            self.mss = mss.mss()
            # 获取主显示器
            self.monitor = self.mss.monitors[1]  # monitors[0]是所有显示器的组合
            return True
        except Exception as e:
            self.logger.error(f"初始化MSS截图失败: {e}")
            self.cleanup()
            return False

    def capture(self) -> np.ndarray:
        try:
            # 如果 mss 实例不存在，重新初始化
            if self.mss is None:
                if not self.initialize():
                    return None

            # 截取全屏，直接返回BGRA格式
            return np.array(self.mss.grab(self.monitor))

        except Exception as e:
            self.logger.error(f"MSS截图失败: {str(e)}")
            # 发生错误时清理并重新初始化
            self.cleanup()
            return None

    def cleanup(self):
        """清理MSS资源"""
        try:
            if self.mss is not None:
                self.mss.close()
                self.mss = None
                self.monitor = None
        except Exception as e:
            self.logger.error(f"清理MSS截图资源失败: {e}")
