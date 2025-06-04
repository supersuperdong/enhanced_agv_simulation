"""
性能监控工具
监控系统性能、内存使用、FPS等指标
"""

import time
import psutil
import threading
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    fps: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    agv_count: int
    order_count: int
    task_queue_size: int
    frame_time_ms: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'fps': self.fps,
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'memory_percent': self.memory_percent,
            'agv_count': self.agv_count,
            'order_count': self.order_count,
            'task_queue_size': self.task_queue_size,
            'frame_time_ms': self.frame_time_ms
        }


class FPSCounter:
    """FPS计数器"""

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_frame_time = time.time()

    def tick(self) -> float:
        """记录一帧，返回当前FPS"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time

        if len(self.frame_times) < 2:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_avg_frame_time_ms(self) -> float:
        """获取平均帧时间（毫秒）"""
        if not self.frame_times:
            return 0.0
        return (sum(self.frame_times) / len(self.frame_times)) * 1000


class PerformanceMonitor(QObject):
    """性能监控器"""

    # 信号
    metrics_updated = pyqtSignal(object)  # PerformanceMetrics
    alert_triggered = pyqtSignal(str, str)  # alert_type, message

    def __init__(self, simulation_widget=None):
        super().__init__()
        self.simulation_widget = simulation_widget

        # 监控配置
        self.enabled = False
        self.sample_interval = 1.0  # 秒
        self.max_history_size = 1000

        # 数据存储
        self.metrics_history = deque(maxlen=self.max_history_size)
        self.fps_counter = FPSCounter()

        # 系统监控
        self.process = psutil.Process()

        # 性能阈值
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'fps_min': 20.0,
            'frame_time_max_ms': 50.0
        }

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._collect_metrics)

        # 统计信息
        self.start_time = time.time()
        self.total_frames = 0
        self.alert_count = 0

    def start_monitoring(self):
        """开始监控"""
        if not self.enabled:
            self.enabled = True
            self.start_time = time.time()
            self.timer.start(int(self.sample_interval * 1000))
            print("性能监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if self.enabled:
            self.enabled = False
            self.timer.stop()
            print("性能监控已停止")

    def tick_frame(self):
        """记录一帧（由主循环调用）"""
        if self.enabled:
            self.total_frames += 1
            self.fps_counter.tick()

    def _collect_metrics(self):
        """收集性能指标"""
        if not self.enabled:
            return

        try:
            # 获取系统指标
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # 获取FPS和帧时间
            fps = self.fps_counter.get_avg_frame_time_ms()
            current_fps = 1000.0 / fps if fps > 0 else 0.0

            # 获取仿真指标
            agv_count = 0
            order_count = 0
            task_queue_size = 0

            if self.simulation_widget:
                agv_count = len(getattr(self.simulation_widget, 'agvs', []))

                if hasattr(self.simulation_widget, 'task_scheduler'):
                    scheduler = self.simulation_widget.task_scheduler
                    order_queue = scheduler.order_queue
                    order_count = (len(order_queue.pending_orders) +
                                   len(order_queue.processing_orders))
                    task_queue_size = len(scheduler.agv_tasks)

            # 创建指标对象
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                fps=current_fps,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                agv_count=agv_count,
                order_count=order_count,
                task_queue_size=task_queue_size,
                frame_time_ms=fps
            )

            # 存储指标
            self.metrics_history.append(metrics)

            # 检查阈值
            self._check_thresholds(metrics)

            # 发送信号
            self.metrics_updated.emit(metrics)

        except Exception as e:
            print(f"性能指标收集失败: {e}")

    def _check_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        alerts = []

        # CPU使用率检查
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")

        # 内存使用率检查
        if metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")

        # FPS检查
        if metrics.fps < self.thresholds['fps_min']:
            alerts.append(f"FPS过低: {metrics.fps:.1f}")

        # 帧时间检查
        if metrics.frame_time_ms > self.thresholds['frame_time_max_ms']:
            alerts.append(f"帧时间过长: {metrics.frame_time_ms:.1f}ms")

        # 发送警报
        for alert in alerts:
            self.alert_count += 1
            self.alert_triggered.emit("performance", alert)

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前指标"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, count: int = None) -> List[PerformanceMetrics]:
        """获取指标历史"""
        if count is None:
            return list(self.metrics_history)
        else:
            return list(self.metrics_history)[-count:]

    def get_average_metrics(self, duration_seconds: int = 60) -> Dict:
        """获取指定时间段的平均指标"""
        if not self.metrics_history:
            return {}

        cutoff_time = time.time() - duration_seconds
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {}

        return {
            'avg_fps': sum(m.fps for m in recent_metrics) / len(recent_metrics),
            'avg_cpu': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_mb': sum(m.memory_mb for m in recent_metrics) / len(recent_metrics),
            'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'avg_frame_time_ms': sum(m.frame_time_ms for m in recent_metrics) / len(recent_metrics),
            'sample_count': len(recent_metrics)
        }

    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        runtime = time.time() - self.start_time
        avg_metrics = self.get_average_metrics(300)  # 5分钟平均值

        current = self.get_current_metrics()

        return {
            'runtime_seconds': runtime,
            'total_frames': self.total_frames,
            'overall_avg_fps': self.total_frames / runtime if runtime > 0 else 0,
            'alert_count': self.alert_count,
            'metrics_collected': len(self.metrics_history),
            'current_metrics': current.to_dict() if current else None,
            'recent_averages': avg_metrics,
            'monitoring_enabled': self.enabled
        }

    def export_metrics(self, filepath: str, format: str = 'json') -> bool:
        """导出性能指标"""
        try:
            import json
            import csv

            data = [m.to_dict() for m in self.metrics_history]

            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        'summary': self.get_performance_summary(),
                        'metrics': data
                    }, f, indent=2)

            elif format.lower() == 'csv':
                if data:
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)

            print(f"性能指标导出成功: {filepath}")
            return True

        except Exception as e:
            print(f"性能指标导出失败: {e}")
            return False

    def reset_metrics(self):
        """重置指标"""
        self.metrics_history.clear()
        self.fps_counter = FPSCounter()
        self.start_time = time.time()
        self.total_frames = 0
        self.alert_count = 0
        print("性能指标已重置")

    def set_thresholds(self, **kwargs):
        """设置性能阈值"""
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value
                print(f"阈值更新: {key} = {value}")

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        try:
            import platform

            # CPU信息
            cpu_info = {
                'count': psutil.cpu_count(),
                'physical_count': psutil.cpu_count(logical=False),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }

            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': memory.total / 1024 ** 3,
                'available_gb': memory.available / 1024 ** 3,
                'percent_used': memory.percent
            }

            # 系统信息
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture()[0]
            }

            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'system': system_info,
                'process_info': {
                    'pid': self.process.pid,
                    'create_time': self.process.create_time(),
                    'num_threads': self.process.num_threads()
                }
            }

        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return {}


class PerformanceAnalyzer:
    """性能分析器"""

    @staticmethod
    def analyze_fps_stability(metrics: List[PerformanceMetrics]) -> Dict:
        """分析FPS稳定性"""
        if len(metrics) < 10:
            return {"error": "数据点不足"}

        fps_values = [m.fps for m in metrics]

        avg_fps = sum(fps_values) / len(fps_values)
        min_fps = min(fps_values)
        max_fps = max(fps_values)

        # 计算标准差
        variance = sum((x - avg_fps) ** 2 for x in fps_values) / len(fps_values)
        std_dev = variance ** 0.5

        # 计算变异系数
        cv = (std_dev / avg_fps) * 100 if avg_fps > 0 else 0

        # 稳定性评级
        if cv < 5:
            stability = "excellent"
        elif cv < 10:
            stability = "good"
        elif cv < 20:
            stability = "fair"
        else:
            stability = "poor"

        return {
            'avg_fps': avg_fps,
            'min_fps': min_fps,
            'max_fps': max_fps,
            'std_dev': std_dev,
            'coefficient_of_variation': cv,
            'stability_rating': stability,
            'sample_count': len(fps_values)
        }

    @staticmethod
    def analyze_resource_usage(metrics: List[PerformanceMetrics]) -> Dict:
        """分析资源使用情况"""
        if not metrics:
            return {"error": "无数据"}

        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_mb for m in metrics]

        return {
            'cpu_usage': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'avg_mb': sum(memory_values) / len(memory_values),
                'max_mb': max(memory_values),
                'min_mb': min(memory_values),
                'growth_mb': memory_values[-1] - memory_values[0] if len(memory_values) > 1 else 0
            }
        }

    @staticmethod
    def find_performance_bottlenecks(metrics: List[PerformanceMetrics]) -> List[str]:
        """查找性能瓶颈"""
        bottlenecks = []

        if not metrics:
            return bottlenecks

        recent_metrics = metrics[-30:]  # 最近30个样本

        # 检查FPS问题
        avg_fps = sum(m.fps for m in recent_metrics) / len(recent_metrics)
        if avg_fps < 30:
            bottlenecks.append(f"FPS过低 (平均 {avg_fps:.1f})")

        # 检查CPU问题
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu > 70:
            bottlenecks.append(f"CPU使用率高 (平均 {avg_cpu:.1f}%)")

        # 检查内存问题
        memory_growth = recent_metrics[-1].memory_mb - recent_metrics[0].memory_mb
        if memory_growth > 50:  # 50MB增长
            bottlenecks.append(f"内存增长异常 (+{memory_growth:.1f}MB)")

        # 检查帧时间问题
        avg_frame_time = sum(m.frame_time_ms for m in recent_metrics) / len(recent_metrics)
        if avg_frame_time > 33:  # 超过30FPS对应的帧时间
            bottlenecks.append(f"帧时间过长 (平均 {avg_frame_time:.1f}ms)")

        return bottlenecks

    @staticmethod
    def generate_performance_report(monitor: PerformanceMonitor) -> str:
        """生成性能报告"""
        summary = monitor.get_performance_summary()
        metrics = monitor.get_metrics_history()

        if not metrics:
            return "无性能数据可用于分析"

        fps_analysis = PerformanceAnalyzer.analyze_fps_stability(metrics)
        resource_analysis = PerformanceAnalyzer.analyze_resource_usage(metrics)
        bottlenecks = PerformanceAnalyzer.find_performance_bottlenecks(metrics)

        report = f"""性能分析报告
