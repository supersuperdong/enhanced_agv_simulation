"""
AGV模型类 - 增加电量管理
"""

import math
import random
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QRectF


class AGV:
    """AGV自动导引车 - 支持电量管理"""

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
        self.width = 48
        self.height = 48
        self.color = QColor(255, 140, 0)

        # 运动属性
        self.angle = 0
        self.target_angle = 0
        self.speed = 4
        self.moving = False

        # 路径属性
        self.path = []
        self.path_index = 0
        self.task_target = None

        # 状态属性
        self.status = "空闲"
        self.waiting = False
        self.collision_buffer = 60
        self.wait_counter = 0
        self.priority = 5

        # 电量管理
        self.battery = 100.0  # 电量百分比
        self.is_charging = False
        self.need_charge = False

        # 订单相关
        self.current_order = None
        self.is_loaded = False  # 是否载货
        self.loading_time = 0  # 上下料倒计时
        self.is_loading = False  # 是否正在上下料

        # 添加到达节点的回调
        self.on_node_arrived = None  # 回调函数: (agv, node) -> None

        # 占用起始节点
        start_node.occupied_by = self.id

    def update_battery(self):
        """更新电量"""
        if self.is_charging:
            # 充电中
            self.battery = min(100.0, self.battery + 2.0 / 60)  # 2%/秒
            if self.battery >= 100.0:
                self.is_charging = False
                self.status = "充电完成"
        elif self.is_loading:
            # 上下料消耗
            self.battery -= 0.15 / 60  # 0.15%/秒
        elif self.moving:
            # 移动中消耗电量
            if self.is_loaded:
                self.battery -= 0.3 / 60  # 载货时0.3%/秒
            else:
                self.battery -= 0.2 / 60  # 空载时0.2%/秒
        else:
            # 空闲消耗
            self.battery -= 0.05 / 60  # 0.05%/秒

        # 检查是否需要充电
        if self.battery < 30 and not self.current_order and not self.is_charging:
            self.need_charge = True

    def start_charging(self):
        """开始充电"""
        if self.current_node.node_type == 'charging':
            self.is_charging = True
            self.status = f"充电中 {self.battery:.1f}%"
            self.moving = False
            self.target_node = None
            self.path = []


    def set_path(self, path):
        """设置路径"""
        if len(path) > 1:
            self.path = path
            self.path_index = 0
            self.task_target = path[-1]  # 最终目标

            # 修复：显示下一个节点而不是终点
            next_node_id = path[1]
            self.status = f"前往节点 {next_node_id}"

            self.waiting = False
            self.wait_counter = 0

    def set_target(self, node):
        """设置移动目标"""
        if node.id not in self.current_node.connections:
            return False

        # 严格检查：节点必须完全空闲或被自己占用/预约
        if node.occupied_by is not None and node.occupied_by != self.id:
            self.status = f"等待节点 {node.id} (被占用)"
            self.waiting = True
            return False

        if node.reserved_by is not None and node.reserved_by != self.id:
            self.status = f"等待节点 {node.id} (已预约)"
            self.waiting = True
            return False

        # 预约目标节点
        self.target_node = node
        node.reserved_by = self.id
        node.reservation_time = 100  # 给充足的预约时间

        # 计算朝向
        dx = node.x - self.x
        dy = node.y - self.y
        self.target_angle = self._normalize_angle(math.degrees(math.atan2(dy, dx)))

        self.moving = True
        self.waiting = False
        self.status = f"移动至节点 {node.id}"
        return True

    def move(self, nodes, other_agvs):
        """移动逻辑"""
        # 更新电量
        self.update_battery()

        # 处理上下料
        if self.is_loading:
            self.loading_time -= 1 / 60
            if self.loading_time <= 0:
                self._finish_loading()
            return

        # 充电中不移动
        if self.is_charging:
            self.status = f"充电中 {self.battery:.1f}%"
            return

        if not self.moving or not self.target_node:
            self._try_next_path_step(nodes)
            return

        # 关键修复：移动前再次检查目标节点是否被其他AGV占用或预约
        if self.target_node.occupied_by is not None and self.target_node.occupied_by != self.id:
            # 目标节点被其他AGV占用了，停止移动
            self.moving = False
            self.waiting = True
            self.wait_counter += 1
            self.status = f"等待节点 {self.target_node.id} (被AGV#{self.target_node.occupied_by}占用)"
            # 释放预约
            if self.target_node.reserved_by == self.id:
                self.target_node.reserved_by = None
            self.target_node = None
            return

        if self.target_node.reserved_by is not None and self.target_node.reserved_by != self.id:
            # 目标节点被其他AGV预约了，停止移动
            self.moving = False
            self.waiting = True
            self.wait_counter += 1
            self.status = f"等待节点 {self.target_node.id} (被AGV#{self.target_node.reserved_by}预约)"
            self.target_node = None
            return

        # 旋转到目标角度
        if self._rotate_to_target():
            # 移动到目标
            self._move_to_target(other_agvs)

    def start_loading(self, duration):
        """开始上下料"""
        self.is_loading = True
        self.loading_time = duration
        self.moving = False

    def _finish_loading(self):
        """完成上下料"""
        self.is_loading = False

        if self.current_order:
            if not self.is_loaded:
                # 完成装货
                self.is_loaded = True
                self.status = "装货完成"
                if self.current_order.drop_path:
                    self.set_path(self.current_order.drop_path)
            else:
                # 完成卸货
                self.is_loaded = False
                self.status = "订单完成"
                if self.current_order:
                    self.current_order.complete()
                self.current_order = None



    def _try_next_path_step(self, nodes):
        """尝试执行路径中的下一步 - 修复版"""
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
                # 修复：明确显示正在等待的是下一个节点
                self.status = f"等待节点 {next_node_id} (被AGV#{next_node.occupied_by}占用)"

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

        # 触发到达节点回调
        if self.on_node_arrived:
            self.on_node_arrived(self, self.current_node)

        # 检查是否是临时让路
        if hasattr(self, '_temp_bypass') and self._temp_bypass:
            self._temp_bypass = False
            # 恢复原始路径
            if hasattr(self, '_original_path') and self._original_path:
                self.set_path(self._original_path)
                self._original_path = None
                self._original_target = None
                return

        # 更新路径状态
        if self.path:
            self.path_index += 1
            if self.path_index >= len(self.path) - 1:
                # 到达路径终点
                self._handle_arrival()
                self.path = []
                self.path_index = 0
                self.task_target = None

    def _handle_arrival(self):
        """处理到达目的地"""
        if self.current_order:
            if self.current_node.node_type == 'pickup' and not self.is_loaded:
                # 到达上料点
                self.status = "正在装货"
                self.start_loading(random.uniform(3, 10))
                if self.current_order:
                    self.current_order.start_loading()
            elif self.current_node.node_type == 'dropoff' and self.is_loaded:
                # 到达下料点
                self.status = "正在卸货"
                self.start_loading(random.uniform(3, 10))
                if self.current_order:
                    self.current_order.start_unloading()
        elif self.need_charge and self.current_node.node_type == 'charging':
            # 到达充电点
            self.start_charging()
            self.need_charge = False
        else:
            self.status = f"已到达 {self.current_node.id}"

    def _check_collision_at(self, x, y, other_agvs):
        """检查指定位置是否碰撞"""
        for agv in other_agvs:
            if agv.id == self.id:
                continue
            distance = math.sqrt((x - agv.x)**2 + (y - agv.y)**2)
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
                             key=lambda n: (n.x - self.x)**2 + (n.y - self.y)**2)

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
        """绘制AGV"""
        painter.save()
        painter.translate(int(self.x), int(self.y))
        painter.rotate(self.angle)

        # 根据状态选择颜色
        if self.battery < 30:
            base_color = QColor(255, 100, 100)  # 低电量红色
        elif self.is_charging:
            base_color = QColor(100, 255, 100)  # 充电中绿色
        elif self.is_loading:
            base_color = QColor(255, 255, 100)  # 上下料黄色
        else:
            base_color = self.color

        color = base_color.lighter(140) if self.waiting else base_color
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(-self.width//2, -self.height//2, self.width, self.height)

        # 绘制载货标识
        if self.is_loaded:
            painter.setBrush(QBrush(QColor(50, 50, 200)))
            painter.drawEllipse(-4, -4, 8, 8)

        # 绘制方向指示
        front_size = 6
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(self.width//2 - front_size, -front_size//2, front_size, front_size)

        painter.restore()

        # 绘制ID和电量
        painter.setFont(QFont('Arial', 8, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        text_rect = QRectF(self.x - self.width//2, self.y - self.height//2,
                          self.width, self.height)
        painter.drawText(text_rect, Qt.AlignCenter, f"#{self.id}")

        # 绘制电量条
        battery_width = 20
        battery_height = 3
        battery_x = self.x - battery_width//2
        battery_y = self.y + self.height//2 + 2

        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(int(battery_x), int(battery_y), battery_width, battery_height)

        # 电量颜色
        if self.battery > 60:
            battery_color = QColor(0, 255, 0)
        elif self.battery > 30:
            battery_color = QColor(255, 255, 0)
        else:
            battery_color = QColor(255, 0, 0)

        painter.setBrush(QBrush(battery_color))
        painter.drawRect(int(battery_x), int(battery_y),
                        int(battery_width * self.battery / 100), battery_height)

        # 等待状态指示
        if self.waiting:
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(QPen(Qt.red))
            painter.drawEllipse(int(self.x + self.width//2 - 4),
                              int(self.y - self.height//2 + 4), 8, 8)

    def destroy(self):
        """清理资源"""
        if self.current_node and self.current_node.occupied_by == self.id:
            self.current_node.occupied_by = None
        if self.target_node and self.target_node.reserved_by == self.id:
            self.target_node.reserved_by = None
        self.path = []
        self.status = "已销毁"