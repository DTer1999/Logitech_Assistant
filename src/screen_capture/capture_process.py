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
            buffer=shared_mem.buf[0:],  # 直接使用共享内存
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
            start_time = time.perf_counter()  # 记录开始时间

            # 检查命令队列
            while not command_queue.empty():
                try:
                    cmd, value = command_queue.get_nowait()
                    if cmd == "set_fps":
                        fps = value
                        frame_interval = 1.0 / fps
                        settings.set('capture', 'fps', fps)
                        logger.info(f"帧率已更改为: {fps}")
                    elif cmd == "set_method":
                        method = value
                        capture_method = CaptureManager().get_capture(method)  # 更新捕获方法
                        settings.set('capture', 'method', method)
                        logger.info(f"捕获方法已更改为: {method}")
                    elif cmd == "stop":
                        logger.info("收到停止命令")
                        return
                except Exception as e:
                    logger.error(f"处理命令失败: {e}")

            # 控制帧率
            current_time = time.perf_counter()
            if current_time - last_frame_time >= frame_interval:
                try:
                    # 使用选择的方法截图
                    frame = capture_method.capture()

                    if frame is not None:
                        # 确保帧为BGR格式
                        if isinstance(frame, np.ndarray):
                            if frame.shape[2] == 4:  # BGRA转BGR
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                            elif frame.shape[2] == 3:
                                pass  # 已是BGR
                            else:
                                logger.error(f"不支持的帧格式: {frame.shape}")
                                continue
                        else:
                            logger.error(f"不支持的帧类型: {type(frame)}")
                            continue

                        # 调整大小到目标尺寸
                        if frame.shape[:2] != frame_shape[:2]:
                            frame = cv2.resize(frame, (frame_shape[1], frame_shape[0]))

                        # 更新共享内存
                        np.copyto(shared_array, frame)
                        last_frame_time = current_time  # 更新最后帧时间

                        # 保存图片
                        # PictureUtil.savePicture(frame)

                        # 记录截图时间
                        # logger.debug(f"截图成功，时间间隔: {time.perf_counter() - start_time:.2f}秒")
                    else:
                        logger.warning("捕获的帧为空")

                except Exception as e:
                    logger.error(f"截图失败: {e}")

            # 记录每次循环的时间
            # logger.debug(f"循环耗时: {time.perf_counter() - start_time:.2f}秒")
            settings.save()
    except Exception as e:
        logger.error(f"截图进程出错: {e}")
    finally:
        if shared_mem:
            shared_mem.close()
            shared_mem.unlink()
