"""
增强的AGV模型类 - 集成电量系统和订单处理
"""

import math
import random
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QRectF

from .battery_system import BatterySystem


class EnhancedAGV:
    """增强的AGV自动导引车 - 集成电量和订单系统"""

    def __init__(self, agv_id, start_node):
        # 基本属性
        self.id = agv_id
        self.name = f"AGV-{agv_id}"

        # 位置属性
        self.current_node = start_node
        self.target_node = None
        self.x = start_node.x
        self.y = start_node.y

        # 外观属性
        self.width = 24
        self.height = 24
        self.color = QColor(255, 140, 0)

        # 运动属性
        self.angle = 0
        self.target_angle = 0
        self.speed = 2
        self.moving = False

        # 路径属性
        self.path = []
        self.path_index = 0
        self.task_target = None

        # 状态属性
        self.status = "待机"
        self.waiting = False
        self.collision_buffer = 25
        self.wait_counter = 0
        self.priority = 5

        # 电量系统
        self.battery_system = BatterySystem(
            capacity=100.0,
            initial_charge=random.uniform(80, 100)  # 随机初始电量
        )

        # 载货状态
        self.is_carrying_cargo = False
        self.current_order = None

        # 充电状态
        self.is_at_charging_station = False
        self.charging_station_id = None

        # 性能统计
        self.total_distance_traveled = 0.0
        self.total_orders_completed = 0
        self.total_charging_time = 0.0

        # 占用起始节点
        start_node.occupied_by = self.id

    def set_path(self, path):
        """设置路径"""
        if len(path) > 1:
            self.path = path
            self.path_index = 0
            self.task_target = path[-1]
            self.status = f"前往节点 {self.task_target}"
            self.waiting = False
            self.wait_counter = 0

    def set_target(self, node):
        """设置移动目标"""
        if node.id not in self.current_node.connections:
            return False

        if node.occupied_by is not None and node.occupied_by != self.id:
            self.status = f"等待节点 {node.id}"
            self.waiting = True
            return False

        self.target_node = node
        node.reserved_by = self.id
        node.reservation_time = 50

        # 计算朝向
        dx = node.x - self.x
        dy = node.y - self.y
        self.target_angle = self._normalize_angle(math.degrees(math.atan2(dy, dx)))

        self.moving = True
        self.waiting = False
        self.status = f"移动至节点 {node.id}"
        return True

    def move(self, nodes, other_agvs):
        """移动逻辑 - 集成电量检查"""
        # 更新电量系统
        self.battery_system.update(
            is_moving=self.moving,
            is_carrying_cargo=self.is_carrying_cargo
        )

        # 检查电量是否足够移动
        if not self.battery_system.can_move():
            self._handle_battery_empty()
            return

        # 检查是否在充电站
        self._check_charging_station(nodes)

        # 如果电量危险且不在充电，优先充电
        if (self.battery_system.needs_immediate_charging() and
                not self.battery_system.is_charging and
                not self.is_at_charging_station):
            self._emergency_charging_mode()
            return

        # 正常移动逻辑
        if not self.moving or not self.target_node:
            self._try_next_path_step(nodes)
            return

        # 检查目标节点占用
        if (self.target_node.occupied_by is not None and
                self.target_node.occupied_by != self.id):
            self.waiting = True
            self.wait_counter += 1
            self.status = f"等待节点 {self.target_node.id}"
            return

        # 旋转到目标角度
        if self._rotate_to_target():
            # 移动到目标
            self._move_to_target(other_agvs)

    def _handle_battery_empty(self):
        """处理电量耗尽"""
        if self.moving:
            self.moving = False
            self.target_node = None
            self.status = "电量耗尽，无法移动"
            print(f"⚠️ AGV#{self.id} 电量耗尽，停止移动")

    def _check_charging_station(self, nodes):
        """检查是否在充电站"""
        current_node = self.current_node

        # 检查当前节点是否为充电站
        if current_node.node_type == 'charging':
            if not self.is_at_charging_station:
                self.is_at_charging_station = True
                self.charging_station_id = current_node.id
                print(f"AGV#{self.id} 到达充电站 {current_node.id}")

            # 如果需要充电，开始充电
            if (self.battery_system.needs_charging() and
                    not self.battery_system.is_charging):
                self.battery_system.start_charging()
                self.status = f"在充电站 {current_node.id} 充电中"
        else:
            if self.is_at_charging_station:
                self.is_at_charging_station = False
                self.charging_station_id = None
                if self.battery_system.is_charging:
                    self.battery_system.stop_charging()

    def _emergency_charging_mode(self):
        """紧急充电模式"""
        self.status = "紧急充电模式 - 电量危险"
        if self.moving:
            self.moving = False
            self.target_node = None

    def _try_next_path_step(self, nodes):
        """尝试执行路径中的下一步"""
        if not self.path or self.path_index + 1 >= len(self.path):
            return

        next_node_id = self.path[self.path_index + 1]
        if next_node_id in nodes:
            next_node = nodes[next_node_id]
            if next_node.occupied_by is None or next_node.occupied_by == self.id:
                if self.set_target(next_node):
                    self.wait_counter = 0
            else:
                self.waiting = True
                self.wait_counter += 1

    def _rotate_to_target(self):
        """旋转到目标角度"""
        self.angle = self._normalize_angle(self.angle)
        self.target_angle = self._normalize_angle(self.target_angle)

        diff = self.target_angle - self.angle
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        if abs(diff) <= 3:
            self.angle = self.target_angle
            return True

        rotation_step = 3
        self.angle += rotation_step if diff > 0 else -rotation_step
        self.angle = self._normalize_angle(self.angle)
        return False

    def _move_to_target(self, other_agvs):
        """移动到目标节点"""
        dx = self.target_node.x - self.x
        dy = self.target_node.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < self.speed:
            self._arrive_at_target()
        else:
            # 检查碰撞
            future_x = self.x + self.speed * dx / distance
            future_y = self.y + self.speed * dy / distance

            if not self._check_collision_at(future_x, future_y, other_agvs):
                # 记录移动距离
                self.total_distance_traveled += self.speed

                self.x = future_x
                self.y = future_y
                self.waiting = False
                self.wait_counter = 0
            else:
                self.waiting = True
                self.wait_counter += 1
                self.status = "避让其他AGV"

    def _arrive_at_target(self):
        """到达目标节点"""
        # 释放当前节点
        if self.current_node and self.current_node.occupied_by == self.id:
            self.current_node.occupied_by = None

        # 更新位置
        self.x = self.target_node.x
        self.y = self.target_node.y
        self.current_node = self.target_node
        self.target_node = None
        self.moving = False

        # 占用新节点
        self.current_node.occupied_by = self.id
        if self.current_node.reserved_by == self.id:
            self.current_node.reserved_by = None

        # 处理订单相关逻辑
        self._handle_order_progress()

        # 更新路径状态
        if self.path:
            self.path_index += 1
            if self.path_index >= len(self.path) - 1:
                self.status = f"已到达 {self.current_node.id}"
                self.path = []
                self.path_index = 0
                self.task_target = None
            else:
                self.status = f"路径中 {self.current_node.id}"

    def _handle_order_progress(self):
        """处理订单进度"""
        if not self.current_order:
            return

        current_node_id = self.current_node.id

        # 检查是否到达上货点
        if (current_node_id == self.current_order.pickup_node_id and
                not self.is_carrying_cargo):
            self._pickup_cargo()

        # 检查是否到达下货点
        elif (current_node_id == self.current_order.dropoff_node_id and
              self.is_carrying_cargo):
            self._dropoff_cargo()

    def _pickup_cargo(self):
        """上货"""
        self.is_carrying_cargo = True
        self.status = f"在 {self.current_node.id} 上货"
        print(f"AGV#{self.id} 在节点 {self.current_node.id} 上货")

    def _dropoff_cargo(self):
        """下货"""
        self.is_carrying_cargo = False
        self.total_orders_completed += 1

        if self.current_order:
            print(f"AGV#{self.id} 在节点 {self.current_node.id} 完成订单 {self.current_order.id}")
            self.current_order = None

        self.status = f"在 {self.current_node.id} 下货完成"

    def assign_order(self, order):
        """分配订单"""
        self.current_order = order
        self.status = f"接受订单 {order.id}"

    def _check_collision_at(self, x, y, other_agvs):
        """检查指定位置是否碰撞"""
        for agv in other_agvs:
            if agv.id == self.id:
                continue
            distance = math.sqrt((x - agv.x) ** 2 + (y - agv.y) ** 2)
            if distance < self.collision_buffer:
                return True
        return False

    def _normalize_angle(self, angle):
        """角度归一化"""
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle -= 360
        return angle

    def stop(self, nodes):
        """停止AGV"""
        if self.moving:
            # 找最近节点
            closest_node = min(nodes.values(),
                               key=lambda n: (n.x - self.x) ** 2 + (n.y - self.y) ** 2)

            if closest_node and (closest_node.occupied_by is None or
                                 closest_node.occupied_by == self.id):
                # 释放当前节点
                if self.current_node and self.current_node.occupied_by == self.id:
                    self.current_node.occupied_by = None

                # 移动到最近节点
                self.current_node = closest_node
                self.x = closest_node.x
                self.y = closest_node.y
                closest_node.occupied_by = self.id

        # 重置状态
        self.moving = False
        self.target_node = None
        self.path = []
        self.path_index = 0
        self.task_target = None
        self.status = "已停止"
        self.waiting = False
        self.wait_counter = 0

    def draw(self, painter):
        """绘制AGV - 增强版本包含电量显示"""
        painter.save()
        painter.translate(int(self.x), int(self.y))
        painter.rotate(self.angle)

        # 根据状态调整颜色
        if self.battery_system.current_charge <= 0:
            color = QColor(128, 128, 128)  # 灰色表示没电
        elif self.battery_system.is_charging:
            color = QColor(0, 150, 255)  # 蓝色表示充电中
        elif self.waiting:
            color = self.color.lighter(140)
        else:
            color = self.color

        # 绘制主体
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(-self.width // 2, -self.height // 2, self.width, self.height)

        # 绘制方向指示
        front_size = 6
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(self.width // 2 - front_size, -front_size // 2, front_size, front_size)

        # 绘制载货指示
        if self.is_carrying_cargo:
            painter.setBrush(QBrush(QColor(255, 215, 0)))  # 金色
            painter.drawEllipse(-3, -3, 6, 6)

        painter.restore()

        # 绘制ID
        painter.setFont(QFont('Arial', 8, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        text_rect = QRectF(self.x - self.width // 2, self.y - self.height // 2,
                           self.width, self.height)
        painter.drawText(text_rect, Qt.AlignCenter, f"#{self.id}")

        # 绘制电量指示器
        battery_x = int(self.x - self.width // 2)
        battery_y = int(self.y - self.height // 2 - 15)
        self.battery_system.draw_battery_indicator(painter, battery_x, battery_y, 24, 8)

        # 绘制电量百分比
        if self.battery_system.current_charge < 50:  # 低电量时显示百分比
            painter.setFont(QFont('Arial', 6))
            painter.setPen(QPen(Qt.red if self.battery_system.current_charge < 20 else Qt.black))
            painter.drawText(battery_x, battery_y - 2, f"{self.battery_system.current_charge:.0f}%")

        # 等待状态指示
        if self.waiting:
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(QPen(Qt.red))
            painter.drawEllipse(int(self.x + self.width // 2 - 4),
                                int(self.y - self.height // 2 + 4), 8, 8)

        # 充电状态指示
        if self.battery_system.is_charging:
            painter.setBrush(QBrush(QColor(0, 255, 255)))
            painter.setPen(QPen(QColor(0, 255, 255)))
            painter.drawEllipse(int(self.x - self.width // 2 - 4),
                                int(self.y - self.height // 2 + 4), 8, 8)

    def get_detailed_status(self):
        """获取详细状态信息"""
        battery_status = self.battery_system.get_statistics()

        return {
            'id': self.id,
            'name': self.name,
            'position': (self.x, self.y),
            'current_node': self.current_node.id,
            'target_node': self.target_node.id if self.target_node else None,
            'status': self.status,
            'moving': self.moving,
            'waiting': self.waiting,
            'carrying_cargo': self.is_carrying_cargo,
            'current_order': self.current_order.id if self.current_order else None,
            'battery': battery_status,
            'at_charging_station': self.is_at_charging_station,
            'total_distance': round(self.total_distance_traveled, 1),
            'orders_completed': self.total_orders_completed
        }

    def destroy(self):
        """清理资源"""
        if self.current_node and self.current_node.occupied_by == self.id:
            self.current_node.occupied_by = None
        if self.target_node and self.target_node.reserved_by == self.id:
            self.target_node.reserved_by = None
        if self.battery_system.is_charging:
            self.battery_system.stop_charging()
        self.path = []
        self.status = "已销毁"