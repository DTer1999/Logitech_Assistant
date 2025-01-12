import logging
import sys

from ...config.settings import ConfigManager


class ProcessLogger:
    """进程专用的普通日志记录器"""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProcessLogger()
        return cls._instance

    def __init__(self):
        if ProcessLogger._instance is not None:
            raise Exception("This class is a singleton!")

        self.logger = logging.getLogger("ProcessLogger")
        self.logger.setLevel(logging.DEBUG)
        self.settings = ConfigManager("capture_config")
        self._setup_logger()
        ProcessLogger._instance = self

    def _setup_logger(self):
        # 确保日志目录存在
        logs_path = self.settings.get_path("logs")

        # 文件处理器
        file_handler = logging.FileHandler(
            logs_path / "process.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # 设置格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def cleanup(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
