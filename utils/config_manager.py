"""
配置管理系统
支持JSON、YAML、INI等多种配置文件格式
"""

import json
import os
import configparser
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from PyQt5.QtCore import QSettings


@dataclass
class SimulationConfig:
    """仿真配置"""
    # 基础设置
    window_width: int = 1920
    window_height: int = 1080
    fps_target: int = 60
    auto_save_interval: int = 300  # 秒

    # 地图设置
    default_map_path: str = "Map.db"
    control_zone_path: str = "control_zone.txt"
    zoom_min: float = 0.1
    zoom_max: float = 5.0

    # AGV设置
    agv_default_speed: float = 2.0
    agv_default_size: int = 24
    collision_buffer: int = 25
    battery_capacity: float = 100.0

    # 电量设置
    discharge_rate_moving: float = 0.8
    discharge_rate_idle: float = 0.02
    discharge_rate_carrying: float = 1.2
    charge_rate: float = 8.0
    low_battery_threshold: float = 30.0
    critical_battery_threshold: float = 15.0

    # 订单设置
    default_generation_rate: float = 0.5  # 每分钟
    order_timeout_base: float = 300.0  # 秒
    priority_weights: Dict[str, int] = None

    # 调度设置
    default_strategy: str = "BALANCED"
    assignment_interval: float = 2.0
    max_retry_attempts: int = 3

    # 显示设置
    show_battery_indicators: bool = True
    show_path_arrows: bool = True
    show_control_zones: bool = True
    show_node_ids: bool = True

    # 性能设置
    max_log_lines: int = 1000
    enable_debug_mode: bool = False
    enable_performance_monitoring: bool = False

    def __post_init__(self):
        if self.priority_weights is None:
            self.priority_weights = {
                "LOW": 10,
                "NORMAL": 60,
                "HIGH": 20,
                "URGENT": 8,
                "EMERGENCY": 2
            }


@dataclass
class UIConfig:
    """UI配置"""
    theme: str = "default"
    font_family: str = "Arial"
    font_size: int = 10
    colors: Dict[str, str] = None

    # 控制面板设置
    control_panel_width: int = 400
    show_advanced_controls: bool = True
    auto_refresh_interval: int = 1000

    # 表格设置
    table_row_height: int = 25
    table_alternate_colors: bool = True

    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                "background": "#EBF0F5",
                "agv_default": "#FF8C00",
                "agv_charging": "#0096FF",
                "agv_low_battery": "#FF4444",
                "node_normal": "#C8C8C8",
                "node_pickup": "#4CAF50",
                "node_dropoff": "#F44336",
                "node_charging": "#FFC107",
                "control_zone": "#FFA500",
                "path_normal": "#DCDCDC",
                "path_active": "#64B4FF",
                "path_planned": "#FF6464"
            }


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.ensure_config_dir()

        # 配置文件路径
        self.sim_config_path = os.path.join(config_dir, "simulation.json")
        self.ui_config_path = os.path.join(config_dir, "ui.json")
        self.user_settings_path = os.path.join(config_dir, "user_settings.ini")

        # 配置对象
        self.simulation = SimulationConfig()
        self.ui = UIConfig()
        self.user_settings = QSettings(self.user_settings_path, QSettings.IniFormat)

        # 加载配置
        self.load_all_configs()

    def ensure_config_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            print(f"创建配置目录: {self.config_dir}")

    def load_all_configs(self):
        """加载所有配置"""
        try:
            self.load_simulation_config()
            self.load_ui_config()
            print("配置加载成功")
        except Exception as e:
            print(f"配置加载失败: {e}")
            self.create_default_configs()

    def load_simulation_config(self):
        """加载仿真配置"""
        if os.path.exists(self.sim_config_path):
            try:
                with open(self.sim_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 更新配置对象
                    for key, value in data.items():
                        if hasattr(self.simulation, key):
                            setattr(self.simulation, key, value)
                print("仿真配置加载成功")
            except Exception as e:
                print(f"仿真配置加载失败: {e}")
                self.save_simulation_config()  # 保存默认配置

    def load_ui_config(self):
        """加载UI配置"""
        if os.path.exists(self.ui_config_path):
            try:
                with open(self.ui_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.ui, key):
                            setattr(self.ui, key, value)
                print("UI配置加载成功")
            except Exception as e:
                print(f"UI配置加载失败: {e}")
                self.save_ui_config()

    def save_simulation_config(self):
        """保存仿真配置"""
        try:
            with open(self.sim_config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.simulation), f, indent=2, ensure_ascii=False)
            print("仿真配置保存成功")
        except Exception as e:
            print(f"仿真配置保存失败: {e}")

    def save_ui_config(self):
        """保存UI配置"""
        try:
            with open(self.ui_config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.ui), f, indent=2, ensure_ascii=False)
            print("UI配置保存成功")
        except Exception as e:
            print(f"UI配置保存失败: {e}")

    def save_all_configs(self):
        """保存所有配置"""
        self.save_simulation_config()
        self.save_ui_config()
        self.user_settings.sync()

    def create_default_configs(self):
        """创建默认配置文件"""
        print("创建默认配置文件...")
        self.save_simulation_config()
        self.save_ui_config()

    def get_user_setting(self, key: str, default_value: Any = None) -> Any:
        """获取用户设置"""
        return self.user_settings.value(key, default_value)

    def set_user_setting(self, key: str, value: Any):
        """设置用户设置"""
        self.user_settings.setValue(key, value)

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.simulation = SimulationConfig()
        self.ui = UIConfig()
        self.save_all_configs()
        print("配置已重置为默认值")

    def update_simulation_config(self, **kwargs):
        """更新仿真配置"""
        for key, value in kwargs.items():
            if hasattr(self.simulation, key):
                setattr(self.simulation, key, value)
                print(f"更新仿真配置: {key} = {value}")
        self.save_simulation_config()

    def update_ui_config(self, **kwargs):
        """更新UI配置"""
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
                print(f"更新UI配置: {key} = {value}")
        self.save_ui_config()

    def export_config(self, filepath: str):
        """导出配置到文件"""
        try:
            config_data = {
                "simulation": asdict(self.simulation),
                "ui": asdict(self.ui),
                "user_settings": {
                    key: self.user_settings.value(key)
                    for key in self.user_settings.allKeys()
                }
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"配置导出成功: {filepath}")
            return True
        except Exception as e:
            print(f"配置导出失败: {e}")
            return False

    def import_config(self, filepath: str):
        """从文件导入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 导入仿真配置
            if "simulation" in config_data:
                sim_data = config_data["simulation"]
                for key, value in sim_data.items():
                    if hasattr(self.simulation, key):
                        setattr(self.simulation, key, value)

            # 导入UI配置
            if "ui" in config_data:
                ui_data = config_data["ui"]
                for key, value in ui_data.items():
                    if hasattr(self.ui, key):
                        setattr(self.ui, key, value)

            # 导入用户设置
            if "user_settings" in config_data:
                for key, value in config_data["user_settings"].items():
                    self.user_settings.setValue(key, value)

            self.save_all_configs()
            print(f"配置导入成功: {filepath}")
            return True
        except Exception as e:
            print(f"配置导入失败: {e}")
            return False

    def validate_config(self) -> Dict[str, list]:
        """验证配置有效性"""
        errors = {"simulation": [], "ui": []}

        # 验证仿真配置
        sim = self.simulation
        if sim.fps_target < 1 or sim.fps_target > 120:
            errors["simulation"].append("FPS目标值应在1-120之间")

        if sim.zoom_min <= 0 or sim.zoom_max <= sim.zoom_min:
            errors["simulation"].append("缩放范围设置无效")

        if sim.agv_default_speed <= 0:
            errors["simulation"].append("AGV默认速度必须大于0")

        if not (0 < sim.low_battery_threshold < sim.critical_battery_threshold < 100):
            errors["simulation"].append("电量阈值设置无效")

        # 验证UI配置
        ui = self.ui
        if ui.font_size < 6 or ui.font_size > 72:
            errors["ui"].append("字体大小应在6-72之间")

        if ui.control_panel_width < 200 or ui.control_panel_width > 800:
            errors["ui"].append("控制面板宽度应在200-800之间")

        return errors

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        return f"""配置摘要:
仿真设置:
  - 窗口尺寸: {self.simulation.window_width}x{self.simulation.window_height}
  - 目标FPS: {self.simulation.fps_target}
  - AGV默认速度: {self.simulation.agv_default_speed}
  - 低电量阈值: {self.simulation.low_battery_threshold}%
  - 订单生成速率: {self.simulation.default_generation_rate}/分钟

