from typing import Dict, Optional, Tuple, List
import numpy as np
import cv2
import mss
import os
from ..config.settings import Settings
from ..utils.logger import Logger

class ImageRecognition:
    """图像识别类，用于处理屏幕捕获和图像识别"""
    
    def __init__(self, settings: Settings, logger: Logger):
        """初始化截图工具"""
        self.settings = settings
        self.logger = logger
        self.sct = mss.mss()
    
    def __del__(self):
        """清理资源"""
        try:
            self.sct.close()
        except Exception as e:
            self.logger.error(f"清理截图资源失败: {e}")

    def capture_screen(self, region: List[int]) -> np.ndarray:
        """
        捕获屏幕指定区域
        Args:
            region: [x, y, width, height] 格式的区域坐标
        Returns:
            numpy.ndarray: BGR格式的图像数组，失败返回空数组
        """
        try:
            with mss.mss() as sct:
                monitor = {
                    "left": region[0],
                    "top": region[1],
                    "width": region[2],
                    "height": region[3]
                }
                screenshot = np.array(sct.grab(monitor))
                return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return np.array([])

    def img_read(self, image_path: str) -> Optional[np.ndarray]:
        """
        读取图像文件
        Args:
            image_path: 图像文件路径
        Returns:
            Optional[numpy.ndarray]: BGR格式的图像数组，失败返回None
        """
        try:
            if not image_path or not os.path.exists(image_path):
                return None
                
            img = cv2.imread(image_path)
            if img is None:
                self.logger.error(f"无法读取图像: {image_path}")
                return None
                
            return img
            
        except Exception as e:
            self.logger.error(f"读取图像失败 {image_path}: {e}")
            return None
    def identify_from_templates(
        self,
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
        # 输入验证
        if frame is None or frame.size == 0 or not templates:
            return 'none'

        recognition = self.settings.get_recognition_settings()
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
            self.logger.error(f"图像匹配失败: {e}")
            return 'none'

    def process_region(
        self,
        frame: np.ndarray,
        templates: Dict[str, np.ndarray],
        category: str
    ) -> Tuple[str, str]:
        """
        处理特定区域的图像识别
        Args:
            frame: 图像帧
            templates: 模板字典
            category: 类别名称
        Returns:
            Tuple[str, str]: (类别, 识别结果)
        """
        try:
            if frame is None or frame.size == 0:
                return category, 'none'
            
            result = self.identify_from_templates(frame, templates)
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
        """
        批量处理多个区域的图像识别
        Args:
            regions: 区域字典 {类别: [x, y, width, height]}
            templates: 模板字典 {类别: {名称: 模板图像}}
            exclude_categories: 要排除的类别列表
        Returns:
            Dict[str, str]: {类别: 识别结果}
        """
        results = {}
        exclude_categories = exclude_categories or []

        try:
            for category, region in regions.items():
                if category in exclude_categories:
                    continue

                frame = self.capture_screen(region)
                if frame is not None and frame.size > 0:
                    category_templates = templates.get(category.split('_')[0], {})
                    _, result = self.process_region(frame, category_templates, category)
                    results[category] = result
                else:
                    results[category] = 'none'

        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")

        return results