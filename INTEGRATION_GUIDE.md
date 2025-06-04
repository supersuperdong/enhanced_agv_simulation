# RCS-Lite AGV 增强仿真系统集成指南

## 概述

这个增强版本在原有的AGV仿真系统基础上，新增了三个核心功能：

1. **订单系统** - 基于泊松分布的动态订单生成
2. **电量系统** - 真实的AGV电量管理和充电机制
3. **任务调度系统** - 智能的订单分配和AGV调度

## 🚀 新增功能详解

### 1. 订单系统 (Order System)

#### 核心特性
- **泊松分布生成**: 模拟真实工厂环境中的随机订单到达
- **优先级管理**: 支持普通、高优先级、紧急等多种订单类型
- **智能路线**: 自动在上料点(PP)和下料点(AP)之间生成任务
- **时间管理**: 订单截止时间、等待时间、完成时间统计

#### 使用方法
```python
# 启动订单生成
order_generator = simulation_widget.get_order_generator()
order_generator.set_generation_rate(1.0)  # 每分钟1个订单
order_generator.start_generation()

# 手动生成订单
order = order_generator.manual_generate_order(
    pickup_node_id='PP99',
    dropoff_node_id='AP120',
    priority=OrderPriority.HIGH
)
```

### 2. 电量系统 (Battery System)

#### 核心特性
- **真实消耗**: 移动时消耗0.8%/秒，载货时额外消耗1.2%/秒
- **智能充电**: 低电量时自动寻找充电站，充电速率8%/秒
- **可视化显示**: AGV头顶电量条，低电量红色预警
- **充电站管理**: 支持多AGV排队充电，充电位占用管理

#### 使用方法
```python
# 获取AGV电量信息
agv = simulation_widget.agvs[0]
battery_status = agv.battery_system.get_statistics()
print(f"电量: {battery_status['current_charge']:.1f}%")

# 手动开始充电
if agv.current_node.node_type == 'charging':
    agv.battery_system.start_charging()
```

### 3. 任务调度系统 (Task Scheduling)

#### 核心特性
- **多种策略**: FIFO、优先级、最短距离、截止时间等调度算法
- **智能分配**: 考虑AGV位置、电量、任务复杂度的最优分配
- **消息队列**: 订单队列管理，支持实时监控和统计
- **完整生命周期**: 上货→运输→下货→充电的完整任务流程

#### 调度策略说明
- **FIFO**: 先到先服务，适合均匀负载
- **PRIORITY**: 优先级调度，紧急订单优先
- **SHORTEST_JOB**: 最短任务优先，提高吞吐量
- **NEAREST_FIRST**: 最近距离优先，减少空载时间
- **BALANCED**: 平衡调度，综合考虑多种因素

## 📁 新增文件结构

```
agv_simulation_system/
├── models/
│   ├── order.py                    # 订单系统
│   ├── battery_system.py           # 电量管理
│   ├── task_scheduler.py           # 任务调度
│   ├── enhanced_agv.py             # 增强AGV模型
│   └── __init__.py                 # 更新的模型导入
├── ui/
│   ├── enhanced_simulation_widget.py   # 增强仿真组件
│   ├── enhanced_control_panel.py       # 增强控制面板
│   └── enhanced_main_window.py         # 增强主窗口
├── enhanced_main.py                # 新的主程序入口
└── INTEGRATION_GUIDE.md           # 本集成指南
```

## 🔧 集成步骤

### 步骤1: 安装依赖

确保已安装所有必要的依赖包：

```bash
pip install PyQt5 pandas numpy
```

### 步骤2: 使用增强版本

#### 选项A: 直接使用增强版本（推荐）

```python
# enhanced_main.py
from ui.enhanced_main_window import EnhancedMainWindow

app = QApplication(sys.argv)
window = EnhancedMainWindow()
window.show()
sys.exit(app.exec_())
```

#### 选项B: 在现有项目中集成

```python
# 在现有的simulation_widget中集成
from models.order import OrderGenerator
from models.task_scheduler import TaskScheduler
from models.enhanced_agv import EnhancedAGV

class YourSimulationWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 初始化订单系统
        self.order_generator = OrderGenerator(self.nodes)
        self.task_scheduler = TaskScheduler(self)
        
        # 连接信号
        self.order_generator.order_generated.connect(
            self.task_scheduler.add_order
        )
```

### 步骤3: 配置系统参数

```python
# 配置订单生成速率
order_generator.set_generation_rate(0.5)  # 每分钟0.5个订单

# 配置调度策略
task_scheduler.set_scheduling_strategy(SchedulingStrategy.BALANCED)

# 配置AGV电量参数
agv.battery_system.discharge_rate_moving = 0.8  # 移动耗电
agv.battery_system.charge_rate = 8.0           # 充电速率
```

## 🎮 使用指南

### 启动完整演示

1. **运行程序**
   ```bash
   python enhanced_main.py
   ```

