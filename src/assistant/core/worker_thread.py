from PyQt5.QtCore import QThread, pyqtSignal

from .pubg_main import PubgCore
from ..utils.logger_factory import LoggerFactory


class WorkerThread(QThread):
    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.logger = LoggerFactory.get_logger()
        self.pubg_core = PubgCore()
        self._is_running = False
        self.stop_signal.connect(self.stop)

    def run(self):

        if self._is_running:
            return
        try:
            self.logger.info("线程开始运行")
            self._is_running = True
            # self.pubg_core = PubgCore()
            self.pubg_core.start()
        except Exception as e:
            self.logger.error(f"线程运行错误: {e}")
            self._is_running = False
            self.stop_signal.emit()

    def stop(self):

        if self.is_alive():
            self.pubg_core.stop()
            self._is_running = False
            # 设置超时等待
            if not self.wait(5000):  # 等待5秒
                self.terminate()  # 强制终止
                self.logger.error("线程强制终止")
        self.logger.close_progress(7)

    def is_alive(self):
        return self._is_running and self.isRunning()
