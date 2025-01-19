import time
from multiprocessing import shared_memory, Queue

import cv2
import numpy as np

from src.config.settings import ConfigManager
from src.screen_capture.capture_manager import CaptureManager
from src.screen_capture.utils.process_logger import ProcessLogger


def capture_worker(
        shared_memory_name: str,
        frame_shape: tuple,
        command_queue: Queue
):
    """截图进程的工作函数"""
    logger = ProcessLogger.get_instance()
    settings = ConfigManager("capture_config")
    shared_mem = shared_memory.SharedMemory(name=shared_memory_name)

    try:
        shared_array = np.ndarray(
            frame_shape,
            dtype=np.uint8,
            buffer=shared_mem.buf[0:],
            strides=None,
            order='C'
        )

        # 初始化捕获方法
        method = settings.get('capture', 'method', 'dxgi')
        capture_method = CaptureManager().get_capture(method)

        fps = settings.get('capture', 'fps', 60)
        frame_interval = 1.0 / fps
        last_frame_time = time.perf_counter()

        while True:
            # 检查命令队列
            if not command_queue.empty():
                try:
                    # 队列出队
                    cmd, value = command_queue.get()
                    if cmd == "set_fps":
                        fps = value
                        frame_interval = 1.0 / fps
                        settings.set('capture', 'fps', fps)
                        logger.info(f"帧率已更改为: {fps}")
                    elif cmd == "set_method":
                        method = value
                        capture_method = CaptureManager().get_capture(method)
                        settings.set('capture', 'method', method)
                        logger.info(f"捕获方法已更改为: {method}")
                    elif cmd == "get_frame":
                        start_time = time.perf_counter()
                        current_time = time.perf_counter()
                        elapsed_time = current_time - last_frame_time

                        # 如果距离上次截图时间不够，等待剩余时间
                        if elapsed_time < frame_interval:
                            wait_time = frame_interval - elapsed_time
                            time.sleep(wait_time)

                        logger.debug(f"截图成功，时间间隔: {time.perf_counter() - last_frame_time:.2f}秒")

                        try:
                            frame = capture_method.capture()

                            if frame is not None and not np.all(frame == 0):
                                # 确保帧为BGR格式
                                if isinstance(frame, np.ndarray):
                                    if frame.shape[2] == 4:  # BGRA转BGR
                                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                                    # elif frame.shape[2] == 3:
                                    #     pass  # 已是BGR
                                    # else:
                                    #     logger.error(f"不支持的帧格式: {frame.shape}")
                                    #     continue

                                    # # 调整大小到目标尺寸
                                    # if frame.shape[:2] != frame_shape[:2]:
                                    #     frame = cv2.resize(frame, (frame_shape[1], frame_shape[0]))

                                    # 更新共享内存
                                    np.copyto(shared_array, frame)
                                    last_frame_time = time.perf_counter()  # 更新最后截图时间

                                    # logger.debug(f"截图成功，时间间隔: {time.perf_counter() - start_time:.2f}秒")
                                else:
                                    logger.error(f"不支持的帧类型: {type(frame)}")
                        except Exception as e:
                            logger.error(f"截图失败: {e}")
                    elif cmd == "stop":
                        logger.info("收到停止命令")
                        return
                except Exception as e:
                    logger.error(f"处理命令失败: {e}")

            # 短暂休眠以避免CPU占用过高
            time.sleep(0.001)

    except Exception as e:
        logger.error(f"截图进程出错: {e}")
    finally:
        if shared_mem:
            shared_mem.close()
            shared_mem.unlink()
