import time
import uuid
from multiprocessing import Process, shared_memory, Queue

import numpy as np

from src.config.settings import ConfigManager
from src.screen_capture.utils.process_logger import ProcessLogger


class ScreenCaptureDaemon:
    def __init__(self, command_queue: Queue = Queue()):
        # 通过工厂获取 process 类型的 logger
        self.logger = ProcessLogger.get_instance()
        self.settings = ConfigManager("capture_config")
        self.process = None
        self.shared_mem = None
        self.command_queue = command_queue
        self.frame_shape = (
            self.settings.get('frame_shape', 'height', 1440),
            self.settings.get('frame_shape', 'width', 2560),
            self.settings.get('frame_shape', 'channels', 3)
        )
        self.running = False

        # 生成唯一的内存名称
        self.memory_name = f"ScreenCaptureMemory_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        # 保存内存名称到文件
        self.settings.set('capture', 'memory_name', self.memory_name)
        self.settings.save()

    def start(self):
        """启动后台进程"""
        try:
            self.running = True

            # 创建共享内存
            buffer_size = int(np.prod(self.frame_shape))  # 计算共享内存大小
            self.shared_mem = shared_memory.SharedMemory(
                name=self.memory_name,
                create=True,
                size=buffer_size
            )
            self.logger.info(f"成功创建共享内存: {self.memory_name}")

            # 创建命令队列
            # self.command_queue = Queue()

            # 创建并启动截图进程
            from .capture_process import capture_worker
            self.process = Process(
                target=capture_worker,
                args=(
                    self.memory_name,
                    self.frame_shape,
                    self.command_queue
                ),
                name="obs64"  # 设置进程名
            )
            self.process.start()
            self.logger.info("截图进程已启动")

            # 等待进程启动
            time.sleep(0.1)

            # 检查进程是否成功启动
            if not self.process.is_alive():
                raise Exception("截图进程启动失败")

            return True

        except Exception as e:
            self.logger.error(f"启动后台进程失败: {e}")
            self.cleanup()
            return False

    def stop(self):
        """停止守护进程"""
        try:
            self.running = False
            if self.process and self.process.is_alive():
                # 1. 先发送停止信号
                if self.command_queue:
                    self.command_queue.put(("stop", None))
                    time.sleep(0.1)  # 给一点时间处理停止命令

                # 2. 等待进程自然结束
                self.process.join(timeout=1.0)

                # 3. 如果还活着，发送终止信号
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(timeout=1.0)

                    # 4. 如果还是活着，强制结束
                    if self.process.is_alive():
                        self.process.kill()
                        self.process.join(timeout=0.5)

                self.logger.info("截图进程已停止")
        except Exception as e:
            self.logger.error(f"停止进程失败: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        try:
            # 1. 确保进程已经停止
            if self.process:
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(timeout=1.0)
                    if self.process.is_alive():
                        self.process.kill()
                        self.process.join(timeout=0.5)
                self.process = None

            # 2. 清理共享内存（带重试机制）
            if self.shared_mem:
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        self.shared_mem.close()
                        self.shared_mem.unlink()
                        self.logger.info(f"成功清理共享内存，尝试次数：{attempt + 1}")
                        break
                    except Exception as e:
                        self.logger.error(f"清理共享内存尝试 {attempt + 1} 失败: {e}")
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)  # 等待后重试
                self.shared_mem = None

            # 3. 清理命令队列
            if self.command_queue:
                while not self.command_queue.empty():
                    self.command_queue.get()
                self.command_queue = None

            self.logger.info("资源清理完成")

        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")

    def __del__(self):
        """析构函数，确保清理资源"""
        # 不在这里清理共享内存，让 cleanup 方法来处理
        if hasattr(self, 'running') and self.running:
            self.stop()
