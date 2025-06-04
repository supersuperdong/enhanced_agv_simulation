"""
增强的控制面板模块 - 集成订单系统、电量管理和任务调度
"""

import random
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QCheckBox, QTextEdit,
                             QGroupBox, QMessageBox, QScrollArea, QSpinBox,
                             QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                             QTabWidget, QProgressBar, QSlider, QFrame,
                             QSplitter, QGridLayout)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QTimer

from models.order import OrderGenerator, OrderPriority
from models.task_scheduler import TaskScheduler, SchedulingStrategy


class ControlPanel(QWidget):
    """增强的AGV仿真控制面板 - 集成完整功能"""

    def __init__(self, simulation_widget, parent=None):
        super().__init__(parent)
        self.simulation_widget = simulation_widget

        # 初始化子系统
        self._init_subsystems()
        self._setup_ui()
        self._setup_timers()
        self._connect_signals()

    def _init_subsystems(self):
        """初始化子系统"""
        # 订单生成器
        self.order_generator = OrderGenerator(self.simulation_widget.nodes)

        # 任务调度器
        self.task_scheduler = TaskScheduler(self.simulation_widget)

        # 连接信号
        self.order_generator.order_generated.connect(self.task_scheduler.add_order)

    def _setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 主控制标签页
        self.tab_widget.addTab(self._create_main_control_tab(), "主控制")

        # 订单管理标签页
        self.tab_widget.addTab(self._create_order_management_tab(), "订单管理")

        # AGV状态标签页
        self.tab_widget.addTab(self._create_agv_status_tab(), "AGV状态")

        # 系统监控标签页
        self.tab_widget.addTab(self._create_system_monitor_tab(), "系统监控")

        main_layout.addWidget(self.tab_widget)

    def _create_main_control_tab(self):
        """创建主控制标签页"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # 系统控制组
        layout.addWidget(self._create_system_control_group())

        # AGV管理组
        layout.addWidget(self._create_agv_management_group())

        # 任务调度组
        layout.addWidget(self._create_task_scheduling_group())

        # 快速操作组
        layout.addWidget(self._create_quick_actions_group())

        layout.addStretch()
        return tab_widget

    def _create_order_management_tab(self):
        """创建订单管理标签页"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # 订单生成控制
        layout.addWidget(self._create_order_generation_group())

        # 订单队列显示
        layout.addWidget(self._create_order_queue_group())

        return tab_widget

    def _create_agv_status_tab(self):
        """创建AGV状态标签页"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # AGV状态表格
        self.agv_status_table = QTableWidget()
        self.agv_status_table.setColumnCount(8)
        self.agv_status_table.setHorizontalHeaderLabels([
            "AGV ID", "状态", "电量", "位置", "任务", "载货", "等待", "总里程"
        ])
        layout.addWidget(self.agv_status_table)

        # AGV操作按钮
        button_layout = QHBoxLayout()

        self.charge_all_button = QPushButton("全部充电")
        self.charge_all_button.clicked.connect(self._charge_all_agvs)
        button_layout.addWidget(self.charge_all_button)

        self.emergency_stop_button = QPushButton("紧急停止")
        self.emergency_stop_button.setStyleSheet("background-color: #ff4444; color: white;")
        self.emergency_stop_button.clicked.connect(self._emergency_stop_all)
        button_layout.addWidget(self.emergency_stop_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return tab_widget

    def _create_system_monitor_tab(self):
        """创建系统监控标签页"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # 统计信息组
        layout.addWidget(self._create_statistics_group())

        # 系统日志
        layout.addWidget(self._create_system_log_group())

        return tab_widget

    def _create_system_control_group(self):
        """创建系统控制组"""
        group = QGroupBox("系统控制")
        layout = QVBoxLayout(group)

        # 仿真控制
        sim_layout = QHBoxLayout()

        self.start_simulation_button = QPushButton("启动仿真")
        self.start_simulation_button.clicked.connect(self._start_simulation)
        sim_layout.addWidget(self.start_simulation_button)

        self.pause_simulation_button = QPushButton("暂停仿真")
        self.pause_simulation_button.clicked.connect(self._pause_simulation)
        sim_layout.addWidget(self.pause_simulation_button)

        self.reset_simulation_button = QPushButton("重置仿真")
        self.reset_simulation_button.clicked.connect(self._reset_simulation)
        sim_layout.addWidget(self.reset_simulation_button)

        layout.addLayout(sim_layout)

        # 碰撞检测
        self.collision_check = QCheckBox("启用碰撞检测")
        self.collision_check.setChecked(True)
        self.collision_check.stateChanged.connect(self._toggle_collision_detection)
        layout.addWidget(self.collision_check)

        return group

    def _create_agv_management_group(self):
        """创建AGV管理组"""
        group = QGroupBox("AGV管理")
        layout = QVBoxLayout(group)

        # 添加AGV
        add_layout = QHBoxLayout()

        self.add_agv_button = QPushButton("添加AGV")
        self.add_agv_button.clicked.connect(self._add_agv)
        add_layout.addWidget(self.add_agv_button)

        add_layout.addWidget(QLabel("数量:"))
        self.agv_count_spinbox = QSpinBox()
        self.agv_count_spinbox.setRange(1, 10)
        self.agv_count_spinbox.setValue(1)
        add_layout.addWidget(self.agv_count_spinbox)

        self.add_multiple_button = QPushButton("批量添加")
        self.add_multiple_button.clicked.connect(self._add_multiple_agvs)
        add_layout.addWidget(self.add_multiple_button)

        layout.addLayout(add_layout)

        # 电量管理
        battery_layout = QHBoxLayout()

        self.low_battery_threshold = QSpinBox()
        self.low_battery_threshold.setRange(10, 50)
        self.low_battery_threshold.setValue(30)
        self.low_battery_threshold.setSuffix("%")
        battery_layout.addWidget(QLabel("低电量阈值:"))
        battery_layout.addWidget(self.low_battery_threshold)

        self.auto_charge_check = QCheckBox("自动充电")
        self.auto_charge_check.setChecked(True)
        battery_layout.addWidget(self.auto_charge_check)

        layout.addLayout(battery_layout)

        return group

    def _create_task_scheduling_group(self):
        """创建任务调度组"""
        group = QGroupBox("任务调度")
        layout = QVBoxLayout(group)

        # 调度策略
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("调度策略:"))

        self.strategy_combo = QComboBox()
        for strategy in SchedulingStrategy:
            self.strategy_combo.addItem(strategy.value, strategy)
        self.strategy_combo.setCurrentIndex(5)  # 默认平衡调度
        self.strategy_combo.currentTextChanged.connect(self._change_scheduling_strategy)
        strategy_layout.addWidget(self.strategy_combo)

        layout.addLayout(strategy_layout)

        # 调度参数
        params_layout = QGridLayout()

        params_layout.addWidget(QLabel("分配间隔:"), 0, 0)
        self.assignment_interval_spinbox = QDoubleSpinBox()
        self.assignment_interval_spinbox.setRange(0.5, 10.0)
        self.assignment_interval_spinbox.setValue(2.0)
        self.assignment_interval_spinbox.setSuffix(" 秒")
        params_layout.addWidget(self.assignment_interval_spinbox, 0, 1)

        layout.addLayout(params_layout)

        return group

    def _create_order_generation_group(self):
        """创建订单生成组"""
        group = QGroupBox("订单生成控制")
        layout = QVBoxLayout(group)

        # 生成控制
        gen_layout = QHBoxLayout()

        self.start_generation_button = QPushButton("开始生成")
        self.start_generation_button.clicked.connect(self._start_order_generation)
        gen_layout.addWidget(self.start_generation_button)

        self.stop_generation_button = QPushButton("停止生成")
        self.stop_generation_button.clicked.connect(self._stop_order_generation)
        gen_layout.addWidget(self.stop_generation_button)

        self.manual_order_button = QPushButton("手动生成订单")
        self.manual_order_button.clicked.connect(self._manual_generate_order)
        gen_layout.addWidget(self.manual_order_button)

        layout.addLayout(gen_layout)

        # 生成参数
        params_layout = QGridLayout()

        params_layout.addWidget(QLabel("生成速率:"), 0, 0)
        self.generation_rate_slider = QSlider(Qt.Horizontal)
        self.generation_rate_slider.setRange(1, 30)  # 0.1 到 3.0 订单/分钟
        self.generation_rate_slider.setValue(5)  # 默认0.5订单/分钟
        self.generation_rate_slider.valueChanged.connect(self._update_generation_rate)
        params_layout.addWidget(self.generation_rate_slider, 0, 1)

        self.rate_label = QLabel("0.5 订单/分钟")
        params_layout.addWidget(self.rate_label, 0, 2)

        layout.addLayout(params_layout)

        return group

    def _create_order_queue_group(self):
        """创建订单队列组"""
        group = QGroupBox("订单队列")
        layout = QVBoxLayout(group)

        # 订单表格
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels([
            "订单ID", "上货点", "下货点", "优先级", "状态", "剩余时间", "分配AGV"
        ])
        layout.addWidget(self.order_table)

        # 队列统计
        stats_layout = QHBoxLayout()

        self.pending_orders_label = QLabel("待处理: 0")
        stats_layout.addWidget(self.pending_orders_label)

        self.processing_orders_label = QLabel("处理中: 0")
        stats_layout.addWidget(self.processing_orders_label)

        self.completed_orders_label = QLabel("已完成: 0")
        stats_layout.addWidget(self.completed_orders_label)

        layout.addLayout(stats_layout)

        return group

    def _create_quick_actions_group(self):
        """创建快速操作组"""
        group = QGroupBox("快速操作")
        layout = QHBoxLayout(group)

        self.demo_button = QPushButton("演示模式")
        self.demo_button.clicked.connect(self._start_demo)
        layout.addWidget(self.demo_button)

        self.clear_all_button = QPushButton("清空所有")
        self.clear_all_button.clicked.connect(self._clear_all)
        layout.addWidget(self.clear_all_button)

        return group

    def _create_statistics_group(self):
        """创建统计信息组"""
        group = QGroupBox("系统统计")
        layout = QGridLayout(group)

        # 系统运行时间
        self.runtime_label = QLabel("运行时间: 00:00:00")
        layout.addWidget(self.runtime_label, 0, 0, 1, 2)

        # 订单统计
        self.total_orders_label = QLabel("总订单数: 0")
        layout.addWidget(self.total_orders_label, 1, 0)

        self.completion_rate_label = QLabel("完成率: 0%")
        layout.addWidget(self.completion_rate_label, 1, 1)

        # AGV统计
        self.total_distance_label = QLabel("总里程: 0.0")
        layout.addWidget(self.total_distance_label, 2, 0)

        self.avg_battery_label = QLabel("平均电量: 0%")
        layout.addWidget(self.avg_battery_label, 2, 1)

        return group

    def _create_system_log_group(self):
        """创建系统日志组"""
        group = QGroupBox("系统日志")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 日志控制
        log_control_layout = QHBoxLayout()

        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self._clear_log)
        log_control_layout.addWidget(self.clear_log_button)

        self.export_log_button = QPushButton("导出日志")
        self.export_log_button.clicked.connect(self._export_log)
        log_control_layout.addWidget(self.export_log_button)

        log_control_layout.addStretch()
        layout.addLayout(log_control_layout)

        return group

    def _setup_timers(self):
        """设置定时器"""
        # 主更新定时器
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._update_main)
        self.main_timer.start(1000)  # 1秒更新一次

        # 快速更新定时器
        self.fast_timer = QTimer()
        self.fast_timer.timeout.connect(self._update_fast)
        self.fast_timer.start(100)  # 100ms更新一次

        # 统计定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(5000)  # 5秒更新一次

    def _connect_signals(self):
        """连接信号"""
        pass

    # =============================================================================
    # 主要控制方法
    # =============================================================================

    def _start_simulation(self):
        """启动仿真"""
        self.order_generator.start_generation()
        self._log_message("仿真系统已启动")

    def _pause_simulation(self):
        """暂停仿真"""
        self.order_generator.stop_generation()
        self._log_message("仿真系统已暂停")

    def _reset_simulation(self):
        """重置仿真"""
        # 停止所有AGV
        self.simulation_widget.stop_all_agvs()

        # 清空订单队列
        self.task_scheduler.order_queue.pending_orders.clear()
        self.task_scheduler.order_queue.processing_orders.clear()

        # 停止订单生成
        self.order_generator.stop_generation()

        self._log_message("仿真系统已重置")

    def _add_agv(self):
        """添加AGV"""
        agv = self.simulation_widget.add_agv()
        if agv:
            self._log_message(f"添加AGV #{agv.id}")
        else:
            self._log_message("无法添加AGV: 没有可用节点")

    def _add_multiple_agvs(self):
        """批量添加AGV"""
        count = self.agv_count_spinbox.value()
        added = 0

        for _ in range(count):
            agv = self.simulation_widget.add_agv()
            if agv:
                added += 1
            else:
                break

        self._log_message(f"批量添加AGV: 成功添加 {added}/{count}")

    def _charge_all_agvs(self):
        """所有AGV充电"""
        charged_count = 0
        for agv in self.simulation_widget.agvs:
            if hasattr(agv, 'battery_system'):
                if not agv.battery_system.is_charging:
                    # 这里应该调用调度器来安排充电任务
                    charged_count += 1

        self._log_message(f"安排 {charged_count} 个AGV充电")

    def _emergency_stop_all(self):
        """紧急停止所有AGV"""
        self.simulation_widget.stop_all_agvs()
        self.order_generator.stop_generation()
        self._log_message("🚨 紧急停止所有AGV")

    def _start_order_generation(self):
        """开始订单生成"""
        self.order_generator.start_generation()
        self._log_message("订单生成器已启动")

    def _stop_order_generation(self):
        """停止订单生成"""
        self.order_generator.stop_generation()
        self._log_message("订单生成器已停止")

    def _manual_generate_order(self):
        """手动生成订单"""
        order = self.order_generator.manual_generate_order()
        if order:
            self._log_message(f"手动生成订单: {order.id}")

    def _update_generation_rate(self, value):
        """更新生成速率"""
        rate = value / 10.0  # 0.1 到 3.0
        self.order_generator.set_generation_rate(rate)
        self.rate_label.setText(f"{rate:.1f} 订单/分钟")

    def _change_scheduling_strategy(self):
        """更改调度策略"""
        strategy_data = self.strategy_combo.currentData()
        if strategy_data:
            self.task_scheduler.set_scheduling_strategy(strategy_data)

    def _start_demo(self):
        """启动演示模式"""
        # 添加几个AGV
        for _ in range(3):
            self.simulation_widget.add_agv()

        # 启动订单生成
        self.order_generator.set_generation_rate(1.0)
        self.order_generator.start_generation()

        self._log_message("演示模式已启动")

    def _clear_all(self):
        """清空所有"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有AGV和订单吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 清空AGV
            self.simulation_widget.agvs.clear()

            # 清空订单
            self.task_scheduler.order_queue.pending_orders.clear()
            self.task_scheduler.order_queue.processing_orders.clear()

            # 停止生成
            self.order_generator.stop_generation()

            self._log_message("已清空所有AGV和订单")

    def _toggle_collision_detection(self, state):
        """切换碰撞检测"""
        enabled = (state == Qt.Checked)
        self.simulation_widget.set_collision_detection(enabled)
        self._log_message(f"碰撞检测已{'开启' if enabled else '关闭'}")

    # =============================================================================
    # 更新方法
    # =============================================================================

    def _update_main(self):
        """主更新"""
        # 更新订单生成器
        self.order_generator.update()

        # 更新任务调度器
        self.task_scheduler.update()

        # 更新订单表格
        self._update_order_table()

    def _update_fast(self):
        """快速更新"""
        # 更新AGV状态表格
        self._update_agv_status_table()

    def _update_statistics(self):
        """更新统计信息"""
        # 订单统计
        queue_stats = self.task_scheduler.order_queue.get_statistics()
        self.pending_orders_label.setText(f"待处理: {queue_stats['pending_count']}")
        self.processing_orders_label.setText(f"处理中: {queue_stats['processing_count']}")
        self.completed_orders_label.setText(f"已完成: {queue_stats['completed_count']}")

        self.total_orders_label.setText(f"总订单数: {queue_stats['total_orders']}")
        completion_rate = queue_stats['completion_rate'] * 100
        self.completion_rate_label.setText(f"完成率: {completion_rate:.1f}%")

        # AGV统计
        if hasattr(self.simulation_widget, 'agvs') and self.simulation_widget.agvs:
            total_distance = sum(getattr(agv, 'total_distance_traveled', 0)
                                 for agv in self.simulation_widget.agvs)
            self.total_distance_label.setText(f"总里程: {total_distance:.1f}")

            avg_battery = sum(getattr(agv, 'battery_system', type('', (), {'current_charge': 0})).current_charge
                              for agv in self.simulation_widget.agvs) / len(self.simulation_widget.agvs)
            self.avg_battery_label.setText(f"平均电量: {avg_battery:.1f}%")

    def _update_order_table(self):
        """更新订单表格"""
        all_orders = (list(self.task_scheduler.order_queue.pending_orders) +
                      list(self.task_scheduler.order_queue.processing_orders.values()) +
                      self.task_scheduler.order_queue.completed_orders[-10:])  # 显示最近10个完成的订单

        self.order_table.setRowCount(len(all_orders))

        for row, order in enumerate(all_orders):
            self.order_table.setItem(row, 0, QTableWidgetItem(order.id))
            self.order_table.setItem(row, 1, QTableWidgetItem(str(order.pickup_node_id)))
            self.order_table.setItem(row, 2, QTableWidgetItem(str(order.dropoff_node_id)))
            self.order_table.setItem(row, 3, QTableWidgetItem(order.priority.name))
            self.order_table.setItem(row, 4, QTableWidgetItem(order.status.value))

            remaining_time = order.get_remaining_time()
            time_str = f"{remaining_time / 60:.1f}分钟" if remaining_time > 0 else "已过期"
            self.order_table.setItem(row, 5, QTableWidgetItem(time_str))

            agv_id = order.assigned_agv_id if order.assigned_agv_id else "未分配"
            self.order_table.setItem(row, 6, QTableWidgetItem(str(agv_id)))

    def _update_agv_status_table(self):
        """更新AGV状态表格"""
        agvs = getattr(self.simulation_widget, 'agvs', [])
        self.agv_status_table.setRowCount(len(agvs))

        for row, agv in enumerate(agvs):
            self.agv_status_table.setItem(row, 0, QTableWidgetItem(str(agv.id)))
            self.agv_status_table.setItem(row, 1, QTableWidgetItem(agv.status))

            # 电量显示
            if hasattr(agv, 'battery_system'):
                battery_text = f"{agv.battery_system.current_charge:.1f}%"
                if agv.battery_system.is_charging:
                    battery_text += " 🔌"
                battery_item = QTableWidgetItem(battery_text)

                # 根据电量设置颜色
                if agv.battery_system.current_charge < 20:
                    battery_item.setBackground(QColor(255, 200, 200))
                elif agv.battery_system.current_charge < 50:
                    battery_item.setBackground(QColor(255, 255, 200))

                self.agv_status_table.setItem(row, 2, battery_item)
            else:
                self.agv_status_table.setItem(row, 2, QTableWidgetItem("未知"))

            self.agv_status_table.setItem(row, 3, QTableWidgetItem(agv.current_node.id))

            # 任务信息
            task_info = "无"
            if hasattr(agv, 'current_order') and agv.current_order:
                task_info = f"订单{agv.current_order.id}"
            self.agv_status_table.setItem(row, 4, QTableWidgetItem(task_info))

            # 载货状态
            cargo_status = "是" if getattr(agv, 'is_carrying_cargo', False) else "否"
            self.agv_status_table.setItem(row, 5, QTableWidgetItem(cargo_status))

            # 等待状态
            waiting_status = "是" if agv.waiting else "否"
            self.agv_status_table.setItem(row, 6, QTableWidgetItem(waiting_status))

            # 总里程
            total_distance = getattr(agv, 'total_distance_traveled', 0)
            self.agv_status_table.setItem(row, 7, QTableWidgetItem(f"{total_distance:.1f}"))

    # =============================================================================
    # 日志方法
    # =============================================================================

    def _log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # 限制日志行数
        document = self.log_text.document()
        if document.blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
            cursor.removeSelectedText()

    def _clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def _export_log(self):
        """导出日志"""
        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self, "导出日志",
            f"agv_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self._log_message(f"日志已导出到: {filename}")
            except Exception as e:
                self._log_message(f"导出日志失败: {e}")

    # =============================================================================
    # 公共接口
    # =============================================================================

    def get_order_generator(self):
        """获取订单生成器"""
        return self.order_generator

    def get_task_scheduler(self):
        """获取任务调度器"""
        return self.task_scheduler