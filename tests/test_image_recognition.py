import pytest
import numpy as np
import cv2
from src.core.image_recognition import ImageRecognition

class TestImageRecognition:
    """图像识别测试类"""

    @pytest.fixture
    def recognition(self):
        """创建图像识别实例"""
        return ImageRecognition()

    @pytest.fixture
    def sample_image(self):
        """创建示例图像"""
        # 使用 BGR 格式创建图像
        return np.zeros((100, 100, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_templates(self):
        """创建示例模板"""
        return {
            "template1": np.zeros((20, 20, 3), dtype=np.uint8),
            "template2": np.ones((20, 20, 3), dtype=np.uint8) * 255  # 使用255而不是1
        }

    def test_identify_from_templates_empty_frame(self, recognition, sample_templates):
        """测试空图像帧的识别"""
        # 测试 None 和空数组两种情况
        assert recognition.identify_from_templates(None, sample_templates) == 'none'
        assert recognition.identify_from_templates(np.array([]), sample_templates) == 'none'

    def test_identify_from_templates_empty_templates(self, recognition, sample_image):
        """测试空模板的识别"""
        assert recognition.identify_from_templates(sample_image, {}) == 'none'
        assert recognition.identify_from_templates(sample_image, None) == 'none'

    def test_identify_from_templates_invalid_template(self, recognition, sample_image):
        """测试无效模板的识别"""
        templates = {"invalid": None, "empty": np.array([])}
        assert recognition.identify_from_templates(sample_image, templates) == 'none'

    def test_identify_from_templates_match(self, recognition):
        """测试模板匹配"""
        # 创建一个具有明显特征的图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[40:60, 40:60] = [255, 255, 255]  # BGR 白色方块

        # 创建完全匹配的模板
        template = np.zeros((20, 20, 3), dtype=np.uint8)
        template[:, :] = [255, 255, 255]  # BGR 白色

        templates = {"white_square": template}
        
        # 确保阈值设置合适
        recognition.THRESHOLD = 0.8  # 可以根据需要调整
        result = recognition.identify_from_templates(image, templates)
        assert result == 'white_square'

    def test_process_region(self, recognition):
        """测试区域处理"""
        # 创建真实的测试数据
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[30:50, 30:50] = [255, 255, 255]  # 添加特征

        template = np.zeros((20, 20, 3), dtype=np.uint8)
        template[:, :] = [255, 255, 255]

        templates = {"test": template}
        category = "test_category"

        result_category, result_name = recognition.process_region(
            image,
            templates,
            category
        )
        
        assert result_category == category
        assert isinstance(result_name, str)
        assert result_name in ['test', 'none']

    def test_batch_process_regions(self, recognition, monkeypatch):
        """测试批量区域处理"""
        # Mock capture_screen 方法
        def mock_capture_screen(region):
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        monkeypatch.setattr(ImageRecognition, 'capture_screen', mock_capture_screen)

        # 创建测试数据
        regions = {
            "region1": [0, 0, 100, 100],
            "region2": [100, 100, 100, 100]
        }
        templates = {
            "region": {  # 修改为正确的类别名
                "template1": np.zeros((20, 20, 3), dtype=np.uint8)
            }
        }
        exclude = ["region2"]

        results = recognition.batch_process_regions(regions, templates, exclude)
        
        assert isinstance(results, dict)
        assert "region1" in results
        assert "region2" not in results
        assert isinstance(results["region1"], str)

    @pytest.mark.parametrize("image_shape,template_shape", [
        ((100, 100, 3), (20, 20, 3)),    # BGR 图像
        ((100, 100, 1), (20, 20, 1)),    # 灰度图像
        ((100, 100, 3), (20, 20, 1)),    # BGR 和灰度
        ((100, 100, 1), (20, 20, 3))     # 灰度和 BGR
    ])
    def test_different_image_types(self, recognition, image_shape, template_shape):
        """测试不同类型图像的处理"""
        # 创建合适的测试数据
        image = np.zeros(image_shape, dtype=np.uint8)
        if len(image_shape) == 3 and image_shape[2] == 3:
            image[40:60, 40:60] = [255, 255, 255]
        else:
            image[40:60, 40:60] = 255

        template = np.zeros(template_shape, dtype=np.uint8)
        if len(template_shape) == 3 and template_shape[2] == 3:
            template[:, :] = [255, 255, 255]
        else:
            template[:, :] = 255

        templates = {"test": template}

        # 执行测试
        result = recognition.identify_from_templates(image, templates)
        assert isinstance(result, str)
        assert result in ['test', 'none']

    def test_img_read(self, recognition, tmp_path):
        """测试图像读取"""
        # 创建临时测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[40:60, 40:60] = [255, 255, 255]
        
        # 保存测试图像
        test_file = tmp_path / "test.png"
        cv2.imwrite(str(test_file), test_image)
        
        # 测试正常读取
        result = recognition.img_read(str(test_file))
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        
        # 测试读取不存在的文件
        assert recognition.img_read("nonexistent.png") is None 