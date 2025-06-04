"""
节点模型类 - 优化版本
"""

from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QRectF


class Node:
    """地图节点类 - 优化版本"""

    def __init__(self, id, x, y, node_type='normal'):
        self.id = id
        self.x = x
        self.y = y
        self.size = 24  # 节点大小放大一倍：12×12 → 24×24
        self.connections = []  # 连接的其他节点ID
        self.node_type = node_type  # 节点类型
        self.neighbors = {}  # 邻居节点和距离
        self.occupied_by = None  # 占用的AGV ID
        self.reserved_by = None  # 预定的AGV ID
        self.reservation_time = 0  # 预定时间

    def add_connection(self, node_id, distance):
        """添加连接"""
        if node_id not in self.connections:
            self.connections.append(node_id)
        self.neighbors[node_id] = distance

    def get_node_color(self, is_in_control_zone=False):
        """获取节点颜色"""
        # 如果节点在管控区内，显示橙色
        if is_in_control_zone:
            return QColor(255, 165, 0)  # 橙色

        # 否则按照节点类型显示颜色
        colors = {
            'normal': QColor(200, 200, 200),    # 灰白色
            'pickup': QColor(76, 175, 80),      # 绿色
            'dropoff': QColor(244, 67, 54),     # 红色
            'charging': QColor(255, 193, 7)     # 金色
        }
        return colors.get(self.node_type, colors['normal'])

    def is_special_node(self):
        """判断是否为特殊节点（已弃用，现在通过管控区状态决定形状）"""
        return False

    def draw(self, painter, is_highlighted=False, is_in_control_zone=False):
        """绘制节点"""
        color = self.get_node_color(is_in_control_zone)

        # 设置画笔和画刷
        if is_highlighted:
            painter.setBrush(QBrush(color.lighter(120)))
            painter.setPen(QPen(QColor(255, 0, 0), 3))
        else:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black, 1))

        # 所有节点都绘制为方块
        half_size = self.size // 2
        painter.drawRect(
            int(self.x - half_size),
            int(self.y - half_size),
            self.size,
            self.size
        )

        # 绘制节点ID文字（调整字体大小适应12*12的节点）
        if is_in_control_zone:
            text_color = Qt.white  # 橙色背景用白色文字
        else:
            text_color = Qt.white if self.node_type != 'charging' else Qt.black

        painter.setPen(QPen(text_color))
        painter.setFont(QFont('Arial', 4, QFont.Bold))  # 字体改小适应12*12节点

        text_rect = QRectF(
            self.x - half_size,
            self.y - half_size,
            self.size,
            self.size
        )
        painter.drawText(text_rect, Qt.AlignCenter, str(self.id))

        # 显示占用状态
        if self.occupied_by is not None:
            painter.setPen(QPen(Qt.darkRed))
            painter.setFont(QFont('Arial', 3))  # 状态文字也改小
            status_rect = QRectF(
                self.x - half_size,
                self.y + half_size + 1,
                self.size,
                8
            )
            painter.drawText(status_rect, Qt.AlignCenter, f"AGV#{self.occupied_by}")

    def is_point_inside(self, x, y):
        """检查点是否在节点内部（方形检测）"""
        half_size = self.size // 2
        return (self.x - half_size <= x <= self.x + half_size and
                self.y - half_size <= y <= self.y + half_size)