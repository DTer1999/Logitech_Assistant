import time
from multiprocessing import shared_memory, Queue

import numpy as np
import psutil

from ..utils.logger_factory import LoggerFactory
from ...config.settings import ConfigManager


class FrameClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = FrameClient()
        return cls._instance

    def __init__(self):
        if FrameClient._instance is not None:
            raise Exception("This class is a singleton!")

        self.logger = LoggerFactory.get_logger()
        self.shared_mem = None
        self.command_queue = Queue()
        self.frame_shape = (1440, 2560, 3)
        self._is_connected = False
        self._last_frame = None
        self._last_frame_time = 0
        self._frame_interval = 1.0 / 10  # 默认60fps

        FrameClient._instance = self

    def connect(self) -> bool:
        """连接到后台进程，带重试机制"""
        if self._is_connected:
            return True

        # 最多等待5秒
        max_retries = 10
        retry_interval = 0.5

        for _ in range(max_retries):
            try:
                # 从配置文件获取当前的共享内存名称
                settings = ConfigManager("capture_config")
                memory_name = settings.get('capture', 'memory_name')

                if not memory_name:
                    raise FileNotFoundError("未找到有效的共享内存名称")

                self.shared_mem = shared_memory.SharedMemory(
                    name=memory_name,
                    create=False
                )
                # self.command_queue = 
                self._is_connected = True
                self.logger.info("成功连接到截图进程")
                return True
            except FileNotFoundError:
                time.sleep(retry_interval)
            except Exception as e:
                self.logger.error(f"连接失败: {e}")
                return False

        self.logger.error("连接超时")
        return False

    def set_capture_method(self, method: str):
        """设置截图方式"""
        if self.command_queue:
            self.command_queue.put(("set_method", method))

    def set_fps(self, fps: int):
        """设置帧率"""
        if self.command_queue:
            self.command_queue.put(("set_fps", fps))
            self._frame_interval = 1.0 / fps
            self.logger.info(f"设置帧率为: {fps}")

    def is_capture_running(self) -> bool:
        """检查截图进程是否运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'obs64.exe':
                return True
        return False

    def get_frame(self):
        """获取当前帧"""
        if not self.shared_mem:
            return None

        current_time = time.perf_counter()

        # 如果缓存的帧还在有效期内，直接返回缓存的帧
        # if (self._last_frame is not None and
        #     current_time - self._last_frame_time < self._frame_interval):
        #     return self._last_frame.copy()

        # 发送获取帧的命令
        self.command_queue.put(("get_frame", None))
        
        try:
            # 设置最大等待时间，避免无限等待
            max_retries = 50  # 最多等待5秒
            retry_count = 5

            while True:
                frame = np.ndarray(
                    self.frame_shape,
                    dtype=np.uint8,
                    buffer=self.shared_mem.buf,
                    strides=None,
                    order='C'
                )

                # 检查是否获取到有效帧
                if not np.all(frame == 0):
                    self._last_frame = frame.copy()
                    self._last_frame_time = current_time
                    # 清空共享内存 - 使用字节类型的0
                    self.shared_mem.buf[:] = bytes([0] * len(self.shared_mem.buf))
                    return self._last_frame.copy()

                # 增加重试次数
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.warning("等待帧数据超时")
                    return None

                # 短暂等待后重试
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"获取帧失败: {e}")
            return None

    def _need_modify_frame(self):
        """判断是否需要修改帧数据"""
        # 如果后续处理需要修改帧数据，返回True
        # 目前默认返回False，直接使用共享内存中的数据
        return False

    def close(self):
        """关闭连接"""
        if self.shared_mem:
            self.shared_mem.close()
            self._is_connected = False