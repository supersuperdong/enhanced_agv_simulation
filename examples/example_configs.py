"""
RCS-Lite AGV增强仿真系统 - 示例配置文件
展示如何配置和使用各种功能
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 示例配置数据
EXAMPLE_CONFIGS = {
    # 基础演示配置
    "demo_basic": {
        "simulation": {
            "window_width": 1600,
            "window_height": 900,
            "fps_target": 60,
            "agv_default_speed": 2.0,
            "collision_buffer": 25,
            "default_generation_rate": 0.8,
            "low_battery_threshold": 30.0,
            "critical_battery_threshold": 15.0,
            "enable_debug_mode": False
        },
        "ui": {
            "theme": "default",
            "font_size": 10,
            "control_panel_width": 350,
            "show_advanced_controls": True,
            "auto_refresh_interval": 1000
        },
        "description": "基础演示配置，适合快速体验系统功能"
    },

    # 高性能配置
    "performance_optimized": {
        "simulation": {
            "window_width": 1920,
            "window_height": 1080,
            "fps_target": 30,  # 降低FPS以提高性能
            "agv_default_speed": 3.0,  # 提高AGV速度
            "collision_buffer": 20,  # 减小碰撞缓冲区
            "default_generation_rate": 2.0,  # 提高订单生成速率
            "assignment_interval": 1.0,  # 快速任务分配
            "low_battery_threshold": 25.0,
            "enable_debug_mode": False,
            "enable_performance_monitoring": True
        },
        "ui": {
            "auto_refresh_interval": 2000,  # 降低刷新频率
            "table_alternate_colors": False,
            "show_battery_indicators": True,
            "show_path_arrows": False  # 减少绘制元素
        },
        "description": "性能优化配置，适合大规模仿真"
    },

    # 研究开发配置
    "research_development": {
        "simulation": {
            "window_width": 1920,
            "window_height": 1080,
            "fps_target": 60,
            "agv_default_speed": 1.5,  # 较慢速度便于观察
            "default_generation_rate": 0.5,  # 较低生成速率
            "assignment_interval": 3.0,  # 较长分配间隔
            "enable_debug_mode": True,
            "enable_performance_monitoring": True,
            "max_log_lines": 2000,
            "auto_save_interval": 60  # 1分钟自动保存
        },
        "ui": {
            "show_advanced_controls": True,
            "auto_refresh_interval": 500,
            "table_row_height": 30,
            "font_size": 11
        },
        "battery": {
            "discharge_rate_moving": 0.6,  # 较慢放电
            "discharge_rate_carrying": 1.0,  # 载货额外消耗
            "charge_rate": 10.0,  # 快速充电
            "capacity": 120.0  # 更大电池容量
        },
        "description": "研究开发配置，便于详细观察和数据收集"
    },

    # 压力测试配置
    "stress_test": {
        "simulation": {
            "window_width": 1920,
            "window_height": 1080,
            "fps_target": 30,
            "agv_default_speed": 4.0,  # 高速度
            "default_generation_rate": 5.0,  # 高订单生成速率
            "assignment_interval": 0.5,  # 快速分配
            "collision_buffer": 15,  # 小碰撞缓冲区
            "max_retry_attempts": 5,
            "enable_performance_monitoring": True
        },
        "ui": {
            "auto_refresh_interval": 200,
            "show_advanced_controls": True
        },
        "battery": {
            "discharge_rate_moving": 1.2,  # 快速放电
            "charge_rate": 15.0  # 快速充电
        },
        "description": "压力测试配置，测试系统极限性能"
    },

    # 教学演示配置
    "educational": {
        "simulation": {
            "window_width": 1600,
            "window_height": 900,
            "fps_target": 45,
            "agv_default_speed": 1.8,
            "default_generation_rate": 1.0,
            "assignment_interval": 2.0,
            "enable_debug_mode": False,
            "show_battery_indicators": True,
            "show_path_arrows": True,
            "show_control_zones": True,
            "show_node_ids": True
        },
        "ui": {
            "theme": "educational",
            "font_size": 12,
            "control_panel_width": 400,
            "show_advanced_controls": True,
            "auto_refresh_interval": 1000,
            "colors": {
                "agv_default": "#FF8C00",
                "agv_charging": "#0096FF",
                "node_pickup": "#4CAF50",
                "node_dropoff": "#F44336",
                "path_active": "#64B4FF"
            }
        },
        "description": "教学演示配置，适合课堂展示和学习"
    }
}

# 预设的调度策略配置
SCHEDULING_STRATEGIES = {
    "efficiency_first": {
        "strategy": "NEAREST_FIRST",
        "assignment_interval": 1.0,
        "description": "效率优先：选择最近的AGV，减少空载时间"
    },
    "priority_based": {
        "strategy": "PRIORITY",
        "assignment_interval": 1.5,
        "description": "优先级优先：紧急订单优先处理"
    },
    "balanced_approach": {
        "strategy": "BALANCED",
        "assignment_interval": 2.0,
        "description": "平衡方案：综合考虑距离、电量、优先级"
    },
    "deadline_critical": {
        "strategy": "DEADLINE_FIRST",
        "assignment_interval": 0.8,
        "description": "截止时间优先：避免订单超时"
    }
}

# 电量管理策略
BATTERY_STRATEGIES = {
    "conservative": {
        "low_battery_threshold": 40.0,
        "critical_battery_threshold": 20.0,
        "charge_rate": 6.0,
        "description": "保守策略：较早充电，确保电量充足"
    },
    "aggressive": {
        "low_battery_threshold": 20.0,
        "critical_battery_threshold": 10.0,
        "charge_rate": 12.0,
        "description": "激进策略：尽可能延迟充电，快速充电"
    },
    "balanced": {
        "low_battery_threshold": 30.0,
        "critical_battery_threshold": 15.0,
        "charge_rate": 8.0,
        "description": "平衡策略：适中的充电时机和速度"
    }
}

# 场景配置
SCENARIO_CONFIGS = {
    "warehouse_morning_rush": {
        "description": "仓库早高峰场景",
        "config": {
            "order_generation_rate": 3.0,
            "agv_count": 8,
            "battery_strategy": "conservative",
            "scheduling_strategy": "efficiency_first",
            "priority_distribution": {
                "LOW": 5,
                "NORMAL": 70,
                "HIGH": 20,
                "URGENT": 5
            }
        }
    },
    "factory_steady_state": {
        "description": "工厂稳态生产场景",
        "config": {
            "order_generation_rate": 1.5,
            "agv_count": 6,
            "battery_strategy": "balanced",
            "scheduling_strategy": "balanced_approach",
            "priority_distribution": {
                "LOW": 10,
                "NORMAL": 80,
                "HIGH": 10
            }
        }
    },
    "emergency_response": {
        "description": "应急响应场景",
        "config": {
            "order_generation_rate": 2.5,
            "agv_count": 10,
            "battery_strategy": "aggressive",
            "scheduling_strategy": "priority_based",
            "priority_distribution": {
                "HIGH": 40,
                "URGENT": 40,
                "EMERGENCY": 20
            }
        }
    }
}


def create_config_file(config_name: str, output_path: str = None) -> str:
    """创建配置文件"""
    if config_name not in EXAMPLE_CONFIGS:
        raise ValueError(f"未知配置: {config_name}. 可用配置: {list(EXAMPLE_CONFIGS.keys())}")

    config_data = EXAMPLE_CONFIGS[config_name]

    if output_path is None:
        output_path = f"config_{config_name}.json"

    # 确保目录存在
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    print(f"配置文件已创建: {output_path}")
    print(f"描述: {config_data.get('description', '无描述')}")

    return output_path


def create_all_example_configs(output_dir: str = "config_examples") -> list:
    """创建所有示例配置文件"""
    os.makedirs(output_dir, exist_ok=True)
    created_files = []

    for config_name in EXAMPLE_CONFIGS:
        output_path = os.path.join(output_dir, f"{config_name}.json")
        created_file = create_config_file(config_name, output_path)
        created_files.append(created_file)

    # 创建调度策略配置
    strategies_path = os.path.join(output_dir, "scheduling_strategies.json")
    with open(strategies_path, 'w', encoding='utf-8') as f:
        json.dump(SCHEDULING_STRATEGIES, f, indent=2, ensure_ascii=False)
    created_files.append(strategies_path)

    # 创建电量策略配置
    battery_path = os.path.join(output_dir, "battery_strategies.json")
    with open(battery_path, 'w', encoding='utf-8') as f:
        json.dump(BATTERY_STRATEGIES, f, indent=2, ensure_ascii=False)
    created_files.append(battery_path)

    # 创建场景配置
    scenarios_path = os.path.join(output_dir, "scenario_configs.json")
    with open(scenarios_path, 'w', encoding='utf-8') as f:
        json.dump(SCENARIO_CONFIGS, f, indent=2, ensure_ascii=False)
    created_files.append(scenarios_path)

    print(f"所有示例配置已创建在: {output_dir}")
    return created_files


def load_config_from_file(config_path: str) -> dict:
    """从文件加载配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}


