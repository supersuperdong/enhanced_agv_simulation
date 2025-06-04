#!/usr/bin/env python3
"""
RCS-Lite AGV增强智能仿真系统 v6.3 - 简化版主入口
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数 - 简化版本"""
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("RCS-Lite AGV增强仿真系统")
    app.setApplicationVersion("6.3")
    app.setApplicationDisplayName("AGV增强仿真系统")
    app.setStyle('Fusion')

    try:
        # 直接导入主窗口
        from ui.main_window import MainWindow

        # 创建并显示主窗口
        window = MainWindow()
        window.show()

        # 显示欢迎消息
        if hasattr(window, 'status_bar'):
            window.status_bar.showMessage(
                "欢迎使用RCS-Lite AGV增强仿真系统！点击仿真→启动仿真开始",
                5000
            )

        # 运行应用程序
        return app.exec_()

    except ImportError as e:
        QMessageBox.critical(
            None, "模块加载失败",
            f"无法加载必要模块: {str(e)}\n\n"
            "请检查文件完整性和依赖安装"
        )
        return 1
    except Exception as e:
        QMessageBox.critical(
            None, "程序启动失败",
            f"程序启动时发生错误:\n{str(e)}"
        )
        return 1


if __name__ == "__main__":
    # 处理命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help']:
            print("""RCS-Lite AGV增强仿真系统 v6.3

用法: python main.py

核心功能:
• 泊松分布订单生成系统
• 真实AGV电量管理
• 智能任务调度算法  
• 完整AGV生命周期仿真

快速开始:
1. 运行程序: python main.py
2. 点击"演示模式"开始体验
3. 查看AGV自动执行任务和充电

系统要求:
• Python 3.7+
• PyQt5
• pandas
            """)
            sys.exit(0)
        elif arg == '--version':
            print("RCS-Lite AGV增强仿真系统 v6.3")
            sys.exit(0)

    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行失败: {e}")
        sys.exit(1)