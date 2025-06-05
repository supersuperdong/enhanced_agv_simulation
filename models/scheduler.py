"""
调度系统 - 增强版，支持死锁检测和智能充电分配
"""

import random
import math
from models.order import Order
from algorithms.path_planner import PathPlanner


class DeadlockDetector:
    """死锁检测器"""

    def detect_deadlock(self, agvs):
        """检测死锁情况"""
        deadlocks = []

        for i, agv1 in enumerate(agvs):
            if not agv1.moving or not agv1.target_node:
                continue

            for agv2 in agvs[i+1:]:
                if not agv2.moving or not agv2.target_node:
                    continue

                # 检测相向而行的情况
                if (agv1.current_node.id == agv2.target_node.id and
                    agv2.current_node.id == agv1.target_node.id):
                    deadlocks.append((agv1, agv2))

        return deadlocks

    def resolve_deadlock(self, agv1, agv2, nodes):
        """解决死锁"""
        # 计算优先级
        priority1 = self._calculate_priority(agv1)
        priority2 = self._calculate_priority(agv2)

        # 低优先级的AGV让路
        if priority1 > priority2:
            return self._find_bypass_route(agv2, agv1, nodes)
        else:
            return self._find_bypass_route(agv1, agv2, nodes)

    def _calculate_priority(self, agv):
        """计算AGV优先级"""
        priority = 0

        # 载货优先
        if agv.is_loaded:
            priority += 100

        # 低电量优先
        priority += (100 - agv.battery)

        # ID小的优先（平局决定）
        priority -= agv.id * 0.1

        return priority

    def _find_bypass_route(self, yielding_agv, priority_agv, nodes):
        """为让路的AGV寻找绕行路径"""
        # 找到当前节点的所有邻居
        current_node = yielding_agv.current_node
        neighbors = [nodes[nid] for nid in current_node.connections
                    if nid != yielding_agv.target_node.id and
                    nodes[nid].occupied_by is None]

        if neighbors:
            # 选择一个临时节点
            temp_node = random.choice(neighbors)
            return temp_node
        return None


