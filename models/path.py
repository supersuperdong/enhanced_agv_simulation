"""
路径模型类 - 优化版本
"""

import math
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPolygonF
from PyQt5.QtCore import Qt, QPointF


class Path:
    """地图路径类 - 优化版本"""

    def __init__(self, start_node, end_node, path_type='normal', is_bidirectional=False):
        self.start_node = start_node
        self.end_node = end_node
        self.path_type = path_type
        self.is_bidirectional = is_bidirectional
        self.width = 4

    def get_pen(self):
        """获取画笔"""
        colors = {
            'active': QColor(100, 180, 255),     # 蓝色
            'planned': QColor(255, 100, 100),    # 红色
            'normal': QColor(220, 220, 220)      # 灰白色
        }

        color = colors.get(self.path_type, colors['normal'])

        if self.path_type == 'planned':
            # 规划路径使用虚线，线条更细
            pen = QPen(color, self.width - 1, Qt.CustomDashLine)
            pen.setDashPattern([1, 1.5])
            return pen
        else:
            # 其他路径使用实线
            return QPen(color, self.width, Qt.SolidLine)

    def draw(self, painter):
        """绘制路径"""
        # 绘制路径线
        painter.setPen(self.get_pen())
        painter.drawLine(int(self.start_node.x), int(self.start_node.y),
                        int(self.end_node.x), int(self.end_node.y))

        # 绘制方向箭头
        if self.is_bidirectional:
            self._draw_bidirectional_arrows(painter)
        else:
            self._draw_single_arrow(painter)

    def _draw_single_arrow(self, painter):
        """绘制单向箭头"""
        arrow_pos = 0.7  # 箭头位置比例
        arrow_x = self.start_node.x + (self.end_node.x - self.start_node.x) * arrow_pos
        arrow_y = self.start_node.y + (self.end_node.y - self.start_node.y) * arrow_pos

        # 计算方向
        dx = self.end_node.x - self.start_node.x
        dy = self.end_node.y - self.start_node.y
        length = math.sqrt(dx*dx + dy*dy)

        if length == 0:
            return

        ux, uy = dx/length, dy/length
        self._draw_arrow_at(painter, arrow_x, arrow_y, ux, uy)

    def _draw_bidirectional_arrows(self, painter):
        """绘制双向箭头"""
        dx = self.end_node.x - self.start_node.x
        dy = self.end_node.y - self.start_node.y
        length = math.sqrt(dx*dx + dy*dy)

        if length == 0:
            return

        ux, uy = dx/length, dy/length

        # 正向箭头
        arrow1_x = self.start_node.x + dx * 0.7
        arrow1_y = self.start_node.y + dy * 0.7
        self._draw_arrow_at(painter, arrow1_x, arrow1_y, ux, uy)

        # 反向箭头
        arrow2_x = self.start_node.x + dx * 0.3
        arrow2_y = self.start_node.y + dy * 0.3
        self._draw_arrow_at(painter, arrow2_x, arrow2_y, -ux, -uy)

    def _draw_arrow_at(self, painter, x, y, ux, uy):
        """在指定位置绘制箭头"""
        arrow_length = 10  # 箭头长度放大一倍：5 → 10
        arrow_width = 4    # 箭头宽度放大一倍：2 → 4

        # 箭头三个顶点
        tip_x = x + ux * arrow_length * 0.5
        tip_y = y + uy * arrow_length * 0.5

        base_x = x - ux * arrow_length * 0.5
        base_y = y - uy * arrow_length * 0.5

        left_x = base_x - uy * arrow_width
        left_y = base_y + ux * arrow_width

        right_x = base_x + uy * arrow_width
        right_y = base_y - ux * arrow_width

        # 绘制箭头
        painter.setBrush(QBrush(Qt.black))
        painter.setPen(QPen(Qt.black, 1))

        arrow_polygon = QPolygonF([
            QPointF(tip_x, tip_y),
            QPointF(left_x, left_y),
            QPointF(right_x, right_y)
        ])
        painter.drawPolygon(arrow_polygon)