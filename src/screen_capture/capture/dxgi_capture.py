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
        self.frame_data = np.empty((self.target_height, self.target_width, 4), dtype=np.uint8)  # 预分配数组

    def initialize(self):
        """初始化 DXGI 捕获"""
        if self._initialized:
            return True
        # import cProfile
        # self.profiler = cProfile.Profile()
        # self.profiler.enable()  # 开始性能分析
        if not self.handle:
            self.logger.error("DXGI handle is null")
            return False

        self._initialized = self.dll.InitializeCapture(self.handle)
        if not self._initialized:
            self.logger.error("Failed to initialize DXGI capture")
        else:
            self.logger.info("DXGI capture initialized successfully")
            # 捕获第一帧以确保初始化完成
            # first_frame = self.capture()
            # if first_frame is None:
            #     self.logger.error("Failed to capture first frame")
            #     self._initialized = False
            
        return self._initialized

    def capture(self):
        """执行截图
        
        Returns:
            numpy.ndarray: 如果成功，返回 RGB 格式的 numpy 数组
            None: 如果失败
        """
        try:
            # 确保指针为空
            self._data_ptr = POINTER(c_ubyte)()
            
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

            try:
                buffer_size = self._stride.value * self._height.value
                # 创建数组的副本以避免内存访问问题
                frame_data = np.ctypeslib.as_array(self._data_ptr, shape=(buffer_size,)).copy()

                # 重塑数组为正确的维度 (BGRA)
                actual_width = self._stride.value // 4  # BGRA 格式，每像素4字节
                frame = frame_data.reshape(self._height.value, actual_width, 4)

                # 转换 BGRA 为 RGB (去掉 alpha 通道并调换通道顺序)
                rgb_frame = frame[..., [2, 1, 0]].copy()  # 创建副本以确保内存安全

                return rgb_frame

            finally:
                # 确保在任何情况下都释放内存
                if self._data_ptr:
                    ctypes.windll.ole32.CoTaskMemFree(self._data_ptr)
                    self._data_ptr = POINTER(c_ubyte)()

        except Exception as e:
            self.logger.error(f"捕获屏幕失败: {e}")
            return None

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
        """析构函数，确保资源被正确释放"""
        try:
            self.cleanup()
        except:
            pass