2. **启动演示模式**
   - 点击控制面板中的"演示模式"按钮
   - 或使用菜单 "仿真 → 启动仿真"

3. **观察系统运行**
   - AGV自动接受订单并执行运输任务
   - 低电量时自动前往充电站充电
   - 实时显示订单队列和AGV状态

### 手动控制

#### 订单管理
```python
# 手动生成订单
order_generator.manual_generate_order()

# 调整生成速率
order_generator.set_generation_rate(2.0)  # 每分钟2个订单

# 暂停/恢复生成
order_generator.stop_generation()
order_generator.start_generation()
```

#### AGV管理
```python
# 添加AGV
agv = simulation_widget.add_agv()

# 检查AGV状态
status = agv.get_detailed_status()
print(status)

# 强制充电
if agv.battery_system.needs_charging():
    # AGV会自动寻找充电站
    pass
```

#### 调度控制
```python
# 更改调度策略
scheduler.set_scheduling_strategy(SchedulingStrategy.PRIORITY)

# 强制分配订单
scheduler.force_assign_order(order_id, agv_id)

# 获取统计信息
stats = scheduler.get_statistics()
```

## 📊 监控和分析

### 实时监控指标

1. **订单指标**
   - 待处理订单数量
   - 平均等待时间
   - 订单完成率
   - 超时订单数量

2. **AGV指标**
   - 平均电量水平
   - 充电频率
   - 总行驶里程
   - 任务完成数量

3. **系统指标**
   - 整体吞吐量
   - 资源利用率
   - 调度效率
   - 运行时间

### 数据导出

```python
# 导出统计报告
stats_data = {
    'map_info': simulation_widget.get_map_info(),
    'order_stats': task_scheduler.get_statistics(),
    'agv_details': [agv.get_detailed_status() for agv in agvs]
}

# 保存为JSON
import json
with open('simulation_report.json', 'w') as f:
    json.dump(stats_data, f, indent=2)
```

## 🔬 高级功能

### 自定义调度算法

```python
class CustomScheduler(TaskScheduler):
    def _calculate_agv_score(self, agv, order):
        # 实现自定义评分算法
        score = super()._calculate_agv_score(agv, order)
        
        # 添加自定义逻辑
        if agv.total_orders_completed > 10:
            score += 100  # 经验AGV加分
            
        return score
```

### 自定义订单类型

```python
class UrgentOrder(Order):
    def __init__(self, pickup_node_id, dropoff_node_id):
        super().__init__(pickup_node_id, dropoff_node_id, OrderPriority.URGENT)
        self.deadline = self.create_time + 60  # 1分钟截止时间
```

### 电量策略优化

```python
# 自定义电量管理策略
class EcoAGV(EnhancedAGV):
    def _should_charge(self):
        # 实现节能充电策略
        if self.battery_system.current_charge < 20:
            return True
        elif self.is_carrying_cargo and self.battery_system.current_charge < 40:
            return True
        return False
```

## 🛠️ 故障排除

### 常见问题

1. **AGV不移动**
   - 检查电量是否耗尽
   - 确认路径规划是否成功
   - 查看节点占用状态

2. **订单不生成**
   - 确认上料点(PP)和下料点(AP)节点存在
   - 检查订单生成器是否启动
   - 验证生成速率设置

3. **充电不工作**
   - 确认充电点(CP)节点存在
   - 检查充电站是否被占用
   - 验证AGV是否到达充电站

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查系统状态
def debug_system_state():
    print("=== 系统状态 ===")
    print(f"AGV数量: {len(simulation_widget.agvs)}")
    print(f"订单队列: {len(task_scheduler.order_queue.pending_orders)}")
    print(f"充电站状态: {simulation_widget.get_charging_stations()}")
    
    for agv in simulation_widget.agvs:
        status = agv.get_detailed_status()
        print(f"AGV#{agv.id}: {status['status']}, 电量: {status['battery']['charge']:.1f}%")
```

## 📈 性能优化建议

1. **订单生成速率**: 建议0.5-2.0订单/分钟，避免系统过载
2. **AGV数量**: 根据地图大小调整，建议节点数/50个AGV
3. **充电站配置**: 建议每20个AGV配置1个充电站
4. **调度策略**: 复杂地图使用BALANCED，简单地图使用NEAREST_FIRST

## 📚 扩展开发

### 添加新功能模块

1. 在`models/`目录创建新模块
2. 在`__init__.py`中导入
3. 在仿真组件中集成
4. 在控制面板中添加UI

### 贡献代码

1. Fork项目
2. 创建功能分支
3. 实现新功能并添加测试
4. 提交Pull Request

## 📞 技术支持

如有问题，请参考：
- 系统日志输出
- 控制面板状态监控
- 内置帮助文档

---

**祝你使用愉快！这个增强版本将为你提供完整的AGV仿真体验。** 🚀[deployment_checklist.md](../../Downloads/deployment_checklist.md)