"""
RCS-Lite AGV增强仿真系统 - 完整使用示例
展示订单系统、电量管理和任务调度的完整使用流程
"""

import sys
import time
import random
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from models.order import Order, OrderPriority, OrderGenerator
from models.battery_system import BatterySystem, BatteryStatus
from models.task_scheduler import TaskScheduler, SchedulingStrategy
from models.agv import EnhancedAGV
from models.node import Node
from utils.config_manager import get_config, apply_preset_config
from utils.performance_monitor import start_performance_monitoring
from utils.data_analyzer import AGVDataAnalyzer


class AGVSimulationDemo:
    """AGV仿真系统演示类"""

    def __init__(self):
        self.nodes = {}
        self.agvs = []
        self.order_generator = None
        self.task_scheduler = None
        self.performance_monitor = None

        # 创建演示地图
        self._create_demo_map()

        # 初始化子系统
        self._init_subsystems()

        # 统计信息
        self.demo_stats = {
            'orders_generated': 0,
            'orders_completed': 0,
            'total_distance': 0.0,
            'charging_sessions': 0,
            'start_time': time.time()
        }

    def _create_demo_map(self):
        """创建演示地图"""
        print("🗺️ 创建演示地图...")

        # 创建节点网络
        node_configs = [
            # 上货点 (Pickup Points)
            ("PP01", 100, 100, "pickup"),
            ("PP02", 100, 300, "pickup"),
            ("PP03", 100, 500, "pickup"),

            # 下货点 (Dropoff Points)
            ("AP01", 500, 100, "dropoff"),
            ("AP02", 500, 300, "dropoff"),
            ("AP03", 500, 500, "dropoff"),

            # 充电站 (Charging Points)
            ("CP01", 300, 50, "charging"),
            ("CP02", 300, 550, "charging"),

            # 中转节点 (Normal Points)
            ("N01", 200, 200, "normal"),
            ("N02", 300, 200, "normal"),
            ("N03", 400, 200, "normal"),
            ("N04", 200, 400, "normal"),
            ("N05", 300, 400, "normal"),
            ("N06", 400, 400, "normal"),
        ]

        # 创建节点
        for node_id, x, y, node_type in node_configs:
            self.nodes[node_id] = Node(node_id, x, y, node_type)

        # 设置节点连接
        self._setup_node_connections()

        print(f"✅ 地图创建完成: {len(self.nodes)} 个节点")

    def _setup_node_connections(self):
        """设置节点连接"""
        # 定义连接关系 (node_id, connected_nodes)
        connections = [
            ("PP01", ["N01", "CP01"]),
            ("PP02", ["N01", "N04"]),
            ("PP03", ["N04", "CP02"]),
            ("AP01", ["N03", "CP01"]),
            ("AP02", ["N03", "N06"]),
            ("AP03", ["N06", "CP02"]),
            ("CP01", ["PP01", "AP01", "N02"]),
            ("CP02", ["PP03", "AP03", "N05"]),
            ("N01", ["PP01", "PP02", "N02", "N04"]),
            ("N02", ["N01", "N03", "N05", "CP01"]),
            ("N03", ["N02", "N06", "AP01", "AP02"]),
            ("N04", ["N01", "N05", "PP02", "PP03"]),
            ("N05", ["N04", "N06", "N02", "CP02"]),
            ("N06", ["N05", "N03", "AP02", "AP03"]),
        ]

        # 建立双向连接
        for node_id, connected_list in connections:
            node = self.nodes[node_id]
            for connected_id in connected_list:
                if connected_id in self.nodes:
                    connected_node = self.nodes[connected_id]
                    distance = ((node.x - connected_node.x) ** 2 +
                                (node.y - connected_node.y) ** 2) ** 0.5
                    node.add_connection(connected_id, distance)

    def _init_subsystems(self):
        """初始化子系统"""
        print("🔧 初始化子系统...")

        # 订单生成器
        self.order_generator = OrderGenerator(self.nodes)
        self.order_generator.order_generated.connect(self._on_order_generated)

        # 任务调度器 (需要模拟仿真组件)
        self.task_scheduler = TaskScheduler(self)
        self.task_scheduler.task_assigned.connect(self._on_task_assigned)
        self.task_scheduler.task_completed.connect(self._on_task_completed)

        # 性能监控
        self.performance_monitor = start_performance_monitoring(self)

        print("✅ 子系统初始化完成")

    def add_agv(self, start_node_id=None, agv_config=None):
        """添加AGV"""
        if start_node_id is None:
            # 随机选择起始节点
            available_nodes = [nid for nid, node in self.nodes.items()
                               if node.occupied_by is None and node.node_type == 'normal']
            if not available_nodes:
                available_nodes = list(self.nodes.keys())
            start_node_id = random.choice(available_nodes)

        if start_node_id not in self.nodes:
            print(f"❌ 无效的起始节点: {start_node_id}")
            return None

        start_node = self.nodes[start_node_id]
        if start_node.occupied_by is not None:
            print(f"❌ 节点 {start_node_id} 已被占用")
            return None

        # 创建AGV
        agv_id = len(self.agvs) + 1
        agv = EnhancedAGV(agv_id, start_node)

        # 应用自定义配置
        if agv_config:
            if 'speed' in agv_config:
                agv.speed = agv_config['speed']
            if 'battery_capacity' in agv_config:
                agv.battery_system.capacity = agv_config['battery_capacity']
            if 'color' in agv_config:
                agv.color = agv_config['color']

        self.agvs.append(agv)
        print(f"🤖 AGV #{agv_id} 已添加到节点 {start_node_id}")
        return agv

    def _find_agv_by_id(self, agv_id):
        """查找AGV"""
        return next((agv for agv in self.agvs if agv.id == agv_id), None)

    def send_agv_to_target(self, agv_id, target_node_id, algorithm='a_star'):
        """发送AGV到目标"""
        agv = self._find_agv_by_id(agv_id)
        if not agv or target_node_id not in self.nodes:
            return False

        # 简化的路径规划
        from algorithms.path_planner import PathPlanner
        try:
            path = PathPlanner.plan_path(
                algorithm, self.nodes, agv.current_node.id, target_node_id, self.agvs
            )
            if path:
                agv.set_path(path)
                return True
        except Exception as e:
            print(f"路径规划失败: {e}")
        return False

    def _on_order_generated(self, order):
        """订单生成回调"""
        self.demo_stats['orders_generated'] += 1
        print(f"📋 新订单生成: {order.id} ({order.pickup_node_id} → {order.dropoff_node_id})")

    def _on_task_assigned(self, agv_id, task):
        """任务分配回调"""
        print(f"🎯 任务分配: AGV #{agv_id} 接受订单 {task.order.id if task.order else 'N/A'}")

    def _on_task_completed(self, agv_id, task):
        """任务完成回调"""
        if task.order:
            self.demo_stats['orders_completed'] += 1
            print(f"✅ 任务完成: AGV #{agv_id} 完成订单 {task.order.id}")

    def update_simulation(self):
        """更新仿真"""
        # 更新AGV
        for agv in self.agvs:
            agv.move(self.nodes, self.agvs)

        # 更新订单生成器
        self.order_generator.update()

        # 更新任务调度器
        self.task_scheduler.update()

        # 更新统计信息
        self.demo_stats['total_distance'] = sum(
            getattr(agv, 'total_distance_traveled', 0) for agv in self.agvs
        )

    def get_system_status(self):
        """获取系统状态"""
        # AGV状态统计
        agv_status = {
            'total': len(self.agvs),
            'moving': sum(1 for agv in self.agvs if agv.moving),
            'charging': sum(1 for agv in self.agvs if agv.battery_system.is_charging),
            'carrying': sum(1 for agv in self.agvs if agv.is_carrying_cargo),
            'low_battery': sum(1 for agv in self.agvs if agv.battery_system.needs_charging())
        }

        # 订单状态统计
        order_stats = self.task_scheduler.order_queue.get_statistics()

        # 运行时间
        runtime = time.time() - self.demo_stats['start_time']

        return {
            'runtime_seconds': runtime,
            'agv_status': agv_status,
            'order_stats': order_stats,
            'demo_stats': self.demo_stats
        }

    def print_status_report(self):
        """打印状态报告"""
        status = self.get_system_status()

        print("\n" + "=" * 60)
        print("📊 系统状态报告")
        print("=" * 60)

        # 运行时间
        runtime = status['runtime_seconds']
        print(f"⏱️  运行时间: {runtime // 60:.0f}分 {runtime % 60:.0f}秒")

        # AGV状态
        agv = status['agv_status']
        print(
            f"🤖 AGV状态: 总数{agv['total']} | 移动{agv['moving']} | 充电{agv['charging']} | 载货{agv['carrying']} | 低电{agv['low_battery']}")

        # 订单状态
        orders = status['order_stats']
        print(
            f"📋 订单状态: 待处理{orders['pending_count']} | 处理中{orders['processing_count']} | 已完成{orders['completed_count']}")

        # 性能指标
        demo = status['demo_stats']
        completion_rate = (demo['orders_completed'] / max(demo['orders_generated'], 1)) * 100
        print(f"📈 性能指标: 完成率{completion_rate:.1f}% | 总里程{demo['total_distance']:.1f}")

        print("=" * 60)

    def run_demo_scenario(self, scenario_name="basic_demo"):
        """运行演示场景"""
        scenarios = {
            "basic_demo": self._basic_demo_scenario,
            "stress_test": self._stress_test_scenario,
            "battery_management": self._battery_management_scenario,
            "priority_orders": self._priority_orders_scenario
        }

        if scenario_name in scenarios:
            print(f"🎬 开始演示场景: {scenario_name}")
            scenarios[scenario_name]()
        else:
            print(f"❌ 未知场景: {scenario_name}")

    def _basic_demo_scenario(self):
        """基础演示场景"""
        print("📖 基础演示场景：展示完整的订单-运输-充电流程")

        # 添加3个AGV
        for i in range(3):
            agv_config = {
                'speed': 2.0 + random.uniform(-0.5, 0.5),
                'battery_capacity': 100.0
            }
            self.add_agv(agv_config=agv_config)

        # 设置适中的订单生成速率
        self.order_generator.set_generation_rate(1.0)  # 每分钟1个订单
        self.order_generator.start_generation()

        # 设置平衡调度策略
        self.task_scheduler.set_scheduling_strategy(SchedulingStrategy.BALANCED)

        print("✅ 基础演示场景设置完成")

    def _stress_test_scenario(self):
        """压力测试场景"""
        print("🔥 压力测试场景：高订单量和多AGV测试")

        # 添加8个AGV
        for i in range(8):
            agv_config = {
                'speed': 3.0,
                'battery_capacity': 80.0  # 较小电池增加充电频率
            }
            self.add_agv(agv_config=agv_config)

        # 高订单生成速率
        self.order_generator.set_generation_rate(3.0)  # 每分钟3个订单
        self.order_generator.start_generation()

        # 效率优先调度
        self.task_scheduler.set_scheduling_strategy(SchedulingStrategy.NEAREST_FIRST)

        print("✅ 压力测试场景设置完成")

    def _battery_management_scenario(self):
        """电量管理场景"""
        print("🔋 电量管理场景：展示低电量和充电管理")

        # 添加AGV并设置低初始电量
        for i in range(4):
            agv = self.add_agv()
            if agv:
                # 设置不同的初始电量
                agv.battery_system.current_charge = 20 + random.uniform(0, 30)
                agv.battery_system.low_threshold = 35.0  # 较高的充电阈值

        # 适中的订单生成速率
        self.order_generator.set_generation_rate(1.5)
        self.order_generator.start_generation()

        print("✅ 电量管理场景设置完成")

    def _priority_orders_scenario(self):
        """优先级订单场景"""
        print("⭐ 优先级订单场景：展示不同优先级的订单处理")

        # 添加AGV
        for i in range(5):
            self.add_agv()

        # 设置优先级调度
        self.task_scheduler.set_scheduling_strategy(SchedulingStrategy.PRIORITY)

        # 手动生成不同优先级的订单
        priorities = [OrderPriority.LOW, OrderPriority.NORMAL, OrderPriority.HIGH,
                      OrderPriority.URGENT, OrderPriority.EMERGENCY]

        for priority in priorities:
            order = self.order_generator.manual_generate_order(priority=priority)
            time.sleep(0.1)  # 小间隔

        # 继续自动生成
        self.order_generator.set_generation_rate(0.8)
        self.order_generator.start_generation()

        print("✅ 优先级订单场景设置完成")


