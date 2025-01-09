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
        self.screen_width = self.settings.get('capture', 'screen_width', 2560)
        self.screen_height = self.settings.get('capture', 'screen_height', 1440)
        self.initialize()

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
            self.cleanup()  # 确保清理资源
            return False

    def capture(self) -> np.ndarray:
        if not self.mfcDC or not self.saveDC:
            self.initialize()
        try:
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(self.mfcDC, self.screen_width, self.screen_height)
            self.saveDC.SelectObject(saveBitMap)

            # 复制全屏内容到位图
            self.saveDC.BitBlt(
                (0, 0), (self.screen_width, self.screen_height),
                self.mfcDC, (0, 0),
                win32con.SRCCOPY
            )

            # 转换为numpy数组，直接返回BGRA格式
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (self.screen_height, self.screen_width, 4)

            # 清理位图资源
            win32gui.DeleteObject(saveBitMap.GetHandle())

            # 直接返回BGRA格式
            return img

        except Exception as e:
            self.logger.error(f"Win32截图失败: {e}")
        finally:
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
