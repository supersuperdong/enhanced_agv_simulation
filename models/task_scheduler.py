"""
修复后的任务调度系统 - 解决竞态条件问题
"""

import time
import heapq
from collections import deque
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from .order import Order, OrderStatus, OrderPriority


class SchedulingStrategy(Enum):
    """调度策略枚举"""
    FIFO = "先进先出"
    PRIORITY = "优先级调度"
    SHORTEST_JOB = "最短作业优先"
    NEAREST_FIRST = "最近距离优先"
    DEADLINE_FIRST = "截止时间优先"
    BALANCED = "平衡调度"


class TaskType(Enum):
    """任务类型枚举"""
    TRANSPORT = "运输任务"
    CHARGING = "充电任务"
    MAINTENANCE = "维护任务"
    RETURN_HOME = "回仓任务"


class Task:
    """任务类"""

    def __init__(self, task_type, agv_id, target_node_id, order=None):
        self.task_type = task_type
        self.agv_id = agv_id
        self.target_node_id = target_node_id
        self.order = order

        self.create_time = time.time()
        self.start_time = None
        self.complete_time = None
        self.estimated_duration = self._estimate_duration()

        # 任务状态
        self.is_started = False
        self.is_completed = False
        self.is_cancelled = False

        # 任务阶段标记 - 关键修复点
        self.picked_up = False
        self.delivered = False

    def _estimate_duration(self):
        """估算任务持续时间"""
        if self.task_type == TaskType.CHARGING:
            return 120
        elif self.task_type == TaskType.TRANSPORT:
            return 60
        elif self.task_type == TaskType.MAINTENANCE:
            return 300
        else:
            return 30

    def start(self):
        """开始任务"""
        self.is_started = True
        self.start_time = time.time()
        if self.order:
            self.order.start_execution()

    def complete(self):
        """完成任务"""
        self.is_completed = True
        self.complete_time = time.time()
        if self.order:
            self.order.complete()

    def cancel(self):
        """取消任务"""
        self.is_cancelled = True
        if self.order:
            self.order.cancel()

    def get_priority_score(self):
        """获取优先级分数（用于排序）"""
        base_score = 0

        if self.task_type == TaskType.CHARGING:
            base_score = 1000
        elif self.order:
            priority_scores = {
                OrderPriority.EMERGENCY: 900,
                OrderPriority.URGENT: 700,
                OrderPriority.HIGH: 500,
                OrderPriority.NORMAL: 300,
                OrderPriority.LOW: 100
            }
            base_score = priority_scores.get(self.order.priority, 300)

        age_factor = min(100, (time.time() - self.create_time) / 60)
        return base_score + age_factor


class OrderQueue:
    """订单队列管理器"""

    def __init__(self):
        self.pending_orders = deque()
        self.processing_orders = {}  # agv_id -> order
        self.completed_orders = []
        self.cancelled_orders = []

        # 统计信息
        self.total_orders = 0
        self.completion_times = []
        self.waiting_times = []

    def add_order(self, order):
        """添加新订单"""
        self.pending_orders.append(order)
        self.total_orders += 1
        print(f"新订单加入队列: {order}")

    def get_next_order(self, strategy=SchedulingStrategy.PRIORITY):
        """获取下一个订单"""
        if not self.pending_orders:
            return None

        if strategy == SchedulingStrategy.FIFO:
            return self.pending_orders.popleft()

        elif strategy == SchedulingStrategy.PRIORITY:
            orders_list = list(self.pending_orders)
            orders_list.sort(key=lambda o: (o.priority.value, o.create_time), reverse=True)
            self.pending_orders.clear()
            self.pending_orders.extend(orders_list[1:])
            return orders_list[0]

        elif strategy == SchedulingStrategy.DEADLINE_FIRST:
            orders_list = list(self.pending_orders)
            orders_list.sort(key=lambda o: o.deadline)
            self.pending_orders.clear()
            self.pending_orders.extend(orders_list[1:])
            return orders_list[0]

        else:
            return self.pending_orders.popleft()

    def assign_order(self, order, agv_id):
        """分配订单给AGV"""
        order.assign_to_agv(agv_id)
        self.processing_orders[agv_id] = order
        waiting_time = time.time() - order.create_time
        self.waiting_times.append(waiting_time)

    def complete_order(self, agv_id):
        """完成订单"""
        if agv_id in self.processing_orders:
            order = self.processing_orders.pop(agv_id)
            order.complete()
            self.completed_orders.append(order)

            completion_time = order.get_total_time()
            self.completion_times.append(completion_time)

            print(f"订单完成: {order}")

    def cancel_order(self, order_id):
        """取消订单"""
        # 从待处理队列中查找并移除
        for i, order in enumerate(self.pending_orders):
            if order.id == order_id:
                order.cancel()
                self.cancelled_orders.append(order)
                del self.pending_orders[i]
                return True

        # 从处理中订单查找并取消
        for agv_id, order in self.processing_orders.items():
            if order.id == order_id:
                order.cancel()
                self.cancelled_orders.append(order)
                del self.processing_orders[agv_id]
                return True

        return False

    def clean_expired_orders(self):
        """清理过期订单"""
        expired_count = 0

        current_orders = list(self.pending_orders)
        self.pending_orders.clear()

        for order in current_orders:
            if order.is_expired():
                order.status = OrderStatus.EXPIRED
                self.cancelled_orders.append(order)
                expired_count += 1
            else:
                self.pending_orders.append(order)

        if expired_count > 0:
            print(f"清理了 {expired_count} 个过期订单")

        return expired_count

    def get_statistics(self):
        """获取统计信息"""
        avg_waiting_time = sum(self.waiting_times) / len(self.waiting_times) if self.waiting_times else 0
        avg_completion_time = sum(self.completion_times) / len(self.completion_times) if self.completion_times else 0

        return {
            'pending_count': len(self.pending_orders),
            'processing_count': len(self.processing_orders),
            'completed_count': len(self.completed_orders),
            'cancelled_count': len(self.cancelled_orders),
            'total_orders': self.total_orders,
            'avg_waiting_time': avg_waiting_time,
            'avg_completion_time': avg_completion_time,
            'completion_rate': len(self.completed_orders) / max(1, self.total_orders)
        }


