#!/usr/bin/env python3
"""
RCS-Lite AGV增强仿真系统快速部署脚本
自动检查环境、安装依赖、配置系统
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path


class AGVSystemSetup:
    """AGV系统快速部署工具"""

    def __init__(self):
        self.system_info = {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
        self.setup_log = []

    def log(self, message, level="INFO"):
        """记录日志"""
        log_entry = f"[{level}] {message}"
        print(log_entry)
        self.setup_log.append(log_entry)

    def check_python_version(self) -> bool:
        """检查Python版本"""
        self.log("检查Python版本...")

        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 7:
            self.log(f"Python版本检查通过: {self.system_info['python_version']}")
            return True
        else:
            self.log(f"Python版本过低: {self.system_info['python_version']}, 需要3.7+", "ERROR")
            return False

    def check_virtual_environment(self) -> bool:
        """检查是否在虚拟环境中"""
        in_venv = (hasattr(sys, 'real_prefix') or
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

        if in_venv:
            self.log("检测到虚拟环境，推荐做法")
            return True
        else:
            self.log("未检测到虚拟环境，建议使用虚拟环境", "WARNING")
            return False

    def install_dependencies(self, mode="basic") -> bool:
        """安装依赖包"""
        self.log(f"开始安装依赖包 ({mode} 模式)...")

        try:
            # 升级pip
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

            if mode == "basic":
                packages = ["PyQt5>=5.15.0", "pandas>=1.3.0"]
            elif mode == "recommended":
                packages = ["PyQt5>=5.15.0", "pandas>=1.3.0", "numpy>=1.21.0",
                            "matplotlib>=3.5.0", "Pillow>=8.0.0"]
            elif mode == "full":
                # 安装完整依赖
                if os.path.exists("requirements_enhanced.txt"):
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                                           '-r', 'requirements_enhanced.txt'])
                    self.log("从requirements_enhanced.txt安装完整依赖")
                    return True
                else:
                    packages = ["PyQt5>=5.15.0", "pandas>=1.3.0", "numpy>=1.21.0",
                                "matplotlib>=3.5.0", "Pillow>=8.0.0", "scipy>=1.7.0",
                                "seaborn>=0.11.0", "psutil>=5.8.0"]
            else:
                self.log(f"未知的安装模式: {mode}", "ERROR")
                return False

            # 安装包
            for package in packages:
                self.log(f"安装 {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

            self.log("依赖安装完成")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"依赖安装失败: {e}", "ERROR")
            return False

    def create_project_structure(self) -> bool:
        """创建项目目录结构"""
        self.log("创建项目目录结构...")

        directories = [
            "config",
            "logs",
            "exports",
            "analysis_output",
            "backups"
        ]

        try:
            for directory in directories:
                Path(directory).mkdir(exist_ok=True)
                self.log(f"创建目录: {directory}")

            return True

        except Exception as e:
            self.log(f"目录创建失败: {e}", "ERROR")
            return False

    def create_sample_configs(self) -> bool:
        """创建示例配置文件"""
        self.log("创建示例配置文件...")

        try:
            # 创建示例仿真配置
            sim_config = {
                "window_width": 1920,
                "window_height": 1080,
                "default_generation_rate": 0.5,
                "agv_default_speed": 2.0,
                "low_battery_threshold": 30.0,
                "enable_debug_mode": False
            }

            import json
            config_path = Path("config/simulation_example.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(sim_config, f, indent=2, ensure_ascii=False)

            self.log(f"示例配置已创建: {config_path}")

            # 创建启动脚本
            self.create_launch_scripts()

            return True

        except Exception as e:
            self.log(f"配置文件创建失败: {e}", "ERROR")
            return False

    def create_launch_scripts(self):
        """创建启动脚本"""
        self.log("创建启动脚本...")

        # Windows批处理脚本
        if self.system_info['platform'] == 'Windows':
            batch_content = """@echo off
echo Starting RCS-Lite AGV Enhanced Simulation System...
python enhanced_main.py
pause
"""
            with open("start_agv_system.bat", 'w', encoding='utf-8') as f:
                f.write(batch_content)
            self.log("Windows启动脚本已创建: start_agv_system.bat")

        # Unix/Linux shell脚本
        else:
            shell_content = """#!/bin/bash
