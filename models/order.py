"""
订单系统模型
支持泊松分布生成和订单管理
"""

import random
import time
import uuid
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "待分配"
    ASSIGNED = "已分配"
    IN_PROGRESS = "执行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    EXPIRED = "已过期"


class OrderPriority(Enum):
    """订单优先级枚举"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    EMERGENCY = 10


class Order:
    """订单类"""

    def __init__(self, pickup_node_id, dropoff_node_id, priority=OrderPriority.NORMAL):
        self.id = str(uuid.uuid4())[:8]  # 8位订单ID
        self.pickup_node_id = pickup_node_id
        self.dropoff_node_id = dropoff_node_id
        self.priority = priority
        self.status = OrderStatus.PENDING

        # 时间相关
        self.create_time = time.time()
        self.assign_time = None
        self.start_time = None
        self.complete_time = None

        # 截止时间（基于优先级计算）
        self.deadline = self.create_time + self._calculate_deadline()

        # AGV分配
        self.assigned_agv_id = None

        # 货物信息
        self.cargo_type = self._generate_cargo_type()
        self.weight = random.uniform(10, 100)  # kg

    def _calculate_deadline(self):
        """根据优先级计算截止时间"""
        base_time = 300  # 5分钟基础时间
        priority_multiplier = {
            OrderPriority.EMERGENCY: 0.3,
            OrderPriority.URGENT: 0.5,
            OrderPriority.HIGH: 0.7,
            OrderPriority.NORMAL: 1.0,
            OrderPriority.LOW: 1.5
        }
        return base_time * priority_multiplier.get(self.priority, 1.0)

    def _generate_cargo_type(self):
        """生成随机货物类型"""
        cargo_types = [
            "电子元件", "机械零件", "原材料", "成品包装",
            "化工原料", "食品原料", "医疗用品", "工具设备"
        ]
        return random.choice(cargo_types)

    def assign_to_agv(self, agv_id):
        """分配给AGV"""
        self.assigned_agv_id = agv_id
        self.assign_time = time.time()
        self.status = OrderStatus.ASSIGNED

    def start_execution(self):
        """开始执行"""
        self.start_time = time.time()
        self.status = OrderStatus.IN_PROGRESS

    def complete(self):
        """完成订单"""
        self.complete_time = time.time()
        self.status = OrderStatus.COMPLETED

    def cancel(self):
        """取消订单"""
        self.status = OrderStatus.CANCELLED

    def is_expired(self):
        """检查是否过期"""
        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return False
        return time.time() > self.deadline

    def get_remaining_time(self):
        """获取剩余时间（秒）"""
        return max(0, self.deadline - time.time())

    def get_age(self):
        """获取订单年龄（秒）"""
        return time.time() - self.create_time

    def get_execution_time(self):
        """获取执行时间"""
        if self.complete_time and self.start_time:
            return self.complete_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0

    def get_total_time(self):
        """获取总时间（从创建到完成）"""
        if self.complete_time:
            return self.complete_time - self.create_time
        return time.time() - self.create_time

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'pickup_node': self.pickup_node_id,
            'dropoff_node': self.dropoff_node_id,
            'priority': self.priority.name,
            'status': self.status.value,
            'cargo_type': self.cargo_type,
            'weight': self.weight,
            'create_time': self.create_time,
            'deadline': self.deadline,
            'remaining_time': self.get_remaining_time(),
            'assigned_agv': self.assigned_agv_id
        }

    def __str__(self):
        return f"Order {self.id}: {self.pickup_node_id}→{self.dropoff_node_id} [{self.status.value}]"


class OrderGenerator(QObject):
    """订单生成器 - 使用泊松分布"""

    order_generated = pyqtSignal(object)  # 新订单信号

    def __init__(self, nodes_dict):
        super().__init__()
        self.nodes_dict = nodes_dict
        self.is_active = False

        # 泊松分布参数
        self.lambda_rate = 0.5  # 每分钟平均订单数
        self.next_order_time = 0

        # 节点筛选
        self.pickup_nodes = self._get_nodes_by_type('pickup')
        self.dropoff_nodes = self._get_nodes_by_type('dropoff')

        # 统计信息
        self.total_generated = 0
        self.last_generation_time = time.time()

    def _get_nodes_by_type(self, node_type):
        """获取指定类型的节点"""
        return [node_id for node_id, node in self.nodes_dict.items()
                if node.node_type == node_type]

    def set_generation_rate(self, lambda_rate):
        """设置生成速率（每分钟平均订单数）"""
        self.lambda_rate = max(0.1, min(10.0, lambda_rate))
        print(f"订单生成速率设置为: {self.lambda_rate:.1f} 订单/分钟")

    def start_generation(self):
        """开始生成订单"""
        self.is_active = True
        self.next_order_time = time.time() + self._get_next_interval()
        print(f"订单生成器已启动，速率: {self.lambda_rate:.1f} 订单/分钟")

    def stop_generation(self):
        """停止生成订单"""
        self.is_active = False
        print("订单生成器已停止")

    def update(self):
        """更新方法，需要定期调用"""
        if not self.is_active:
            return

        current_time = time.time()

        # 检查是否到了生成下一个订单的时间
        if current_time >= self.next_order_time:
            self._generate_order()
            self.next_order_time = current_time + self._get_next_interval()

    def _get_next_interval(self):
        """获取下一个订单间隔（泊松分布）"""
        # 将每分钟的速率转换为每秒
        rate_per_second = self.lambda_rate / 60.0

        # 使用指数分布（泊松过程的间隔时间）
        if rate_per_second > 0:
            interval = random.expovariate(rate_per_second)
            # 限制间隔在合理范围内
            return max(5.0, min(300.0, interval))  # 5秒到5分钟
        return 60.0  # 默认1分钟

    def _generate_order(self):
        """生成一个新订单"""
        if not self.pickup_nodes or not self.dropoff_nodes:
            print("警告：没有可用的上货点或下货点")
            return None

        # 随机选择上货点和下货点
        pickup_node = random.choice(self.pickup_nodes)
        dropoff_node = random.choice(self.dropoff_nodes)

        # 确保不是同一个节点
        if pickup_node == dropoff_node and len(self.dropoff_nodes) > 1:
            dropoff_nodes_copy = self.dropoff_nodes.copy()
            dropoff_nodes_copy.remove(pickup_node)
            dropoff_node = random.choice(dropoff_nodes_copy)

        # 生成优先级（大部分是普通优先级）
        priority_weights = {
            OrderPriority.LOW: 10,
            OrderPriority.NORMAL: 60,
            OrderPriority.HIGH: 20,
            OrderPriority.URGENT: 8,
            OrderPriority.EMERGENCY: 2
        }
        priority = random.choices(
            list(priority_weights.keys()),
            weights=list(priority_weights.values())
        )[0]

        # 创建订单
        order = Order(pickup_node, dropoff_node, priority)
        self.total_generated += 1

        print(f"生成新订单: {order}")

        # 发送信号
        self.order_generated.emit(order)

        return order

    def manual_generate_order(self, pickup_node_id=None, dropoff_node_id=None, priority=None):
        """手动生成订单"""
        pickup_node = pickup_node_id or random.choice(self.pickup_nodes)
        dropoff_node = dropoff_node_id or random.choice(self.dropoff_nodes)
        priority = priority or OrderPriority.NORMAL

        order = Order(pickup_node, dropoff_node, priority)
        self.total_generated += 1

        print(f"手动生成订单: {order}")
        self.order_generated.emit(order)

        return order

    def get_statistics(self):
        """获取统计信息"""
        current_time = time.time()
        runtime = max(1, current_time - self.last_generation_time)

        return {
            'total_generated': self.total_generated,
            'generation_rate': self.lambda_rate,
            'actual_rate': (self.total_generated / runtime) * 60,  # 每分钟
            'pickup_nodes_count': len(self.pickup_nodes),
            'dropoff_nodes_count': len(self.dropoff_nodes),
            'is_active': self.is_active
        }