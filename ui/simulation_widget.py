"""
增强仿真显示组件模块 - 集成订单系统、电量管理和任务调度
"""

import random
import datetime
import time
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer

from models.agv import AGV
from models.path import Path
from models.order import OrderGenerator, Order, OrderStatus
from models.battery_system import ChargingStation
from models.task_scheduler import TaskScheduler
from algorithms.path_planner import PathPlanner
from data.map_loader import MapLoader
from models.control_zone_manager import ControlZoneManager


class SimulationWidget(QWidget):
    """增强AGV仿真显示组件 - 集成完整功能"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget()
        self._init_data()
        self._init_subsystems()
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

        # 充电站管理
        self.charging_stations = {}

        # 仿真状态
        self.simulation_running = True
        self.simulation_speed = 1.0
        self.start_time = time.time()

    def _init_subsystems(self):
        """初始化子系统"""
        # 订单生成器
        self.order_generator = OrderGenerator(self.nodes)

        # 任务调度器
        self.task_scheduler = TaskScheduler(self)

        # 连接信号
        self.order_generator.order_generated.connect(self.task_scheduler.add_order)
        self.task_scheduler.task_assigned.connect(self._on_task_assigned)
        self.task_scheduler.task_completed.connect(self._on_task_completed)

    def _init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_simulation)
        self.timer.start(16)  # ~60 FPS

    def _load_initial_data(self):
        """加载初始数据"""
        self.load_database_map()
        self.control_zone_manager.load_control_zones()
        self._init_charging_stations()

    def _init_charging_stations(self):
        """初始化充电站"""
        for node_id, node in self.nodes.items():
            if node.node_type == 'charging':
                self.charging_stations[node_id] = ChargingStation(node_id, max_agvs=2)
                print(f"初始化充电站: {node_id}")

    # =============================================================================
    # 地图加载
    # =============================================================================

    def load_database_map(self, db_path="Map.db"):
        """加载数据库地图"""
        try:
            self.nodes, self.paths = MapLoader.load_from_database(db_path)
            self.map_source = f"数据库: {db_path}"
            self._reset_simulation()

            # 重新初始化子系统
            self.order_generator = OrderGenerator(self.nodes)
            self.task_scheduler = TaskScheduler(self)
            self.order_generator.order_generated.connect(self.task_scheduler.add_order)

            self._init_charging_stations()
            self.update()
            return True
        except Exception as e:
            print(f"加载数据库地图失败: {e}")
            self.map_source = f"数据库加载失败"
            return False

    def _reset_simulation(self):
        """重置仿真状态"""
        # 清理AGV
        for agv in self.agvs:
            agv.destroy()

        self.agvs = []
        self.agv_counter = 1
        self.planned_paths = []
        self.active_paths = []

        # 重置时间
        self.start_time = time.time()

    # =============================================================================
    # AGV管理 - 增强版本
    # =============================================================================

    def add_agv(self, start_node_id=None):
        """添加增强AGV"""
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
                  QColor(255, 100, 100), QColor(100, 255, 100), QColor(100, 100, 255)]
        agv.color = colors[(self.agv_counter - 1) % len(colors)]

        self.agvs.append(agv)
        self.agv_counter += 1

        print(f"添加增强AGV #{agv.id}，电量: {agv.battery_system.current_charge:.1f}%")
        return agv

    def remove_agv(self, agv_id):
        """移除AGV"""
        for i, agv in enumerate(self.agvs):
            if agv.id == agv_id:
                agv.destroy()

                # 清理相关路径和任务
                self.planned_paths = [p for p in self.planned_paths
                                      if not hasattr(p, 'agv_id') or p.agv_id != agv_id]

                # 清理任务调度器中的任务
                if hasattr(self.task_scheduler, 'agv_tasks'):
                    self.task_scheduler.agv_tasks.pop(agv_id, None)

                del self.agvs[i]
                self.update()
                print(f"移除AGV #{agv_id}")
                return True
        return False

    def send_agv_to_target(self, agv_id, target_node_id, algorithm='dijkstra'):
        """发送AGV到目标 - 考虑电量"""
        agv = self._find_agv_by_id(agv_id)
        if not agv or target_node_id not in self.nodes:
            return False

        # 检查电量是否足够
        if not agv.battery_system.can_move():
            print(f"AGV #{agv_id} 电量不足，无法移动")
            return False

        try:
            path = PathPlanner.plan_path(
                algorithm, self.nodes, agv.current_node.id, target_node_id, self.agvs
            )
            if path:
                # 估算路径能耗
                estimated_consumption = len(path) * 2.0  # 简化估算
                if agv.battery_system.current_charge > estimated_consumption:
                    agv.set_path(path)
                    self._update_planned_paths(path, agv.id)
                    return True
                else:
                    print(f"AGV #{agv_id} 电量不足以完成路径，需要充电")
                    return False
        except Exception as e:
            print(f"路径规划失败: {e}")
        return False

    def stop_all_agvs(self):
        """停止所有AGV"""
        for agv in self.agvs:
            agv.stop(self.nodes)
        self.planned_paths = []
        print("所有AGV已停止")

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
    # 仿真更新 - 增强版本
    # =============================================================================

    def _update_simulation(self):
        """更新仿真 - 集成所有子系统"""
        if not self.simulation_running:
            return

        # 更新节点预定
        for node in self.nodes.values():
            if node.reservation_time > 0:
                node.reservation_time -= 1
            elif node.reservation_time == 0 and node.reserved_by is not None:
                node.reserved_by = None

        # 更新AGV - 包含电量系统
        for agv in self.agvs:
            agv.move(self.nodes, self.agvs)

        # 更新订单生成器
        self.order_generator.update()

        # 更新任务调度器
        self.task_scheduler.update()

        # 更新充电站
        self._update_charging_stations()

        # 更新活动路径
        self._update_active_paths()

        # 处理紧急充电需求
        self._handle_emergency_charging()

        self.update()

    def _update_charging_stations(self):
        """更新充电站状态"""
        for station_id, station in self.charging_stations.items():
            # 检查是否有AGV到达充电站
            for agv in self.agvs:
                if (agv.current_node.id == station_id and
                        not agv.battery_system.is_charging and
                        agv.battery_system.needs_charging()):

                    if station.can_accept_agv():
                        station.add_agv_to_charge(agv.id)
                        agv.battery_system.start_charging()
                        print(f"AGV #{agv.id} 开始在充电站 {station_id} 充电")

                # 检查是否充电完成
                elif (agv.battery_system.is_charging and
                      agv.battery_system.is_fully_charged()):

                    if station.is_agv_charging(agv.id):
                        next_agv_id = station.remove_agv_from_charge(agv.id)
                        agv.battery_system.stop_charging()
                        print(f"AGV #{agv.id} 在充电站 {station_id} 充电完成")

                        # 处理等待队列中的下一个AGV
                        if next_agv_id:
                            next_agv = self._find_agv_by_id(next_agv_id)
                            if next_agv and next_agv.current_node.id == station_id:
                                next_agv.battery_system.start_charging()

    def _handle_emergency_charging(self):
        """处理紧急充电需求"""
        for agv in self.agvs:
            if (agv.battery_system.current_charge <= 0 and
                    not agv.battery_system.is_charging):

                # 寻找最近的充电站
                nearest_station = self._find_nearest_charging_station(agv)
                if nearest_station:
                    print(f"🚨 AGV #{agv.id} 紧急充电，前往充电站 {nearest_station}")
                    # 这里可以强制规划到充电站的路径

    def _find_nearest_charging_station(self, agv):
        """查找最近的充电站"""
        if not self.charging_stations:
            return None

        nearest_station = None
        min_distance = float('inf')

        for station_id in self.charging_stations.keys():
            station_node = self.nodes[station_id]
            distance = ((agv.x - station_node.x) ** 2 + (agv.y - station_node.y) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_station = station_id

        return nearest_station

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
    # 任务调度回调
    # =============================================================================

    def _on_task_assigned(self, agv_id, task):
        """任务分配回调"""
        agv = self._find_agv_by_id(agv_id)
        if agv and task.order:
            agv.assign_order(task.order)
            print(f"任务分配: AGV #{agv_id} 接受订单 {task.order.id}")

    def _on_task_completed(self, agv_id, task):
        """任务完成回调"""
        agv = self._find_agv_by_id(agv_id)
        if agv:
            agv.current_order = None
            print(f"任务完成: AGV #{agv_id} 完成任务")

    # =============================================================================
    # 鼠标事件 - 增强功能
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
        zoom_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
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
            if (agv.x - agv.width / 2 <= x <= agv.x + agv.width / 2 and
                    agv.y - agv.height / 2 <= y <= agv.y + agv.height / 2):
                return agv
        return None

    def _show_agv_info(self, agv):
        """显示AGV详细信息 - 更新版本支持新状态"""
        try:
            from ui.agv_property_dialog import AGVPropertyDialog
            result, _ = AGVPropertyDialog.edit_agv_properties(agv, self)

            if result == 2:  # 删除
                self.remove_agv(agv.id)
            elif result == 1:  # 更新
                self.update()
        except ImportError:
            # 简化版信息显示 - 包含新状态
            status = agv.get_detailed_status()
            battery_info = status['battery']

            # 构建详细状态信息
            status_info = []
            status_info.append(f"AGV #{agv.id} - 详细状态")
            status_info.append(f"位置: ({agv.x:.1f}, {agv.y:.1f})")
            status_info.append(f"当前节点: {agv.current_node.id}")

            if agv.target_node:
                status_info.append(f"目标节点: {agv.target_node.id}")

            status_info.append(f"状态: {agv.status}")
            status_info.append(f"电量: {battery_info['charge']:.1f}% ({battery_info['status']})")

            # 任务状态
            if agv.current_order:
                status_info.append(f"当前订单: {agv.current_order.id}")

            status_info.append(f"载货: {'是' if agv.is_carrying_cargo else '否'}")

            # 新增状态信息
            if agv.is_loading:
                remaining_time = agv.loading_duration - (time.time() - agv.loading_start_time)
                status_info.append(f"上货中: 剩余 {remaining_time:.1f}秒")
            elif agv.is_unloading:
                remaining_time = agv.unloading_duration - (time.time() - agv.unloading_start_time)
                status_info.append(f"下货中: 剩余 {remaining_time:.1f}秒")

            status_info.append(f"可接受新任务: {'是' if agv.ready_for_new_task else '否'}")
            status_info.append(f"移动中: {'是' if agv.moving else '否'}")
            status_info.append(f"等待中: {'是' if agv.waiting else '否'}")

            if agv.is_at_charging_station:
                status_info.append(f"充电站: {agv.charging_station_id}")

            status_info.append(f"总里程: {status['total_distance']:.1f}")
            status_info.append(f"完成订单: {status['orders_completed']}")

            info_text = "\n".join(status_info)

            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, f"AGV #{agv.id}",
                                         info_text + "\n\n删除此AGV?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove_agv(agv.id)
    def _handle_node_click(self, target_node):
        """处理节点点击 - 增强版本"""
        # 手动分配空闲AGV到点击的节点
        available_agvs = [agv for agv in self.agvs
                          if not agv.moving and agv.battery_system.can_move()]

        if available_agvs:
            # 选择最近的AGV
            nearest_agv = min(available_agvs,
                              key=lambda a: ((a.x - target_node.x) ** 2 + (a.y - target_node.y) ** 2) ** 0.5)

            if target_node.id in nearest_agv.current_node.connections:
                if target_node.occupied_by is None:
                    nearest_agv.set_target(target_node)
                    print(f"手动控制: AGV #{nearest_agv.id} 前往节点 {target_node.id}")

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
        elif event.key() == Qt.Key_P:
            self._toggle_pause()

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

    def _toggle_pause(self):
        """切换暂停"""
        self.simulation_running = not self.simulation_running
        print(f"仿真{'继续' if self.simulation_running else '暂停'}")

    def reset_view(self):
        """重置视图"""
        self.zoom_scale = 1.0
        self.pan_x = self.pan_y = 0
        self.update()

    # =============================================================================
    # 绘制 - 增强版本
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

        # 绘制节点（包含充电站特殊标识）
        highlighted_nodes = set()
        for agv in self.agvs:
            if agv.path:
                highlighted_nodes.update(agv.path)

        control_zone_nodes = self.control_zone_manager.get_control_zone_nodes()

        for node_id, node in self.nodes.items():
            is_highlighted = node_id in highlighted_nodes
            is_in_control_zone = str(node_id) in control_zone_nodes
            node.draw(painter, is_highlighted, is_in_control_zone)

            # 绘制充电站额外信息
            if node_id in self.charging_stations:
                self._draw_charging_station_info(painter, node, self.charging_stations[node_id])

        # 绘制AGV
        for agv in self.agvs:
            agv.draw(painter)

    def _draw_charging_station_info(self, painter, node, station):
        """绘制充电站信息"""
        # 绘制充电站标识
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        painter.drawEllipse(int(node.x - 15), int(node.y - 15), 30, 30)

        # 显示使用情况
        if station.charging_agvs:
            painter.setFont(QFont('Arial', 8))
            painter.setPen(QPen(Qt.blue))
            painter.drawText(int(node.x - 10), int(node.y + 20),
                             f"{len(station.charging_agvs)}/{station.max_agvs}")

    def _draw_ui_info(self, painter):
        """绘制UI信息 - 增强版本包含新状态统计"""
        painter.setPen(QPen(Qt.black))
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.drawText(10, 20, "增强AGV仿真系统 v6.3 - 支持上下货等待")

        painter.setFont(QFont('Arial', 10))

        # 基础信息
        control_zone_info = self.control_zone_manager.get_zone_info()
        control_nodes_count = len(self.control_zone_manager.get_control_zone_nodes())

        # 电量统计
        if self.agvs:
            total_battery = sum(agv.battery_system.current_charge for agv in self.agvs)
            avg_battery = total_battery / len(self.agvs)
            low_battery_count = sum(1 for agv in self.agvs
                                    if agv.battery_system.needs_charging())
            charging_count = sum(1 for agv in self.agvs
                                 if agv.battery_system.is_charging)

            # 新增状态统计
            loading_count = sum(1 for agv in self.agvs if agv.is_loading)
            unloading_count = sum(1 for agv in self.agvs if agv.is_unloading)
            available_count = sum(1 for agv in self.agvs if agv.is_available_for_task())
            carrying_count = sum(1 for agv in self.agvs if agv.is_carrying_cargo)
        else:
            avg_battery = 0
            low_battery_count = 0
            charging_count = 0
            loading_count = 0
            unloading_count = 0
            available_count = 0
            carrying_count = 0

        # 订单统计
        if hasattr(self, 'task_scheduler'):
            queue_stats = self.task_scheduler.order_queue.get_statistics()
            pending_orders = queue_stats['pending_count']
            processing_orders = queue_stats['processing_count']
            completed_orders = queue_stats['completed_count']
            active_tasks = len(self.task_scheduler.agv_tasks)
        else:
            pending_orders = processing_orders = completed_orders = active_tasks = 0

        # 运行时间
        runtime = time.time() - self.start_time
        runtime_str = f"{int(runtime // 3600):02d}:{int((runtime % 3600) // 60):02d}:{int(runtime % 60):02d}"

        info_lines = [
            f"地图: {self.map_source}",
            f"节点: {len(self.nodes)} (橙色管控区: {control_nodes_count})",
            f"路径: {len(self.paths)}, 充电站: {len(self.charging_stations)}个",
            f"AGV总数: {len(self.agvs)} (可用: {available_count}, 载货: {carrying_count})",
            f"AGV状态: 上货{loading_count}个, 下货{unloading_count}个, 充电{charging_count}个",
            f"电量: 平均{avg_battery:.1f}%, 低电{low_battery_count}个",
            f"订单: 待处理{pending_orders}, 处理中{processing_orders}, 已完成{completed_orders}",
            f"任务: 活动任务{active_tasks}个",
            f"运行时间: {runtime_str}",
            f"缩放: {self.zoom_scale:.1f}x, 状态: {'运行' if self.simulation_running else '暂停'}"
        ]

        for i, line in enumerate(info_lines):
            painter.drawText(10, 35 + i * 15, line)
    # =============================================================================
    # 其他方法
    # =============================================================================

    def get_map_info(self):
        """获取地图信息 - 增强版本包含新统计"""
        agv_stats = {}
        if self.agvs:
            total_battery = sum(agv.battery_system.current_charge for agv in self.agvs)
            agv_stats = {
                'avg_battery': total_battery / len(self.agvs),
                'low_battery_count': sum(1 for agv in self.agvs if agv.battery_system.needs_charging()),
                'charging_count': sum(1 for agv in self.agvs if agv.battery_system.is_charging),
                'loading_count': sum(1 for agv in self.agvs if agv.is_loading),
                'unloading_count': sum(1 for agv in self.agvs if agv.is_unloading),
                'available_count': sum(1 for agv in self.agvs if agv.is_available_for_task()),
                'carrying_count': sum(1 for agv in self.agvs if agv.is_carrying_cargo),
                'total_distance': sum(getattr(agv, 'total_distance_traveled', 0) for agv in self.agvs),
                'total_orders': sum(getattr(agv, 'total_orders_completed', 0) for agv in self.agvs)
            }

        # 任务统计
        task_stats = {}
        if hasattr(self, 'task_scheduler'):
            queue_stats = self.task_scheduler.order_queue.get_statistics()
            task_stats = {
                'pending_orders': queue_stats['pending_count'],
                'processing_orders': queue_stats['processing_count'],
                'completed_orders': queue_stats['completed_count'],
                'active_tasks': len(self.task_scheduler.agv_tasks),
                'total_assignments': self.task_scheduler.total_assignments,
                'failed_assignments': self.task_scheduler.failed_assignments
            }

        return {
            'source': self.map_source,
            'node_count': len(self.nodes),
            'path_count': len(self.paths),
            'agv_count': len(self.agvs),
            'charging_station_count': len(self.charging_stations),
            'agv_stats': agv_stats,
            'task_stats': task_stats,
            'simulation_running': self.simulation_running,
            'runtime': time.time() - self.start_time
        }

    def get_agv_list(self):
        """获取AGV列表 - 增强版本包含新状态"""
        agv_list = []
        for agv in self.agvs:
            status_details = {
                'id': agv.id,
                'status': agv.status,
                'waiting': agv.waiting,
                'battery': agv.battery_system.current_charge,
                'carrying_cargo': agv.is_carrying_cargo,
                'loading': agv.is_loading,
                'unloading': agv.is_unloading,
                'available': agv.is_available_for_task(),
                'at_charging_station': agv.is_at_charging_station,
                'current_order': agv.current_order.id if agv.current_order else None,
                'position': (agv.x, agv.y),
                'current_node': agv.current_node.id
            }
            agv_list.append(status_details)

        return agv_list

    def set_collision_detection(self, enabled):
        """设置碰撞检测"""
        for agv in self.agvs:
            agv.collision_buffer = 25 if enabled else 0

    def set_simulation_speed(self, speed):
        """设置仿真速度"""
        self.simulation_speed = max(0.1, min(5.0, speed))
        interval = int(16 / self.simulation_speed)
        self.timer.start(interval)

    def pause_simulation(self):
        """暂停仿真"""
        self.simulation_running = False

    def resume_simulation(self):
        """恢复仿真"""
        self.simulation_running = True

    def get_order_generator(self):
        """获取订单生成器"""
        return self.order_generator

    def get_task_scheduler(self):
        """获取任务调度器"""
        return self.task_scheduler

    def get_charging_stations(self):
        """获取充电站信息"""
        return {station_id: station.get_status()
                for station_id, station in self.charging_stations.items()}