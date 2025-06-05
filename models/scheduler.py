"""
调度系统
"""

import random
from models.order import Order
from algorithms.path_planner import PathPlanner


class Scheduler:
    """AGV调度系统"""

    def __init__(self):
        self.orders = []  # 所有订单
        self.pending_orders = []  # 待分配订单
        self.order_counter = 1

    def create_order(self, pickup_node, dropoff_node):
        """创建新订单"""
        order = Order(self.order_counter, pickup_node, dropoff_node)
        self.order_counter += 1
        self.orders.append(order)
        self.pending_orders.append(order)
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
                    'dijkstra', nodes, agv.current_node.id, order.pickup_node, agvs
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
                    'dijkstra', nodes, order.pickup_node, order.dropoff_node, agvs
                )

                if drop_path:
                    # 分配订单
                    order.pickup_path = best_path
                    order.drop_path = drop_path
                    order.assign_to_agv(best_agv)
                    best_agv.set_path(best_path)

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
                    # 找最近的充电点
                    charging_nodes = [n for n in nodes.values() if n.node_type == 'charging']
                    if charging_nodes:
                        best_node = None
                        best_path = None
                        min_distance = float('inf')

                        for node in charging_nodes:
                            path = PathPlanner.plan_path(
                                'dijkstra', nodes, agv.current_node.id, node.id, agvs
                            )
                            if path and len(path) < min_distance:
                                min_distance = len(path)
                                best_node = node
                                best_path = path

                        if best_path:
                            agv.set_path(best_path)
                            agv.need_charge = True
                            agv.status = "前往充电"

    def _is_on_main_road(self, agv, nodes):
        """判断AGV是否在主干道上"""
        # 简单判断：连接数大于2的节点视为主干道
        return len(agv.current_node.connections) > 2

    def get_statistics(self):
        """获取统计信息"""
        stats = {
            "总订单": len(self.orders),
            "待分配": len(self.pending_orders),
            "进行中": len([o for o in self.orders if o.status in ["已分配", "取货中", "运输中", "卸货中"]]),
            "已完成": len([o for o in self.orders if o.status == "已完成"])
        }
        return stats