def apply_config_to_system(config_data: dict, simulation_widget, control_panel):
    """将配置应用到系统"""
    try:
        # 应用仿真配置
        if 'simulation' in config_data:
            sim_config = config_data['simulation']

            # 设置AGV参数
            if 'agv_default_speed' in sim_config:
                for agv in simulation_widget.agvs:
                    agv.speed = sim_config['agv_default_speed']

            # 设置订单生成速率
            if 'default_generation_rate' in sim_config:
                order_generator = simulation_widget.get_order_generator()
                order_generator.set_generation_rate(sim_config['default_generation_rate'])

            # 设置电量参数
            if 'low_battery_threshold' in sim_config:
                for agv in simulation_widget.agvs:
                    agv.battery_system.low_threshold = sim_config['low_battery_threshold']

        # 应用UI配置
        if 'ui' in config_data:
            ui_config = config_data['ui']

            # 设置刷新间隔
            if 'auto_refresh_interval' in ui_config:
                if hasattr(control_panel, 'main_timer'):
                    control_panel.main_timer.start(ui_config['auto_refresh_interval'])

        print("配置应用成功")
        return True

    except Exception as e:
        print(f"应用配置失败: {e}")
        return False


def create_custom_config_template() -> dict:
    """创建自定义配置模板"""
    template = {
        "description": "自定义配置模板",
        "simulation": {
            "window_width": 1920,
            "window_height": 1080,
            "fps_target": 60,
            "agv_default_speed": 2.0,
            "collision_buffer": 25,
            "default_generation_rate": 1.0,
            "assignment_interval": 2.0,
            "low_battery_threshold": 30.0,
            "critical_battery_threshold": 15.0,
            "enable_debug_mode": False,
            "enable_performance_monitoring": False
        },
        "ui": {
            "theme": "default",
            "font_family": "Arial",
            "font_size": 10,
            "control_panel_width": 400,
            "show_advanced_controls": True,
            "auto_refresh_interval": 1000,
            "colors": {
                "background": "#EBF0F5",
                "agv_default": "#FF8C00",
                "agv_charging": "#0096FF",
                "node_pickup": "#4CAF50",
                "node_dropoff": "#F44336"
            }
        },
        "battery": {
            "capacity": 100.0,
            "discharge_rate_moving": 0.8,
            "discharge_rate_idle": 0.02,
            "discharge_rate_carrying": 1.2,
            "charge_rate": 8.0
        },
        "scheduling": {
            "default_strategy": "BALANCED",
            "max_retry_attempts": 3,
            "priority_weights": {
                "LOW": 10,
                "NORMAL": 60,
                "HIGH": 20,
                "URGENT": 8,
                "EMERGENCY": 2
            }
        }
    }

    return template


