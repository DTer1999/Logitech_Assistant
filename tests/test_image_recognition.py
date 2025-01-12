import time
import unittest
from pathlib import Path

import cv2
import numpy as np
from src.core.image_recognition import ImageRecognition
from src.utils.logger_factory import LoggerFactory

from src.config.settings import Settings


class TestImageRecognition(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.settings = Settings.get_instance()
        self.image_recognition = ImageRecognition()
        self.test_data_dir = Path(__file__).parent / 'test_data'
        self.test_data_dir.mkdir(exist_ok=True)
        self.logger = LoggerFactory.get_logger()

        # 加载实际的模板图像
        self.templates = {}
        self.load_templates()

    def load_templates(self):
        """从实际目录加载模板图像"""
        template_dir = Path('E:/pubg/Logitech_Assistant/temp/assets/Attachment')
        if not template_dir.exists():
            self.skipTest("模板目录不存在")

        # 遍历所有png文件
        for img_path in template_dir.glob('*.png'):
            template_name = img_path.stem  # 获取文件名（不含扩展名）
            template = cv2.imread(str(img_path))
            if template is not None:
                self.templates[template_name] = template
                # 保存一份到测试目录（用于调试）
                cv2.imwrite(str(self.test_data_dir / f'{template_name}.png'), template)

        if not self.templates:
            self.skipTest("没有找到模板图像")

    def test_exact_match(self):
        """测试完全匹配的情况"""
        for template_name, template in self.templates.items():
            with self.subTest(template=template_name):
                frame = template.copy()
                result = self.image_recognition.identify_from_templates(frame, self.templates)
                self.assertEqual(result, template_name)

    def test_no_match(self):
        """测试无匹配的情况"""
        # 创建一个完全不同的图像（全黑）
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.image_recognition.identify_from_templates(frame, self.templates)
        self.assertEqual(result, 'none')

    def test_partial_match(self):
        """测试部分匹配的情况"""
        for template_name, template in list(self.templates.items())[:3]:  # 只测试前3个模板
            with self.subTest(template=template_name):
                frame = template.copy()
                # 添加一些噪声
                noise = np.random.normal(0, 25, frame.shape).astype(np.uint8)
                frame = cv2.add(frame, noise)
                # 保存用于调试
                cv2.imwrite(str(self.test_data_dir / f'{template_name}_noise.png'), frame)

                result = self.image_recognition.identify_from_templates(frame, self.templates)
                self.assertEqual(result, template_name)

    def test_empty_inputs(self):
        """测试空输入的情况"""
        # 测试空frame
        result = self.image_recognition.identify_from_templates(None, self.templates)
        self.assertEqual(result, 'none')

        # 测试空templates
        if self.templates:
            frame = next(iter(self.templates.values())).copy()
            result = self.image_recognition.identify_from_templates(frame, {})
            self.assertEqual(result, 'none')

    def test_different_sizes(self):
        """测试不同尺寸的情况"""
        if not self.templates:
            self.skipTest("没有模板可供测试")

        template_name = next(iter(self.templates.keys()))
        template = self.templates[template_name]

        # 创建一个更大的图像
        h, w = template.shape[:2]
        frame = np.ones((h * 2, w * 2, 3), dtype=np.uint8) * 255

        # 在中间放置模板
        y, x = h // 2, w // 2
        frame[y:y + h, x:x + w] = template

        # 保存用于调试
        cv2.imwrite(str(self.test_data_dir / f'{template_name}_larger.png'), frame)

        result = self.image_recognition.identify_from_templates(frame, self.templates)
        self.assertEqual(result, template_name)

    def test_capture_screen(self):
        """测试屏幕截图功能"""
        try:
            # 测试不同的截图方法
            capture_methods = ['win32', 'mss', 'nvidia']

            for method in capture_methods:
                with self.subTest(method=method):
                    # 设置当前截图方法
                    self.settings.set('capture', 'method', method)

                    # 执行截图
                    frame = self.image_recognition.capture_screen()

                    if frame is None:
                        self.logger.warning(f"{method} 截图失败")
                        continue

                    # 验证截图结果
                    self.assertIsNotNone(frame)
                    self.assertGreater(frame.shape[0], 0)  # 高度
                    self.assertGreater(frame.shape[1], 0)  # 宽度
                    self.assertEqual(frame.shape[2], 3)  # 通道数

                    # 保存截图用于调试
                    save_path = self.test_data_dir / f'screen_capture_{method}.png'
                    cv2.imwrite(str(save_path), frame)
                    self.logger.info(f"{method} 截图已保存到: {save_path}")

                    # 测试缓存机制
                    cache_duration = self.settings.get('capture', 'cache_duration', 1.0)
                    frame2 = self.image_recognition.capture_screen()

                    # 验证在缓存时间内返回相同的图像
                    np.testing.assert_array_equal(
                        frame, frame2,
                        f"{method} 截图缓存机制失效"
                    )

                    # 等待缓存过期
                    time.sleep(cache_duration + 0.1)

                    # 再次截图，应该得到新的图像
                    frame3 = self.image_recognition.capture_screen()
                    with self.assertRaises(AssertionError):
                        np.testing.assert_array_equal(
                            frame, frame3,
                            f"{method} 截图缓存未更新"
                        )

                    # 保存新截图用于对比
                    cv2.imwrite(
                        str(self.test_data_dir / f'screen_capture_{method}_new.png'),
                        frame3
                    )

        except Exception as e:
            self.logger.error(f"截图测试失败: {e}")
            self.fail(f"截图测试失败: {e}")

    def test_screen_regions_match(self):
        """测试截图区域与模板匹配"""
        try:
            # 读取并放大截图
            frame = cv2.imread('E:/pubg/Logitech_Assistant/tests/picture/region_mss_muzzles_sniper.png')
            if frame is None:
                self.logger.error("无法加载截图")
                return

            # 放大到512x512（与模板图片相同大小）
            frame = cv2.resize(frame, (512, 512), interpolation=cv2.INTER_CUBIC)

            # 参数范围
            block_sizes = [7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45]  # 邻域大小
            c_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]  # 常数差值
            kernel_sizes = [(3, 3), (5, 5), (7, 7), (9, 9)]  # 形态学操作核大小
            iterations = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # 形态学操作迭代次数

            best_overall_score = 0
            best_params = None
            best_frame_binary = None
            best_template = None

            # 只处理指定的模板文件
            template_path = Path(
                'E:/pubg/Logitech_Assistant/temp/assets/Attachment/Item_Attach_Weapon_Muzzle_Compensator_Large_C.png')

            # 读取模板图片（保持alpha通道）
            template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
            if template is None:
                self.logger.error("无法加载模板图片")
                return

            # 创建纯黑背景
            template_binary = np.zeros_like(template[:, :, 0])
            # 将有内容的部分（alpha > 0）设为白色
            if template.shape[2] == 4:
                template_binary[template[:, :, 3] > 0] = 255

            # 提取模板轮廓
            contours, _ = cv2.findContours(template_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            template_contour = np.zeros_like(template_binary)
            cv2.drawContours(template_contour, contours, -1, 255, 1)

            # 参数循环
            for block_size in block_sizes:
                for c in c_values:
                    for kernel_size in kernel_sizes:
                        for iteration in iterations:
                            # 将截图转为灰度图并二值化
                            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            # 使用自适应阈值处理
                            frame_binary = cv2.adaptiveThreshold(
                                frame_gray,
                                255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV,
                                block_size,
                                c
                            )

                            # 形态学操作清理噪点
                            kernel = np.ones(kernel_size, np.uint8)
                            frame_binary = cv2.morphologyEx(frame_binary, cv2.MORPH_OPEN, kernel, iterations=iteration)
                            frame_binary = cv2.morphologyEx(frame_binary, cv2.MORPH_CLOSE, kernel, iterations=iteration)

                            # 提取截图轮廓
                            contours, _ = cv2.findContours(frame_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            frame_contour = np.zeros_like(frame_binary)
                            cv2.drawContours(frame_contour, contours, -1, 255, 1)

                            # 模板匹配
                            result = cv2.matchTemplate(frame_contour, template_contour, cv2.TM_CCOEFF_NORMED)
                            score = result[0][0]

                            if score > best_overall_score:
                                best_overall_score = score
                                best_params = {
                                    'block_size': block_size,
                                    'c': c,
                                    'kernel_size': kernel_size,
                                    'iterations': iteration
                                }
                                best_frame_binary = frame_contour.copy()
                                best_template = template_contour.copy()

                                self.logger.info(f"新的最佳匹配分数: {score:.4f}")
                                self.logger.info(f"参数: {best_params}")

                                # 保存当前最佳结果
                                cv2.imwrite(str(self.test_data_dir / f'frame_contour_score_{score:.4f}.png'),
                                            frame_contour)

            # 输出最终结果
            self.logger.info("=== 最终结果 ===")
            self.logger.info(f"最佳匹配分数: {best_overall_score:.4f}")
            self.logger.info(f"最佳参数: {best_params}")

            # 可视化最佳匹配结果
            if best_frame_binary is not None:
                # 将二值图转换为3通道图像用于可视化
                frame_vis = cv2.cvtColor(best_frame_binary, cv2.COLOR_GRAY2BGR)
                template_vis = cv2.cvtColor(best_template, cv2.COLOR_GRAY2BGR)

                self.visualize_match_result(
                    frame_vis,
                    template_vis,
                    f"best_match_score_{best_overall_score:.4f}"
                )

        except Exception as e:
            self.logger.error(f"测试失败: {e}")

    def tearDown(self):
        """测试后的清理工作"""
        # 可以选择是否保留测试图像
        # import shutil
        # shutil.rmtree(self.test_data_dir)
        pass

    def visualize_match_result(self, frame: np.ndarray, template: np.ndarray, region_name: str):
        """可视化匹配结果"""
        try:
            # 确保两个图像都是3通道的
            if len(frame.shape) == 2:  # 如果是灰度图
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            if len(template.shape) == 2:  # 如果是灰度图
                template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)

            # 创建一个并排显示的图像
            h1, w1 = frame.shape[:2]
            h2, w2 = template.shape[:2]
            vis_h = max(h1, h2)
            vis_w = w1 + w2 + 10  # 10像素的间隔
            vis = np.ones((vis_h, vis_w, 3), dtype=np.uint8) * 255

            # 放置截图区域
            vis[:h1, :w1] = frame
            # 放置模板图像
            vis[:h2, w1 + 10:w1 + 10 + w2] = template

            # 添加标签
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(vis, "Screen", (10, 20), font, 0.5, (0, 0, 0), 1)
            cv2.putText(vis, "Template", (w1 + 20, 20), font, 0.5, (0, 0, 0), 1)

            # 保存结果
            cv2.imwrite(str(self.test_data_dir / f'comparison_{region_name}.png'), vis)

        except Exception as e:
            self.logger.error(f"可视化匹配结果失败: {e}")


if __name__ == '__main__':
    unittest.main()
