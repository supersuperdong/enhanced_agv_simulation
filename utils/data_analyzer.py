"""
数据分析工具
分析AGV仿真数据，生成统计报告和可视化图表
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """分析结果"""
    title: str
    data: Dict
    charts: List[str] = None  # 图表文件路径
    recommendations: List[str] = None

    def __post_init__(self):
        if self.charts is None:
            self.charts = []
        if self.recommendations is None:
            self.recommendations = []


class AGVDataAnalyzer:
    """AGV数据分析器"""

    def __init__(self):
        self.data = {}
        self.results = []

        # 设置matplotlib中文支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置seaborn样式
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def load_simulation_data(self, data_source) -> bool:
        """加载仿真数据"""
        try:
            if isinstance(data_source, str):
                # 从文件加载
                with open(data_source, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            elif isinstance(data_source, dict):
                # 直接使用字典数据
                self.data = data_source
            else:
                print("不支持的数据源类型")
                return False

            print(f"数据加载成功，包含 {len(self.data)} 个数据集")
            return True

        except Exception as e:
            print(f"数据加载失败: {e}")
            return False

    def analyze_order_performance(self) -> AnalysisResult:
        """分析订单性能"""
        try:
            order_data = self.data.get('order_statistics', {})
            queue_stats = order_data.get('queue_stats', {})

            # 基础统计
            total_orders = queue_stats.get('total_orders', 0)
            completed_orders = queue_stats.get('completed_count', 0)
            pending_orders = queue_stats.get('pending_count', 0)
            processing_orders = queue_stats.get('processing_count', 0)

            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            avg_waiting_time = queue_stats.get('avg_waiting_time', 0)
            avg_completion_time = queue_stats.get('avg_completion_time', 0)

            analysis_data = {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'processing_orders': processing_orders,
                'completion_rate': completion_rate,
                'avg_waiting_time_seconds': avg_waiting_time,
                'avg_completion_time_seconds': avg_completion_time,
                'avg_waiting_time_minutes': avg_waiting_time / 60,
                'avg_completion_time_minutes': avg_completion_time / 60
            }

            # 生成建议
            recommendations = []
            if completion_rate < 80:
                recommendations.append("订单完成率偏低，建议增加AGV数量或优化调度策略")
            if avg_waiting_time > 300:  # 5分钟
                recommendations.append("订单等待时间过长，建议优化任务分配算法")
            if pending_orders > processing_orders * 2:
                recommendations.append("积压订单较多，建议提高处理能力")

            if not recommendations:
                recommendations.append("订单处理性能良好")

            return AnalysisResult(
                title="订单性能分析",
                data=analysis_data,
                recommendations=recommendations
            )

        except Exception as e:
            print(f"订单性能分析失败: {e}")
            return AnalysisResult("订单性能分析", {"error": str(e)})

    def analyze_agv_efficiency(self) -> AnalysisResult:
        """分析AGV效率"""
        try:
            agv_details = self.data.get('agv_details', [])

            if not agv_details:
                return AnalysisResult("AGV效率分析", {"error": "无AGV数据"})

            # 计算各项指标
            total_distance = sum(agv.get('total_distance', 0) for agv in agv_details)
            total_orders = sum(agv.get('orders_completed', 0) for agv in agv_details)
            avg_battery = sum(agv.get('battery', {}).get('charge', 0) for agv in agv_details) / len(agv_details)

            # 单个AGV统计
            agv_stats = []
            for agv in agv_details:
                battery_info = agv.get('battery', {})
                agv_stats.append({
                    'id': agv.get('id'),
                    'distance': agv.get('total_distance', 0),
                    'orders': agv.get('orders_completed', 0),
                    'battery': battery_info.get('charge', 0),
                    'efficiency': agv.get('orders_completed', 0) / max(agv.get('total_distance', 1), 1)  # 订单/距离
                })

            # 找出最高效和最低效的AGV
            if agv_stats:
                most_efficient = max(agv_stats, key=lambda x: x['efficiency'])
                least_efficient = min(agv_stats, key=lambda x: x['efficiency'])
            else:
                most_efficient = least_efficient = None

            analysis_data = {
                'agv_count': len(agv_details),
                'total_distance': total_distance,
                'total_orders_completed': total_orders,
                'avg_distance_per_agv': total_distance / len(agv_details),
                'avg_orders_per_agv': total_orders / len(agv_details),
                'avg_battery_level': avg_battery,
                'most_efficient_agv': most_efficient,
                'least_efficient_agv': least_efficient,
                'agv_statistics': agv_stats
            }

            # 生成建议
            recommendations = []
            if avg_battery < 50:
                recommendations.append("AGV平均电量较低，建议增加充电站或优化充电策略")
            if total_orders / len(agv_details) < 5:
                recommendations.append("AGV平均完成订单数较少，建议检查任务分配效率")

            efficiency_variance = np.var([agv['efficiency'] for agv in agv_stats])
            if efficiency_variance > 1.0:
                recommendations.append("AGV效率差异较大，建议平衡工作负载")

            return AnalysisResult(
                title="AGV效率分析",
                data=analysis_data,
                recommendations=recommendations
            )

        except Exception as e:
            print(f"AGV效率分析失败: {e}")
            return AnalysisResult("AGV效率分析", {"error": str(e)})

    def analyze_battery_usage(self) -> AnalysisResult:
        """分析电量使用情况"""
        try:
            agv_details = self.data.get('agv_details', [])

            if not agv_details:
                return AnalysisResult("电量使用分析", {"error": "无AGV数据"})

            battery_levels = []
            charging_agvs = 0
            low_battery_agvs = 0

            for agv in agv_details:
                battery_info = agv.get('battery', {})
                charge_level = battery_info.get('charge', 0)
                battery_levels.append(charge_level)

                if battery_info.get('charging', False):
                    charging_agvs += 1
                if charge_level < 30:
                    low_battery_agvs += 1

            analysis_data = {
                'avg_battery_level': np.mean(battery_levels),
                'min_battery_level': np.min(battery_levels),
                'max_battery_level': np.max(battery_levels),
                'battery_std_dev': np.std(battery_levels),
                'charging_agvs': charging_agvs,
                'low_battery_agvs': low_battery_agvs,
                'battery_distribution': {
                    'critical_0_15': sum(1 for b in battery_levels if b < 15),
                    'low_15_30': sum(1 for b in battery_levels if 15 <= b < 30),
                    'medium_30_60': sum(1 for b in battery_levels if 30 <= b < 60),
                    'good_60_85': sum(1 for b in battery_levels if 60 <= b < 85),
                    'excellent_85_100': sum(1 for b in battery_levels if b >= 85)
                }
            }

            # 生成建议
            recommendations = []
            if analysis_data['avg_battery_level'] < 40:
                recommendations.append("整体电量水平偏低，建议增加充电站数量")
            if low_battery_agvs > len(agv_details) * 0.3:
                recommendations.append("低电量AGV比例过高，建议优化充电调度")
            if analysis_data['battery_std_dev'] > 25:
                recommendations.append("AGV电量分布不均，建议平衡工作负载")

            return AnalysisResult(
                title="电量使用分析",
                data=analysis_data,
                recommendations=recommendations
            )

        except Exception as e:
            print(f"电量使用分析失败: {e}")
            return AnalysisResult("电量使用分析", {"error": str(e)})

    def create_order_trend_chart(self, output_path: str = "order_trend.png") -> str:
        """创建订单趋势图"""
        try:
            # 模拟时间序列数据（实际使用时应从真实数据中提取）
            time_points = pd.date_range(start='2024-01-01 08:00', periods=24, freq='H')
            orders_completed = np.random.poisson(5, 24).cumsum()
            orders_pending = np.random.poisson(2, 24)

            plt.figure(figsize=(12, 6))

            plt.subplot(1, 2, 1)
            plt.plot(time_points, orders_completed, 'b-', label='累计完成订单', linewidth=2)
            plt.title('订单完成趋势')
            plt.xlabel('时间')
            plt.ylabel('累计订单数')
            plt.legend()
            plt.xticks(rotation=45)

            plt.subplot(1, 2, 2)
            plt.plot(time_points, orders_pending, 'r-', label='待处理订单', linewidth=2)
            plt.title('待处理订单变化')
            plt.xlabel('时间')
            plt.ylabel('订单数')
            plt.legend()
            plt.xticks(rotation=45)

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            print(f"创建订单趋势图失败: {e}")
            return ""

    def create_agv_efficiency_chart(self, output_path: str = "agv_efficiency.png") -> str:
        """创建AGV效率图表"""
        try:
            agv_details = self.data.get('agv_details', [])

            if not agv_details:
                return ""

            # 提取数据
            agv_ids = [f"AGV{agv.get('id', i)}" for i, agv in enumerate(agv_details)]
            distances = [agv.get('total_distance', 0) for agv in agv_details]
            orders = [agv.get('orders_completed', 0) for agv in agv_details]
            batteries = [agv.get('battery', {}).get('charge', 0) for agv in agv_details]

            fig, axes = plt.subplots(2, 2, figsize=(15, 10))

            # 距离对比
            axes[0, 0].bar(agv_ids, distances, color='skyblue')
            axes[0, 0].set_title('AGV行驶距离对比')
            axes[0, 0].set_ylabel('距离')
            axes[0, 0].tick_params(axis='x', rotation=45)

            # 订单完成数对比
            axes[0, 1].bar(agv_ids, orders, color='lightgreen')
            axes[0, 1].set_title('AGV完成订单数对比')
            axes[0, 1].set_ylabel('订单数')
            axes[0, 1].tick_params(axis='x', rotation=45)

            # 电量分布
            axes[1, 0].bar(agv_ids, batteries, color='orange')
            axes[1, 0].set_title('AGV当前电量')
            axes[1, 0].set_ylabel('电量 (%)')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].axhline(y=30, color='red', linestyle='--', label='低电量线')
            axes[1, 0].legend()

            # 效率散点图
            efficiency = [o / max(d, 1) for o, d in zip(orders, distances)]
            axes[1, 1].scatter(distances, orders, s=100, alpha=0.7, c=batteries, cmap='viridis')
            axes[1, 1].set_title('AGV效率分析（订单数 vs 行驶距离）')
            axes[1, 1].set_xlabel('行驶距离')
            axes[1, 1].set_ylabel('完成订单数')

            # 添加颜色条
            cbar = plt.colorbar(axes[1, 1].collections[0], ax=axes[1, 1])
            cbar.set_label('电量 (%)')

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            print(f"创建AGV效率图表失败: {e}")
            return ""

    def create_battery_analysis_chart(self, output_path: str = "battery_analysis.png") -> str:
        """创建电量分析图表"""
        try:
            agv_details = self.data.get('agv_details', [])

            if not agv_details:
                return ""

            batteries = [agv.get('battery', {}).get('charge', 0) for agv in agv_details]

            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            # 电量分布直方图
            axes[0].hist(batteries, bins=10, color='lightblue', alpha=0.7, edgecolor='black')
            axes[0].set_title('AGV电量分布')
            axes[0].set_xlabel('电量 (%)')
            axes[0].set_ylabel('AGV数量')
            axes[0].axvline(x=30, color='red', linestyle='--', label='低电量线')
            axes[0].axvline(x=np.mean(batteries), color='green', linestyle='-',
                            label=f'平均值 ({np.mean(batteries):.1f}%)')
            axes[0].legend()

            # 电量等级饼图
            battery_levels = {
                '危险 (0-15%)': sum(1 for b in batteries if b < 15),
                '低 (15-30%)': sum(1 for b in batteries if 15 <= b < 30),
                '中等 (30-60%)': sum(1 for b in batteries if 30 <= b < 60),
                '良好 (60-85%)': sum(1 for b in batteries if 60 <= b < 85),
                '优秀 (85-100%)': sum(1 for b in batteries if b >= 85)
            }

            # 过滤掉0值
            battery_levels = {k: v for k, v in battery_levels.items() if v > 0}

            colors = ['red', 'orange', 'yellow', 'lightgreen', 'green'][:len(battery_levels)]
            axes[1].pie(battery_levels.values(), labels=battery_levels.keys(),
                        autopct='%1.1f%%', colors=colors)
            axes[1].set_title('电量等级分布')

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            print(f"创建电量分析图表失败: {e}")
            return ""

    def generate_comprehensive_report(self, output_dir: str = "analysis_output") -> str:
        """生成综合分析报告"""
        import os

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 执行各项分析
        order_analysis = self.analyze_order_performance()
        agv_analysis = self.analyze_agv_efficiency()
        battery_analysis = self.analyze_battery_usage()

        # 生成图表
        chart_paths = []

        order_chart = self.create_order_trend_chart(
            os.path.join(output_dir, "order_trend.png")
        )
        if order_chart:
            chart_paths.append(order_chart)

        agv_chart = self.create_agv_efficiency_chart(
            os.path.join(output_dir, "agv_efficiency.png")
        )
        if agv_chart:
            chart_paths.append(agv_chart)

        battery_chart = self.create_battery_analysis_chart(
            os.path.join(output_dir, "battery_analysis.png")
        )
        if battery_chart:
            chart_paths.append(battery_chart)

        # 生成HTML报告
        html_content = self._generate_html_report(
            order_analysis, agv_analysis, battery_analysis, chart_paths
        )

        report_path = os.path.join(output_dir, "analysis_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 生成JSON数据
        json_data = {
            'generated_at': datetime.now().isoformat(),
            'order_analysis': order_analysis.data,
            'agv_analysis': agv_analysis.data,
            'battery_analysis': battery_analysis.data,
            'recommendations': {
                'order': order_analysis.recommendations,
                'agv': agv_analysis.recommendations,
                'battery': battery_analysis.recommendations
            }
        }

        json_path = os.path.join(output_dir, "analysis_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"综合分析报告生成完成: {report_path}")
        return report_path

    def _generate_html_report(self, order_analysis, agv_analysis, battery_analysis, chart_paths) -> str:
        """生成HTML报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AGV仿真系统分析报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }
        .chart { text-align: center; margin: 20px 0; }
        .recommendations { background: #e8f5e8; padding: 15px; border-radius: 5px; }
        .error { color: red; font-weight: bold; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AGV仿真系统分析报告</h1>
        <p>生成时间: {timestamp}</p>
    </div>

    <div class="section">
        <h2>📋 订单性能分析</h2>
        {order_content}
    </div>

    <div class="section">
        <h2>🤖 AGV效率分析</h2>
        {agv_content}
    </div>

    <div class="section">
        <h2>🔋 电量使用分析</h2>
        {battery_content}
    </div>

    <div class="section">
        <h2>📊 数据可视化</h2>
        {charts_content}
    </div>
</body>
</html>
        """

        # 格式化各部分内容
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        order_content = self._format_analysis_section(order_analysis)
        agv_content = self._format_analysis_section(agv_analysis)
        battery_content = self._format_analysis_section(battery_analysis)

        charts_content = ""
        for chart_path in chart_paths:
            chart_name = os.path.basename(chart_path)
            charts_content += f'<div class="chart"><img src="{chart_name}" alt="{chart_name}" style="max-width: 100%;"></div>'

        return html_template.format(
            timestamp=timestamp,
            order_content=order_content,
            agv_content=agv_content,
            battery_content=battery_content,
            charts_content=charts_content
        )

    def _format_analysis_section(self, analysis: AnalysisResult) -> str:
        """格式化分析节内容"""
        if 'error' in analysis.data:
            return f'<p class="error">分析失败: {analysis.data["error"]}</p>'

        content = ""

        # 显示关键指标
        for key, value in analysis.data.items():
            if isinstance(value, (int, float)):
                if 'percent' in key or 'rate' in key:
                    content += f'<div class="metric"><strong>{key}:</strong> {value:.1f}%</div>'
                elif 'time' in key and 'seconds' in key:
                    content += f'<div class="metric"><strong>{key}:</strong> {value:.1f}秒</div>'
                else:
                    content += f'<div class="metric"><strong>{key}:</strong> {value:.2f}</div>'

        # 显示建议
        if analysis.recommendations:
            content += '<div class="recommendations"><h4>💡 建议:</h4><ul>'
            for rec in analysis.recommendations:
                content += f'<li>{rec}</li>'
            content += '</ul></div>'

        return content


def analyze_simulation_data(data_file: str, output_dir: str = "analysis_output") -> str:
    """分析仿真数据的便捷函数"""
    analyzer = AGVDataAnalyzer()

    if analyzer.load_simulation_data(data_file):
        return analyzer.generate_comprehensive_report(output_dir)
    else:
        return ""


# 示例使用
if __name__ == "__main__":
    # 创建示例数据进行测试
    sample_data = {
        "order_statistics": {
            "queue_stats": {
                "total_orders": 100,
                "completed_count": 85,
                "pending_count": 10,
                "processing_count": 5,
                "avg_waiting_time": 120,
                "avg_completion_time": 300
            }
        },
        "agv_details": [
            {
                "id": 1,
                "total_distance": 1500,
                "orders_completed": 15,
                "battery": {"charge": 65, "charging": False}
            },
            {
                "id": 2,
                "total_distance": 1200,
                "orders_completed": 12,
                "battery": {"charge": 40, "charging": True}
            },
            {
                "id": 3,
                "total_distance": 1800,
                "orders_completed": 20,
                "battery": {"charge": 80, "charging": False}
            }
        ]
    }

    analyzer = AGVDataAnalyzer()
    analyzer.data = sample_data

    print("生成分析报告...")
    report_path = analyzer.generate_comprehensive_report()
    print(f"报告已生成: {report_path}")