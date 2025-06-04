# RCS-Lite AGV增强仿真系统 - API参考文档

## 概述

本文档提供了RCS-Lite AGV增强仿真系统的完整API参考，包括所有主要类、方法和配置选项。

## 核心模块

### 1. 订单系统 (Order System)

#### Order 类

表示单个订单的核心类。

```python
class Order:
    def __init__(self, pickup_node_id: str, dropoff_node_id: str, priority: OrderPriority = OrderPriority.NORMAL)
```

**属性:**
- `id: str` - 唯一订单ID
- `pickup_node_id: str` - 上货点节点ID
- `dropoff_node_id: str` - 下货点节点ID
- `priority: OrderPriority` - 订单优先级
- `status: OrderStatus` - 订单状态
- `create_time: float` - 创建时间戳
- `deadline: float` - 截止时间戳
- `assigned_agv_id: int` - 分配的AGV ID

**方法:**

```python
def assign_to_agv(self, agv_id: int) -> None:
    """分配订单给指定AGV"""

def start_execution(self) -> None:
    """开始执行订单"""

def complete(self) -> None:
    """完成订单"""

def cancel(self) -> None:
    """取消订单"""

def is_expired(self) -> bool:
    """检查订单是否过期"""

def get_remaining_time(self) -> float:
    """获取剩余时间（秒）"""

def to_dict(self) -> dict:
    """转换为字典格式"""
```

#### OrderGenerator 类

订单生成器，支持泊松分布生成。

```python
class OrderGenerator(QObject):
    def __init__(self, nodes_dict: dict)
```

**信号:**
- `order_generated = pyqtSignal(object)` - 新订单生成信号

**方法:**

```python
def set_generation_rate(self, lambda_rate: float) -> None:
    """设置生成速率（每分钟平均订单数）"""

def start_generation(self) -> None:
    """开始自动生成订单"""

def stop_generation(self) -> None:
    """停止自动生成订单"""

def manual_generate_order(self, pickup_node_id: str = None, 
                         dropoff_node_id: str = None, 
                         priority: OrderPriority = None) -> Order:
    """手动生成订单"""

def get_statistics(self) -> dict:
    """获取生成统计信息"""
```

### 2. 电量系统 (Battery System)

#### BatterySystem 类

AGV电量管理系统。

```python
class BatterySystem:
    def __init__(self, capacity: float = 100.0, initial_charge: float = 100.0)
```

**属性:**
- `capacity: float` - 电池总容量 (%)
- `current_charge: float` - 当前电量 (%)
- `discharge_rate_moving: float` - 移动时放电速率 (%/秒)
- `discharge_rate_idle: float` - 待机时放电速率 (%/秒)
- `charge_rate: float` - 充电速率 (%/秒)
- `is_charging: bool` - 是否正在充电

**方法:**

```python
def update(self, is_moving: bool = False, is_carrying_cargo: bool = False) -> None:
    """更新电量状态"""

def start_charging(self) -> None:
    """开始充电"""

def stop_charging(self) -> None:
    """停止充电"""

def can_move(self) -> bool:
    """检查是否有足够电量移动"""

def needs_charging(self) -> bool:
    """检查是否需要充电"""

def needs_immediate_charging(self) -> bool:
    """检查是否需要立即充电"""

def is_fully_charged(self) -> bool:
    """检查是否满电"""

def get_battery_status(self) -> BatteryStatus:
    """获取电量状态枚举"""

def estimate_remaining_time(self, is_moving: bool = False, 
                          is_carrying_cargo: bool = False) -> float:
    """估算剩余使用时间（分钟）"""

def can_complete_task(self, estimated_task_time_minutes: float, 
                     is_moving: bool = True, 
                     is_carrying_cargo: bool = True) -> bool:
    """检查是否有足够电量完成任务"""

def get_statistics(self) -> dict:
    """获取电量统计信息"""
```

#### ChargingStation 类

充电站管理类。

