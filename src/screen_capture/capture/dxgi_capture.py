import ctypes
from ctypes import c_void_p, c_bool, c_uint, c_ulonglong, POINTER, c_ubyte

import numpy as np

from .base_capture import BaseCapture


class DXGICapture(BaseCapture):
    def __init__(self):
        super().__init__()
        self.method = 'dxgi'

        # 从配置文件获取分辨率
        self.target_width = self.settings.get('frame_shape', 'width', 2560)  # 默认1920
        self.target_height = self.settings.get('frame_shape', 'height', 1440)  # 默认1080

        # 加载 DLL
        dll_path = self.settings.get_path('dll') / 'CaptureScreen.dll'
        self.dll = ctypes.CDLL(str(dll_path))

        # 设置函数参数和返回类型
        self.dll.CreateScreenCapture.restype = c_void_p
        self.dll.DestroyScreenCapture.argtypes = [c_void_p]
        self.dll.InitializeCapture.argtypes = [c_void_p]
        self.dll.InitializeCapture.restype = c_bool
        self.dll.GetNextFrameData.argtypes = [
            c_void_p,
            POINTER(POINTER(c_ubyte)),
            POINTER(c_uint),
            POINTER(c_uint),
            POINTER(c_uint),
            POINTER(c_ulonglong)
        ]
        self.dll.GetNextFrameData.restype = c_bool

        # 预先创建捕获帧所需的 ctypes 对象
        self._data_ptr = POINTER(c_ubyte)()
        self._width = c_uint(self.target_width)  # 使用配置的宽度
        self._height = c_uint(self.target_height)  # 使用配置的高度
        self._stride = c_uint()  # stride 需要从DLL获取，因为可能包含内存对齐
        self._timestamp = c_ulonglong()

        # 创建实例
        self.handle = self.dll.CreateScreenCapture()
        if not self.handle:
            self.logger.error("Failed to create DXGI screen capture instance")
            raise RuntimeError("Failed to create DXGI screen capture instance")

        self._initialized = False   

    def initialize(self):
        """初始化 DXGI 捕获"""
        if self._initialized:
            return True

        if not self.handle:
            self.logger.error("DXGI handle is null")
            return False

        self._initialized = self.dll.InitializeCapture(self.handle)
        if not self._initialized:
            self.logger.error("Failed to initialize DXGI capture")
        else:
            self.logger.info("DXGI capture initialized successfully")
        return self._initialized

    def capture(self):
        """获取一帧画面
        
        Returns:
            tuple: (frame, timestamp) 如果成功，frame 是 BGRA 格式的 numpy 数组，timestamp 是时间戳
                  None 如果失败
        """
        if not self._initialized and not self.initialize():
            return None

        try:
            success = self.dll.GetNextFrameData(
                self.handle,
                ctypes.byref(self._data_ptr),
                ctypes.byref(self._width),
                ctypes.byref(self._height),
                ctypes.byref(self._stride),
                ctypes.byref(self._timestamp)
            )

            if not success or not self._data_ptr:
                return None

            # 计算实际的数据大小
            buffer_size = self._stride.value * self._height.value

            # 创建 numpy 数组，确保复制数据
            frame_data = np.fromiter(
                (self._data_ptr[i] for i in range(buffer_size)),
                dtype=np.uint8
            )

            # 重塑数组
            frame = frame_data.reshape(self._height.value, self._stride.value // 4, 4)

            # 如果需要，裁剪到实际宽度
            if self._stride.value // 4 != self._width.value:
                frame = frame[:, :self._width.value]

            # 直接返回 BGRA 格式，不做转换
            return frame

        except Exception as e:
            self.logger.error(f"Error in DXGI capture: {e}")
            return None
        finally:
            if self._data_ptr:
                ctypes.windll.ole32.CoTaskMemFree(self._data_ptr)

    def cleanup(self):
        """释放资源"""
        if hasattr(self, 'handle') and self.handle:
            try:
                self.dll.DestroyScreenCapture(self.handle)
                self.handle = None
                self._initialized = False
            except:
                pass

    def __del__(self):
        """析构时释放资源"""
        self.cleanup()
