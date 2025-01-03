import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple, List

import cv2
import numpy as np

from .capture.capture_manager import CaptureManager
from ..config.settings import Settings
from ..utils.logger_factory import LoggerFactory


class ImageRecognition:
    """图像识别类，用于处理屏幕捕获和图像识别"""

    def __init__(self):
        """初始化截图工具"""
        self.settings = Settings.get_instance()
        self.logger = LoggerFactory.get_logger()
        self.capture_manager = CaptureManager()
        # 添加缓存相关属性
        self._frame_cache = None
        self._last_capture_time = 0
        self._cache_duration = self.settings.get('capture', 'cache_duration', 1.0)  # 默认1秒
    

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
        settings = Settings.get_instance()
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

                # 确保frame和template具有相同的通道数
                if len(frame.shape) != len(template.shape):
                    if len(frame.shape) == 3:
                        template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
                    else:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 确保尺寸合适
                if template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
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
        """捕获屏幕，使用缓存机制"""
        current_time = time.time()

        # 如果缓存存在且未过期，直接返回缓存
        if (self._frame_cache is not None and
                current_time - self._last_capture_time < self._cache_duration):
            return self._frame_cache.copy()  # 返回副本避免修改缓存

        try:
            method = self.settings.get('capture', 'method', 'win32')
            capture = self.capture_manager.get_capture(method)
            # 更新缓存和时间戳
            self._frame_cache = capture.capture()
            self._last_capture_time = current_time
            return self._frame_cache.copy()
        except Exception as e:
            self.logger.error(f"捕获屏幕失败: {e}")
            self._frame_cache = None  # 清除可能的无效缓存
    
    def process_region(
        self,
            category: str,
        templates: Dict[str, np.ndarray],
            region: list
    ) -> Tuple[str, str]:
        """
        处理特定区域的图像识别
        Args:
            templates: 模板字典
            category: 类别名称
            region: 截取位置
        Returns:
            Tuple[str, str]: (类别, 识别结果)
        """
        try:
            frame = self.capture_screen()
            cropped = frame[region[1]:region[1] + region[3], region[0]:region[0] + region[2]]
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
        results = {}
        exclude_categories = exclude_categories or []

        try:
            # 使用缓存机制获取frame
            frame = self.capture_screen()
            if frame is not None and frame.size > 0:
                with ThreadPoolExecutor(max_workers=7) as executor:
                    future_to_category = {
                        executor.submit(
                            self._process_single_region,
                            frame,
                            category,
                            region,
                            templates.get(category.split('_')[0], {})
                        ): category
                        for category, region in regions.items()
                        if category not in exclude_categories
                    }

                    for future in as_completed(future_to_category):
                        category = future_to_category[future]
                        try:
                            result = future.result()
                            results[category] = result
                        except Exception as e:
                            self.logger.error(f"处理区域 {category} 失败: {e}")
                            results[category] = 'none'
                            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")

        return results

    def _process_single_region(
            self,
            frame: np.ndarray,
            category: str,
            region: List[int],
            templates: Dict[str, np.ndarray]
    ) -> str:
        """处理单个区域的图像识别"""
        try:
            # 截取区域
            x, y, w, h = region
            cropped = frame[y:y + h, x:x + w]
            # 进行识别
            return self.identify_from_templates(cropped, templates)
        except Exception as e:
            self.logger.error(f"处理区域失败 {category}: {e}")
            return 'none'

    def cleanup(self):
        """清理资源"""
        self._frame_cache = None
        self.capture_manager.cleanup()
