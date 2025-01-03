import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


class Settings:
    """全局设置管理类（单例模式）"""

    _instance: Optional['Settings'] = None

    def __new__(cls) -> 'Settings':
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化设置（只在第一次创建实例时执行）"""
        if self._initialized:
            return

        self._initialized = True
        self.config: Dict[str, Any] = {}
        self.load()

    @classmethod
    def get_instance(cls) -> 'Settings':
        """获取Settings实例的类方法"""
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

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
            raise ValueError(f"未知的路径类型: {path_type}")

        # 获取应用根目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境
            base_path = Path(__file__).parent.parent.parent

        path = base_path / paths[path_type]
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

    def load(self) -> None:
        """从YAML文件加载设置"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'resources' / 'config' / 'application.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self.config = yaml_config
            else:
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
        except Exception as e:
            print(f"加载设置失败: {e}")
            raise

    def save(self) -> None:
        """保存设置到YAML文件"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'resources' / 'config' / 'application.yaml'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存设置失败: {e}")
