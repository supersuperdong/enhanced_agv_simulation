"""
地图加载器模块 - 简化版
只支持从SQLite数据库加载地图数据
"""

import sqlite3
from models.node import Node
from models.path import Path


class MapLoader:
    """地图加载器 - 简化版，只支持SQLite数据库"""

    @staticmethod
    def load_from_database(db_path="Map.db"):
        """
        从SQLite数据库加载地图数据

        Args:
            db_path: 数据库文件路径

        Returns:
            tuple: (nodes字典, paths列表)

        Raises:
            Exception: 数据库连接或数据加载失败时抛出异常
        """
        try:
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 读取节点数据
            cursor.execute("SELECT id, canRotate, pointId, x, y FROM T_GraphPoint")
            points_data = cursor.fetchall()

            # 读取边数据
            cursor.execute("""
                SELECT id, beginAngle, beginPointId, endAngle, endPointId, passAngles, weight 
                FROM T_GraphEdge
            """)
            edges_data = cursor.fetchall()

            conn.close()

            # 验证数据
            if not points_data:
                raise Exception("数据库中没有找到节点数据")

            # 处理节点数据
            nodes = MapLoader._process_points_data(points_data)

            # 处理边数据
            paths = MapLoader._process_edges_data(edges_data, nodes)

            return nodes, paths

        except sqlite3.Error as e:
            raise Exception(f"数据库连接或查询失败: {str(e)}")
        except Exception as e:
            raise Exception(f"加载数据库地图失败: {str(e)}")

    @staticmethod
    def _process_points_data(points_data):
        """
        处理节点数据

        Args:
            points_data: 节点数据列表

        Returns:
            dict: 节点字典
        """
        nodes = {}

        # 获取坐标范围用于缩放
        x_coords = [row[3] for row in points_data]  # x坐标
        y_coords = [row[4] for row in points_data]  # y坐标

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # 计算缩放比例
        scale = MapLoader._calculate_scale(min_x, max_x, min_y, max_y)

        # 创建节点
        for row in points_data:
            db_id, can_rotate, point_id, x, y = row

            # 缩放并居中坐标
            scaled_x = (x - min_x) * scale + 100  # 添加边距
            scaled_y = (y - min_y) * scale + 100

            # 确定节点类型
            node_type = MapLoader._get_node_type(point_id)

            nodes[point_id] = Node(point_id, scaled_x, scaled_y, node_type)

        return nodes

    @staticmethod
    def _process_edges_data(edges_data, nodes):
        """
        处理边数据

        Args:
            edges_data: 边数据列表
            nodes: 节点字典

        Returns:
            list: 路径列表
        """
        if not edges_data:
            return []

        # 收集所有边对
        edge_pairs = set()
        for row in edges_data:
            db_id, begin_angle, begin_id, end_angle, end_id, pass_angles, weight = row

            if begin_id in nodes and end_id in nodes:
                # 添加单向连接
                nodes[begin_id].add_connection(end_id, weight)
                edge_pairs.add((begin_id, end_id))

        # 检测双向连接
        bidirectional_edges = MapLoader._detect_bidirectional_edges(edge_pairs)

        # 创建路径对象
        paths = []
        processed_edges = set()

        for row in edges_data:
            db_id, begin_angle, begin_id, end_angle, end_id, pass_angles, weight = row

            if begin_id in nodes and end_id in nodes:
                edge_key = (begin_id, end_id)

                if edge_key not in processed_edges:
                    is_bidirectional = MapLoader._is_bidirectional_edge(
                        begin_id, end_id, bidirectional_edges
                    )

                    path = Path(nodes[begin_id], nodes[end_id],
                                is_bidirectional=is_bidirectional)
                    paths.append(path)
                    processed_edges.add(edge_key)

                    # 如果是双向边，也标记反向边为已处理
                    if is_bidirectional:
                        processed_edges.add((end_id, begin_id))

        return paths

    @staticmethod
    def _calculate_scale(min_x, max_x, min_y, max_y):
        """
        计算地图缩放比例

        Args:
            min_x, max_x, min_y, max_y: 坐标范围

        Returns:
            float: 缩放比例
        """
        target_width = 1400  # 目标宽度
        target_height = 1000  # 目标高度

        scale_x = target_width / (max_x - min_x) if max_x > min_x else 1
        scale_y = target_height / (max_y - min_y) if max_y > min_y else 1

        # 将基础缩放比例再放大一倍，让路径长度也相应放大
        base_scale = min(scale_x, scale_y) * 0.85
        return base_scale * 2  # 放大一倍，让节点间距离也放大

    @staticmethod
    def _get_node_type(point_id):
        """
        根据节点ID确定节点类型

        Args:
            point_id: 节点ID

        Returns:
            str: 节点类型
        """
        point_id_str = str(point_id).upper()

        if point_id_str.startswith('PP'):
            return 'pickup'
        elif point_id_str.startswith('CP'):
            return 'charging'
        elif point_id_str.startswith('AP'):
            return 'dropoff'
        else:
            return 'normal'

    @staticmethod
    def _detect_bidirectional_edges(edge_pairs):
        """
        检测双向边

        Args:
            edge_pairs: 边对集合

        Returns:
            set: 双向边集合
        """
        bidirectional_edges = set()

        for begin_id, end_id in edge_pairs:
            if (end_id, begin_id) in edge_pairs:
                # 使用排序后的元组作为键，避免重复
                edge_key = (min(str(begin_id), str(end_id)),
                            max(str(begin_id), str(end_id)))
                bidirectional_edges.add(edge_key)

        return bidirectional_edges

    @staticmethod
    def _is_bidirectional_edge(begin_id, end_id, bidirectional_edges):
        """
        检查边是否为双向边

        Args:
            begin_id: 起始节点ID
            end_id: 结束节点ID
            bidirectional_edges: 双向边集合

        Returns:
            bool: 是否为双向边
        """
        edge_key = (min(str(begin_id), str(end_id)),
                    max(str(begin_id), str(end_id)))
        return edge_key in bidirectional_edges

    @staticmethod
    def validate_map_data(nodes, paths):
        """
        验证地图数据的完整性

        Args:
            nodes: 节点字典
            paths: 路径列表

        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {
                'node_count': len(nodes),
                'path_count': len(paths),
                'node_types': {},
                'isolated_nodes': []
            }
        }

        if not nodes:
            result['valid'] = False
            result['errors'].append("没有找到节点数据")
            return result

        # 统计节点类型
        for node in nodes.values():
            node_type = node.node_type
            result['stats']['node_types'][node_type] = result['stats']['node_types'].get(node_type, 0) + 1

        # 检查孤立节点
        for node_id, node in nodes.items():
            if not node.connections:
                result['stats']['isolated_nodes'].append(node_id)

        if result['stats']['isolated_nodes']:
            result['warnings'].append(f"发现 {len(result['stats']['isolated_nodes'])} 个孤立节点")

        return result