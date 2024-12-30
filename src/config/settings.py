import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class Settings:
    """配置管理类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "window": {
            "width": 600,
            "height": 600,
            "opacity": 0.8,
            "always_on_top": True
        },
        "recognition": {
            "threshold": 0.9,
            "interval": 0.01,
            "max_retries": 3
        },
        "label": {
            "font_size": 14,
            "font_family": "Microsoft YaHei",
            "background_color": "rgba(0, 0, 0, 150)",
            "text_color": "white",
            "opacity": 0.8
        },
        "paths": {
            "templates": "resources/templates",
            "config": "resources/config",
            "logs": "logs"
        }
    }

    def __init__(self):
        """初始化配置管理器"""
        self.config_path = self._get_config_path()
        self.config = self._load_config()
        self._ensure_directories()

    def _get_base_path(self) -> Path:
        """获取基础路径
        在开发环境下返回项目根目录
        在打包环境下返回可执行文件所在目录
        """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的环境
            return Path(sys._MEIPASS)
        else:
            # 开发环境
            return Path(__file__).parent.parent.parent

    def _ensure_directories(self):
        """确保必要的目录存在"""
        base_path = self._get_base_path()
        for path_name, relative_path in self.config['paths'].items():
            # 构建路径
            path = base_path / relative_path
            path.mkdir(parents=True, exist_ok=True)

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        return self._get_base_path() / "resources/config/config.json"

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    return self._merge_configs(self.DEFAULT_CONFIG, user_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return self.DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """递归合并配置字典"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result

    def save(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            section: 配置节名称
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default

    def set(self, section: str, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            section: 配置节名称
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
            return True
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False

    def get_path(self, path_name: str) -> Optional[Path]:
        """获取特定路径的绝对路径"""
        try:
            relative_path = self.get('paths', path_name)
            if not relative_path:
                return None

            base_path = self._get_base_path()
            absolute_path = base_path / relative_path
            absolute_path.mkdir(parents=True, exist_ok=True)
            
            return absolute_path
            
        except Exception as e:
            print(f"获取路径失败 {path_name}: {e}")
            return None

    def get_template_path(self) -> Optional[Path]:
        """获取模板路径
        
        Args:
            screen_resolution: 屏幕分辨率
            
        Returns:
            Optional[Path]: 模板路径
        """
        templates_path = self.get_path('templates')
        if templates_path:
            return templates_path / f"{self.get('screen', 'width')}{self.get('screen', 'height')}"
        return None

    def get_window_settings(self) -> Dict[str, Any]:
        """获取窗口设置"""
        return self.config.get('window', self.DEFAULT_CONFIG['window'])

    def get_recognition_settings(self) -> Dict[str, Any]:
        """获取识别设置"""
        return self.config.get('recognition', self.DEFAULT_CONFIG['recognition'])

    def get_label_settings(self) -> Dict[str, Any]:
        """获取标签设置"""
        return self.config.get('label', self.DEFAULT_CONFIG['label'])

    def get_screen_settings(self) -> Dict[str, Any]:
        """获取屏幕设置"""
        return self.config.get('screen', self.DEFAULT_CONFIG['screen'])
    

    def reset_section(self, section: str) -> bool:
        """重置指定配置节
        
        Args:
            section: 配置节名称
            
        Returns:
            bool: 是否重置成功
        """
        try:
            if section in self.DEFAULT_CONFIG:
                self.config[section] = self.DEFAULT_CONFIG[section].copy()
                return True
            return False
        except Exception as e:
            print(f"重置配置节失败: {e}")
            return False

    def reset_all(self) -> bool:
        """重置所有配置"""
        try:
            self.config = self.DEFAULT_CONFIG.copy()
            return self.save()
        except Exception as e:
            print(f"重置所有配置失败: {e}")
            return False 