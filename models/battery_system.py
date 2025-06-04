"""
AGV电量管理系统
包含电量消耗、充电逻辑和电量预警
"""

import time
import math
from enum import Enum
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import QRectF


class BatteryStatus(Enum):
    """电量状态枚举"""
    FULL = "满电"
    HIGH = "电量充足"
    MEDIUM = "电量正常"
    LOW = "电量不足"
    CRITICAL = "电量危险"
    EMPTY = "电量耗尽"
    CHARGING = "充电中"


class BatterySystem:
    """AGV电量系统"""

    def __init__(self, capacity=100.0, initial_charge=100.0):
        # 电池基本参数
        self.capacity = capacity  # 总容量 (%)
        self.current_charge = min(initial_charge, capacity)  # 当前电量 (%)

        # 消耗和充电速率
        self.discharge_rate_moving = 0.8  # 移动时每秒消耗 (%)
        self.discharge_rate_idle = 0.02  # 待机时每秒消耗 (%)
        self.discharge_rate_carrying = 1.2  # 载货时额外消耗 (%)
        self.charge_rate = 8.0  # 充电时每秒恢复 (%)

        # 阈值设置
        self.critical_threshold = 15.0  # 危险阈值
        self.low_threshold = 30.0  # 低电量阈值
        self.medium_threshold = 60.0  # 中等电量阈值
        self.high_threshold = 90.0  # 高电量阈值

        # 状态跟踪
        self.is_charging = False
        self.charging_start_time = None
        self.last_update_time = time.time()

        # 统计信息
        self.total_consumed = 0.0
        self.total_charged = 0.0
        self.charging_cycles = 0

        # 预警系统
        self.low_battery_warned = False
        self.critical_battery_warned = False

    def update(self, is_moving=False, is_carrying_cargo=False):
        """更新电量状态"""
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        if time_delta <= 0:
            return

        if self.is_charging:
            self._update_charging(time_delta)
        else:
            self._update_discharge(time_delta, is_moving, is_carrying_cargo)

        self.last_update_time = current_time

        # 更新预警状态
        self._update_warning_status()

    def _update_discharge(self, time_delta, is_moving, is_carrying_cargo):
        """更新放电"""
        if self.current_charge <= 0:
            return

        # 计算放电速率
        discharge_rate = self.discharge_rate_idle

        if is_moving:
            discharge_rate = self.discharge_rate_moving
            if is_carrying_cargo:
                discharge_rate += self.discharge_rate_carrying

        # 计算消耗量
        consumption = discharge_rate * time_delta

        # 更新电量
        self.current_charge = max(0, self.current_charge - consumption)
        self.total_consumed += consumption

    def _update_charging(self, time_delta):
        """更新充电"""
        if self.current_charge >= self.capacity:
            self.is_charging = False
            self.charging_start_time = None
            return

        # 计算充电量
        charge_amount = self.charge_rate * time_delta

        # 更新电量
        old_charge = self.current_charge
        self.current_charge = min(self.capacity, self.current_charge + charge_amount)
        self.total_charged += (self.current_charge - old_charge)

    def start_charging(self):
        """开始充电"""
        if not self.is_charging:
            self.is_charging = True
            self.charging_start_time = time.time()
            self.charging_cycles += 1
            print(f"开始充电，当前电量: {self.current_charge:.1f}%")

    def stop_charging(self):
        """停止充电"""
        if self.is_charging:
            self.is_charging = False
            charge_time = time.time() - self.charging_start_time if self.charging_start_time else 0
            print(f"停止充电，充电时间: {charge_time:.1f}秒，当前电量: {self.current_charge:.1f}%")
            self.charging_start_time = None

    def can_move(self):
        """检查是否有足够电量移动"""
        return self.current_charge > 0

    def needs_charging(self):
        """检查是否需要充电"""
        return self.current_charge <= self.low_threshold

    def needs_immediate_charging(self):
        """检查是否需要立即充电"""
        return self.current_charge <= self.critical_threshold

    def is_fully_charged(self):
        """检查是否满电"""
        return self.current_charge >= self.capacity * 0.98  # 98%算作满电

    def get_battery_status(self):
        """获取电量状态"""
        if self.is_charging:
            return BatteryStatus.CHARGING
        elif self.current_charge <= 0:
            return BatteryStatus.EMPTY
        elif self.current_charge <= self.critical_threshold:
            return BatteryStatus.CRITICAL
        elif self.current_charge <= self.low_threshold:
            return BatteryStatus.LOW
        elif self.current_charge <= self.medium_threshold:
            return BatteryStatus.MEDIUM
        elif self.current_charge <= self.high_threshold:
            return BatteryStatus.HIGH
        else:
            return BatteryStatus.FULL

    def get_battery_color(self):
        """获取电量状态对应的颜色"""
        status = self.get_battery_status()
        color_map = {
            BatteryStatus.FULL: QColor(0, 255, 0),  # 绿色
            BatteryStatus.HIGH: QColor(150, 255, 0),  # 浅绿
            BatteryStatus.MEDIUM: QColor(255, 255, 0),  # 黄色
            BatteryStatus.LOW: QColor(255, 150, 0),  # 橙色
            BatteryStatus.CRITICAL: QColor(255, 0, 0),  # 红色
            BatteryStatus.EMPTY: QColor(128, 128, 128),  # 灰色
            BatteryStatus.CHARGING: QColor(0, 150, 255)  # 蓝色
        }
        return color_map.get(status, QColor(128, 128, 128))

    def estimate_remaining_time(self, is_moving=False, is_carrying_cargo=False):
        """估算剩余使用时间（分钟）"""
        if self.current_charge <= 0:
            return 0

        discharge_rate = self.discharge_rate_idle
        if is_moving:
            discharge_rate = self.discharge_rate_moving
            if is_carrying_cargo:
                discharge_rate += self.discharge_rate_carrying

        if discharge_rate <= 0:
            return float('inf')

        remaining_minutes = (self.current_charge / discharge_rate) / 60
        return remaining_minutes

    def estimate_charging_time(self):
        """估算充满电所需时间（分钟）"""
        if self.is_fully_charged():
            return 0

        remaining_capacity = self.capacity - self.current_charge
        charging_time_minutes = (remaining_capacity / self.charge_rate) / 60
        return charging_time_minutes

    def can_complete_task(self, estimated_task_time_minutes, is_moving=True, is_carrying_cargo=True):
        """检查是否有足够电量完成任务"""
        remaining_time = self.estimate_remaining_time(is_moving, is_carrying_cargo)
        safety_margin = 5  # 5分钟安全余量
        return remaining_time >= estimated_task_time_minutes + safety_margin

    def _update_warning_status(self):
        """更新预警状态"""
        # 低电量预警
        if self.current_charge <= self.low_threshold and not self.low_battery_warned:
            self.low_battery_warned = True
            print(f"⚠️ 电量预警: 电量不足 {self.current_charge:.1f}%")
        elif self.current_charge > self.low_threshold:
            self.low_battery_warned = False

        # 危险电量预警
        if self.current_charge <= self.critical_threshold and not self.critical_battery_warned:
            self.critical_battery_warned = True
            print(f"🚨 电量危险: 电量严重不足 {self.current_charge:.1f}%，需要立即充电！")
        elif self.current_charge > self.critical_threshold:
            self.critical_battery_warned = False

    def draw_battery_indicator(self, painter, x, y, width=20, height=10):
        """绘制电量指示器"""
        painter.save()

        # 电池外框
        battery_rect = QRectF(x, y, width, height)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(battery_rect)

        # 电池正极
        positive_rect = QRectF(x + width, y + height * 0.3, 2, height * 0.4)
        painter.drawRect(positive_rect)

        # 电量填充
        charge_width = (width - 2) * (self.current_charge / 100.0)
        if charge_width > 0:
            charge_rect = QRectF(x + 1, y + 1, charge_width, height - 2)
            painter.setBrush(QBrush(self.get_battery_color()))
            painter.drawRect(charge_rect)

        # 充电动画
        if self.is_charging:
            # 绘制闪电符号
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            lightning_x = x + width * 0.5
            lightning_y = y + height * 0.2
            lightning_points = [
                (lightning_x - 2, lightning_y),
                (lightning_x + 1, lightning_y + 3),
                (lightning_x - 1, lightning_y + 3),
                (lightning_x + 2, lightning_y + 6)
            ]
            for i in range(len(lightning_points) - 1):
                painter.drawLine(lightning_points[i][0], lightning_points[i][1],
                                 lightning_points[i + 1][0], lightning_points[i + 1][1])

        painter.restore()

    def get_statistics(self):
        """获取统计信息"""
        return {
            'current_charge': self.current_charge,
            'capacity': self.capacity,
            'charge_percentage': (self.current_charge / self.capacity) * 100,
            'status': self.get_battery_status().value,
            'is_charging': self.is_charging,
            'total_consumed': self.total_consumed,
            'total_charged': self.total_charged,
            'charging_cycles': self.charging_cycles,
            'estimated_remaining_time': self.estimate_remaining_time(),
            'needs_charging': self.needs_charging(),
            'needs_immediate_charging': self.needs_immediate_charging()
        }

    def to_dict(self):
        """转换为字典格式"""
        return {
            'charge': round(self.current_charge, 1),
            'status': self.get_battery_status().value,
            'charging': self.is_charging,
            'remaining_time': round(self.estimate_remaining_time(), 1)
        }


