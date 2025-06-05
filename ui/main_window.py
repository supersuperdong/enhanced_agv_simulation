"""
主窗口模块 - 简化版
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter,
                             QStatusBar, QApplication)
from PyQt5.QtCore import Qt, QTimer

from ui.simulation_widget import SimulationWidget
from ui.control_panel import ControlPanel


class MainWindow(QMainWindow):
    """AGV仿真系统主窗口 - 简化版"""

    DEFAULT_WIDTH = 1750
    DEFAULT_HEIGHT = 1050
    MIN_WIDTH = 1200
    MIN_HEIGHT = 800

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_widgets()
        self._create_status_bar()
        self._setup_layout()
        self._setup_timer()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("RCS-Lite AGV智能仿真系统 v7.0")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _create_widgets(self):
        """创建主要组件"""
        self.simulation_widget = SimulationWidget()
        self.control_panel = ControlPanel(self.simulation_widget)

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('就绪')

    def _setup_layout(self):
        """设置布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.simulation_widget)
        splitter.addWidget(self.control_panel)
        splitter.setSizes([int(self.DEFAULT_WIDTH * 0.8), int(self.DEFAULT_WIDTH * 0.2)])

        layout = QHBoxLayout(central_widget)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)

    def _setup_timer(self):
        """设置定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)

    def _update_status(self):
        """更新状态栏"""
        try:
            map_info = self.simulation_widget.get_map_info()
            agv_count = map_info['agv_count']
            node_count = map_info['node_count']

            stats = self.simulation_widget.scheduler.get_statistics()

            status_text = f"节点: {node_count} | AGV: {agv_count} | 订单: {stats['总订单']} | {map_info['source']}"
            self.status_bar.showMessage(status_text)

        except Exception:
            self.status_bar.showMessage("状态更新失败")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        if hasattr(self.simulation_widget, 'timer'):
            self.simulation_widget.timer.stop()
        if hasattr(self.simulation_widget, 'scheduler_timer'):
            self.simulation_widget.scheduler_timer.stop()
        event.accept()

    def keyPressEvent(self, event):
        """全局键盘事件处理"""
        self.simulation_widget.keyPressEvent(event)

    def get_simulation_widget(self):
        """获取仿真组件"""
        return self.simulation_widget

    def get_control_panel(self):
        """获取控制面板"""
        return self.control_panel