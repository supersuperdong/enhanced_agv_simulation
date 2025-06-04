"""
RCS-Lite AGV增强仿真系统测试套件
测试订单系统、电量系统和任务调度系统
"""

import unittest
import sys
import os
import time
import tempfile
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.order import Order, OrderGenerator, OrderStatus, OrderPriority
from models.battery_system import BatterySystem, BatteryStatus, ChargingStation
from models.task_scheduler import TaskScheduler, TaskType, SchedulingStrategy
from models.agv import AGV
from models.node import Node


class TestOrderSystem(unittest.TestCase):
    """订单系统测试"""

    def setUp(self):
        """测试设置"""
        # 创建测试节点
        self.pickup_node = Node("PP01", 100, 100, "pickup")
        self.dropoff_node = Node("AP01", 200, 200, "dropoff")

        # 创建测试订单
        self.test_order = Order("PP01", "AP01", OrderPriority.NORMAL)

    def test_order_creation(self):
        """测试订单创建"""
        self.assertEqual(self.test_order.pickup_node_id, "PP01")
        self.assertEqual(self.test_order.dropoff_node_id, "AP01")
        self.assertEqual(self.test_order.priority, OrderPriority.NORMAL)
        self.assertEqual(self.test_order.status, OrderStatus.PENDING)
        self.assertIsNotNone(self.test_order.id)
        self.assertIsNotNone(self.test_order.create_time)

    def test_order_assignment(self):
        """测试订单分配"""
        agv_id = 1
        self.test_order.assign_to_agv(agv_id)

        self.assertEqual(self.test_order.assigned_agv_id, agv_id)
        self.assertEqual(self.test_order.status, OrderStatus.ASSIGNED)
        self.assertIsNotNone(self.test_order.assign_time)

    def test_order_execution(self):
        """测试订单执行"""
        self.test_order.start_execution()
        self.assertEqual(self.test_order.status, OrderStatus.IN_PROGRESS)
        self.assertIsNotNone(self.test_order.start_time)

        self.test_order.complete()
        self.assertEqual(self.test_order.status, OrderStatus.COMPLETED)
        self.assertIsNotNone(self.test_order.complete_time)

    def test_order_expiration(self):
        """测试订单过期"""
        # 创建一个已过期的订单
        expired_order = Order("PP01", "AP01")
        expired_order.create_time = time.time() - 1000  # 1000秒前
        expired_order.deadline = time.time() - 100  # 100秒前过期

        self.assertTrue(expired_order.is_expired())

    def test_order_generator(self):
        """测试订单生成器"""
        nodes = {
            "PP01": Node("PP01", 100, 100, "pickup"),
            "AP01": Node("AP01", 200, 200, "dropoff")
        }

        generator = OrderGenerator(nodes)
        self.assertEqual(len(generator.pickup_nodes), 1)
        self.assertEqual(len(generator.dropoff_nodes), 1)

        # 测试手动生成订单
        order = generator.manual_generate_order("PP01", "AP01", OrderPriority.HIGH)
        self.assertIsNotNone(order)
        self.assertEqual(order.pickup_node_id, "PP01")
        self.assertEqual(order.priority, OrderPriority.HIGH)


