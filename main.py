#!/usr/bin/env python3
"""
RCS-Lite AGV智能仿真系统 v6.0 - 数据库直连版本
主入口文件
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("RCS-Lite AGV仿真系统")
    app.setApplicationVersion("6.2")
    app.setOrganizationName("RCS-Lite")

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()