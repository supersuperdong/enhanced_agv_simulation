"""
控制面板模块 - 支持订单管理
"""

import random
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QCheckBox, QTextEdit,
                             QGroupBox, QMessageBox, QScrollArea)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer


class ControlPanel(QWidget):
    """AGV仿真控制面板 - 支持订单管理"""

    def __init__(self, simulation_widget, parent=None):
        super().__init__(parent)
        self.simulation_widget = simulation_widget
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建滚动内容部件
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        # 创建各个控制组
        scroll_layout.addWidget(self._create_title())
        scroll_layout.addWidget(self._create_agv_group())
        scroll_layout.addWidget(self._create_order_group())
        scroll_layout.addWidget(self._create_control_group())
        scroll_layout.addWidget(self._create_log_group())

        # 添加伸缩项
        scroll_layout.addStretch()

        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _create_title(self):
        """创建标题"""
        title_label = QLabel("智能控制面板")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        return title_label

    def _create_agv_group(self):
        """创建AGV管理组"""
        agv_group = QGroupBox("AGV管理")
        agv_layout = QVBoxLayout(agv_group)

        # 添加AGV
        add_agv_layout = QHBoxLayout()

        self.add_agv_button = QPushButton("添加AGV")
        self.add_agv_button.clicked.connect(self._add_agv)
        add_agv_layout.addWidget(self.add_agv_button)

        self.agv_count_label = QLabel("AGV数量: 0")
        add_agv_layout.addWidget(self.agv_count_label)

        add_agv_layout.addStretch()

        agv_layout.addLayout(add_agv_layout)

        # AGV列表
        self.agv_list = QTextEdit()
        self.agv_list.setMaximumHeight(100)
        self.agv_list.setReadOnly(True)
        agv_layout.addWidget(self.agv_list)

        return agv_group

    def _create_order_group(self):
        """创建订单管理组"""
        order_group = QGroupBox("订单管理")
        order_layout = QVBoxLayout(order_group)

        # 订单操作按钮
        order_button_layout = QHBoxLayout()

        self.create_order_button = QPushButton("创建订单")
        self.create_order_button.clicked.connect(self._create_order)
        order_button_layout.addWidget(self.create_order_button)

        self.auto_order_button = QPushButton("自动订单")
        self.auto_order_button.clicked.connect(self._auto_orders)
        order_button_layout.addWidget(self.auto_order_button)

        order_layout.addLayout(order_button_layout)

        # 订单状态
        self.order_status = QTextEdit()
        self.order_status.setMaximumHeight(150)
        self.order_status.setReadOnly(True)
        order_layout.addWidget(self.order_status)

        return order_group

    def _create_control_group(self):
        """创建控制组"""
        control_group = QGroupBox("仿真控制")
        control_layout = QVBoxLayout(control_group)

        # 停止按钮
        self.stop_all_button = QPushButton("停止所有AGV")
        self.stop_all_button.clicked.connect(self._stop_all_agvs)
        control_layout.addWidget(self.stop_all_button)

        # 碰撞检测开关
        self.collision_check = QCheckBox("启用碰撞检测")
        self.collision_check.setChecked(True)
        self.collision_check.stateChanged.connect(self._toggle_collision_detection)
        control_layout.addWidget(self.collision_check)

        return control_group

    def _create_log_group(self):
        """创建状态日志组"""
        log_group = QGroupBox("状态日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        return log_group

    def _setup_timer(self):
        """设置更新定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)

    # =============================================================================
    # AGV管理方法
    # =============================================================================

    def _add_agv(self):
        """添加AGV"""
        agv = self.simulation_widget.add_agv()
        if agv:
            self._log_message(f"AGV #{agv.id} 已添加")
        else:
            self._log_message("无法添加AGV: 没有可用节点")

    def _stop_all_agvs(self):
        """停止所有AGV"""
        agv_count = len(self.simulation_widget.agvs)
        self.simulation_widget.stop_all_agvs()

        if agv_count > 0:
            self._log_message(f"已停止 {agv_count} 个AGV")
        else:
            self._log_message("没有AGV在运行")

    def _toggle_collision_detection(self, state):
        """切换碰撞检测开关"""
        enabled = (state == Qt.Checked)
        self.simulation_widget.set_collision_detection(enabled)
        self._log_message(f"碰撞检测已{'开启' if enabled else '关闭'}")

    # =============================================================================
    # 订单管理方法
    # =============================================================================

    def _create_order(self):
        """创建订单"""
        order = self.simulation_widget.create_order()
        if order:
            self._log_message(f"订单 #{order.id} 已创建: {order.pickup_node} → {order.dropoff_node}")
        else:
            self._log_message("无法创建订单: 没有上料点或下料点")

    def _auto_orders(self):
        """自动创建订单"""
        self.simulation_widget.create_auto_orders()
        self._log_message("已自动创建订单")

    # =============================================================================
    # UI更新方法
    # =============================================================================

    def _update_ui(self):
        """更新UI状态"""
        # 更新AGV数量
        self.agv_count_label.setText(f"AGV数量: {len(self.simulation_widget.agvs)}")

        # 更新AGV列表
        self._update_agv_list()

        # 更新订单状态
        self._update_order_status()

    def _update_agv_list(self):
        """更新AGV列表"""
        agv_info = []
        for agv in self.simulation_widget.agvs:
            status = agv.status
            battery = f"{agv.battery:.1f}%"
            order = f"订单#{agv.current_order.id}" if agv.current_order else "无"
            agv_info.append(f"AGV#{agv.id}: {status} | 电量:{battery} | {order}")

        self.agv_list.setText("\n".join(agv_info))

    def _update_order_status(self):
        """更新订单状态"""
        stats = self.simulation_widget.scheduler.get_statistics()

        order_lines = [
            f"订单统计:",
            f"  总数: {stats['总订单']}",
            f"  待分配: {stats['待分配']}",
            f"  进行中: {stats['进行中']}",
            f"  已完成: {stats['已完成']}"
        ]

        # 显示最近订单
        recent_orders = self.simulation_widget.scheduler.orders[-5:]
        if recent_orders:
            order_lines.append("\n最近订单:")
            for order in reversed(recent_orders):
                order_lines.append(f"  #{order.id}: {order.pickup_node}→{order.dropoff_node} [{order.status}]")

        self.order_status.setText("\n".join(order_lines))

    # =============================================================================
    # 辅助方法
    # =============================================================================

    def _log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # 限制日志行数
        document = self.log_text.document()
        if document.blockCount() > 50:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 10)
            cursor.removeSelectedText()

    def get_simulation_widget(self):
        """获取仿真组件引用"""
        return self.simulation_widget