class ChargingStation:
    """充电站类"""

    def __init__(self, node_id, max_agvs=2):
        self.node_id = node_id
        self.max_agvs = max_agvs
        self.charging_agvs = set()
        self.queue = []  # 等待充电的AGV队列

        # 充电站状态
        self.is_operational = True
        self.efficiency = 1.0  # 充电效率倍数

        # 统计信息
        self.total_charging_sessions = 0
        self.total_energy_provided = 0.0

    def can_accept_agv(self):
        """检查是否能接受新的AGV"""
        return (self.is_operational and
                len(self.charging_agvs) < self.max_agvs)

    def add_agv_to_charge(self, agv_id):
        """添加AGV到充电站"""
        if self.can_accept_agv():
            self.charging_agvs.add(agv_id)
            self.total_charging_sessions += 1
            return True
        else:
            # 添加到等待队列
            if agv_id not in self.queue:
                self.queue.append(agv_id)
            return False

    def remove_agv_from_charge(self, agv_id):
        """从充电站移除AGV"""
        if agv_id in self.charging_agvs:
            self.charging_agvs.remove(agv_id)

            # 处理等待队列
            if self.queue:
                next_agv = self.queue.pop(0)
                self.charging_agvs.add(next_agv)
                return next_agv

        return None

    def get_queue_position(self, agv_id):
        """获取AGV在队列中的位置"""
        try:
            return self.queue.index(agv_id) + 1
        except ValueError:
            return -1

    def is_agv_charging(self, agv_id):
        """检查AGV是否正在充电"""
        return agv_id in self.charging_agvs

    def get_status(self):
        """获取充电站状态"""
        return {
            'node_id': self.node_id,
            'operational': self.is_operational,
            'charging_count': len(self.charging_agvs),
            'max_capacity': self.max_agvs,
            'queue_length': len(self.queue),
            'utilization': len(self.charging_agvs) / self.max_agvs,
            'efficiency': self.efficiency
        }