==================

运行概况:
- 运行时间: {summary['runtime_seconds']:.1f} 秒
- 总帧数: {summary['total_frames']}
- 平均FPS: {summary['overall_avg_fps']:.1f}
- 警报次数: {summary['alert_count']}

FPS分析:
- 平均FPS: {fps_analysis.get('avg_fps', 0):.1f}
- FPS范围: {fps_analysis.get('min_fps', 0):.1f} - {fps_analysis.get('max_fps', 0):.1f}
- 稳定性: {fps_analysis.get('stability_rating', 'unknown')}
- 变异系数: {fps_analysis.get('coefficient_of_variation', 0):.1f}%

资源使用:
- 平均CPU: {resource_analysis.get('cpu_usage', {}).get('avg', 0):.1f}%
- 峰值CPU: {resource_analysis.get('cpu_usage', {}).get('max', 0):.1f}%
- 平均内存: {resource_analysis.get('memory_usage', {}).get('avg_mb', 0):.1f} MB
- 内存增长: {resource_analysis.get('memory_usage', {}).get('growth_mb', 0):.1f} MB

性能瓶颈:
"""

        if bottlenecks:
            for bottleneck in bottlenecks:
                report += f"- {bottleneck}\n"
        else:
            report += "- 未发现明显瓶颈\n"

        return report


# 全局性能监控器实例
performance_monitor = None


def get_performance_monitor(simulation_widget=None) -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor(simulation_widget)
    return performance_monitor


def start_performance_monitoring(simulation_widget=None):
    """启动性能监控"""
    monitor = get_performance_monitor(simulation_widget)
    monitor.start_monitoring()
    return monitor


def stop_performance_monitoring():
    """停止性能监控"""
    if performance_monitor:
        performance_monitor.stop_monitoring()