```python
class ChargingStation:
    def __init__(self, node_id: str, max_agvs: int = 2)
```

**方法:**

```python
def can_accept_agv(self) -> bool:
    """检查是否能接受新的AGV"""

def add_agv_to_charge(self, agv_id: int) -> bool:
    """添加AGV到充电站"""

def remove_agv_from_charge(self, agv_id: int) -> int:
    """从充电站移除AGV，返回下一个等待的AGV ID"""

def is_agv_charging(self, agv_id: int) -> bool:
    """检查AGV是否正在充电"""

def get_status(self) -> dict:
    """获取充电站状态"""
```

### 3. 任务调度系统 (Task Scheduling)

#### TaskScheduler 类

智能任务调度器。

```python
class TaskScheduler(QObject):
    def __init__(self, simulation_widget)
```

**信号:**
- `task_assigned = pyqtSignal(str, object)` - 任务分配信号
- `task_completed = pyqtSignal(str, object)` - 任务完成信号

**方法:**

```python
def add_order(self, order: Order) -> None:
    """添加新订单到队列"""

def update(self) -> None:
    """更新调度器（需要定期调用）"""

def set_scheduling_strategy(self, strategy: SchedulingStrategy) -> None:
    """设置调度策略"""

def force_assign_order(self, order_id: str, agv_id: int) -> bool:
    """强制分配订单给指定AGV"""

def get_statistics(self) -> dict:
    """获取调度统计信息"""
```

#### OrderQueue 类

订单队列管理器。

```python
class OrderQueue:
    def __init__(self)
```

**方法:**

```python
def add_order(self, order: Order) -> None:
    """添加新订单"""

def get_next_order(self, strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY) -> Order:
    """获取下一个要处理的订单"""

def assign_order(self, order: Order, agv_id: int) -> None:
    """分配订单给AGV"""

def complete_order(self, agv_id: int) -> None:
    """完成订单"""

def cancel_order(self, order_id: str) -> bool:
    """取消订单"""

def clean_expired_orders(self) -> int:
    """清理过期订单"""

def get_statistics(self) -> dict:
    """获取队列统计信息"""
```

### 4. 增强AGV模型

#### EnhancedAGV 类

集成了电量和订单处理的增强AGV类。

```python
class EnhancedAGV:
    def __init__(self, agv_id: int, start_node: Node)
```

**属性:**
- `id: int` - AGV唯一ID
- `battery_system: BatterySystem` - 电量管理系统
- `current_order: Order` - 当前执行的订单
- `is_carrying_cargo: bool` - 是否载货
- `total_orders_completed: int` - 完成的订单总数
- `total_distance_traveled: float` - 总行驶距离

**方法:**

```python
def assign_order(self, order: Order) -> None:
    """分配订单给AGV"""

def move(self, nodes: dict, other_agvs: list) -> None:
    """移动逻辑（集成电量检查）"""

def get_detailed_status(self) -> dict:
    """获取详细状态信息"""

def destroy(self) -> None:
    """清理资源"""
```

### 5. 仿真组件

#### EnhancedSimulationWidget 类

增强的仿真显示组件。

```python
class EnhancedSimulationWidget(QWidget):
    def __init__(self, parent=None)
```

**方法:**

```python
def add_agv(self, start_node_id: str = None) -> EnhancedAGV:
    """添加增强AGV"""

def remove_agv(self, agv_id: int) -> bool:
    """移除AGV"""

def send_agv_to_target(self, agv_id: int, target_node_id: str, 
                      algorithm: str = 'dijkstra') -> bool:
    """发送AGV到目标（考虑电量）"""

def stop_all_agvs(self) -> None:
    """停止所有AGV"""

def pause_simulation(self) -> None:
    """暂停仿真"""

def resume_simulation(self) -> None:
    """恢复仿真"""

def set_simulation_speed(self, speed: float) -> None:
    """设置仿真速度"""

def get_order_generator(self) -> OrderGenerator:
    """获取订单生成器"""

def get_task_scheduler(self) -> TaskScheduler:
    """获取任务调度器"""

def get_charging_stations(self) -> dict:
    """获取充电站信息"""

def get_map_info(self) -> dict:
    """获取地图信息"""
```

