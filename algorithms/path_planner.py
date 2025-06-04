"""
路径规划算法模块
包含Dijkstra和A*算法的实现
"""

import heapq
import math


class PathPlanner:
    """路径规划器，支持Dijkstra和A*算法，支持有向图和碰撞避免"""

    @staticmethod
    def dijkstra(nodes, start_id, end_id, agvs=None):
        """
        Dijkstra最短路径算法 - 支持有向图和碰撞避免

        Args:
            nodes: 节点字典
            start_id: 起始节点ID
            end_id: 目标节点ID
            agvs: AGV列表，用于碰撞避免

        Returns:
            list: 路径节点ID列表，如果无路径则返回空列表
        """
        if start_id not in nodes or end_id not in nodes:
            return []

        # 初始化距离和前驱
        distances = {node_id: float('inf') for node_id in nodes}
        distances[start_id] = 0
        previous = {}
        unvisited = [(0, start_id)]

        while unvisited:
            current_dist, current_id = heapq.heappop(unvisited)

            if current_id == end_id:
                break

            if current_dist > distances[current_id]:
                continue

            # 只考虑当前节点能直接到达的节点（有向图）
            for neighbor_id in nodes[current_id].connections:
                if neighbor_id in nodes:
                    # 计算到邻居节点的距离成本
                    distance = PathPlanner._calculate_cost(
                        nodes[current_id], nodes[neighbor_id], agvs, start_id
                    )

                    new_distance = distances[current_id] + distance

                    if new_distance < distances[neighbor_id]:
                        distances[neighbor_id] = new_distance
                        previous[neighbor_id] = current_id
                        heapq.heappush(unvisited, (new_distance, neighbor_id))

        # 重构路径
        return PathPlanner._reconstruct_path(previous, start_id, end_id)

    @staticmethod
    def a_star(nodes, start_id, end_id, agvs=None):
        """
        A*寻路算法 - 支持有向图和碰撞避免

        Args:
            nodes: 节点字典
            start_id: 起始节点ID
            end_id: 目标节点ID
            agvs: AGV列表，用于碰撞避免

        Returns:
            list: 路径节点ID列表，如果无路径则返回空列表
        """
        if start_id not in nodes or end_id not in nodes:
            return []

        def heuristic(node1_id, node2_id):
            """计算启发式距离（欧几里得距离）"""
            node1 = nodes[node1_id]
            node2 = nodes[node2_id]
            return math.sqrt((node1.x - node2.x) ** 2 + (node1.y - node2.y) ** 2)

        # A*算法的数据结构
        open_set = [(0, start_id)]
        came_from = {}
        g_score = {node_id: float('inf') for node_id in nodes}
        g_score[start_id] = 0
        f_score = {node_id: float('inf') for node_id in nodes}
        f_score[start_id] = heuristic(start_id, end_id)

        while open_set:
            current_id = heapq.heappop(open_set)[1]

            if current_id == end_id:
                # 找到目标，重构路径
                path = []
                while current_id in came_from:
                    path.append(current_id)
                    current_id = came_from[current_id]
                path.append(start_id)
                path.reverse()
                return path

            # 只考虑当前节点能直接到达的节点（有向图）
            for neighbor_id in nodes[current_id].connections:
                if neighbor_id in nodes:
                    # 计算到邻居节点的实际成本
                    base_cost = PathPlanner._calculate_cost(
                        nodes[current_id], nodes[neighbor_id], agvs, start_id
                    )

                    tentative_g_score = g_score[current_id] + base_cost

                    if tentative_g_score < g_score[neighbor_id]:
                        came_from[neighbor_id] = current_id
                        g_score[neighbor_id] = tentative_g_score
                        f_score[neighbor_id] = g_score[neighbor_id] + heuristic(neighbor_id, end_id)

                        # 检查是否已在开放集合中
                        if not PathPlanner._is_in_open_set(open_set, neighbor_id):
                            heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))

        return []  # 无路径

    @staticmethod
    def _calculate_cost(current_node, neighbor_node, agvs, start_id):
        """
        计算从当前节点到邻居节点的成本

        Args:
            current_node: 当前节点
            neighbor_node: 邻居节点
            agvs: AGV列表
            start_id: 起始节点ID（用于判断是否为当前AGV的起始位置）

        Returns:
            float: 移动成本
        """
        # 基础距离
        base_distance = current_node.neighbors.get(neighbor_node.id, 100)

        # 如果没有AGV信息，返回基础距离
        if agvs is None:
            return base_distance

        # 检查邻居节点是否被其他AGV占用
        if neighbor_node.occupied_by is not None:
            # 检查是否是自己目前正在占用的节点
            is_own_node = False
            for agv in agvs:
                if (agv.current_node.id == start_id and
                        agv.current_node.id == neighbor_node.id):
                    is_own_node = True
                    break

            if not is_own_node:
                # 被其他AGV占用，增加成本但不完全禁止通过
                return base_distance * 5

        return base_distance

    @staticmethod
    def _reconstruct_path(previous, start_id, end_id):
        """
        从前驱信息重构路径

        Args:
            previous: 前驱节点字典
            start_id: 起始节点ID
            end_id: 目标节点ID

        Returns:
            list: 路径节点ID列表
        """
        path = []
        current = end_id

        while current in previous:
            path.append(current)
            current = previous[current]

        path.append(start_id)
        path.reverse()

        return path if len(path) > 1 else []

    @staticmethod
    def _is_in_open_set(open_set, node_id):
        """检查节点是否已在开放集合中"""
        for _, existing_node_id in open_set:
            if existing_node_id == node_id:
                return True
        return False

    @classmethod
    def plan_path(cls, algorithm, nodes, start_id, end_id, agvs=None):
        """
        统一的路径规划接口

        Args:
            algorithm: 算法名称 ('dijkstra' 或 'a_star')
            nodes: 节点字典
            start_id: 起始节点ID
            end_id: 目标节点ID
            agvs: AGV列表

        Returns:
            list: 路径节点ID列表
        """
        if algorithm.lower() == 'dijkstra':
            return cls.dijkstra(nodes, start_id, end_id, agvs)
        elif algorithm.lower() == 'a_star' or algorithm.lower() == 'astar':
            return cls.a_star(nodes, start_id, end_id, agvs)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

    @staticmethod
    def validate_path(nodes, path):
        """
        验证路径的有效性

        Args:
            nodes: 节点字典
            path: 路径节点ID列表

        Returns:
            bool: 路径是否有效
        """
        if not path or len(path) < 2:
            return False

        for i in range(len(path) - 1):
            current_id = path[i]
            next_id = path[i + 1]

            # 检查节点是否存在
            if current_id not in nodes or next_id not in nodes:
                return False

            # 检查连接是否存在
            if next_id not in nodes[current_id].connections:
                return False

        return True