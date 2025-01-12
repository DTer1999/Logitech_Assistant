import json
import sys
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """全局设置管理类（单例模式）"""

    _instances: Dict[str, 'ConfigManager'] = {}

    def __new__(cls, config_file):
        if config_file not in cls._instances:
            instance = super(ConfigManager, cls).__new__(cls)
            instance.config = instance.load_config(config_file)
            cls._instances[config_file] = instance
        return cls._instances[config_file]

    def __init__(self, config_file: str):
        """初始化设置（只在第一次创建实例时执行）"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True
        # self.config: Dict[str, Any] = {}

    def get_root_path(self) -> Path:
        """获取应用根目录"""
        if getattr(sys, 'frozen', False):
            return Path(sys._MEIPASS)
        return Path(__file__).parent.parent.parent

    def get_path(self, path_type: str, create: bool = True) -> Path:
        """获取指定类型的路径
        
        Args:
            path_type: 路径类型 (logs/config/assets/cache)
            create: 如果为True且路径不存在，则创建文件夹
            
        Returns:
            Path: 根据运行环境返回开发或打包后的路径
            
        Raises:
            ValueError: 当路径类型未知时抛出
        """
        paths = self.config.get('paths', {})
        if path_type not in paths:
            raise ValueError(f"未知的路径类型: {paths}{path_type}")

        # 获取应用根目录
        path = self.get_root_path() / paths[path_type]
        
        if create:
            path.mkdir(parents=True, exist_ok=True)

        return path

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            section: 配置部分名称
            key: 配置项名称，如果为None则返回整个部分
            default: 默认值
        """
        if key is None:
            return self.config.get(section, default)

        section_data = self.config.get(section, {})
        if isinstance(section_data, dict):
            return section_data.get(key, default)
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """设置指定配置项的值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

    def load_config(self, config_file: str):
        """加载配置文件"""
        self.config_file = self.get_root_path() / 'resources' / 'config' / (config_file + '.json')
        if not self.config_file.is_file():
            raise FileNotFoundError(f"配置文件未找到: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self) -> None:
        try:
            config_path = self.config_file
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存设置失败: {e}")