def interactive_demo():
    """交互式演示"""
    print("🎮 RCS-Lite AGV增强仿真系统 - 交互式演示")
    print("=" * 60)

    demo = AGVSimulationDemo()

    commands = {
        '1': ('基础演示', lambda: demo.run_demo_scenario("basic_demo")),
        '2': ('压力测试', lambda: demo.run_demo_scenario("stress_test")),
        '3': ('电量管理', lambda: demo.run_demo_scenario("battery_management")),
        '4': ('优先级订单', lambda: demo.run_demo_scenario("priority_orders")),
        '5': ('添加AGV', lambda: demo.add_agv()),
        '6': ('手动生成订单', lambda: demo.order_generator.manual_generate_order()),
        '7': ('状态报告', lambda: demo.print_status_report()),
        '8': ('开始/停止订单生成', lambda: toggle_order_generation()),
        '9': ('更改调度策略', lambda: change_scheduling_strategy()),
        '0': ('退出', lambda: None)
    }

    def toggle_order_generation():
        if demo.order_generator.is_active:
            demo.order_generator.stop_generation()
            print("⏸️ 订单生成已停止")
        else:
            demo.order_generator.start_generation()
            print("▶️ 订单生成已启动")

    def change_scheduling_strategy():
        strategies = list(SchedulingStrategy)
        print("可用调度策略:")
        for i, strategy in enumerate(strategies):
            print(f"  {i + 1}. {strategy.value}")

        try:
            choice = int(input("选择策略编号: ")) - 1
            if 0 <= choice < len(strategies):
                demo.task_scheduler.set_scheduling_strategy(strategies[choice])
                print(f"✅ 调度策略已更改为: {strategies[choice].value}")
        except (ValueError, IndexError):
            print("❌ 无效选择")

    # 主循环
    while True:
        print("\n📋 可用命令:")
        for key, (desc, _) in commands.items():
            print(f"  {key}. {desc}")

        choice = input("\n选择命令 (回车更新仿真): ").strip()

        if choice == '':
            # 更新仿真
            demo.update_simulation()
            if demo.performance_monitor:
                demo.performance_monitor.tick_frame()
        elif choice in commands:
            desc, action = commands[choice]
            if choice == '0':
                print("👋 演示结束")
                break
            try:
                action()
            except Exception as e:
                print(f"❌ 执行失败: {e}")
        else:
            print("❌ 无效命令")


