import os
import sys
import time

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
from screen_capture.screen_capture_daemon import ScreenCaptureDaemon


def main():
    # 检查是否已经运行
    import psutil
    current_process = psutil.Process()
    for proc in psutil.process_iter(['name']):
        if (proc.info['name'] == 'obs64' and
                proc.pid != current_process.pid):
            print("截图进程已在运行")
            return
    from multiprocessing import Queue
    command_queue = Queue()
    for _ in range(100):
        command_queue.put(("get_frame", None))

    # 启动后台程序
    daemon = ScreenCaptureDaemon(command_queue)
    if daemon.start():
        try:
            # 保持主进程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在关闭程序...")
        finally:
            daemon.stop()


if __name__ == '__main__':
    main()
