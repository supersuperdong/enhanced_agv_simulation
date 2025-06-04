#!/usr/bin/env python3
"""
RCS-Lite AGV增强智能仿真系统 v6.3 - 主入口文件
集成订单系统、电量管理和任务调度的完整版本
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def show_splash_screen():
    """显示启动画面"""
    app = QApplication.instance()

    # 创建简单的启动画面
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.darkBlue)

    splash = QSplashScreen(splash_pix)
    splash.setFont(QFont('Arial', 16, QFont.Bold))
    splash.showMessage(
        "RCS-Lite AGV增强仿真系统 v6.3\n\n"
        "正在加载...\n"
        "• 订单系统\n"
        "• 电量管理\n"
        "• 任务调度\n"
        "• 智能仿真",
        Qt.AlignCenter | Qt.AlignBottom,
        Qt.white
    )

    splash.show()
    app.processEvents()

    return splash


def check_dependencies():
    """检查依赖包"""
    required_packages = ['PyQt5', 'pandas']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        QMessageBox.critical(
            None, "依赖包缺失",
            f"缺少必要的依赖包:\n{', '.join(missing_packages)}\n\n"
            f"请运行: pip install {' '.join(missing_packages)}"
        )
        return False

    return True


def check_database():
    """检查数据库文件"""
    db_path = "Map.db"
    if not os.path.exists(db_path):
        reply = QMessageBox.question(
            None, "数据库文件缺失",
            f"未找到地图数据库文件: {db_path}\n\n"
            "是否继续运行？(系统将使用默认配置)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        return reply == QMessageBox.Yes
    return True


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("RCS-Lite AGV增强仿真系统")
    app.setApplicationVersion("6.3")
    app.setOrganizationName("RCS-Lite")
    app.setApplicationDisplayName("AGV增强仿真系统")

    # 设置应用程序样式
    app.setStyle('Fusion')

    try:
        # 显示启动画面
        splash = show_splash_screen()

        # 检查依赖
        splash.showMessage("检查系统依赖...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        app.processEvents()

        if not check_dependencies():
            return 1

        # 检查数据库
        splash.showMessage("检查数据库文件...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        app.processEvents()

        if not check_database():
            return 1

        # 导入增强主窗口
        splash.showMessage("加载增强仿真组件...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        app.processEvents()

        try:
            from ui.enhanced_main_window import EnhancedMainWindow
        except ImportError as e:
            # 如果增强版本不可用，回退到原版本
            QMessageBox.warning(
                None, "组件加载失败",
                f"无法加载增强组件: {str(e)}\n\n"
                "将使用基础版本..."
            )
            from ui.main_window import MainWindow as EnhancedMainWindow

        # 创建主窗口
        splash.showMessage("初始化用户界面...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        app.processEvents()

        window = EnhancedMainWindow()

        # 延迟显示主窗口，让启动画面显示足够时间
        def show_main_window():
            splash.finish(window)
            window.show()

            # 显示欢迎消息
            if hasattr(window, 'status_bar'):
                window.status_bar.showMessage(
                    "欢迎使用RCS-Lite AGV增强仿真系统！点击"+
                "仿真→启动仿真"+
                "开始",
                5000
                )

                QTimer.singleShot(2000, show_main_window)  # 2秒后显示主窗口

                # 运行应用程序
                return app.exec_()

            except Exception as e:
            # 错误处理
            error_msg = f"程序启动时发生错误:\n\n{str(e)}\n\n详细信息:\n{traceback.format_exc()}"

            try:
                splash.close()
            except:
                pass

            QMessageBox.critical(None, "程序启动失败", error_msg)
            return 1

    def run_basic_version():
        """运行基础版本（备用方案）"""
        try:
            from ui.main_window import MainWindow
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            return app.exec_()
        except Exception as e:
            print(f"基础版本启动失败: {e}")
            return 1

    def show_help():
        """显示帮助信息"""
        help_text = """
RCS-Lite AGV增强仿真系统 v6.3

用法:
    python enhanced_main.py [选项]

选项:
    -h, --help      显示此帮助信息
    --basic         运行基础版本
    --version       显示版本信息
    --check         检查系统环境

功能特性:
    • 泊松分布订单生成系统
    • 真实AGV电量管理
    • 智能任务调度算法
    • 完整AGV生命周期仿真
    • 实时监控和统计分析

系统要求:
    • Python 3.7+
    • PyQt5
    • pandas
    • Map.db数据库文件

快速开始:
    1. 确保已安装依赖: pip install PyQt5 pandas
    2. 运行程序: python enhanced_main.py
    3. 点击"演示模式"开始体验

技术支持:
    • 查看INTEGRATION_GUIDE.md获取详细说明
    • 使用内置帮助菜单获取操作指南
    """
        print(help_text)

    def show_version():
        """显示版本信息"""
        version_text = """
RCS-Lite AGV增强仿真系统
版本: 6.3
构建日期: 2024年12月
框架: PyQt5
Python要求: 3.7+

新增功能:
- 订单系统 (泊松分布生成)
- 电量管理 (真实消耗/充电)
- 任务调度 (智能分配算法)
- 完整仿真 (运输-充电闭环)

原有功能:
- 数据库地图加载
- A*/Dijkstra路径规划
- 碰撞检测与避让
- 管控区显示
- 高清地图导出
    """
        print(version_text)

    def check_environment():
        """检查系统环境"""
        print("=== 系统环境检查 ===")

        # Python版本
        print(f"Python版本: {sys.version}")

        # 检查依赖包
        print("\n依赖包检查:")
        required_packages = {
            'PyQt5': 'PyQt5',
            'pandas': 'pandas',
            'sqlite3': 'sqlite3'
        }

        for name, module in required_packages.items():
            try:
                imported = __import__(module)
                version = getattr(imported, '__version__', '未知')
                print(f"  ✓ {name}: {version}")
            except ImportError:
                print(f"  ✗ {name}: 未安装")

        # 检查文件
        print("\n文件检查:")
        required_files = [
            'Map.db',
            'control_zone.txt',
            'ui/enhanced_main_window.py',
            'models/order.py',
            'models/battery_system.py',
            'models/task_scheduler.py'
        ]

        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"  ✓ {file_path}")
            else:
                print(f"  ✗ {file_path}: 文件缺失")

        print("\n=== 检查完成 ===")

    if __name__ == "__main__":
        # 处理命令行参数
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()

            if arg in ['-h', '--help']:
                show_help()
                sys.exit(0)
            elif arg == '--version':
                show_version()
                sys.exit(0)
            elif arg == '--check':
                check_environment()
                sys.exit(0)
            elif arg == '--basic':
                print("启动基础版本...")
                sys.exit(run_basic_version())
            else:
                print(f"未知参数: {arg}")
                print("使用 -h 或 --help 查看帮助")
                sys.exit(1)

        # 正常启动
        try:
            exit_code = main()
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            sys.exit(0)
        except Exception as e:
            print(f"程序运行时发生未处理的异常: {e}")
            traceback.print_exc()
            sys.exit(1)