def gui_demo():
    """GUI演示"""
    print("🖥️ 启动GUI演示...")

    try:
        app = QApplication(sys.argv)

        # 导入GUI组件
        from ui.main_window import EnhancedMainWindow

        # 创建主窗口
        window = EnhancedMainWindow()

        # 获取仿真组件
        simulation = window.get_simulation_widget()

        # 添加一些AGV和订单用于演示
        for i in range(3):
            simulation.add_agv()

        # 启动订单生成
        order_generator = simulation.get_order_generator()
        order_generator.set_generation_rate(1.0)
        order_generator.start_generation()

        # 显示窗口
        window.show()

        print("✅ GUI演示已启动")
        print("💡 提示：点击'演示模式'按钮快速体验完整功能")

        # 运行应用
        sys.exit(app.exec_())

    except ImportError as e:
        print(f"❌ GUI组件加载失败: {e}")
        print("💡 请确保PyQt5已正确安装")
    except Exception as e:
        print(f"❌ GUI演示启动失败: {e}")


def automated_demo():
    """自动化演示"""
    print("🤖 自动化演示：自动运行完整仿真流程")

    demo = AGVSimulationDemo()

    # 运行基础演示场景
    demo.run_demo_scenario("basic_demo")

    print("⏱️ 开始自动化演示，将运行30秒...")

    start_time = time.time()
    last_report_time = start_time

    while time.time() - start_time < 30:  # 运行30秒
        # 更新仿真
        demo.update_simulation()

        # 每5秒打印一次状态报告
        if time.time() - last_report_time >= 5:
            demo.print_status_report()
            last_report_time = time.time()

        # 短暂休眠以控制更新频率
        time.sleep(0.1)

    # 最终报告
    print("\n🏁 自动化演示完成")
    demo.print_status_report()

    # 生成分析报告
    try:
        analyzer = AGVDataAnalyzer()
        # 创建模拟数据用于分析
        demo_data = {
            "order_statistics": demo.task_scheduler.get_statistics(),
            "agv_details": [agv.get_detailed_status() for agv in demo.agvs]
        }
        analyzer.data = demo_data

        # 分析结果
        order_analysis = analyzer.analyze_order_performance()
        agv_analysis = analyzer.analyze_agv_efficiency()

        print("\n📊 性能分析结果:")
        print(f"订单完成率: {order_analysis.data.get('completion_rate', 0):.1f}%")
        print(f"平均AGV效率: {agv_analysis.data.get('avg_orders_per_agv', 0):.1f} 订单/AGV")

    except Exception as e:
        print(f"分析报告生成失败: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="RCS-Lite AGV增强仿真系统使用示例")
    parser.add_argument("--mode", choices=["interactive", "gui", "auto"],
                        default="interactive", help="演示模式")
    parser.add_argument("--scenario", choices=["basic_demo", "stress_test",
                                               "battery_management", "priority_orders"],
                        help="指定演示场景")
    parser.add_argument("--config", help="使用预设配置")

    args = parser.parse_args()

    # 应用预设配置
    if args.config:
        try:
            apply_preset_config(args.config)
            print(f"✅ 已应用预设配置: {args.config}")
        except Exception as e:
            print(f"❌ 配置应用失败: {e}")

    # 根据模式运行演示
    try:
        if args.mode == "interactive":
            interactive_demo()
        elif args.mode == "gui":
            gui_demo()
        elif args.mode == "auto":
            automated_demo()
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()