class Scheduler:
    """AGV调度系统 - 增强版"""

    def __init__(self):
        self.orders = []  # 所有订单
        self.pending_orders = []  # 待分配订单
        self.order_counter = 1
        self.charging_reservations = {}  # 充电点预约 {node_id: set(agv_ids)}
        self.deadlock_detector = DeadlockDetector()

    def create_order(self, pickup_node, dropoff_node):
        """创建新订单"""
        order = Order(self.order_counter, pickup_node, dropoff_node)
        self.order_counter += 1
        self.orders.append(order)
        self.pending_orders.append(order)
        print(f"订单#{order.id}创建: {pickup_node} → {dropoff_node}")
        return order

    def create_random_order(self, nodes):
        """创建随机订单"""
        pickup_nodes = [n for n in nodes.values() if n.node_type == 'pickup']
        dropoff_nodes = [n for n in nodes.values() if n.node_type == 'dropoff']

        if pickup_nodes and dropoff_nodes:
            pickup = random.choice(pickup_nodes)
            dropoff = random.choice(dropoff_nodes)
            return self.create_order(pickup.id, dropoff.id)
        return None

    def assign_orders(self, agvs, nodes):
        """分配订单给AGV"""
        if not self.pending_orders:
            return

        # 找出可用的AGV（空闲、电量充足、不在充电）
        available_agvs = []
        for agv in agvs:
            if (not agv.current_order and
                not agv.is_charging and
                agv.battery > 30 and
                not agv.is_loading):
                available_agvs.append(agv)

        if not available_agvs:
            return

        # 分配订单
        for order in self.pending_orders[:]:
            if not available_agvs:
                break

            # 选择最佳AGV（考虑距离和电量）
            best_agv = None
            best_score = float('inf')
            best_path = None

            for agv in available_agvs:
                # 计算到上料点的路径
                path = PathPlanner.plan_path(
                    'a_star', nodes, agv.current_node.id, order.pickup_node, agvs
                )

                if path:
                    # 评分：距离 + 电量惩罚
                    distance = len(path)
                    battery_penalty = (100 - agv.battery) * 0.1
                    score = distance + battery_penalty

                    if score < best_score:
                        best_score = score
                        best_agv = agv
                        best_path = path

            if best_agv and best_path:
                # 计算从上料点到下料点的路径
                drop_path = PathPlanner.plan_path(
                    'a_star', nodes, order.pickup_node, order.dropoff_node, agvs
                )

                if drop_path:
                    # 分配订单
                    order.pickup_path = best_path
                    order.drop_path = drop_path
                    order.assign_to_agv(best_agv)
                    best_agv.set_path(best_path)

                    print(f"订单#{order.id}分配给AGV#{best_agv.id}")

                    self.pending_orders.remove(order)
                    available_agvs.remove(best_agv)

    def check_idle_agvs(self, agvs, nodes):
        """检查空闲AGV并安排充电"""
        for agv in agvs:
            if (not agv.current_order and
                not agv.moving and
                not agv.is_charging and
                not agv.path):

                # 如果电量低或在主干道上，去充电
                if agv.battery < 80 or self._is_on_main_road(agv, nodes):
                    best_charging_node = self._find_best_charging_node(agv, nodes, agvs)

                    if best_charging_node:
                        path = PathPlanner.plan_path(
                            'a_star', nodes, agv.current_node.id, best_charging_node.id, agvs
                        )

                        if path:
                            agv.set_path(path)
                            agv.need_charge = True
                            agv.status = "前往充电"

                            # 预约充电点
                            if best_charging_node.id not in self.charging_reservations:
                                self.charging_reservations[best_charging_node.id] = set()
                            self.charging_reservations[best_charging_node.id].add(agv.id)

    def check_and_resolve_deadlocks(self, agvs, nodes):
        """检查并解决死锁"""
        deadlocks = self.deadlock_detector.detect_deadlock(agvs)

        for agv1, agv2 in deadlocks:
            # 找到让路节点
            bypass_node = self.deadlock_detector.resolve_deadlock(agv1, agv2, nodes)

            if bypass_node:
                # 计算哪个AGV需要让路
                priority1 = self.deadlock_detector._calculate_priority(agv1)
                priority2 = self.deadlock_detector._calculate_priority(agv2)

                yielding_agv = agv2 if priority1 > priority2 else agv1

                # 临时改变目标
                original_target = yielding_agv.target_node
                original_path = yielding_agv.path

                # 设置临时目标
                yielding_agv.set_target(bypass_node)
                yielding_agv._temp_bypass = True
                yielding_agv._original_target = original_target
                yielding_agv._original_path = original_path

                print(f"AGV#{yielding_agv.id}临时让路给AGV#{(agv1.id if yielding_agv == agv2 else agv2.id)}")

    def _find_best_charging_node(self, agv, nodes, agvs):
        """找到最佳充电点（考虑距离和预约情况）"""
        charging_nodes = [n for n in nodes.values() if n.node_type == 'charging']
        if not charging_nodes:
            return None

        best_node = None
        best_score = float('inf')

        for node in charging_nodes:
            # 检查预约数量
            reservations = len(self.charging_reservations.get(node.id, set()))

            # 如果已经有AGV在充电或预约，增加惩罚
            if node.occupied_by is not None:
                reservations += 2

            # 计算距离
            distance = self._calculate_distance(agv.current_node, node)

            # 综合评分：距离 + 预约惩罚
            score = distance + reservations * 50

            if score < best_score:
                best_score = score
                best_node = node

        return best_node

    def _calculate_distance(self, node1, node2):
        """计算两个节点间的欧氏距离"""
        return math.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)

    def _is_on_main_road(self, agv, nodes):
        """判断AGV是否在主干道上"""
        # 简单判断：连接数大于2的节点视为主干道
        return len(agv.current_node.connections) > 2

    def update_charging_reservations(self, agvs):
        """更新充电点预约状态"""
        # 清理已完成充电的预约
        for node_id in list(self.charging_reservations.keys()):
            self.charging_reservations[node_id] = {
                agv_id for agv_id in self.charging_reservations[node_id]
                if any(agv.id == agv_id and (agv.need_charge or agv.is_charging)
                      for agv in agvs)
            }

            if not self.charging_reservations[node_id]:
                del self.charging_reservations[node_id]

    def get_statistics(self):
        """获取统计信息"""
        stats = {
            "总订单": len(self.orders),
            "待分配": len(self.pending_orders),
            "进行中": len([o for o in self.orders if o.status in ["已分配", "取货中", "运输中", "卸货中"]]),
            "已完成": len([o for o in self.orders if o.status == "已完成"])
        }

        # 添加订单时间统计
        if self.orders:
            completed_orders = [o for o in self.orders if o.status == "已完成"]
            if completed_orders:
                avg_time = sum(o.get_total_time() for o in completed_orders) / len(completed_orders)
                stats["平均完成时间"] = f"{avg_time:.1f}秒"

        return stats