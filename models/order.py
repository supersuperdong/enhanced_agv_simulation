"""
订单模型类
"""

import time
from datetime import datetime


class Order:
    """运输订单"""

    def __init__(self, order_id, pickup_node, dropoff_node):
        self.id = order_id
        self.pickup_node = pickup_node
        self.dropoff_node = dropoff_node

        # 状态
        self.status = "待分配"  # 待分配、已分配、取货中、运输中、卸货中、已完成
        self.assigned_agv = None

        # 路径
        self.pickup_path = []  # AGV到上料点的路径
        self.drop_path = []    # 上料点到下料点的路径

        # 时间记录
        self.create_time = time.time()
        self.assign_time = None
        self.pickup_start_time = None
        self.pickup_end_time = None
        self.dropoff_start_time = None
        self.dropoff_end_time = None
        self.complete_time = None

    def assign_to_agv(self, agv):
        """分配给AGV"""
        self.assigned_agv = agv
        self.status = "已分配"
        self.assign_time = time.time()
        agv.current_order = self

    def start_loading(self):
        """开始装货"""
        self.status = "取货中"
        self.pickup_start_time = time.time()

    def finish_loading(self):
        """完成装货"""
        self.status = "运输中"
        self.pickup_end_time = time.time()

    def start_unloading(self):
        """开始卸货"""
        self.status = "卸货中"
        self.dropoff_start_time = time.time()

    def complete(self):
        """完成订单"""
        self.status = "已完成"
        self.complete_time = time.time()
        self.dropoff_end_time = time.time()

    def get_total_time(self):
        """获取总耗时"""
        if self.complete_time:
            return self.complete_time - self.create_time
        return time.time() - self.create_time

    def get_stage_times(self):
        """获取各阶段耗时"""
        times = {
            "等待分配": 0,
            "移动到取货点": 0,
            "装货": 0,
            "运输": 0,
            "卸货": 0
        }

        if self.assign_time:
            times["等待分配"] = self.assign_time - self.create_time

        if self.pickup_start_time and self.assign_time:
            times["移动到取货点"] = self.pickup_start_time - self.assign_time

        if self.pickup_end_time and self.pickup_start_time:
            times["装货"] = self.pickup_end_time - self.pickup_start_time

        if self.dropoff_start_time and self.pickup_end_time:
            times["运输"] = self.dropoff_start_time - self.pickup_end_time

        if self.dropoff_end_time and self.dropoff_start_time:
            times["卸货"] = self.dropoff_end_time - self.dropoff_start_time

        return times

    def get_detailed_info(self):
        """获取详细订单信息，包括时间统计"""
        stage_times = self.get_stage_times()

        info = {
            "订单ID": self.id,
            "路线": f"{self.pickup_node} → {self.dropoff_node}",
            "状态": self.status,
            "分配AGV": self.assigned_agv.id if self.assigned_agv else "未分配",
            "创建时间": datetime.fromtimestamp(self.create_time).strftime("%H:%M:%S"),
            "总耗时": f"{self.get_total_time():.1f}秒"
        }

        # 添加各阶段详细时间
        info["阶段耗时"] = {
            k: f"{v:.1f}秒" for k, v in stage_times.items() if v > 0
        }

        # 添加预计剩余时间（如果订单未完成）
        if self.status != "已完成":
            elapsed = time.time() - self.create_time
            # 简单估算：平均每个订单60秒
            estimated_remaining = max(0, 60 - elapsed)
            info["预计剩余"] = f"{estimated_remaining:.1f}秒"

        return info