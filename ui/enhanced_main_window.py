"""
增强的主窗口模块 - 集成完整的AGV仿真系统
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter,
                             QMenuBar, QMenu, QAction, QStatusBar, QMessageBox,
                             QApplication, QVBoxLayout, QTabWidget)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer

from ui.enhanced_simulation_widget import EnhancedSimulationWidget
from ui.enhanced_control_panel import EnhancedControlPanel


class EnhancedMainWindow(QMainWindow):
    """增强的AGV仿真系统主窗口 - 完整功能版本"""

    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    MIN_WIDTH = 1400
    MIN_HEIGHT = 900

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_widgets()
        self._create_menu_bar()
        self._create_status_bar()
        self._setup_layout()
        self._setup_timer()
        self._connect_signals()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("RCS-Lite 增强AGV智能仿真系统 v6.3 - 集成订单、电量、调度")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _create_widgets(self):
        """创建主要组件"""
        # 增强仿真组件
        self.simulation_widget = EnhancedSimulationWidget()

        # 增强控制面板
        self.control_panel = EnhancedControlPanel(self.simulation_widget)

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        self._create_file_menu(menubar)
        # 仿真菜单
        self._create_simulation_menu(menubar)
        # 订单菜单
        self._create_order_menu(menubar)
        # AGV菜单
        self._create_agv_menu(menubar)
        # 视图菜单
        self._create_view_menu(menubar)
        # 帮助菜单
        self._create_help_menu(menubar)

    def _create_file_menu(self, menubar):
        """创建文件菜单"""
        file_menu = menubar.addMenu('文件(&F)')

        # 导出地图
        export_action = QAction('导出地图(&E)', self)
        export_action.setShortcut(QKeySequence('Ctrl+E'))
        export_action.triggered.connect(self._export_map)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # 导出日志
        export_log_action = QAction('导出日志(&L)', self)
        export_log_action.triggered.connect(self._export_logs)
        file_menu.addAction(export_log_action)

        # 导出统计报告
        export_stats_action = QAction('导出统计报告(&S)', self)
        export_stats_action.triggered.connect(self._export_statistics)
        file_menu.addAction(export_stats_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction('退出(&Q)', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        return file_menu

    def _create_simulation_menu(self, menubar):
        """创建仿真菜单"""
        sim_menu = menubar.addMenu('仿真(&S)')

        # 启动仿真
        start_action = QAction('启动仿真(&S)', self)
        start_action.setShortcut(QKeySequence('F5'))
        start_action.triggered.connect(self._start_simulation)
        sim_menu.addAction(start_action)

        # 暂停仿真
        pause_action = QAction('暂停仿真(&P)', self)
        pause_action.setShortcut(QKeySequence('F6'))
        pause_action.triggered.connect(self._pause_simulation)
        sim_menu.addAction(pause_action)

        # 重置仿真
        reset_action = QAction('重置仿真(&R)', self)
        reset_action.setShortcut(QKeySequence('F7'))
        reset_action.triggered.connect(self._reset_simulation)
        sim_menu.addAction(reset_action)

        sim_menu.addSeparator()

        # 仿真速度
        speed_menu = sim_menu.addMenu('仿真速度(&D)')
        speeds = [('0.5x', 0.5), ('1x', 1.0), ('2x', 2.0), ('5x', 5.0)]
        for name, speed in speeds:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, s=speed: self._set_simulation_speed(s))
            speed_menu.addAction(action)

        return sim_menu

    def _create_order_menu(self, menubar):
        """创建订单菜单"""
        order_menu = menubar.addMenu('订单(&O)')

        # 启动订单生成
        start_gen_action = QAction('启动订单生成(&S)', self)
        start_gen_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        start_gen_action.triggered.connect(self._start_order_generation)
        order_menu.addAction(start_gen_action)

        # 停止订单生成
        stop_gen_action = QAction('停止订单生成(&T)', self)
        stop_gen_action.setShortcut(QKeySequence('Ctrl+Shift+T'))
        stop_gen_action.triggered.connect(self._stop_order_generation)
        order_menu.addAction(stop_gen_action)

        # 手动生成订单
        manual_order_action = QAction('手动生成订单(&M)', self)
        manual_order_action.setShortcut(QKeySequence('Ctrl+M'))
        manual_order_action.triggered.connect(self._manual_generate_order)
        order_menu.addAction(manual_order_action)

        order_menu.addSeparator()

        # 清空订单队列
        clear_orders_action = QAction('清空订单队列(&C)', self)
        clear_orders_action.triggered.connect(self._clear_order_queue)
        order_menu.addAction(clear_orders_action)

        return order_menu

    def _create_agv_menu(self, menubar):
        """创建AGV菜单"""
        agv_menu = menubar.addMenu('AGV(&A)')

        # 添加AGV
        add_agv_action = QAction('添加AGV(&A)', self)
        add_agv_action.setShortcut(QKeySequence('Ctrl+A'))
        add_agv_action.triggered.connect(self._add_agv)
        agv_menu.addAction(add_agv_action)

        # 批量添加AGV
        batch_add_action = QAction('批量添加AGV(&B)', self)
        batch_add_action.setShortcut(QKeySequence('Ctrl+Shift+A'))
        batch_add_action.triggered.connect(self._batch_add_agvs)
        agv_menu.addAction(batch_add_action)

        agv_menu.addSeparator()

        # 全部充电
        charge_all_action = QAction('全部充电(&C)', self)
        charge_all_action.setShortcut(QKeySequence('Ctrl+C'))
        charge_all_action.triggered.connect(self._charge_all_agvs)
        agv_menu.addAction(charge_all_action)

        # 停止所有AGV
        stop_all_action = QAction('停止所有AGV(&S)', self)
        stop_all_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        stop_all_action.triggered.connect(self._stop_all_agvs)
        agv_menu.addAction(stop_all_action)

        # 紧急停止
        emergency_stop_action = QAction('紧急停止(&E)', self)
        emergency_stop_action.setShortcut(QKeySequence('Ctrl+Shift+E'))
        emergency_stop_action.triggered.connect(self._emergency_stop)
        agv_menu.addAction(emergency_stop_action)

        agv_menu.addSeparator()

        # 碰撞检测
        collision_action = QAction('碰撞检测(&D)', self)
        collision_action.setCheckable(True)
        collision_action.setChecked(True)
        collision_action.triggered.connect(self._toggle_collision_from_menu)
        agv_menu.addAction(collision_action)

        self.collision_action = collision_action

        return agv_menu

    def _create_view_menu(self, menubar):
        """创建视图菜单"""
        view_menu = menubar.addMenu('视图(&V)')

        # 缩放控制
        zoom_in_action = QAction('放大(&I)', self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.simulation_widget._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction('缩小(&O)', self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.simulation_widget._zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_view_action = QAction('重置视图(&R)', self)
        reset_view_action.setShortcut(QKeySequence('R'))
        reset_view_action.triggered.connect(self.simulation_widget.reset_view)
        view_menu.addAction(reset_view_action)

        view_menu.addSeparator()

        # 全屏
        fullscreen_action = QAction('全屏(&F)', self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        return view_menu

    def _create_help_menu(self, menubar):
        """创建帮助菜单"""
        help_menu = menubar.addMenu('帮助(&H)')

        # 使用说明
        usage_action = QAction('使用说明(&U)', self)
        usage_action.setShortcut(QKeySequence.HelpContents)
        usage_action.triggered.connect(self._show_usage)
        help_menu.addAction(usage_action)

        # 系统状态
        system_status_action = QAction('系统状态(&S)', self)
        system_status_action.triggered.connect(self._show_system_status)
        help_menu.addAction(system_status_action)

        # 关于
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        return help_menu

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('增强AGV仿真系统已就绪')

    def _setup_layout(self):
        """设置布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 使用分割器布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.simulation_widget)
        splitter.addWidget(self.control_panel)

        # 设置比例：仿真区域占75%，控制面板占25%
        splitter.setSizes([int(self.DEFAULT_WIDTH * 0.75), int(self.DEFAULT_WIDTH * 0.25)])

        layout = QHBoxLayout(central_widget)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)

    def _setup_timer(self):
        """设置定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # 每2秒更新一次状态栏

    def _connect_signals(self):
        """连接信号"""
        # 这里可以连接仿真组件和控制面板之间的信号
        pass

    # =============================================================================
    # 菜单动作方法
    # =============================================================================

    def _start_simulation(self):
        """启动仿真"""
        self.simulation_widget.resume_simulation()
        self.control_panel._start_simulation()
        self.status_bar.showMessage('仿真已启动', 2000)

    def _pause_simulation(self):
        """暂停仿真"""
        self.simulation_widget.pause_simulation()
        self.control_panel._pause_simulation()
        self.status_bar.showMessage('仿真已暂停', 2000)

    def _reset_simulation(self):
        """重置仿真"""
        reply = QMessageBox.question(
            self, '确认重置',
            '确定要重置整个仿真系统吗？\n这将清除所有AGV、订单和统计数据。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.control_panel._reset_simulation()
            self.status_bar.showMessage('仿真已重置', 2000)

    def _set_simulation_speed(self, speed):
        """设置仿真速度"""
        self.simulation_widget.set_simulation_speed(speed)
        self.status_bar.showMessage(f'仿真速度设置为 {speed}x', 2000)

    def _start_order_generation(self):
        """启动订单生成"""
        self.control_panel._start_order_generation()

    def _stop_order_generation(self):
        """停止订单生成"""
        self.control_panel._stop_order_generation()

    def _manual_generate_order(self):
        """手动生成订单"""
        self.control_panel._manual_generate_order()

    def _clear_order_queue(self):
        """清空订单队列"""
        reply = QMessageBox.question(
            self, '确认清空',
            '确定要清空所有待处理的订单吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            scheduler = self.simulation_widget.get_task_scheduler()
            scheduler.order_queue.pending_orders.clear()
            self.status_bar.showMessage('订单队列已清空', 2000)

    def _add_agv(self):
        """添加AGV"""
        self.control_panel._add_agv()

    def _batch_add_agvs(self):
        """批量添加AGV"""
        self.control_panel._add_multiple_agvs()

    def _charge_all_agvs(self):
        """全部AGV充电"""
        self.control_panel._charge_all_agvs()

    def _stop_all_agvs(self):
        """停止所有AGV"""
        self.simulation_widget.stop_all_agvs()
        self.status_bar.showMessage('所有AGV已停止', 2000)

    def _emergency_stop(self):
        """紧急停止"""
        self.control_panel._emergency_stop_all()

    def _toggle_collision_from_menu(self, checked):
        """从菜单切换碰撞检测"""
        self.control_panel.collision_check.setChecked(checked)
        self.simulation_widget.set_collision_detection(checked)

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.status_bar.showMessage('退出全屏模式', 2000)
        else:
            self.showFullScreen()
            self.status_bar.showMessage('进入全屏模式，按F11退出', 2000)

    def _export_map(self):
        """导出地图"""
        # 这里可以调用仿真组件的导出功能
        self.status_bar.showMessage('地图导出功能开发中...', 3000)

    def _export_logs(self):
        """导出日志"""
        self.control_panel._export_log()

    def _export_statistics(self):
        """导出统计报告"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            import datetime

            filename, _ = QFileDialog.getSaveFileName(
                self, "导出统计报告",
                f"agv_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json)"
            )

            if filename:
                # 收集统计数据
                map_info = self.simulation_widget.get_map_info()
                order_stats = self.simulation_widget.get_task_scheduler().get_statistics()
                generator_stats = self.simulation_widget.get_order_generator().get_statistics()
                charging_stats = self.simulation_widget.get_charging_stations()

                stats_data = {
                    'export_time': datetime.datetime.now().isoformat(),
                    'map_info': map_info,
                    'order_statistics': order_stats,
                    'generator_statistics': generator_stats,
                    'charging_stations': charging_stats,
                    'agv_details': [agv.get_detailed_status() for agv in self.simulation_widget.agvs]
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, ensure_ascii=False, indent=2)

                self.status_bar.showMessage(f'统计报告已导出到: {filename}', 3000)

        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出统计报告失败:\n{str(e)}")

    def _show_usage(self):
        """显示使用说明"""
        usage_text = """增强AGV智能仿真系统使用说明:

🚀 新功能特性:
• 订单系统: 泊松分布自动生成订单，支持优先级管理
• 电量管理: 真实电量消耗，自动充电，低电量预警
• 任务调度: 智能AGV任务分配，多种调度策略
• 完整仿真: 集成运输、充电、等待等完整AGV生命周期

📋 订单管理:
• 自动生成: 按泊松分布随机生成上货→下货任务
• 优先级: 支持普通、高优先级、紧急订单
• 队列管理: 智能订单排队和分配系统
• 实时监控: 订单状态实时显示和统计

🔋 电量系统:
• 真实消耗: 移动、载货时消耗电量，待机时缓慢消耗
• 智能充电: 低电量自动寻找充电站充电
• 电量显示: AGV头顶电量条，电量百分比显示
• 充电站: 支持多AGV同时充电，排队等待

🤖 AGV增强功能:
• 智能调度: 自动分配最优AGV执行订单
• 载货显示: 载货时AGV显示金色圆点
• 状态监控: 详细显示AGV位置、电量、任务状态
• 性能统计: 总里程、完成订单数等统计

🎮 操作指南:
• 鼠标: 滚轮缩放, 右键拖拽, 双击重置
• 点击AGV: 查看详细状态和电量信息
• 点击节点: 手动控制最近的空闲AGV移动
• 快捷键: F5启动 F6暂停 F7重置 P切换暂停

📊 监控面板:
• 主控制: 系统启停、AGV管理、任务调度控制
• 订单管理: 订单生成控制、队列监控
• AGV状态: 详细AGV状态表格，电量监控
• 系统监控: 统计信息、系统日志

🔧 高级功能:
• 调度策略: 支持FIFO、优先级、最近距离等多种策略
• 仿真速度: 可调节0.5x-5x仿真速度
• 数据导出: 支持日志导出、统计报告导出
• 演示模式: 一键启动完整演示

💡 最佳实践:
1. 先添加3-5个AGV
2. 启动订单生成(建议0.5-1.0订单/分钟)
3. 选择合适的调度策略
4. 观察AGV自动执行任务和充电
5. 通过监控面板查看系统状态"""

        QMessageBox.information(self, "使用说明", usage_text)

    def _show_system_status(self):
        """显示系统状态"""
        try:
            map_info = self.simulation_widget.get_map_info()
            agv_stats = map_info.get('agv_stats', {})

            order_stats = self.simulation_widget.get_task_scheduler().get_statistics()
            generator_stats = self.simulation_widget.get_order_generator().get_statistics()

            status_text = f"""系统运行状态报告:

🗺️ 地图信息:
• 节点数量: {map_info['node_count']}
• 路径数量: {map_info['path_count']}
• 充电站数量: {map_info['charging_station_count']}

🤖 AGV状态:
• AGV总数: {map_info['agv_count']}
• 平均电量: {agv_stats.get('avg_battery', 0):.1f}%
• 低电量AGV: {agv_stats.get('low_battery_count', 0)}个
• 正在充电: {agv_stats.get('charging_count', 0)}个
• 总行驶里程: {agv_stats.get('total_distance', 0):.1f}
• 总完成订单: {agv_stats.get('total_orders', 0)}个

📋 订单统计:
• 待处理订单: {order_stats['queue_stats']['pending_count']}
• 处理中订单: {order_stats['queue_stats']['processing_count']}
• 已完成订单: {order_stats['queue_stats']['completed_count']}
• 总订单数: {order_stats['queue_stats']['total_orders']}
• 完成率: {order_stats['queue_stats']['completion_rate'] * 100:.1f}%
• 平均等待时间: {order_stats['queue_stats']['avg_waiting_time']:.1f}秒

🏭 订单生成:
• 生成速率: {generator_stats['generation_rate']:.1f} 订单/分钟
• 总生成数: {generator_stats['total_generated']}
• 生成器状态: {'运行中' if generator_stats['is_active'] else '已停止'}

🎯 任务调度:
• 调度策略: {order_stats['scheduling_strategy']}
• 分配成功率: {order_stats['success_rate'] * 100:.1f}%
• 总分配次数: {order_stats['total_assignments']}
• 活动任务数: {order_stats['active_tasks']}

⏱️ 系统运行:
• 运行时间: {map_info['runtime'] // 3600:.0f}小时{(map_info['runtime'] % 3600) // 60:.0f}分钟
• 仿真状态: {'运行中' if map_info['simulation_running'] else '已暂停'}"""

            QMessageBox.information(self, "系统状态", status_text)

        except Exception as e:
            QMessageBox.warning(self, "获取状态失败", f"无法获取系统状态:\n{str(e)}")

    def _show_about(self):
        """显示关于信息"""
        about_text = """RCS-Lite 增强AGV智能仿真系统

版本: v6.3 - 完整功能版本

🎯 核心功能:
• 数据库地图自动加载
• 智能路径规划(Dijkstra & A*)
• AGV间碰撞检测与避让
• 管控区橙色显示

🚀 增强功能:
• 泊松分布订单生成系统
• 真实电量管理与充电系统
• 智能任务调度与分配
• 完整AGV生命周期仿真

📊 监控功能:
• 实时订单队列管理
• 详细AGV状态监控
• 完整系统统计报告
• 多维度性能分析

🛠️ 技术规格:
• 节点大小: 24×24 像素
• AGV大小: 20×20 像素（带电量显示）
• 路径宽度: 4px
• 箭头尺寸: 10×4 像素
• 刷新频率: ~60 FPS
• 界面框架: PyQt5

🏗️ 系统架构:
• 模块化设计，低耦合
• 订单-调度-执行完整闭环
• 可扩展的调度策略
• 真实场景仿真

开发团队: RCS-Lite
技术支持: AGV仿真实验室

本系统专为教学、研究和工业AGV系统验证设计，
提供完整的AGV调度仿真解决方案。"""

        QMessageBox.about(self, "关于", about_text)

    # =============================================================================
    # 状态更新方法
    # =============================================================================

    def _update_status(self):
        """更新状态栏"""
        try:
            map_info = self.simulation_widget.get_map_info()

            agv_count = map_info['agv_count']
            node_count = map_info['node_count']

            # 获取额外统计信息
            agv_stats = map_info.get('agv_stats', {})
            avg_battery = agv_stats.get('avg_battery', 0)

            order_stats = self.simulation_widget.get_task_scheduler().get_statistics()
            pending_orders = order_stats['queue_stats']['pending_count']

            runtime = map_info['runtime']
            runtime_str = f"{int(runtime // 3600):02d}:{int((runtime % 3600) // 60):02d}:{int(runtime % 60):02d}"

            status_text = (f"节点: {node_count} | AGV: {agv_count} | "
                           f"平均电量: {avg_battery:.1f}% | "
                           f"待处理订单: {pending_orders} | "
                           f"运行时间: {runtime_str} | "
                           f"状态: {'运行' if map_info['simulation_running'] else '暂停'}")

            self.status_bar.showMessage(status_text)

        except Exception as e:
            self.status_bar.showMessage(f"状态更新失败: {str(e)}")

    # =============================================================================
    # 窗口事件方法
    # =============================================================================

    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出增强AGV仿真系统吗？\n未保存的数据将丢失。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 停止所有定时器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            if hasattr(self.simulation_widget, 'timer'):
                self.simulation_widget.timer.stop()

            # 停止子系统
            self.simulation_widget.order_generator.stop_generation()

            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """全局键盘事件处理"""
        if event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
        elif event.key() == Qt.Key_F5:
            self._start_simulation()
        elif event.key() == Qt.Key_F6:
            self._pause_simulation()
        elif event.key() == Qt.Key_F7:
            self._reset_simulation()
        else:
            self.simulation_widget.keyPressEvent(event)

    # =============================================================================
    # 公共接口方法
    # =============================================================================

    def get_simulation_widget(self):
        """获取仿真组件"""
        return self.simulation_widget

    def get_control_panel(self):
        """获取控制面板"""
        return self.control_panel