echo "Starting RCS-Lite AGV Enhanced Simulation System..."
python3 enhanced_main.py
"""
            with open("start_agv_system.sh", 'w', encoding='utf-8') as f:
                f.write(shell_content)

            # 设置执行权限
            os.chmod("start_agv_system.sh", 0o755)
            self.log("Unix/Linux启动脚本已创建: start_agv_system.sh")

    def verify_installation(self) -> bool:
        """验证安装"""
        self.log("验证安装...")

        try:
            # 检查核心模块是否可以导入
            test_imports = [
                ("PyQt5.QtWidgets", "PyQt5"),
                ("pandas", "pandas"),
                ("numpy", "numpy (可选)"),
                ("matplotlib.pyplot", "matplotlib (可选)")
            ]

            success_count = 0
            for module, description in test_imports:
                try:
                    __import__(module)
                    self.log(f"✓ {description} 导入成功")
                    success_count += 1
                except ImportError:
                    if "可选" in description:
                        self.log(f"⚠ {description} 未安装 (可选)", "WARNING")
                    else:
                        self.log(f"✗ {description} 导入失败", "ERROR")

            # 检查关键文件
            required_files = [
                "enhanced_main.py",
                "models/order.py",
                "models/battery_system.py",
                "models/task_scheduler.py"
            ]

            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)

            if missing_files:
                self.log(f"缺少关键文件: {missing_files}", "ERROR")
                return False

            self.log("安装验证完成")
            return True

        except Exception as e:
            self.log(f"安装验证失败: {e}", "ERROR")
            return False

    def create_demo_data(self) -> bool:
        """创建演示数据"""
        self.log("创建演示数据...")

        try:
            # 如果Map.db不存在，创建提示
            if not os.path.exists("Map.db"):
                self.log("警告: 未找到Map.db数据库文件", "WARNING")
                self.log("系统将使用默认配置运行，但可能无法显示地图")

                # 创建空的管控区文件
                if not os.path.exists("control_zone.txt"):
                    with open("control_zone.txt", 'w', encoding='utf-8') as f:
                        f.write("# 管控区配置文件\n# 格式: 每行为一个管控区，节点ID用逗号分隔\n")
                    self.log("已创建空的管控区配置文件")

            return True

        except Exception as e:
            self.log(f"演示数据创建失败: {e}", "ERROR")
            return False

    def generate_setup_report(self) -> str:
        """生成安装报告"""
        report = f"""
RCS-Lite AGV增强仿真系统安装报告
=====================================

系统信息:
- 操作系统: {self.system_info['platform']}
- Python版本: {self.system_info['python_version']}
- 架构: {self.system_info['architecture']}

安装日志:
"""
        for log_entry in self.setup_log:
            report += f"{log_entry}\n"

        report += """
使用指南:
1. 运行程序: python enhanced_main.py
2. 或使用启动脚本 (Windows: start_agv_system.bat, Unix/Linux: ./start_agv_system.sh)
3. 点击"演示模式"快速体验完整功能
4. 查看INTEGRATION_GUIDE.md获取详细说明

注意事项:
- 确保Map.db数据库文件在项目根目录
- 建议在虚拟环境中运行
- 如遇问题，请检查安装日志

技术支持:
- 项目文档: README.md, INTEGRATION_GUIDE.md
- 配置文件: config/目录
- 日志文件: logs/目录
"""

        return report

    def run_setup(self, install_mode="recommended", skip_deps=False) -> bool:
        """运行完整安装流程"""
        self.log("开始RCS-Lite AGV增强仿真系统安装...")
        self.log(f"系统信息: {self.system_info}")

        # 检查Python版本
        if not self.check_python_version():
            return False

        # 检查虚拟环境
        self.check_virtual_environment()

        # 安装依赖
        if not skip_deps:
            if not self.install_dependencies(install_mode):
                return False
        else:
            self.log("跳过依赖安装")

        # 创建项目结构
        if not self.create_project_structure():
            return False

        # 创建配置文件
        if not self.create_sample_configs():
            return False

        # 创建演示数据
        if not self.create_demo_data():
            return False

        # 验证安装
        if not self.verify_installation():
            return False

        # 生成报告
        report = self.generate_setup_report()

        # 保存报告
        report_path = "installation_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        self.log(f"安装完成！报告已保存到: {report_path}")
        print("\n" + "=" * 50)
        print("🎉 安装成功！")
        print("=" * 50)
        print("快速开始:")
        print("  python enhanced_main.py")
        print("或使用启动脚本:")
        if self.system_info['platform'] == 'Windows':
            print("  start_agv_system.bat")
        else:
            print("  ./start_agv_system.sh")
        print("=" * 50)

        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="RCS-Lite AGV增强仿真系统快速部署")
    parser.add_argument("--mode", choices=["basic", "recommended", "full"],
                        default="recommended", help="安装模式")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    parser.add_argument("--check-only", action="store_true", help="仅检查环境")

    args = parser.parse_args()

    setup = AGVSystemSetup()

    if args.check_only:
        print("环境检查模式")
        setup.check_python_version()
        setup.check_virtual_environment()
        setup.verify_installation()
        return

    success = setup.run_setup(
        install_mode=args.mode,
        skip_deps=args.skip_deps
    )

    if success:
        print("\n是否现在启动系统? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes', '是']:
                print("启动系统...")
                os.system("python enhanced_main.py")
        except KeyboardInterrupt:
            print("\n安装完成，您可以稍后手动启动系统")
    else:
        print("安装失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()