class TestBatterySystem(unittest.TestCase):
    """电量系统测试"""

    def setUp(self):
        """测试设置"""
        self.battery = BatterySystem(capacity=100.0, initial_charge=80.0)

    def test_battery_initialization(self):
        """测试电量系统初始化"""
        self.assertEqual(self.battery.capacity, 100.0)
        self.assertEqual(self.battery.current_charge, 80.0)
        self.assertFalse(self.battery.is_charging)

    def test_battery_discharge(self):
        """测试电量消耗"""
        initial_charge = self.battery.current_charge

        # 模拟1秒的移动消耗
        self.battery.update(is_moving=True, is_carrying_cargo=False)

        # 电量应该减少
        self.assertLess(self.battery.current_charge, initial_charge)

    def test_battery_discharge_with_cargo(self):
        """测试载货时的额外消耗"""
        # 重置电量
        self.battery.current_charge = 50.0
        initial_charge = self.battery.current_charge

        # 模拟载货移动
        self.battery.update(is_moving=True, is_carrying_cargo=True)
        charge_after_cargo = self.battery.current_charge

        # 重置电量测试无载货移动
        self.battery.current_charge = 50.0
        self.battery.update(is_moving=True, is_carrying_cargo=False)
        charge_after_no_cargo = self.battery.current_charge

        # 载货时消耗应该更多
        cargo_consumption = initial_charge - charge_after_cargo
        no_cargo_consumption = initial_charge - charge_after_no_cargo
        self.assertGreater(cargo_consumption, no_cargo_consumption)

    def test_battery_charging(self):
        """测试充电"""
        self.battery.current_charge = 20.0
        initial_charge = self.battery.current_charge

        self.battery.start_charging()
        self.assertTrue(self.battery.is_charging)

        # 模拟充电过程
        self.battery.update()

        # 电量应该增加
        self.assertGreater(self.battery.current_charge, initial_charge)

    def test_battery_status(self):
        """测试电量状态"""
        # 测试不同电量下的状态
        test_cases = [
            (0, BatteryStatus.EMPTY),
            (10, BatteryStatus.CRITICAL),
            (25, BatteryStatus.LOW),
            (50, BatteryStatus.MEDIUM),
            (75, BatteryStatus.HIGH),
            (95, BatteryStatus.FULL)
        ]

        for charge, expected_status in test_cases:
            self.battery.current_charge = charge
            self.battery.is_charging = False
            self.assertEqual(self.battery.get_battery_status(), expected_status)

    def test_charging_station(self):
        """测试充电站"""
        station = ChargingStation("CP01", max_agvs=2)

        # 测试添加AGV
        self.assertTrue(station.can_accept_agv())
        self.assertTrue(station.add_agv_to_charge(1))
        self.assertTrue(station.add_agv_to_charge(2))

        # 充电站满了
        self.assertFalse(station.can_accept_agv())
        self.assertFalse(station.add_agv_to_charge(3))  # 应该加入队列

        # 测试移除AGV
        next_agv = station.remove_agv_from_charge(1)
        self.assertEqual(next_agv, 3)  # 队列中的AGV应该被分配


class TestTaskScheduler(unittest.TestCase):
    """任务调度系统测试"""

    def setUp(self):
        """测试设置"""
        # 创建模拟的仿真组件
        self.mock_simulation = Mock()
        self.mock_simulation.nodes = {
            "PP01": Node("PP01", 100, 100, "pickup"),
            "AP01": Node("AP01", 200, 200, "dropoff"),
            "CP01": Node("CP01", 150, 150, "charging")
        }

        # 创建模拟AGV
        self.mock_agv = Mock()
        self.mock_agv.id = 1
        self.mock_agv.current_node = self.mock_simulation.nodes["PP01"]
        self.mock_agv.moving = False
        self.mock_agv.battery_system = Mock()
        self.mock_agv.battery_system.can_move.return_value = True
        self.mock_agv.battery_system.is_charging = False

        self.mock_simulation.agvs = [self.mock_agv]
        self.mock_simulation._find_agv_by_id = Mock(return_value=self.mock_agv)
        self.mock_simulation.send_agv_to_target = Mock(return_value=True)

        self.scheduler = TaskScheduler(self.mock_simulation)

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        self.assertIsNotNone(self.scheduler.order_queue)
        self.assertEqual(self.scheduler.scheduling_strategy, SchedulingStrategy.BALANCED)

    def test_add_order(self):
        """测试添加订单"""
        order = Order("PP01", "AP01")
        self.scheduler.add_order(order)

        self.assertEqual(len(self.scheduler.order_queue.pending_orders), 1)

    def test_get_available_agvs(self):
        """测试获取可用AGV"""
        available_agvs = self.scheduler._get_available_agvs()
        self.assertEqual(len(available_agvs), 1)
        self.assertEqual(available_agvs[0].id, 1)

    def test_agv_score_calculation(self):
        """测试AGV评分计算"""
        order = Order("PP01", "AP01")
        score = self.scheduler._calculate_agv_score(self.mock_agv, order)

        # 分数应该是正数（AGV在上货点，电量充足）
        self.assertGreater(score, 0)

    def test_scheduling_strategies(self):
        """测试不同调度策略"""
        # 添加多个订单
        orders = [
            Order("PP01", "AP01", OrderPriority.LOW),
            Order("PP01", "AP01", OrderPriority.HIGH),
            Order("PP01", "AP01", OrderPriority.URGENT)
        ]

        for order in orders:
            self.scheduler.order_queue.add_order(order)

        # 测试优先级调度
        self.scheduler.scheduling_strategy = SchedulingStrategy.PRIORITY
        next_order = self.scheduler.order_queue.get_next_order(SchedulingStrategy.PRIORITY)
        self.assertEqual(next_order.priority, OrderPriority.URGENT)


