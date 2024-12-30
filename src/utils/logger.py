from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any

class Logger(QObject):
    """日志处理类，支持文件日志和UI更新"""
    
    # 定义信号
    log_signal = pyqtSignal(str)  # 用于更新日志显示
    ui_update_signal = pyqtSignal(dict)  # 用于更新UI组件
    close_progress_signal = pyqtSignal(int)  # 添加关闭进度信号

    def __init__(self, log_path: Path = None):
        """初始化日志处理器
        Args:
            log_path: 日志文件路径，如果为None则使用默认路径
        """
        super().__init__()
        
        # 设置日志路径
        if log_path is None:
            log_path = Path("logs")
            
        self._setup_file_logger(log_path)

    def _setup_file_logger(self, log_path: Path):
        """设置文件日志
        Args:
            log_path: 日志文件路径
        """
        try:
            # 创建日志目录
            log_path.mkdir(parents=True, exist_ok=True)

            # 生成日志文件名
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = log_path / f'pubg_{current_time}.log'

            # 配置日志处理器
            self.file_logger = logging.getLogger('PubgLogger')
            self.file_logger.setLevel(logging.INFO)

            # 文件处理器
            file_handler = logging.FileHandler(
                log_file, 
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)

            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)

            # 添加处理器
            self.file_logger.addHandler(file_handler)

        except Exception as e:
            print(f"设置日志处理器失败: {e}")
            self.file_logger = None

    def _log_to_file(self, level: int, message: str):
        """写入文件日志
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        if self.file_logger:
            try:
                self.file_logger.log(level, message)
            except Exception as e:
                print(f"写入日志失败: {e}")

    def _get_timestamp(self):
        """获取当前时间戳"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _format_message(self, level: str, message: str) -> str:
        """格式化日志消息"""
        return f"[{self._get_timestamp()}] [{level}] {message}"

    def info(self, message: str):
        """记录信息级别日志
        
        Args:
            message: 日志消息
        """
        self._log_to_file(logging.INFO, message)
        formatted_message = self._format_message("INFO", message)
        self.log_signal.emit(formatted_message)

    def warning(self, message: str):
        """记录警告级别日志
        
        Args:
            message: 日志消息
        """
        self._log_to_file(logging.WARNING, message)
        formatted_message = self._format_message("WARNING", message)
        self.log_signal.emit(formatted_message)

    def error(self, message: str):
        """记录错误级别日志
        
        Args:
            message: 日志消息
        """
        self._log_to_file(logging.ERROR, message)
        formatted_message = self._format_message("ERROR", message)
        self.log_signal.emit(formatted_message)

    def debug(self, message: str):
        """记录调试级别日志
        
        Args:
            message: 日志消息
        """
        self._log_to_file(logging.DEBUG, message)
        formatted_message = self._format_message("DEBUG", message)
        self.log_signal.emit(formatted_message)

    def update_ui(self, data: Dict[str, Any]):
        """发送UI更新信号
        
        Args:
            data: 要更新的UI数据
        """
        self.ui_update_signal.emit(data)

    def cleanup(self):
        """清理日志处理器"""
        if self.file_logger:
            try:
                for handler in self.file_logger.handlers[:]:
                    handler.close()
                    self.file_logger.removeHandler(handler)
            except Exception as e:
                print(f"清理日志处理器失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup() 

    def update_close_progress(self, stage: int):
        """发送关闭进度信号"""
        self.close_progress_signal.emit(stage) 