class TaskScheduler(QObject):
    """任务调度器 - 修复版本"""

    task_assigned = pyqtSignal(str, object)
    task_completed = pyqtSignal(str, object)

    def __init__(self, simulation_widget):
        super().__init__()
        self.simulation_widget = simulation_widget
        self.order_queue = OrderQueue()

        # 调度参数
        self.scheduling_strategy = SchedulingStrategy.BALANCED
        self.assignment_interval = 2.0
        self.last_assignment_time = time.time()

        # AGV状态跟踪
        self.agv_tasks = {}  # agv_id -> current_task
        self.agv_capabilities = {}

        # 性能统计
        self.total_assignments = 0
        self.failed_assignments = 0

    def add_order(self, order):
        """添加新订单"""
        self.order_queue.add_order(order)

    def update(self):
        """更新调度器（定期调用）"""
        current_time = time.time()

        # 清理过期订单
        self.order_queue.clean_expired_orders()

        # 检查是否需要分配任务
        if current_time - self.last_assignment_time >= self.assignment_interval:
            self._process_task_assignments()
            self.last_assignment_time = current_time

        # 检查任务完成状态 - 修复版本
        self._check_task_completion_safe()

        # 处理充电需求
        self._handle_charging_needs()

    def _check_task_completion_safe(self):
        """安全检查任务完成状态 - 修复版本"""
        completed_tasks = []

        for agv_id, task in list(self.agv_tasks.items()):  # 使用list()避免字典在迭代时被修改
            agv = self._find_agv_by_id(agv_id)
            if not agv:
                completed_tasks.append(agv_id)
                continue

            try:
                # 检查运输任务完成条件
                if (task.task_type == TaskType.TRANSPORT and
                        task.order and not agv.moving):

                    # 检查是否到达上货点
                    if (agv.current_node.id == task.order.pickup_node_id and
                            not task.picked_up and not agv.is_carrying_cargo):
                        task.picked_up = True
                        print(f"AGV#{agv_id} 到达上货点 {task.order.pickup_node_id}")

                        # 规划到下货点的路径
                        self.simulation_widget.send_agv_to_target(
                            agv_id, task.order.dropoff_node_id, 'a_star'
                        )

                    # 检查是否到达下货点并完成任务 - 关键修复点
                    elif agv.is_task_completed():  # 使用AGV提供的安全方法
                        # 任务完成
                        task.complete()
                        self.order_queue.complete_order(agv_id)

                        # 清理AGV的订单状态
                        agv.clear_current_order()

                        completed_tasks.append(agv_id)
                        print(f"AGV#{agv_id} 完成运输任务: {task.order}")

                # 检查充电任务完成条件
                elif (task.task_type == TaskType.CHARGING and
                      agv.battery_system.is_fully_charged()):
                    task.complete()
                    completed_tasks.append(agv_id)
                    print(f"AGV#{agv_id} 充电完成")

            except Exception as e:
                print(f"检查任务完成状态时发生错误 (AGV#{agv_id}): {e}")
                # 发生错误时，安全地移除任务避免程序崩溃
                completed_tasks.append(agv_id)

        # 清理完成的任务
        for agv_id in completed_tasks:
            if agv_id in self.agv_tasks:
                task = self.agv_tasks.pop(agv_id)
                self.task_completed.emit(agv_id, task)

    def _process_task_assignments(self):
        """处理任务分配"""
        available_agvs = self._get_available_agvs()

        if not available_agvs:
            return

        # 获取待分配的订单
        while available_agvs and self.order_queue.pending_orders:
            order = self.order_queue.get_next_order(self.scheduling_strategy)
            if not order:
                break

            # 选择最适合的AGV
            best_agv = self._select_best_agv(order, available_agvs)
            if best_agv:
                self._assign_transport_task(best_agv, order)
                available_agvs.remove(best_agv)

    def _get_available_agvs(self):
        """获取可用的AGV列表"""
        available_agvs = []

        for agv in self.simulation_widget.agvs:
            if (agv.id not in self.agv_tasks and
                    not agv.moving and
                    agv.battery_system.can_move() and
                    not agv.battery_system.is_charging):
                available_agvs.append(agv)

        return available_agvs

    def _select_best_agv(self, order, available_agvs):
        """选择最适合的AGV"""
        if not available_agvs:
            return None

        best_agv = None
        best_score = float('-inf')

        for agv in available_agvs:
            score = self._calculate_agv_score(agv, order)
            if score > best_score:
                best_score = score
                best_agv = agv

        return best_agv

    def _calculate_agv_score(self, agv, order):
        """计算AGV适合度分数"""
        score = 0

        # 距离因子
        pickup_node = self.simulation_widget.nodes.get(order.pickup_node_id)
        if pickup_node:
            distance = ((agv.x - pickup_node.x) ** 2 + (agv.y - pickup_node.y) ** 2) ** 0.5
            distance_score = max(0, 1000 - distance)
            score += distance_score

        # 电量因子
        battery_score = agv.battery_system.current_charge * 2
        score += battery_score

        # 任务能力因子
        estimated_task_time = self._estimate_task_time(agv, order)
        if agv.battery_system.can_complete_task(estimated_task_time / 60):
            score += 200
        else:
            score -= 500

        return score

    def _estimate_task_time(self, agv, order):
        """估算任务完成时间（秒）"""
        return 90  # 简化估算

    def _assign_transport_task(self, agv, order):
        """分配运输任务"""
        try:
            # 创建运输任务
            task = Task(TaskType.TRANSPORT, agv.id, order.pickup_node_id, order)

            # 规划到上货点的路径
            success = self.simulation_widget.send_agv_to_target(
                agv.id, order.pickup_node_id, 'a_star'
            )

            if success:
                self.agv_tasks[agv.id] = task
                self.order_queue.assign_order(order, agv.id)
                agv.assign_order(order)  # 使用修复后的方法
                task.start()

                self.total_assignments += 1
                self.task_assigned.emit(agv.id, task)

                print(f"分配运输任务: AGV#{agv.id} -> 订单{order.id}")
                return True
            else:
                self.failed_assignments += 1
                print(f"任务分配失败: AGV#{agv.id} 无法到达 {order.pickup_node_id}")
                return False

        except Exception as e:
            print(f"分配任务时发生错误: {e}")
            self.failed_assignments += 1
            return False

    def _handle_charging_needs(self):
        """处理充电需求"""
        for agv in self.simulation_widget.agvs:
            if (agv.battery_system.needs_immediate_charging() and
                    agv.id not in self.agv_tasks and
                    not agv.moving):
                self._assign_charging_task(agv)

    def _assign_charging_task(self, agv):
        """分配充电任务"""
        charging_stations = [node_id for node_id, node in self.simulation_widget.nodes.items()
                             if node.node_type == 'charging']

        if not charging_stations:
            print(f"警告: 没有可用的充电站")
            return False

        # 选择最近的充电站
        best_station = None
        best_distance = float('inf')

        for station_id in charging_stations:
            station_node = self.simulation_widget.nodes[station_id]
            distance = ((agv.x - station_node.x) ** 2 + (agv.y - station_node.y) ** 2) ** 0.5

            if distance < best_distance:
                best_distance = distance
                best_station = station_id

        if best_station:
            task = Task(TaskType.CHARGING, agv.id, best_station)

            success = self.simulation_widget.send_agv_to_target(
                agv.id, best_station, 'a_star'
            )

            if success:
                self.agv_tasks[agv.id] = task
                task.start()
                print(f"分配充电任务: AGV#{agv.id} -> 充电站{best_station}")
                return True

        return False

    def _find_agv_by_id(self, agv_id):
        """查找AGV"""
        return next((agv for agv in self.simulation_widget.agvs if agv.id == agv_id), None)

    def get_statistics(self):
        """获取调度统计信息"""
        queue_stats = self.order_queue.get_statistics()

        return {
            'scheduling_strategy': self.scheduling_strategy.value,
            'total_assignments': self.total_assignments,
            'failed_assignments': self.failed_assignments,
            'success_rate': self.total_assignments / max(1, self.total_assignments + self.failed_assignments),
            'active_tasks': len(self.agv_tasks),
            'queue_stats': queue_stats
        }

    def set_scheduling_strategy(self, strategy):
        """设置调度策略"""
        self.scheduling_strategy = strategy
        print(f"调度策略更改为: {strategy.value}")

    def force_assign_order(self, order_id, agv_id):
        """强制分配订单给指定AGV"""
        for order in self.order_queue.pending_orders:
            if order.id == order_id:
                agv = self._find_agv_by_id(agv_id)
                if agv and agv.id not in self.agv_tasks:
                    self.order_queue.pending_orders.remove(order)
                    return self._assign_transport_task(agv, order)
        return False