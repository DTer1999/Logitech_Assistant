import json
import time
from dataclasses import dataclass
from functools import wraps
from threading import Thread, Lock, Event
from typing import Dict

import keyboard
from pynput import mouse

from ..core.image_recognition import ImageRecognition
from ..utils.constants import translate_name, get_attribute_keys
from ..utils.logger_factory import LoggerFactory
from ...config.settings import ConfigManager


@dataclass
class GameState:
    """游戏状态数据类"""

    def __init__(self):
        self.scope_zoom: float = 1.0
        self.right_button_pressed: bool = False
        self.current_weapon: str = "rifle"
        self.current_scope: str = "none"
        self.is_recognizing: bool = False
        self.off_on_flag: bool = True
        self.results: Dict = {}
        self._lock = Lock()
        self._stop_event = Event()  # 添加事件用于线程同步

    def set_off_on_flag(self, value: bool) -> None:
        """线程安全地设置 off_on_flag"""
        with self._lock:
            self.off_on_flag = value
            if not value:
                self._stop_event.set()  # 设置停止事件
            else:
                self._stop_event.clear()  # 清除停止事件

    def get_off_on_flag(self) -> bool:
        """线程安全地获取 off_on_flag"""
        with self._lock:
            return self.off_on_flag


def monitor_results(method):
    """装饰器：监控 self.results 的变化并在变化时调用 write_files"""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # 保存修改前的状态
        old_results = self.state.results.copy() if hasattr(self.state, 'results') else {}

        # 执行原始方法
        result = method(self, *args, **kwargs)

        # 检查结果是否发生变化
        if hasattr(self.state, 'results'):
            # 开镜的时候才保存数据
            if not self.state.right_button_pressed:
                self.write_files({})
            elif self.state.results != old_results:
                self.write_files(self.state.results)
        self.display_results()
        return result

    return wrapper

