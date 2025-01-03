import glob
import os
import time
from typing import List

import cv2
import keyboard
import numpy as np

from .base_capture import BaseCapture


class NvidiaCapture(BaseCapture):
    def __init__(self):
        super().__init__()
        self.method = 'nvidia'

    def initialize(self) -> bool:
        try:
            # 检查 NVIDIA GeForce Experience 是否安装
            nvidia_path = os.path.expandvars(r'%ProgramFiles%\NVIDIA Corporation\NVIDIA app')
            if not os.path.exists(nvidia_path):
                self.logger.error("未找到 NVIDIA GeForce Experience")
                return False

            # 获取默认的截图保存路径
            self.screenshots_path = os.path.expandvars(r'%USERPROFILE%\Videos\NVIDIA\Desktop')
            self.logger.info("NVIDIA截图初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"NVIDIA截图初始化失败: {e}")
            return False

    def capture(self, region: List[int]) -> np.ndarray:
        try:
            # 记录截图前的文件列表
            before_files = set(glob.glob(os.path.join(self.screenshots_path, "*.png")))

            # 模拟 Alt+F1 (NVIDIA 默认截图快捷键)
            keyboard.press('alt')
            keyboard.press('f1')
            keyboard.release('f1')
            keyboard.release('alt')

            # 等待截图文件生成
            max_wait = 5  # 最多等待2秒
            start_time = time.time()
            new_file = None

            while time.time() - start_time < max_wait:
                current_files = set(glob.glob(os.path.join(self.screenshots_path, "*.png")))
                new_files = current_files - before_files

                if new_files:
                    new_file = max(new_files, key=os.path.getctime)
                    break

                time.sleep(0.1)

            if not new_file:
                self.logger.error("未找到新生成的截图文件")

            # 读取并裁剪图片
            image = cv2.imread(new_file)
            x, y, w, h = region
            cropped = image[y:y + h, x:x + w]

            # 删除原始截图文件
            os.remove(new_file)

            return cropped

        except Exception as e:
            self.logger.error(f"NVIDIA截图失败: {e}")

    def cleanup(self):
        pass