## 配置系统

### ConfigManager 类

配置管理器，支持JSON、YAML、INI等格式。

```python
class ConfigManager:
    def __init__(self, config_dir: str = "config")
```

**方法:**

```python
def load_all_configs(self) -> None:
    """加载所有配置"""

def save_all_configs(self) -> None:
    """保存所有配置"""

def update_simulation_config(self, **kwargs) -> None:
    """更新仿真配置"""

def update_ui_config(self, **kwargs) -> None:
    """更新UI配置"""

def export_config(self, filepath: str) -> bool:
    """导出配置到文件"""

def import_config(self, filepath: str) -> bool:
    """从文件导入配置"""

def reset_to_defaults(self) -> None:
    """重置为默认配置"""

def validate_config(self) -> dict:
    """验证配置有效性"""
```

**配置访问:**

```python
from utils.config_manager import get_config, get_simulation_config, get_ui_config

# 获取配置管理器
config = get_config()

# 获取仿真配置
sim_config = get_simulation_config()
print(f"AGV默认速度: {sim_config.agv_default_speed}")

# 获取UI配置
ui_config = get_ui_config()
print(f"主题: {ui_config.theme}")
```

## 性能监控

### PerformanceMonitor 类

性能监控工具。

```python
class PerformanceMonitor(QObject):
    def __init__(self, simulation_widget=None)
```

**信号:**
- `metrics_updated = pyqtSignal(object)` - 指标更新信号
- `alert_triggered = pyqtSignal(str, str)` - 警报触发信号

**方法:**

```python
def start_monitoring(self) -> None:
    """开始监控"""

def stop_monitoring(self) -> None:
    """停止监控"""

def tick_frame(self) -> None:
    """记录一帧（由主循环调用）"""

def get_current_metrics(self) -> PerformanceMetrics:
    """获取当前指标"""

def get_performance_summary(self) -> dict:
    """获取性能摘要"""

def export_metrics(self, filepath: str, format: str = 'json') -> bool:
    """导出性能指标"""

def set_thresholds(self, **kwargs) -> None:
    """设置性能阈值"""
```

## 数据分析

### AGVDataAnalyzer 类

数据分析工具。

```python
class AGVDataAnalyzer:
    def __init__(self)
```

**方法:**

```python
def load_simulation_data(self, data_source) -> bool:
    """加载仿真数据"""

def analyze_order_performance(self) -> AnalysisResult:
    """分析订单性能"""

def analyze_agv_efficiency(self) -> AnalysisResult:
    """分析AGV效率"""

def analyze_battery_usage(self) -> AnalysisResult:
    """分析电量使用情况"""

def generate_comprehensive_report(self, output_dir: str = "analysis_output") -> str:
    """生成综合分析报告"""

def create_order_trend_chart(self, output_path: str) -> str:
    """创建订单趋势图"""

def create_agv_efficiency_chart(self, output_path: str) -> str:
    """创建AGV效率图表"""
```

## 枚举类型

### OrderStatus
```python
class OrderStatus(Enum):
    PENDING = "待分配"
    ASSIGNED = "已分配"
    IN_PROGRESS = "执行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    EXPIRED = "已过期"
```

### OrderPriority
```python
class OrderPriority(Enum):
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    EMERGENCY = 10
```

### BatteryStatus
```python
class BatteryStatus(Enum):
    FULL = "满电"
    HIGH = "电量充足"
    MEDIUM = "电量正常"
    LOW = "电量不足"
    CRITICAL = "电量危险"
    EMPTY = "电量耗尽"
    CHARGING = "充电中"
```