class TestAGV(unittest.TestCase):
    """增强AGV测试"""

    def setUp(self):
        """测试设置"""
        self.start_node = Node("N01", 100, 100, "normal")
        self.agv = AGV(1, self.start_node)

    def test_agv_initialization(self):
        """测试AGV初始化"""
        self.assertEqual(self.agv.id, 1)
        self.assertEqual(self.agv.current_node, self.start_node)
        self.assertIsNotNone(self.agv.battery_system)
        self.assertFalse(self.agv.is_carrying_cargo)
        self.assertEqual(self.start_node.occupied_by, 1)

    def test_agv_battery_integration(self):
        """测试AGV电量集成"""
        initial_charge = self.agv.battery_system.current_charge

        # 模拟移动
        self.agv.moving = True
        self.agv.move({}, [])

        # 电量应该有所消耗
        self.assertLessEqual(self.agv.battery_system.current_charge, initial_charge)

    def test_agv_cargo_handling(self):
        """测试AGV载货处理"""
        # 创建订单
        order = Order("PP01", "AP01")
        self.agv.assign_order(order)

        self.assertEqual(self.agv.current_order, order)

        # 测试上货
        self.agv.current_node = Node("PP01", 200, 200, "pickup")
        self.agv._pickup_cargo()

        self.assertTrue(self.agv.is_carrying_cargo)

        # 测试下货
        self.agv.current_node = Node("AP01", 300, 300, "dropoff")
        self.agv._dropoff_cargo()

        self.assertFalse(self.agv.is_carrying_cargo)
        self.assertEqual(self.agv.total_orders_completed, 1)

    def test_agv_status_reporting(self):
        """测试AGV状态报告"""
        status = self.agv.get_detailed_status()

        self.assertIn('id', status)
        self.assertIn('battery', status)
        self.assertIn('position', status)
        self.assertIn('total_distance', status)
        self.assertEqual(status['id'], 1)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""

    def setUp(self):
        """集成测试设置"""
        # 创建完整的测试环境
        self.nodes = {
            "PP01": Node("PP01", 100, 100, "pickup"),
            "AP01": Node("AP01", 200, 200, "dropoff"),
            "CP01": Node("CP01", 150, 150, "charging"),
            "N01": Node("N01", 50, 50, "normal")
        }

        # 设置节点连接
        for node_id, node in self.nodes.items():
            for other_id, other_node in self.nodes.items():
                if node_id != other_id:
                    distance = ((node.x - other_node.x) ** 2 + (node.y - other_node.y) ** 2) ** 0.5
                    node.add_connection(other_id, distance)

    def test_end_to_end_order_flow(self):
        """测试端到端订单流程"""
        # 创建AGV
        agv = AGV(1, self.nodes["N01"])

        # 创建订单
        order = Order("PP01", "AP01", OrderPriority.HIGH)

        # 分配订单给AGV
        agv.assign_order(order)
        order.assign_to_agv(agv.id)

        # 验证分配
        self.assertEqual(agv.current_order, order)
        self.assertEqual(order.assigned_agv_id, agv.id)
        self.assertEqual(order.status, OrderStatus.ASSIGNED)

        # 开始执行
        order.start_execution()
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)

        # 完成订单
        order.complete()
        self.assertEqual(order.status, OrderStatus.COMPLETED)

    def test_battery_charge_cycle(self):
        """测试完整充电周期"""
        agv = AGV(1, self.nodes["N01"])

        # 设置低电量
        agv.battery_system.current_charge = 20.0

        # 检查是否需要充电
        self.assertTrue(agv.battery_system.needs_charging())

        # 移动到充电站
        agv.current_node = self.nodes["CP01"]
        agv.battery_system.start_charging()

        # 验证充电状态
        self.assertTrue(agv.battery_system.is_charging)
        self.assertEqual(agv.battery_system.get_battery_status(), BatteryStatus.CHARGING)

        # 模拟充电过程
        while not agv.battery_system.is_fully_charged():
            agv.battery_system.update()
            if agv.battery_system.current_charge > 95:
                break

        # 停止充电
        agv.battery_system.stop_charging()
        self.assertFalse(agv.battery_system.is_charging)
        self.assertGreater(agv.battery_system.current_charge, 90)


