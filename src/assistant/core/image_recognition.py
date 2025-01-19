import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple, List

import cv2
import numpy as np

from ..utils.logger_factory import LoggerFactory
from ...config.settings import ConfigManager


class ImageRecognition:
    """图像识别类，用于处理屏幕捕获和图像识别"""

    def __init__(self):
        """
        初始化图像识别类
        """
        self.logger = LoggerFactory.get_logger()
        self.template_cache = {}
        self.frame_cache = None

    @staticmethod
    def img_read(image_path: str) -> Optional[np.ndarray]:
        """
        读取图像文件
        Args:
            image_path: 图像文件路径
        Returns:
            Optional[numpy.ndarray]: BGR格式的图像数组，失败返回None
        """
        logger = LoggerFactory.get_logger()
        try:
            if not image_path or not os.path.exists(image_path):
                return None
                
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图像: {image_path}")
                return None
                
            return img
            
        except Exception as e:
            logger.error(f"读取图像失败 {image_path}: {e}")
            return None

    @staticmethod
    def identify_from_templates(
        frame: np.ndarray,
        templates: Dict[str, np.ndarray]
    ) -> str:
        """
        从模板中识别图像
        Args:
            frame: 待识别的图像
            templates: 模板字典 {名称: 模板图像}
        Returns:
            str: 识别结果名称，未识别返回'none'
        """
        settings = ConfigManager('config')
        logger = LoggerFactory.get_logger()
        # 输入验证
        if frame is None or frame.size == 0 or not templates:
            return 'none'

        recognition = settings.get('recognition')
        threshold = recognition['threshold']
        max_val = 0
        result_name = 'none'
        try:
            # 遍历所有模板进行匹配
            for name, template in templates.items():
                if template is None or template.size == 0:
                    continue
                # 模板匹配
                result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                _, val, _, _ = cv2.minMaxLoc(result)
                # 更新最佳匹配
                if val > max_val:
                    max_val = val
                    result_name = name

            return result_name if max_val >= threshold else 'none'

        except Exception as e:
            logger.error(f"图像匹配失败: {e}")
            return 'none'

    def capture_screen(self) -> np.ndarray:
        """
        捕获屏幕
        Returns:
            numpy.ndarray: BGR格式的图像数组
        """
        try:
            # 从共享内存获取完整帧
            # from .frame_client import FrameClient
            # frame = FrameClient.get_instance().get_frame()
            from ...screen_capture.capture_process import CaptureManager
            frame = CaptureManager.get_instance().get_frame()
            if frame is None:
                return self.frame_cache
            # frame = cv2.cvtColor(frame, cv2.rgb)
            self.frame_cache = frame
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            self.logger.error(f"捕获屏幕失败: {e}")

    def process_region(
        self,
            category: str,
            templates: Dict[str, np.ndarray],
            region: List[int],
            frame: np.ndarray = None
    ) -> Tuple[str, str]:
        """
        处理特定区域的图像识别
        Args:
            category: 类别名称
            templates: 模板字典
            region: 截取位置 [x, y, w, h]
            frame: 输入帧，默认为None
        Returns:
            Tuple[str, str]: (类别, 识别结果)
        """
        try:
            if frame is None:
                frame = self.capture_screen()
                if frame is None:
                    return category, 'none'

            x, y, w, h = region
            cropped = frame[y:y + h, x:x + w]
            if cropped is None or cropped.size == 0:
                return category, 'none'

            result = self.identify_from_templates(cropped, templates)

            return category, result
            
        except Exception as e:
            self.logger.error(f"处理区域失败: {e}")
            return category, 'none'

    def batch_process_regions(
        self,
        regions: Dict[str, List[int]],
        templates: Dict[str, Dict[str, np.ndarray]],
        exclude_categories: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """批量处理多个区域的图像识别"""
        import cProfile
        self.profiler = cProfile.Profile()
        self.profiler.enable()  # 开始性能分析

        results = {}
        exclude_categories = exclude_categories or []

        try:
            frame = self.capture_screen()
            if frame is None:
                return results
            # if frame is not None and frame.size > 0:
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_category = {
                    executor.submit(
                        self.process_region,
                        category,
                        templates.get(category.split('_')[0], {}),
                        region,
                        frame
                    ): category
                    for category, region in regions.items()
                    if category not in exclude_categories
                }

                for future in as_completed(future_to_category):
                    category = future_to_category[future]
                    try:
                        _, result = future.result()
                        results[category] = result
                    except Exception as e:
                        self.logger.error(f"处理区域 {category} 失败: {e}")
                        results[category] = 'none'
                            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")

        self.profiler.disable()  # 停止性能分析
        self.profiler.print_stats(sort='cumtime')  # 打印性能分析结果
        self.profiler.dump_stats('profile_stats.prof')  # 保存性能分析结果

        return results