class PubgCore():
    """PUBG游戏核心类"""

    # 常量定义
    MAX_ZOOM = 1.6
    MIN_ZOOM = 1.0
    ZOOM_STEP = 0.06

    def __init__(self):
        """初始化"""
        self.settings = ConfigManager("config")
        self.logger = LoggerFactory.get_logger()
        self.file_path = (self.settings.get_path('templates') /
                          (str(self.settings.get("screen", "width"))
                           + str(self.settings.get("screen", "height"))))

        # 确保在创建其他属性之前初始化 image_recognition
        self.image_recognition = ImageRecognition()
        self.state = GameState()
        self.state.off_on_flag = True  # 初始化时设置为True
        self.mouse_listener = None
        self.pose_thread = None
        
        # 加载配置和区域
        self.templates = self._load_templates()
        self.config = self._load_config()
        self.regions = self.config['regions']
        self.shoot_pixel = self.config['shoot_pixel']
        

    def _load_templates(self) -> Dict:
        """加载所有模板图片"""
        self.logger.info("加载模板图片")
        template_dirs = {
            "poses": f"{self.file_path}/weapon_templates/poses/",
            "weapons": f"{self.file_path}/weapon_templates/weapons/",
            "muzzles": f"{self.file_path}/weapon_templates/muzzles/",
            "grips": f"{self.file_path}/weapon_templates/grips/",
            "scopes": f"{self.file_path}/weapon_templates/scopes/",
            "stocks": f"{self.file_path}/weapon_templates/stocks/",
            "bag": f"{self.file_path}/weapon_templates/bag/",
            "car": f"{self.file_path}/weapon_templates/car/",
            "shoot": f"{self.file_path}/weapon_templates/shoot/"
        }

        templates = {}
        for category, path in template_dirs.items():
            templates[category] = {}
            names = get_attribute_keys(category)
            for template_name in names:
                template_path = f"{path}{template_name}.png"
                # 使用实例方法而不是静态方法
                template = self.image_recognition.img_read(template_path)
                if template is not None:
                    templates[category][template_name] = template
        self.logger.info("模板图片加载完成")
        return templates

    def _load_config(self) -> Dict:
        """加载区域配置"""
        self.logger.info("加载识别配置文件")
        config_path = f"{self.file_path}/config.json"
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        self.logger.info("识别配置文件加载完成")
        return config_data

    def on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """处理鼠标滚轮事件"""
        if self.state.right_button_pressed:
            if self.state.current_scope in ["x6", "x8"]:
                if dy > 0:  # 放大
                    self.state.scope_zoom = min(self.state.scope_zoom + self.ZOOM_STEP, self.MAX_ZOOM)
                elif dy < 0:  # 缩小
                    self.state.scope_zoom = max(self.state.scope_zoom - self.ZOOM_STEP, self.MIN_ZOOM)
                self.state.results["scope_zoom"] = round(self.state.scope_zoom, 2)

    def on_click(self, x: int, y: int, button, pressed: bool) -> None:
        """处理鼠标点击事件"""
        if button == mouse.Button.right:
            self.identify_shoot()

    @monitor_results
    def identify_shoot(self) -> None:
        """识别开火状态"""
        if not hasattr(self, 'shoot_pixel'):
            return
        
        try:
            shoot_category, shoot_result = self.image_recognition.process_region(
                "shoot",
                self.templates["shoot"],
                [
                    self.shoot_pixel['x'], 
                    self.shoot_pixel['y'],
                    26,
                    15
                ]
            )
            self.state.right_button_pressed = (shoot_result == 'shoot')
            self.state.results[shoot_category] = shoot_result
        except Exception as e:
            print(f"识别开火状态失败: {e}")
            self.state.right_button_pressed = False

    @monitor_results
    def identify_pose(self, region: list) -> None:
        """持续识别姿势"""
        try:
            while self.state.get_off_on_flag():
                pose_category, pose_result = self.image_recognition.process_region(
                    "poses",
                    self.templates["poses"],
                    region
                )
                self.state.results[pose_category] = pose_result
                time.sleep(1)
        except Exception as e:
            self.logger.error(f"姿势识别线程异常: {e}")
        finally:
            self.logger.info("姿势识别线程正常退出")

    def start(self) -> None:
        self.state.set_off_on_flag(True)  # 使用setter方法

        # 启动鼠标监听
        self.mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.mouse_listener.start()
        self.logger.info("鼠标监听启动")

        # 启动姿势识别线程
        self.pose_thread = Thread(target=self.identify_pose, args=(self.regions["poses"],))
        self.pose_thread.daemon = True
        self.pose_thread.start()
        self.logger.info("姿势识别线程启动")

        # 启动主循环
        self.init_pubg()

    def stop(self) -> None:
        try:
            # 0. 初始进度
            self.logger.close_progress(0)

            # 1. 设置停止标志
            self.state.set_off_on_flag(False)
            self.logger.info("停止标志已设置")
            self.logger.close_progress(1)
            
            # 2. 停止鼠标监听
            if hasattr(self, 'mouse_listener') and self.mouse_listener:
                self.mouse_listener.stop()
                self.logger.info("鼠标监听已停止")
            self.logger.close_progress(2)
            
            # 3. 等待姿势识别线程关闭
            if hasattr(self, 'pose_thread') and self.pose_thread and self.pose_thread.is_alive():
                self.logger.info("等待姿势识别线程关闭...")
                self.pose_thread.join(timeout=3.0)  # 等待最多3秒
                if self.pose_thread.is_alive():
                    self.pose_thread.terminate()
                    self.logger.warning("姿势识别线程未能正常关闭")
                self.pose_thread = None
                self.logger.info("姿势识别线程已停止")
            self.logger.close_progress(3)
            
            # 4. 清理键盘监听
            keyboard.unhook_all()
            self.logger.info("键盘监听已停止")
            self.logger.close_progress(4)

            # 5. 重置状态
            self.state = GameState()
            self.logger.info("状态已重置")
            self.logger.close_progress(5)

            # 6. 最终清理
            self.logger.info("停止过程完成")
            self.logger.close_progress(6)

            # 7. 完成
            self.logger.close_progress(7)
            
        except Exception as e:
            self.logger.error(f"停止功能失败: {e}")
            # 确保进度条能够关闭
            self.logger.close_progress(7)

    def write_files(self, results: Dict) -> None:
        """将识别结果写入文件"""
        temp = self.settings.get_path('temp')
        # 写入 weapon.lua
        with open(f"{temp}/weapon.lua", "w", encoding="utf-8") as f:
            f.write(f'weapon_name = "{results.get("weapons_name_" + self.state.current_weapon, "")}"\n')
            f.write(f'muzzles = "{results.get("muzzles_" + self.state.current_weapon, "")}"\n')
            f.write(f'grips = "{results.get("grips_" + self.state.current_weapon, "")}"\n')
            f.write(f'scopes = "{results.get("scopes_" + self.state.current_weapon, "")}"\n')
            f.write(f'stocks = "{results.get("stocks_" + self.state.current_weapon, "")}"\n')
            f.write(f'poses = "{results.get("poses", "")}"\n')
            f.write(f'scope_zoom = "{results.get("scope_zoom", "1")}"\n')
            f.write(f'bag = "{results.get("bag", "none")}"\n')
            f.write(f'car = "{results.get("car", "none")}"\n')
            f.write(f'shoot = "{results.get("shoot", "none")}"\n')

        # 写入 results.json
        results_json = {
            "weapon_name": translate_name(results.get("weapons_name_" + self.state.current_weapon, "")),
            "muzzles": translate_name(results.get("muzzles_" + self.state.current_weapon, "")),
            "grips": translate_name(results.get("grips_" + self.state.current_weapon, "")),
            "scopes": translate_name(results.get("scopes_" + self.state.current_weapon, "")),
            "stocks": translate_name(results.get("stocks_" + self.state.current_weapon, "")),
            "poses": translate_name(results.get("poses", "")),
            "bag": translate_name(results.get("bag", "none")),
            "car": translate_name(results.get("car", "none")),
            "shoot": translate_name(results.get("shoot", "none"))
        }

        with open(f"{temp}/results.json", 'w', encoding='utf-8') as f:
            json.dump(results_json, f, ensure_ascii=False)

    def init_pubg(self) -> None:
        """主识别循环"""
        # 设置键盘监听
        keyboard.on_press_key('tab', self.toggle_recognition)
        keyboard.on_press_key('esc', self.close_recognition)

        while self.state.get_off_on_flag():
            if keyboard.is_pressed('1'):
                if self.state.current_weapon != "rifle":
                    self.state.current_weapon = "rifle"
                    self.logger.info("切换到枪械1")
                    self.handle_weapon_change()
                    self.display_results()
            elif keyboard.is_pressed('2'):
                if self.state.current_weapon != "sniper":
                    self.state.current_weapon = "sniper"
                    self.logger.info("切换到枪械2")
                    self.handle_weapon_change()
                    self.display_results()

            if self.state.is_recognizing:
                self.logger.info("正在识别中")
                self.process_recognition()
                self.logger.info("识别完成")

            if self.state.right_button_pressed:
                self.logger.info("右键开镜，正在压枪中")
                time.sleep(1)

            time.sleep(0.01)

        # 循环结束后清理资源
        keyboard.unhook_all()
        self.logger.info("主线程结束，关闭自动识别")
        self.logger.close_progress(6)

    @monitor_results
    def process_recognition(self) -> None:
        """处理识别逻辑"""
        extends = ['poses', 'bag', 'shoot']
        self.state.results = self.image_recognition.batch_process_regions(self.regions, self.templates, extends)
        self.state.current_scope = self.state.results.get('scopes_' + self.state.current_weapon,
                                                          self.state.current_scope)
        self.state.is_recognizing = False

    @monitor_results
    def toggle_recognition(self, event) -> None:
        """切换识别状态"""
        time.sleep(0.1)
        bag_category, bag_result = self.image_recognition.process_region("bag", self.templates["bag"],
                                                                         self.regions['bag'])
        self.state.results[bag_category] = bag_result
        self.state.is_recognizing = (bag_result == 'bag')

    @monitor_results
    def close_recognition(self, event) -> None:
        """关闭识别"""
        self.state.is_recognizing = False
        self.state.results = {}

    def handle_weapon_change(self) -> None:
        """处理武器切换"""
        if self.state.current_scope not in ["x6", "x8"]:
            self.state.scope_zoom = 1.0
        self.state.results["scope_zoom"] = self.state.scope_zoom

    def display_results(self) -> None:
        """显示识别结果"""
        if not self.logger:
            return

        # 翻译 results 中的所有字段
        translated_results = {
            key: translate_name(value) if value != "none" else "无"
            for key, value in self.state.results.items()
        }

        # 拼接显示文本
        display_text = (
            f'{translated_results.get("weapons_name_" + self.state.current_weapon, "无")} '
            f'{translated_results.get("muzzles_" + self.state.current_weapon, "无")} '
            f'{translated_results.get("grips_" + self.state.current_weapon, "无")} '
            f'{translated_results.get("scopes_" + self.state.current_weapon, "无")} '
            f'{translated_results.get("stocks_" + self.state.current_weapon, "无")}'
        )

        self.logger.info(f"识别结果: {self.state.results}")
        self.logger.info(f"当前武器: {self.state.current_weapon}")

        # 使用新的单信号方式，将UI所需内容打包到一个字典里
        payload = {
            "label": display_text,
            "results": translated_results,
            "current_weapon": self.state.current_weapon
        }
        self.logger.update_ui(payload) 