class TestPerformance(unittest.TestCase):
    """性能测试"""

    def test_order_generation_performance(self):
        """测试订单生成性能"""
        nodes = {}
        for i in range(10):
            nodes[f"PP{i:02d}"] = Node(f"PP{i:02d}", i * 10, i * 10, "pickup")
            nodes[f"AP{i:02d}"] = Node(f"AP{i:02d}", i * 10 + 5, i * 10 + 5, "dropoff")

        generator = OrderGenerator(nodes)

        # 测试生成1000个订单的时间
        start_time = time.time()
        orders = []
        for _ in range(1000):
            order = generator.manual_generate_order()
            orders.append(order)

        generation_time = time.time() - start_time

        # 应该在1秒内完成
        self.assertLess(generation_time, 1.0)
        self.assertEqual(len(orders), 1000)

    def test_battery_update_performance(self):
        """测试电量更新性能"""
        batteries = [BatterySystem() for _ in range(100)]

        # 测试1000次更新的时间
        start_time = time.time()
        for _ in range(1000):
            for battery in batteries:
                battery.update(is_moving=True, is_carrying_cargo=False)

        update_time = time.time() - start_time

        # 应该在1秒内完成
        self.assertLess(update_time, 1.0)


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestOrderSystem,
        TestBatterySystem,
        TestTaskScheduler,
        TestAGV,
        TestSystemIntegration,
        TestPerformance
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result


def run_specific_test(test_name):
    """运行特定测试"""
    # 测试名称映射
    test_mapping = {
        'order': TestOrderSystem,
        'battery': TestBatterySystem,
        'scheduler': TestTaskScheduler,
        'agv': TestAGV,
        'integration': TestSystemIntegration,
        'performance': TestPerformance
    }

    if test_name in test_mapping:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_mapping[test_name])
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
    else:
        print(f"未知的测试名称: {test_name}")
        print(f"可用的测试: {list(test_mapping.keys())}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RCS-Lite AGV增强系统测试套件")
    parser.add_argument("--test", choices=['order', 'battery', 'scheduler', 'agv', 'integration', 'performance', 'all'],
                        default='all', help="要运行的测试")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    print("=" * 60)
    print("RCS-Lite AGV增强仿真系统 - 测试套件")
    print("=" * 60)

    if args.test == 'all':
        print("运行所有测试...")
        result = run_all_tests()
    else:
        print(f"运行 {args.test} 测试...")
        result = run_specific_test(args.test)

    if result:
        print("\n" + "=" * 60)
        print("测试结果:")
        print(f"运行测试: {result.testsRun}")
        print(f"失败: {len(result.failures)}")
        print(f"错误: {len(result.errors)}")
        print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"- {test}")

        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"- {test}")

        print("=" * 60)

        # 返回适当的退出码
        sys.exit(0 if result.wasSuccessful() else 1)