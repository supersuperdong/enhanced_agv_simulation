"""
仿真显示组件模块 - 支持订单调度
"""

import random
import datetime
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer

from models.agv import AGV
from models.path import Path
from models.scheduler import Scheduler
from algorithms.path_planner import PathPlanner
from data.map_loader import MapLoader
from models.control_zone_manager import ControlZoneManager


class SimulationWidget(QWidget):
    """AGV仿真显示组件 - 支持订单调度"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget()
        self._init_data()
        self._init_timer()
        self._load_initial_data()

    def _init_widget(self):
        """初始化组件"""
        self.setMinimumSize(1400, 1000)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAutoFillBackground(True)

        # 设置背景色
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(235, 240, 245))
        self.setPalette(palette)

    def _init_data(self):
        """初始化数据"""
        # 地图数据
        self.nodes = {}
        self.paths = []
        self.map_source = "未加载"

        # AGV数据
        self.agvs = []
        self.agv_counter = 1

        # 路径数据
        self.active_paths = []
        self.planned_paths = []

        # 视图控制
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_mouse_pos = None

        # 管控区管理器
        self.control_zone_manager = ControlZoneManager()

        # 调度系统
        self.scheduler = Scheduler()

    def _init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_simulation)
        self.timer.start(16)  # ~60 FPS

        # 调度定时器 - 提高频率以更快检测死锁
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self._update_scheduler)
        self.scheduler_timer.start(200)  # 每0.2秒更新一次，更快响应死锁

    def _load_initial_data(self):
        """加载初始数据"""
        self.load_database_map()
        self.control_zone_manager.load_control_zones()

    # =============================================================================
    # 地图加载
    # =============================================================================

    def load_database_map(self, db_path="Map.db"):
        """加载数据库地图"""
        try:
            self.nodes, self.paths = MapLoader.load_from_database(db_path)
            self.map_source = f"数据库: {db_path}"
            self._reset_simulation()
            self.update()
            return True
        except Exception as e:
            print(f"加载数据库地图失败: {e}")
            self.map_source = f"数据库加载失败"
            return False

    def _reset_simulation(self):
        """重置仿真状态"""
        self.agvs = []
        self.agv_counter = 1
        self.planned_paths = []
        self.active_paths = []
        self.scheduler = Scheduler()

    # =============================================================================
    # AGV管理
    # =============================================================================

    def add_agv(self, start_node_id=None):
        """添加AGV"""
        if not self.nodes:
            return None

        # 选择起始节点
        if start_node_id not in self.nodes:
            available_nodes = [nid for nid, node in self.nodes.items()
                             if node.occupied_by is None]
            if not available_nodes:
                return None
            start_node_id = random.choice(available_nodes)

        start_node = self.nodes[start_node_id]
        if start_node.occupied_by is not None:
            return None

        # 创建AGV
        agv = AGV(self.agv_counter, start_node)

        # 设置颜色
        colors = [QColor(255, 140, 0), QColor(0, 180, 120), QColor(180, 0, 180),
                  QColor(255, 100, 100), QColor(100, 255, 100)]
        agv.color = colors[(self.agv_counter - 1) % len(colors)]

        self.agvs.append(agv)
        self.agv_counter += 1
        return agv

    def remove_agv(self, agv_id):
        """移除AGV"""
        for i, agv in enumerate(self.agvs):
            if agv.id == agv_id:
                agv.destroy()
                self.planned_paths = [p for p in self.planned_paths
                                    if not hasattr(p, 'agv_id') or p.agv_id != agv_id]
                del self.agvs[i]
                self.update()
                return True
        return False

    def create_order(self):
        """创建订单"""
        pickup_nodes = [n for n in self.nodes.values() if n.node_type == 'pickup']
        dropoff_nodes = [n for n in self.nodes.values() if n.node_type == 'dropoff']

        if pickup_nodes and dropoff_nodes:
            pickup = random.choice(pickup_nodes)
            dropoff = random.choice(dropoff_nodes)
            order = self.scheduler.create_order(pickup.id, dropoff.id)
            return order
        return None

    def create_auto_orders(self):
        """自动创建订单"""
        # 根据空闲AGV数量创建订单
        idle_agvs = [agv for agv in self.agvs if not agv.current_order and not agv.is_charging]
        orders_to_create = min(len(idle_agvs), 3)  # 最多创建3个订单

        for _ in range(orders_to_create):
            self.scheduler.create_random_order(self.nodes)

    def stop_all_agvs(self):
        """停止所有AGV"""
        for agv in self.agvs:
            agv.stop(self.nodes)
        self.planned_paths = []

    def _find_agv_by_id(self, agv_id):
        """查找AGV"""
        return next((agv for agv in self.agvs if agv.id == agv_id), None)

    def _update_planned_paths(self, path, agv_id=None):
        """更新规划路径"""
        if agv_id is not None:
            self.planned_paths = [p for p in self.planned_paths
                                if not hasattr(p, 'agv_id') or p.agv_id != agv_id]

        if not path:
            return

        for i in range(len(path) - 1):
            planned_path = Path(self.nodes[path[i]], self.nodes[path[i + 1]], 'planned')
            if agv_id is not None:
                planned_path.agv_id = agv_id
            self.planned_paths.append(planned_path)

    # =============================================================================
    # 仿真更新
    # =============================================================================

    def _update_simulation(self):
        """更新仿真"""
        # 更新节点预定
        for node in self.nodes.values():
            if node.reservation_time > 0:
                node.reservation_time -= 1
            elif node.reservation_time == 0 and node.reserved_by is not None:
                node.reserved_by = None

        # 更新AGV
        for agv in self.agvs:
            agv.move(self.nodes, self.agvs)

            # 更新规划路径显示
            if agv.path and agv.path_index < len(agv.path) - 1:
                self._update_planned_paths(agv.path[agv.path_index:], agv.id)

        # 更新活动路径
        self._update_active_paths()

        self.update()

    def _update_scheduler(self):
        """更新调度系统"""
        # 分配订单
        self.scheduler.assign_orders(self.agvs, self.nodes)

        # 检查空闲AGV
        self.scheduler.check_idle_agvs(self.agvs, self.nodes)

        # 检查并解决死锁
        self.scheduler.check_and_resolve_deadlocks(self.agvs, self.nodes)

        # 更新充电预约
        self.scheduler.update_charging_reservations(self.agvs)

    def _update_active_paths(self):
        """更新活动路径"""
        self.active_paths = []
        for agv in self.agvs:
            if agv.moving and agv.target_node:
                for path in self.paths:
                    if (path.start_node.id == agv.current_node.id and
                        path.end_node.id == agv.target_node.id):
                        path.path_type = 'active'
                        self.active_paths.append(path)

    # =============================================================================
    # 鼠标事件
    # =============================================================================

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.RightButton:
            self._start_drag(event.pos())
        elif event.button() == Qt.LeftButton:
            self._handle_click(event.pos())

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.RightButton:
            self._stop_drag()

    def mouseDoubleClickEvent(self, event):
        """双击重置视图"""
        self.reset_view()

    def wheelEvent(self, event):
        """滚轮缩放"""
        zoom_factor = 1.2 if event.angleDelta().y() > 0 else 1/1.2
        mouse_pos = event.pos()

        old_map_x = (mouse_pos.x() - self.pan_x) / self.zoom_scale
        old_map_y = (mouse_pos.y() - self.pan_y) / self.zoom_scale

        self.zoom_scale = max(0.1, min(5.0, self.zoom_scale * zoom_factor))

        new_map_x = (mouse_pos.x() - self.pan_x) / self.zoom_scale
        new_map_y = (mouse_pos.y() - self.pan_y) / self.zoom_scale

        self.pan_x += (new_map_x - old_map_x) * self.zoom_scale
        self.pan_y += (new_map_y - old_map_y) * self.zoom_scale

        self.update()

    def _start_drag(self, pos):
        """开始拖拽"""
        self.dragging = True
        self.last_mouse_pos = pos
        self.setCursor(Qt.ClosedHandCursor)

    def _stop_drag(self):
        """停止拖拽"""
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)

    def _handle_click(self, pos):
        """处理点击"""
        try:
            map_x = (pos.x() - self.pan_x) / self.zoom_scale
            map_y = (pos.y() - self.pan_y) / self.zoom_scale

            # 检查AGV点击
            clicked_agv = self._find_agv_at_position(map_x, map_y)
            if clicked_agv:
                self._show_agv_info(clicked_agv)
                return

            # 检查节点点击
            for node in self.nodes.values():
                if node.is_point_inside(map_x, map_y):
                    self._handle_node_click(node)
                    break
        except Exception as e:
            print(f"处理点击事件错误: {e}")

    def _find_agv_at_position(self, x, y):
        """查找位置上的AGV"""
        for agv in self.agvs:
            if (agv.x - agv.width/2 <= x <= agv.x + agv.width/2 and
                agv.y - agv.height/2 <= y <= agv.y + agv.height/2):
                return agv
        return None

    def _show_agv_info(self, agv):
        """显示AGV信息"""
        try:
            from ui.agv_property_dialog import AGVPropertyDialog
            result, _ = AGVPropertyDialog.edit_agv_properties(agv, self)

            if result == 2:  # 删除
                self.remove_agv(agv.id)
            elif result == 1:  # 更新
                self.update()
        except ImportError:
            # 简化版信息显示
            order_info = f"\n订单: #{agv.current_order.id}" if agv.current_order else "\n无订单"
            info = (f"AGV #{agv.id}\n"
                   f"电量: {agv.battery:.1f}%\n"
                   f"状态: {agv.status}" +
                   order_info)

            reply = QMessageBox.question(self, f"AGV #{agv.id}",
                                       info + "\n\n删除此AGV?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove_agv(agv.id)

    def _handle_node_click(self, target_node):
        """处理节点点击"""
        # 手动控制暂时禁用，避免干扰订单系统
        pass

    # =============================================================================
    # 键盘事件
    # =============================================================================

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom_in()
        elif event.key() == Qt.Key_Minus:
            self._zoom_out()
        elif event.key() == Qt.Key_R:
            self.reset_view()
        elif event.key() == Qt.Key_Space:
            self._center_view()

    def _zoom_in(self):
        """放大"""
        self.zoom_scale = min(5.0, self.zoom_scale * 1.2)
        self.update()

    def _zoom_out(self):
        """缩小"""
        self.zoom_scale = max(0.1, self.zoom_scale / 1.2)
        self.update()

    def _center_view(self):
        """居中"""
        self.pan_x = self.pan_y = 0
        self.update()

    def reset_view(self):
        """重置视图"""
        self.zoom_scale = 1.0
        self.pan_x = self.pan_y = 0
        self.update()

    # =============================================================================
    # 绘制
    # =============================================================================

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.save()
        painter.translate(self.pan_x, self.pan_y)
        painter.scale(self.zoom_scale, self.zoom_scale)

        self._draw_simulation(painter)

        painter.restore()
        self._draw_ui_info(painter)

    def _draw_simulation(self, painter):
        """绘制仿真内容"""
        # 绘制管控区
        self.control_zone_manager.draw_control_zones(painter, self.nodes)

        # 绘制路径
        for path in self.paths:
            path.path_type = 'normal'
            path.draw(painter)

        for path in self.planned_paths:
            path.draw(painter)

        for path in self.active_paths:
            path.path_type = 'active'
            path.draw(painter)

        # 绘制节点
        highlighted_nodes = set()
        for agv in self.agvs:
            if agv.path:
                highlighted_nodes.update(agv.path)

        # 获取管控区节点集合
        control_zone_nodes = self.control_zone_manager.get_control_zone_nodes()

        for node_id, node in self.nodes.items():
            is_highlighted = node_id in highlighted_nodes
            is_in_control_zone = str(node_id) in control_zone_nodes
            node.draw(painter, is_highlighted, is_in_control_zone)

        # 绘制AGV
        for agv in self.agvs:
            agv.draw(painter)

    def _draw_ui_info(self, painter):
        """绘制UI信息"""
        painter.setPen(QPen(Qt.black))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(10, 20, "AGV仿真系统 v7.0")

        painter.setFont(QFont('Arial', 10))

        # 获取统计信息
        stats = self.scheduler.get_statistics()

        info_lines = [
            f"地图: {self.map_source}",
            f"节点: {len(self.nodes)}, AGV: {len(self.agvs)}",
            f"订单: 总{stats['总订单']} 待分配{stats['待分配']} 进行中{stats['进行中']} 完成{stats['已完成']}",
            f"缩放: {self.zoom_scale:.1f}x"
        ]

        for i, line in enumerate(info_lines):
            painter.drawText(10, 35 + i * 15, line)


    # =============================================================================
    # 其他方法
    # =============================================================================

    def get_map_info(self):
        """获取地图信息"""
        return {
            'source': self.map_source,
            'node_count': len(self.nodes),
            'path_count': len(self.paths),
            'agv_count': len(self.agvs)
        }

    def get_agv_list(self):
        """获取AGV列表"""
        return [(agv.id, agv.status, agv.waiting) for agv in self.agvs]

    def set_collision_detection(self, enabled):
        """设置碰撞检测"""
        for agv in self.agvs:
            agv.collision_buffer = 25 if enabled else 0