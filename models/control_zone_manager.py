"""
管控区管理器
"""

from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRectF


class ControlZoneManager:
    """管控区管理器，负责加载和显示管控区"""

    def __init__(self):
        self.control_zones = []  # 管控区列表
        self.zone_color = QColor(255, 165, 0, 80)  # 橙色半透明

    def load_control_zones(self, file_path="control_zone.txt"):
        """
        从文件加载管控区数据

        Args:
            file_path: 管控区文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self.control_zones = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    # 每一行是一个管控区，包含多个节点ID
                    node_ids = [node_id.strip() for node_id in line.split(',')]
                    self.control_zones.append({
                        'id': i + 1,
                        'nodes': node_ids
                    })

            print(f"已加载 {len(self.control_zones)} 个管控区")
            return True

        except Exception as e:
            print(f"加载管控区文件失败: {e}")
            return False

    def get_zone_bounds(self, zone_nodes, nodes_dict):
        """
        计算管控区的边界矩形

        Args:
            zone_nodes: 管控区节点ID列表
            nodes_dict: 节点字典

        Returns:
            tuple: (min_x, min_y, max_x, max_y) 或 None
        """
        valid_nodes = [nodes_dict[node_id] for node_id in zone_nodes
                       if node_id in nodes_dict]

        if not valid_nodes:
            return None

        x_coords = [node.x for node in valid_nodes]
        y_coords = [node.y for node in valid_nodes]

        margin = 15  # 边界扩展
        return (
            min(x_coords) - margin,
            min(y_coords) - margin,
            max(x_coords) + margin,
            max(y_coords) + margin
        )

    def draw_control_zones(self, painter, nodes_dict):
        """
        绘制所有管控区

        Args:
            painter: QPainter对象
            nodes_dict: 节点字典
        """
        if not self.control_zones:
            return

        painter.setPen(QPen(self.zone_color.darker(150), 2))
        painter.setBrush(self.zone_color)

        for zone in self.control_zones:
            bounds = self.get_zone_bounds(zone['nodes'], nodes_dict)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
                painter.drawRect(rect)

    def get_node_zone(self, node_id):
        """
        获取节点所属的管控区

        Args:
            node_id: 节点ID

        Returns:
            int: 管控区ID，如果不属于任何管控区则返回None
        """
        for zone in self.control_zones:
            if str(node_id) in zone['nodes']:
                return zone['id']
        return None

    def is_node_in_control_zone(self, node_id):
        """
        检查节点是否在任何管控区内

        Args:
            node_id: 节点ID

        Returns:
            bool: 如果节点在管控区内返回True，否则返回False
        """
        return self.get_node_zone(node_id) is not None

    def get_control_zone_nodes(self):
        """
        获取所有管控区节点的集合

        Returns:
            set: 包含所有管控区节点ID的集合
        """
        control_nodes = set()
        for zone in self.control_zones:
            control_nodes.update(zone['nodes'])
        return control_nodes

    def get_zone_info(self):
        """获取管控区统计信息"""
        return {
            'total_zones': len(self.control_zones),
            'total_nodes': sum(len(zone['nodes']) for zone in self.control_zones)
        }