def get_config_recommendations(scenario: str) -> dict:
    """获取场景配置建议"""
    recommendations = {
        "small_warehouse": {
            "agv_count": "3-5个",
            "generation_rate": "0.5-1.0订单/分钟",
            "strategy": "NEAREST_FIRST",
            "battery_strategy": "conservative"
        },
        "medium_factory": {
            "agv_count": "6-10个",
            "generation_rate": "1.0-2.0订单/分钟",
            "strategy": "BALANCED",
            "battery_strategy": "balanced"
        },
        "large_logistics": {
            "agv_count": "10-20个",
            "generation_rate": "2.0-5.0订单/分钟",
            "strategy": "PRIORITY",
            "battery_strategy": "aggressive"
        }
    }

    return recommendations.get(scenario, {})


def validate_config(config_data: dict) -> tuple:
    """验证配置数据"""
    errors = []
    warnings = []

    # 验证仿真配置
    if 'simulation' in config_data:
        sim = config_data['simulation']

        # 检查FPS
        if 'fps_target' in sim:
            if sim['fps_target'] < 1 or sim['fps_target'] > 120:
                errors.append("FPS目标值应在1-120之间")

        # 检查AGV速度
        if 'agv_default_speed' in sim:
            if sim['agv_default_speed'] <= 0:
                errors.append("AGV默认速度必须大于0")

        # 检查订单生成速率
        if 'default_generation_rate' in sim:
            if sim['default_generation_rate'] > 10:
                warnings.append("订单生成速率过高可能影响性能")

    # 验证电量配置
    if 'battery' in config_data:
        battery = config_data['battery']

        if 'capacity' in battery:
            if battery['capacity'] <= 0:
                errors.append("电池容量必须大于0")

    return len(errors) == 0, errors, warnings


def main():
    """主函数 - 演示配置系统使用"""
    import argparse

    parser = argparse.ArgumentParser(description="RCS-Lite AGV配置系统示例")
    parser.add_argument("--create", choices=list(EXAMPLE_CONFIGS.keys()) + ["all"],
                        help="创建示例配置")
    parser.add_argument("--output", default="config_examples", help="输出目录")
    parser.add_argument("--template", action="store_true", help="创建自定义模板")
    parser.add_argument("--validate", help="验证配置文件")
    parser.add_argument("--list", action="store_true", help="列出所有可用配置")

    args = parser.parse_args()

    if args.list:
        print("可用的示例配置:")
        for name, config in EXAMPLE_CONFIGS.items():
            print(f"  {name}: {config.get('description', '无描述')}")
        return

    if args.create:
        if args.create == "all":
            create_all_example_configs(args.output)
        else:
            create_config_file(args.create,
                               os.path.join(args.output, f"{args.create}.json"))

    if args.template:
        template = create_custom_config_template()
        template_path = os.path.join(args.output, "custom_template.json")
        os.makedirs(args.output, exist_ok=True)

        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(f"自定义配置模板已创建: {template_path}")

    if args.validate:
        config_data = load_config_from_file(args.validate)
        if config_data:
            is_valid, errors, warnings = validate_config(config_data)

            print(f"配置文件验证结果: {'通过' if is_valid else '失败'}")

            if errors:
                print("错误:")
                for error in errors:
                    print(f"  - {error}")

            if warnings:
                print("警告:")
                for warning in warnings:
                    print(f"  - {warning}")


if __name__ == "__main__":
    main()