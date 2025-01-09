import time

from PyQt5.QtCore import QThread

from .capture_manager import CaptureManager
from ...config.settings import Settings
from ...utils.logger_factory import LoggerFactory


class ScreenCaptureThread(QThread):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        super().__init__()
        self.logger = LoggerFactory.get_logger()
        self.settings = Settings.get_instance()
        method = self.settings.get('capture', 'method', 'dxgi')
        self.capture_method = CaptureManager().get_capture(method)
        self.fps = self.settings.get('capture', 'fps', 60)
        self.last_frame_time = time.time()
        self.frame_time = 1.0 / self.fps
        self.frame = None
        self.paused = False
        self.running = False
        self._initialized = True

    @classmethod
    def get_instance(cls):
        """获取截图线程实例"""
        if cls._instance is None:
            cls()
        return cls._instance

    def set_capture_method(self, capture_method):
        """设置截图方法"""
        self.capture_method = capture_method
        self.logger.info("截图方法已更新")

    def run(self):
        """线程主循环"""
        self.logger.info("截图线程已启动")
        self.running = True
        retry_count = 0
        max_retries = 3  # 最大重试次数

        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                current_time = time.time()
                time_diff = current_time - self.last_frame_time

                if time_diff < self.frame_time:
                    sleep_time = self.frame_time - time_diff
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    continue

                frame = self.capture_method.capture()
                if frame is not None:
                    self.frame = frame
                    self.last_frame_time = time.time()
                    retry_count = 0  # 成功后重置重试计数
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        self.logger.error("连续多次获取帧失败，尝试重新初始化截图方法")
                        # 重新初始化截图方法
                        method = self.settings.get('capture', 'method', 'dxgi')
                        self.capture_method = CaptureManager().get_capture(method)
                        retry_count = 0
                    time.sleep(0.1)  # 失败后等待一段时间再重试

            except Exception as e:
                self.logger.error(f"截图过程出错: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.error("连续多次出错，尝试重新初始化截图方法")
                    # 重新初始化截图方法
                    method = self.settings.get('capture', 'method', 'dxgi')
                    self.capture_method = CaptureManager().get_capture(method)
                    retry_count = 0
                time.sleep(0.1)

    def get_frame(self):
        """获取当前帧"""
        return self.frame

    def set_fps(self, fps):
        """设置目标帧率"""
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.logger.info(f"帧率已设置为: {fps}")

    def set_method(self, method):
        """设置截图方法"""
        self.capture_method = CaptureManager().get_capture(method)
        self.logger.info(f"截图方法已设置为: {method}")

    def pause(self):
        """暂停截图"""
        self.paused = True
        self.logger.info("截图已暂停")

    def resume(self):
        """恢复截图"""
        self.paused = False
        self.logger.info("截图已恢复")

    def stop(self):
        """停止截图线程"""
        self.running = False
        self.wait()
        self.logger.info("截图线程已停止")

    def is_active(self):
        """判断截图线程是否正在运行"""
        return self.isRunning() or self.running