UI设置:
  - 主题: {self.ui.theme}
  - 字体: {self.ui.font_family} {self.ui.font_size}pt
  - 控制面板宽度: {self.ui.control_panel_width}px

文件位置:
  - 仿真配置: {self.sim_config_path}
  - UI配置: {self.ui_config_path}
  - 用户设置: {self.user_settings_path}"""


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager


# 快捷访问函数
def get_simulation_config() -> SimulationConfig:
    """获取仿真配置"""
    return config_manager.simulation


def get_ui_config() -> UIConfig:
    """获取UI配置"""
    return config_manager.ui


def save_configs():
    """保存所有配置"""
    config_manager.save_all_configs()


# 预设配置模板
PRESET_CONFIGS = {
    "performance": {
        "simulation": {
            "fps_target": 30,
            "enable_debug_mode": False,
            "enable_performance_monitoring": True,
            "max_log_lines": 500
        },
        "ui": {
            "auto_refresh_interval": 2000,
            "table_alternate_colors": False
        }
    },

    "demo": {
        "simulation": {
            "default_generation_rate": 1.0,
            "agv_default_speed": 3.0,
            "assignment_interval": 1.0
        },
        "ui": {
            "show_advanced_controls": True,
            "auto_refresh_interval": 500
        }
    },

    "research": {
        "simulation": {
            "enable_debug_mode": True,
            "enable_performance_monitoring": True,
            "max_log_lines": 2000,
            "auto_save_interval": 60
        },
        "ui": {
            "show_advanced_controls": True,
            "table_row_height": 30
        }
    }
}


def apply_preset_config(preset_name: str) -> bool:
    """应用预设配置"""
    if preset_name not in PRESET_CONFIGS:
        print(f"未知的预设配置: {preset_name}")
        return False

    preset = PRESET_CONFIGS[preset_name]

    try:
        # 应用仿真配置
        if "simulation" in preset:
            config_manager.update_simulation_config(**preset["simulation"])

        # 应用UI配置
        if "ui" in preset:
            config_manager.update_ui_config(**preset["ui"])

        print(f"已应用预设配置: {preset_name}")
        return True
    except Exception as e:
        print(f"应用预设配置失败: {e}")
        return False