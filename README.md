# 🚀 RCS-Lite AGV增强智能仿真系统 v6.3

<div align="center">

![AGV仿真系统](https://img.shields.io/badge/AGV-仿真系统-blue)
![Python](https://img.shields.io/badge/Python-3.7+-green)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

**完整的AGV仿真解决方案 | 订单系统 + 电量管理 + 智能调度**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [安装部署](#-安装部署) • [使用指南](#-使用指南) • [API文档](#-api文档)

</div>

---

## 🎯 项目概述

RCS-Lite AGV增强智能仿真系统是一个功能完整的AGV（自动导引车）仿真平台，集成了**订单管理**、**电量系统**和**智能调度**三大核心功能。系统从原有的基础仿真升级为企业级的完整解决方案，支持教学、研究和工业验证等多种应用场景。

### 🌟 核心亮点

- 🎪 **完整闭环仿真** - 从订单生成到任务完成的全流程仿真
- ⚡ **真实电量模型** - 包含消耗、充电、预警的完整电量管理
- 🧠 **智能任务调度** - 6种调度策略，支持优先级和负载均衡
- 📊 **实时监控分析** - 性能监控、数据分析、可视化报告
- 🎮 **直观用户界面** - 多标签页控制面板，丰富的交互功能
- 🛠️ **高度可配置** - 灵活的配置系统，支持多种预设场景

## ✨ 功能特性

### 📋 订单系统 (Order System)
- **泊松分布生成** - 模拟真实工厂环境的随机订单到达
- **五级优先级** - 低、普通、高、紧急、紧急停机
- **智能路线规划** - 自动在上料点(PP)和下料点(AP)间生成任务
- **完整生命周期** - 创建→分配→执行→完成的全程跟踪
- **超时管理** - 自动处理过期订单，支持截止时间预警

### 🔋 电量系统 (Battery System)
- **真实消耗模型** - 移动、载货、待机的差异化电量消耗
- **智能充电管理** - 低电量自动寻找充电站，支持排队充电
- **可视化显示** - AGV头顶电量条，实时电量百分比
- **多级预警** - 低电量黄色预警，危险电量红色报警
- **充电站管理** - 支持多AGV同时充电，智能队列调度

### 🎯 任务调度系统 (Task Scheduling)
- **6种调度策略** - FIFO、优先级、最近距离、平衡调度等
- **智能AGV选择** - 综合考虑距离、电量、任务能力
- **消息队列管理** - 完整的订单队列和任务分配机制
- **实时负载均衡** - 动态调整任务分配，避免局部过载
- **异常处理** - 支持任务重试、超时处理、故障恢复

### 🤖 增强AGV模型
- **集成电量管理** - 内置电量系统，支持自动充电决策
- **载货可视化** - 载货时显示金色圆点标识
- **状态监控** - 实时显示移动、充电、等待、载货状态
- **性能统计** - 总里程、完成订单数、电量使用历史
- **智能避让** - 碰撞检测和路径重规划

### 📊 监控分析系统
- **实时性能监控** - FPS、CPU、内存使用率监控
- **数据分析工具** - 订单性能、AGV效率、电量使用分析
- **可视化报告** - 自动生成图表和HTML分析报告
- **统计导出** - 支持JSON、CSV、Excel等多种格式

## 🚀 快速开始

### 方法一：一键部署（推荐）

```bash
# 1. 下载快速部署脚本
python setup_agv.py --mode recommended

# 2. 启动系统
python main.py

# 3. 点击"演示模式"快速体验
```

### 方法二：手动安装

```bash
# 1. 安装依赖
pip install PyQt5 pandas numpy matplotlib

# 2. 克隆项目
git clone [项目地址]
cd agv_simulation_system

# 3. 运行系统
python main.py
```

### 🎪 首次体验

1. **启动程序** - 运行 `python enhanced_main.py`
2. **演示模式** - 点击控制面板中的"演示模式"按钮
3. **观察仿真** - 观看AGV自动接受订单、执行运输、充电管理
4. **交互操作** - 点击AGV查看详情，点击节点手动控制
5. **监控数据** - 查看订单队列、AGV状态、系统统计

## 🏗️ 系统架构

```
RCS-Lite AGV增强仿真系统
├── 🎯 核心功能层
│   ├── 📋 订单系统 (Order System)
│   ├── 🔋 电量系统 (Battery System)
│   └── 🎯 调度系统 (Task Scheduling)
├── 🤖 仿真引擎层
│   ├── 增强AGV模型 (Enhanced AGV)
│   ├── 路径规划算法 (A* & Dijkstra)
│   └── 碰撞检测系统 (Collision Detection)
├── 🖥️ 用户界面层
│   ├── 多标签控制面板 (Control Panel)
│   ├── 实时仿真显示 (Simulation View)
│   └── 数据监控面板 (Monitoring Dashboard)
├── 🛠️ 工具支持层
│   ├── 配置管理 (Config Manager)
│   ├── 性能监控 (Performance Monitor)
│   └── 数据分析 (Data Analyzer)
└── 📦 部署服务层
    ├── 快速部署脚本 (Setup Scripts)
    ├── 测试套件 (Test Suite)
    └── 文档系统 (Documentation)
```

## 📁 项目结构

```
agv_simulation_system/
├── 📋 核心模型
│   ├── models/
│   │   ├── order.py                    # 订单系统
│   │   ├── battery_system.py           # 电量管理
│   │   ├── task_scheduler.py           # 任务调度
│   │   ├── enhanced_agv.py             # 增强AGV模型
│   │   └── control_zone_manager.py     # 管控区管理
├── 🎨 用户界面
│   ├── ui/
│   │   ├── enhanced_main_window.py     # 增强主窗口
│   │   ├── enhanced_simulation_widget.py  # 增强仿真组件
│   │   ├── enhanced_control_panel.py   # 增强控制面板
│   │   └── agv_property_dialog.py      # AGV属性对话框
├── 🧠 核心算法
│   ├── algorithms/
│   │   └── path_planner.py             # 路径规划算法
├── 📊 数据处理
│   ├── data/
│   │   └── map_loader.py               # 地图加载器
├── 🛠️ 工具组件
│   ├── utils/
│   │   ├── config_manager.py           # 配置管理
│   │   ├── performance_monitor.py      # 性能监控
│   │   └── data_analyzer.py            # 数据分析
├── 🧪 测试系统
│   ├── tests/
│   │   └── test_enhanced_system.py     # 完整测试套件
├── 📚 文档系统
│   ├── docs/
│   │   └── API_REFERENCE.md            # API参考文档
├── 💡 使用示例
│   ├── examples/
│   │   ├── usage_examples.py           # 完整使用示例
│   │   └── example_configs.py          # 示例配置
├── 🚀 主程序
│   ├── enhanced_main.py                # 增强版主程序
│   ├── setup_enhanced_agv.py           # 快速部署脚本
│   └── requirements_enhanced.txt       # 完整依赖列表
└── 📖 项目文档
    ├── README_ENHANCED.md              # 本文档
    ├── INTEGRATION_GUIDE.md            # 集成指南
    ├── PROJECT_SUMMARY.md              # 项目总结
    └── Map.db                          # 地图数据库
```

## 🎮 使用指南

### 基础操作

| 操作 | 方法 | 说明 |
|------|------|------|
| **缩放地图** | 鼠标滚轮 | 滚轮上下缩放视图 |
| **平移地图** | 右键拖拽 | 右键按住拖拽移动视图 |
| **重置视图** | 双击 / R键 | 恢复默认视图位置和缩放 |
| **查看AGV** | 左键点击AGV | 弹出详细属性对话框 |
| **手动控制** | 左键点击节点 | 控制最近的空闲AGV移动 |

### 快捷键

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| **F5** | 启动仿真 | 开始订单生成和任务调度 |
| **F6** | 暂停仿真 | 暂停系统运行 |
| **F7** | 重置仿真 | 清空所有AGV和订单 |
| **P** | 切换暂停 | 快速暂停/恢复 |
| **+/-** | 缩放地图 | 键盘缩放控制 |
| **Ctrl+M** | 手动生成订单 | 立即生成一个订单 |
| **Ctrl+A** | 添加AGV | 快速添加新AGV |
| **F11** | 全屏模式 | 切换全屏显示 |

### 界面说明

#### 主控制标签页
- **系统控制** - 启动/暂停/重置仿真
- **AGV管理** - 添加/删除AGV，批量操作
- **任务调度** - 调度策略选择，参数调整

#### 订单管理标签页
- **订单生成** - 控制自动生成速率和手动生成
- **订单队列** - 实时查看待处理、处理中、已完成订单
- **统计信息** - 订单完成率、平均等待时间等

#### AGV状态标签页
- **状态表格** - 详细显示每个AGV的实时状态
- **电量监控** - 电量分布、充电状态、低电量预警
- **性能指标** - 总里程、完成订单数、效率统计

#### 系统监控标签页
- **运行统计** - 系统运行时间、吞吐量等
- **性能监控** - CPU、内存、FPS等性能指标
- **系统日志** - 详细的操作日志和事件记录

## 🎯 应用场景

### 🏭 工业应用
- **仓库物流优化** - 验证AGV调度算法在实际仓库中的效果
- **产线规划** - 分析不同AGV配置对生产效率的影响
- **设备布局** - 优化AGV路径和充电站位置
- **成本分析** - 评估不同AGV数量和策略的投资回报

### 🎓 教育培训
- **物流课程** - 展示现代物流自动化技术
- **算法教学** - 演示路径规划和调度算法
- **系统设计** - 学习复杂系统的设计和实现
- **项目实践** - 学生毕业设计和课程项目

### 🔬 科研开发
- **算法验证** - 测试新的路径规划和调度算法
- **性能分析** - 对比不同策略在各种场景下的表现
- **数据收集** - 生成大量仿真数据用于机器学习
- **论文支持** - 提供可视化结果和实验数据

### 💼 商业展示
- **产品演示** - 向客户展示AGV系统的能力
- **方案验证** - 在实施前验证解决方案的可行性
- **培训工具** - 培训操作人员和维护人员
- **投标支持** - 提供直观的技术方案展示

## 📊 性能指标

### 系统性能
- **仿真规模** - 支持50+ AGV同时仿真
- **订单处理** - 每分钟处理10+订单的高并发
- **响应延迟** - UI操作响应<100ms
- **内存使用** - 基础运行50MB，满负载<200MB
- **帧率稳定** - 60FPS流畅动画显示

### 功能完整性
- **订单系统** - ✅ 泊松分布生成，5级优先级
- **电量管理** - ✅ 真实消耗模型，智能充电
- **任务调度** - ✅ 6种策略，负载均衡
- **可视化** - ✅ 实时监控，多维度分析
- **扩展性** - ✅ 模块化设计，易于定制

## 🛠️ 安装部署

### 环境要求
- **Python** 3.7+
- **操作系统** Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **内存** 4GB+ 推荐
- **存储** 500MB可用空间

### 依赖安装

#### 最小安装（仅核心功能）
```bash
pip install PyQt5>=5.15.0 pandas>=1.3.0
```

#### 推荐安装（包含可视化）
```bash
pip install PyQt5 pandas numpy matplotlib Pillow
```

#### 完整安装（所有功能）
```bash
pip install -r requirements.txt
```

### 一键部署

```bash
# 下载部署脚本
python setup_agv.py

# 选择安装模式
python setup_agv.py --mode full

# 检查环境
python setup_agv.py --check-only
```

### Docker部署（开发中）

```bash
# 构建镜像
docker build -t agv-simulation .

# 运行容器
docker run -p 5900:5900 agv-simulation
```

## 📚 API文档

### 核心类库

#### 订单系统
```python
from models.order import Order, OrderGenerator, OrderPriority

# 创建订单
order = Order("PP01", "AP01", OrderPriority.HIGH)

# 订单生成器
generator = OrderGenerator(nodes)
generator.set_generation_rate(1.0)  # 每分钟1个订单
generator.start_generation()
```

#### 电量系统
```python
from models.battery_system import BatterySystem

# 创建电量系统
battery = BatterySystem(capacity=100.0, initial_charge=80.0)

# 更新电量状态
battery.update(is_moving=True, is_carrying_cargo=False)

# 检查充电需求
if battery.needs_charging():
    battery.start_charging()
```

#### 任务调度
```python
from models.task_scheduler import TaskScheduler, SchedulingStrategy

# 创建调度器
scheduler = TaskScheduler(simulation_widget)

# 设置调度策略
scheduler.set_scheduling_strategy(SchedulingStrategy.BALANCED)

# 添加订单
scheduler.add_order(order)
```

### 详细API文档

完整的API参考文档请查看 [API_REFERENCE.md](docs/API_REFERENCE.md)

## 🧪 测试验证

### 运行测试套件

```bash
# 运行所有测试
python tests/test_system.py

# 运行特定模块测试
python tests/test_system.py --test order
python tests/test_system.py --test battery
python tests/test_system.py --test scheduler
```

### 测试覆盖

- ✅ **订单系统** - 订单生成、分配、完成流程
- ✅ **电量系统** - 消耗、充电、预警机制
- ✅ **任务调度** - 各种策略的分配逻辑
- ✅ **AGV模型** - 移动、载货、状态管理
- ✅ **系统集成** - 完整流程的端到端测试
- ✅ **性能测试** - 并发处理和内存使用

## 📈 性能优化

### 系统优化建议

1. **订单生成** - 建议速率0.5-2.0订单/分钟
2. **AGV数量** - 根据地图大小，建议节点数/50个AGV
3. **充电配置** - 建议每20个AGV配置1个充电站
4. **调度策略** - 复杂地图用BALANCED，简单地图用NEAREST_FIRST

### 性能监控

```python
from utils.performance_monitor import start_performance_monitoring

# 启动监控
monitor = start_performance_monitoring(simulation_widget)

# 设置阈值
monitor.set_thresholds(cpu_percent=70, memory_percent=80)

# 导出报告
monitor.export_metrics("performance_data.json")
```

## 🔧 配置管理

### 配置文件

```python
from utils.config_manager import get_config

config = get_config()

# 更新仿真配置
config.update_simulation_config(
    agv_default_speed=3.0,
    default_generation_rate=2.0,
    low_battery_threshold=25.0
)

# 导出配置
config.export_config("my_config.json")
```

### 预设配置

```python
from utils.config_manager import apply_preset_config

# 应用预设配置
apply_preset_config("performance")  # 性能优化
apply_preset_config("demo")         # 演示模式
apply_preset_config("research")     # 研究模式
```

## 📊 数据分析

### 分析工具

```python
from utils.data_analyzer import AGVDataAnalyzer

analyzer = AGVDataAnalyzer()
analyzer.load_simulation_data("simulation_data.json")

# 生成综合报告
report_path = analyzer.generate_comprehensive_report()
```

### 分析内容

- **订单性能** - 完成率、等待时间、吞吐量
- **AGV效率** - 利用率、平均距离、任务分布
- **电量使用** - 消耗模式、充电频率、电量分布
- **系统瓶颈** - 性能瓶颈识别和优化建议

## 🤝 贡献指南

### 开发环境

```bash
# 克隆项目
git clone [项目地址]
cd agv_simulation_system

# 创建虚拟环境
python -m venv agv_env
source agv_env/bin/activate  # Linux/Mac
# agv_env\Scripts\activate   # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest flake8 black
```

### 代码规范

- **格式化** - 使用black进行代码格式化
- **类型检查** - 使用mypy进行类型检查
- **文档** - 所有公共函数需要详细的docstring
- **测试** - 新功能需要对应的单元测试

### 提交流程

1. Fork项目并创建功能分支
2. 编写代码和测试
3. 运行完整测试套件
4. 提交Pull Request

## 📄 许可证

本项目采用MIT许可证，详见 [LICENSE](LICENSE) 文件。

## 📞 技术支持

### 获取帮助

- 📖 **文档** - 查看完整的集成指南和API文档
- 🎮 **演示** - 使用内置演示模式快速体验
- 🧪 **测试** - 运行测试套件验证功能
- 💬 **讨论** - 在Issues中提问和讨论

### 常见问题

**Q: 如何解决PyQt5安装问题？**
A: 使用conda安装：`conda install pyqt` 或升级pip后重试

**Q: AGV不移动怎么办？**
A: 检查电量是否耗尽，路径是否规划成功，节点是否被占用

**Q: 订单不生成怎么办？**
A: 确认上货点(PP)和下货点(AP)节点存在，检查生成器是否启动

**Q: 如何提高仿真性能？**
A: 降低FPS目标，减少AGV数量，关闭调试模式

### 版本历史

- **v6.3** - 增强功能完整版（当前版本）
  - ✅ 完整订单系统、电量管理、任务调度
  - ✅ 性能监控、数据分析、配置管理
  - ✅ 完整测试套件、文档系统
  
- **v6.2** - 基础功能优化版
  - ✅ AGV属性编辑、删除功能
  - ✅ 控制面板布局优化
  
- **v6.1** - 核心功能版
  - ✅ 数据库直连、节点尺寸优化
  - ✅ 模块化重构

---

<div align="center">

**🎉 感谢使用RCS-Lite AGV增强智能仿真系统！**

如果觉得项目有用，请给我们一个⭐️

[开始使用](#-快速开始) • [查看文档](#-api文档) • [反馈问题](https://github.com/your-repo/issues)

</div>