### SchedulingStrategy
```python
class SchedulingStrategy(Enum):
    FIFO = "先进先出"
    PRIORITY = "优先级调度"
    SHORTEST_JOB = "最短作业优先"
    NEAREST_FIRST = "最近距离优先"
    DEADLINE_FIRST = "截止时间优先"
    BALANCED = "平衡调度"
```

## 使用示例

### 基础使用

```python
from ui.main_window import EnhancedMainWindow
from PyQt5.QtWidgets import QApplication

# 创建应用程序
app = QApplication([])
window = EnhancedMainWindow()

# 获取仿真组件
simulation = window.get_simulation_widget()

# 添加AGV
agv = simulation.add_agv()
print(f"添加了AGV #{agv.id}")

# 启动订单生成
order_generator = simulation.get_order_generator()
order_generator.set_generation_rate(1.0)  # 每分钟1个订单
order_generator.start_generation()

# 显示窗口
window.show()
app.exec_()
```

### 配置自定义

```python
from utils.config_manager import get_config

config = get_config()

# 更新仿真配置
config.update_simulation_config(
    agv_default_speed=3.0,
    default_generation_rate=2.0,
    low_battery_threshold=25.0
)

# 更新UI配置
config.update_ui_config(
    theme="dark",
    font_size=12
)
```

### 性能监控

```python
from utils.performance_monitor import start_performance_monitoring

# 启动性能监控
monitor = start_performance_monitoring(simulation)

# 设置自定义阈值
monitor.set_thresholds(
    cpu_percent=70.0,
    memory_percent=80.0,
    fps_min=30.0
)

# 导出性能数据
monitor.export_metrics("performance_data.json")
```

### 数据分析

```python
from utils.data_analyzer import AGVDataAnalyzer

# 创建分析器
analyzer = AGVDataAnalyzer()

# 加载数据
analyzer.load_simulation_data("simulation_data.json")

# 生成报告
report_path = analyzer.generate_comprehensive_report("analysis_output")
print(f"分析报告已生成: {report_path}")
```

## 事件和信号

### 订单系统事件
- `order_generated` - 新订单生成
- `order_assigned` - 订单分配
- `order_completed` - 订单完成

### 任务调度事件
- `task_assigned` - 任务分配
- `task_completed` - 任务完成

### 性能监控事件
- `metrics_updated` - 性能指标更新
- `alert_triggered` - 性能警报

### 连接事件示例

```python
def on_order_generated(order):
    print(f"新订单: {order.id}")

def on_task_assigned(agv_id, task):
    print(f"AGV {agv_id} 接受任务")

# 连接信号
order_generator.order_generated.connect(on_order_generated)
task_scheduler.task_assigned.connect(on_task_assigned)
```

## 错误处理

所有API方法都包含适当的错误处理。建议在调用API时使用try-except块：

```python
try:
    agv = simulation.add_agv("invalid_node_id")
except Exception as e:
    print(f"添加AGV失败: {e}")
```

## 线程安全

- 订单生成器和任务调度器使用Qt信号机制，保证线程安全
- 性能监控器使用独立线程，不影响主界面
- 所有UI操作必须在主线程中进行

## 性能建议

1. **订单生成速率**: 建议0.5-2.0订单/分钟
2. **AGV数量**: 根据地图大小调整，建议节点数/50
3. **充电站配置**: 建议每20个AGV配置1个充电站
4. **监控间隔**: 性能监控建议1秒间隔

## 扩展开发

### 自定义调度策略

```python
class CustomScheduler(TaskScheduler):
    def _calculate_agv_score(self, agv, order):
        # 实现自定义评分算法
        score = super()._calculate_agv_score(agv, order)
        # 添加自定义逻辑
        return score
```

### 自定义电量策略

```python
class CustomBattery(BatterySystem):
    def needs_charging(self):
        # 实现自定义充电逻辑
        return self.current_charge < 25.0
```

---

更多详细信息请参考源代码注释和INTEGRATION_GUIDE.md文档。