from typing import List

import cv2
import numpy as np
import win32con
import win32gui
import win32ui

from .base_capture import BaseCapture


class Win32Capture(BaseCapture):
    """使用Win32 API的截图实现"""

    def __init__(self):
        super().__init__()
        self.method = 'win32'
        self.hwnd = None
        self.hwndDC = None
        self.mfcDC = None
        self.saveDC = None

    def initialize(self) -> bool:
        """初始化截图资源"""
        try:
            self.hwnd = win32gui.GetDesktopWindow()
            # 创建设备上下文
            self.hwndDC = win32gui.GetWindowDC(self.hwnd)
            self.mfcDC = win32ui.CreateDCFromHandle(self.hwndDC)
            self.saveDC = self.mfcDC.CreateCompatibleDC()
            return True
        except Exception as e:
            self.logger.error(f"初始化Win32截图失败: {e}")
            return False

    def capture(self, region: List[int]) -> np.ndarray:
        try:
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(self.mfcDC, region[2], region[3])
            self.saveDC.SelectObject(saveBitMap)

            # 复制屏幕内容到位图
            self.saveDC.BitBlt(
                (0, 0), (region[2], region[3]),
                self.mfcDC, (region[0], region[1]),
                win32con.SRCCOPY
            )

            # 转换为numpy数组
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (region[3], region[2], 4)

            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            self.cleanup()

            # 转换为BGR格式
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        except Exception as e:
            self.logger.error(f"Win32截图失败: {e}")
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        try:
            if self.saveDC:
                self.saveDC.DeleteDC()
                self.saveDC = None
            if self.mfcDC:
                self.mfcDC.DeleteDC()
                self.mfcDC = None
            if self.hwndDC and self.hwnd:
                win32gui.ReleaseDC(self.hwnd, self.hwndDC)
                self.hwndDC = None
        except Exception as e:
            self.logger.error(f"清理Win32截图资源失败: {e}")
