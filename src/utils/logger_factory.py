import logging
import sys
from typing import Dict, Type, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from ..config.settings import Settings


class LoggerFactory:
    """日志记录器工厂类（单例模式）"""
    _instance: Optional['QtLogger'] = None
    _loggers: Dict[str, Type['QtLogger']] = {}
    DEFAULT_LOGGER_TYPE = "qt"

    @classmethod
    def register(cls, name: str):
        """注册日志记录器的装饰器"""

        def wrapper(logger_class: Type['QtLogger']):
            cls._loggers[name] = logger_class
            return logger_class

        return wrapper

    @classmethod
    def get_logger(cls) -> 'QtLogger':
        """获取日志记录器实例（单例模式）"""
        if cls._instance is None:
            try:
                settings = Settings.get_instance()
                logger_type = settings.get('logger', 'type', cls.DEFAULT_LOGGER_TYPE)

                if logger_type not in cls._loggers:
                    print(f"警告: 未知的日志记录器类型 '{logger_type}'，使用默认类型 '{cls.DEFAULT_LOGGER_TYPE}'")
                    logger_type = cls.DEFAULT_LOGGER_TYPE

                cls._instance = cls._loggers[logger_type]()

            except Exception as e:
                print(f"创建指定的日志记录器失败: {e}，使用默认类型 '{cls.DEFAULT_LOGGER_TYPE}'")
                if cls.DEFAULT_LOGGER_TYPE not in cls._loggers:
                    raise RuntimeError(f"默认日志记录器类型 '{cls.DEFAULT_LOGGER_TYPE}' 未注册")
                cls._instance = cls._loggers[cls.DEFAULT_LOGGER_TYPE]()

        return cls._instance


@LoggerFactory.register("qt")
class QtLogger(QObject):
    """Qt日志记录器，包含UI信号和文件日志功能"""
    log_signal = pyqtSignal(str)
    ui_update_signal = pyqtSignal(dict)
    close_progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.settings = Settings.get_instance()
        self.logs_path = self.settings.get_path('logs')
        self.log_config = self.settings.get('logger')
        self.format_str = self.log_config.get('format', '[%(time)s] [%(level)s] %(message)s')
        self.time_format = self.log_config.get('time_format', '%H:%M:%S')
        self.level = getattr(logging, self.log_config.get('level', 'DEBUG'))
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("QtLogger")
        self.logger.setLevel(getattr(logging, "INFO"))

        # 确保日志目录存在
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # 文件处理器
        file_handler = logging.FileHandler(
            self.logs_path / self.log_config.get('filename', 'app.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        formatter = logging.Formatter(
            fmt=self.format_str,
            datefmt=self.time_format  # 添加日期格式
        )
        file_handler.setFormatter(formatter)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        self.logger.debug(message)
        self._emit_ui_log('DEBUG', message)

    def info(self, message: str):
        self.logger.info(message)
        self._emit_ui_log('INFO', message)

    def warning(self, message: str):
        self.logger.warning(message)
        self._emit_ui_log('WARN', message)

    def error(self, message: str):
        self.logger.error(message)
        self._emit_ui_log('ERROR', message)

    def close_progress(self, progress: int):
        self.close_progress_signal.emit(progress)

    def update_ui(self, ui_data: dict):
        self.ui_update_signal.emit(ui_data)

    def cleanup(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def _get_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime(self.time_format)

    def _emit_ui_log(self, level: str, message: str):
        """发送UI日志
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        log_data = {
            'asctime': self._get_time(),
            'levelname': level,
            'message': message
        }

        self.log_signal.emit(self.format_str % log_data)
