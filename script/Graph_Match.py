from neo4j import GraphDatabase
from collections import defaultdict, deque
from typing import List, Set, Dict, Tuple, Optional


class Neo4jGraphMatcher:
    def __init__(self, uri: str, username: str, password: str):
        """
        初始化Neo4j连接

        Args:
            uri: Neo4j数据库URI
            username: 用户名
            password: 密码
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.query_edges = []  # 存储查询边（无向图格式）
        self.query_graph = defaultdict(set)  # 邻接表表示的查询图

    def close(self):
        """关闭数据库连接"""
        self.driver.close()

    def _normalize_edge(self, node1: str, node2: str) -> Tuple[str, str]:
        """
        标准化边的表示（按字典序排列，确保无向图的一致性）

        Args:
            node1: 第一个节点
            node2: 第二个节点

        Returns:
            标准化后的边
        """
        return tuple(sorted([node1, node2]))

    def add_edge(self, node1: str, node2: str):
        """
        添加一条边到查询图（无向图）

        Args:
            node1: 第一个节点
            node2: 第二个节点
        """
        # 标准化边的表示
        normalized_edge = self._normalize_edge(node1, node2)

        if normalized_edge not in self.query_edges:
            self.query_edges.append(normalized_edge)
            # 无向图：双向添加邻接关系
            self.query_graph[node1].add(node2)
            self.query_graph[node2].add(node1)
        # 删除重复边提示

    def find_connected_components(self) -> List[Set[str]]:
        """
        使用BFS查找查询图中的所有连通分量

        Returns:
            连通分量列表，每个连通分量是一个节点集合
        """
        visited = set()
        components = []

        for node in self.query_graph:
            if node not in visited:
                component = set()
                queue = deque([node])

                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)

                        for neighbor in self.query_graph[current]:
                            if neighbor not in visited:
                                queue.append(neighbor)

                components.append(component)

        return components

    def get_component_edges(self, component: Set[str]) -> List[Tuple[str, str]]:
        """
        获取连通分量内的所有边（标准化格式）

        Args:
            component: 连通分量节点集合

        Returns:
            该连通分量内的标准化边列表
        """
        edges = []
        for edge in self.query_edges:
            node1, node2 = edge
            if node1 in component and node2 in component:
                edges.append(edge)
        return edges

    def query_database_component(self, component_nodes: Set[str],
                                 component_edges: List[Tuple[str, str]],
                                 node_label: str) -> List[Set[str]]:
        """
        在数据库中查询与给定连通分量匹配的所有连通分量
        必须满足：1) 节点名完全相同 2) 边连接关系完全相同（无向图）

        Args:
            component_nodes: 查询连通分量的节点集合
            component_edges: 查询连通分量的边列表（已标准化）
            node_label: 要查询的节点标签

        Returns:
            匹配的连通分量列表
        """
        if not component_nodes:
            return []

        node_count = len(component_nodes)
        edge_count = len(component_edges)

        with self.driver.session() as session:
            # 首先检查这些节点是否在数据库中存在
            node_list = list(component_nodes)
            check_nodes_query = f"""
            MATCH (n:{node_label})
            WHERE n.name IN $node_names
            RETURN collect(n.name) as existing_nodes
            """

            result = session.run(check_nodes_query, node_names=node_list)
            record = result.single()

            if not record or len(record["existing_nodes"]) != node_count:
                # 如果不是所有节点都存在，则无法匹配
                return []

            existing_nodes = set(record["existing_nodes"])
            if existing_nodes != component_nodes:
                # 如果节点名不完全匹配，则无法匹配
                return []

            # 检查这些节点是否形成连通分量，并且边的连接关系是否匹配
            # 获取数据库中这些节点之间的所有边（无向图处理）
            edges_query = f"""
            MATCH (n1:{node_label})-[r:REL]-(n2:{node_label})
            WHERE n1.name IN $node_names AND n2.name IN $node_names
            AND n1.name < n2.name  // 避免重复计算无向边
            RETURN n1.name as node1, n2.name as node2
            """

            result = session.run(edges_query, node_names=node_list)
            db_edges = []

            for record in result:
                # 标准化数据库中的边
                edge = self._normalize_edge(record["node1"], record["node2"])
                db_edges.append(edge)

            # 检查边是否完全匹配
            query_edge_set = set(component_edges)
            db_edge_set = set(db_edges)

            if query_edge_set == db_edge_set:
                # 还需要验证这些节点在数据库中确实形成一个连通分量
                if self._verify_connectivity_in_db(component_nodes, node_label, session):
                    return [component_nodes]

            return []

    def _verify_connectivity_in_db(self, nodes: Set[str], node_label: str, session) -> bool:
        """
        验证给定节点在数据库中是否形成连通分量

        Args:
            nodes: 节点集合
            node_label: 节点标签
            session: Neo4j会话

        Returns:
            是否连通
        """
        if len(nodes) <= 1:
            return True

        node_list = list(nodes)
        start_node = node_list[0]

        # 从start_node开始，看能否通过无向边到达所有其他节点
        connectivity_query = f"""
        MATCH (start:{node_label} {{name: $start_name}})
        CALL (start) {{
            MATCH path = (start)-[:REL*0..{len(nodes)}]-(end:{node_label})
            WHERE end.name IN $all_nodes
            RETURN collect(DISTINCT end.name) as reachable_nodes
        }}
        RETURN reachable_nodes
        """

        result = session.run(connectivity_query,
                             start_name=start_node,
                             all_nodes=node_list)
        record = result.single()

        if record:
            reachable = set(record["reachable_nodes"])
            return reachable == nodes

        return False

    def search_matches(self, node_label: str) -> Dict[int, List[Set[str]]]:
        """
        搜索当前查询图中所有连通分量在数据库中的匹配
        每个连通分量独立匹配，不要求全部匹配成功

        Args:
            node_label: 要查询的节点标签

        Returns:
            字典，键为连通分量索引，值为匹配的连通分量列表
        """
        components = self.find_connected_components()
        results = {}
        matched_components = []

        # 1. 显示当前连通分量构成
        print(f"当前连通分量数: {len(components)}")
        for i, component in enumerate(components):
            print(f"  连通分量{i + 1}: {sorted(component)}")

        # 2. 执行匹配并收集结果
        for i, component in enumerate(components):
            component_edges = self.get_component_edges(component)
            matches = self.query_database_component(component, component_edges, node_label)
            results[i] = matches

            if matches:
                matched_components.append((i + 1, matches[0]))

        # 3. 显示匹配结果
        if matched_components:
            print("匹配到的连通分量:")
            for comp_id, matched_comp in matched_components:
                print(f"  连通分量{comp_id}: {sorted(matched_comp)}")
        else:
            print("未找到匹配的连通分量")

        return results

    def add_edge_and_search(self, node1: str, node2: str, node_label: str) -> Dict[int, List[Set[str]]]:
        """
        添加边并立即搜索匹配（增量匹配模式）

        Args:
            node1: 第一个节点
            node2: 第二个节点
            node_label: 要查询的节点标签

        Returns:
            匹配结果
        """
        self.add_edge(node1, node2)
        return self.search_matches(node_label)

    def clear_query_graph(self):
        """清空查询图"""
        self.query_edges.clear()
        self.query_graph.clear()

    def get_all_database_components(self, node_label: str) -> List[Set[str]]:
        """
        获取数据库中所有的连通分量

        Args:
            node_label: 要查询的节点标签

        Returns:
            数据库中所有连通分量的列表，每个连通分量是一个节点集合
        """
        with self.driver.session() as session:
            # 获取所有节点
            nodes_query = f"""
            MATCH (n:{node_label})
            RETURN collect(n.name) as all_nodes
            """

            result = session.run(nodes_query)
            record = result.single()

            if not record or not record["all_nodes"]:
                print("数据库中没有找到任何节点")
                return []

            all_nodes = set(record["all_nodes"])

            # 获取所有边（无向图处理）
            edges_query = f"""
            MATCH (n1:{node_label})-[r:REL]-(n2:{node_label})
            WHERE n1.name < n2.name  // 避免重复计算无向边
            RETURN n1.name as node1, n2.name as node2
            """

            result = session.run(edges_query)

            # 构建邻接表
            db_graph = defaultdict(set)

            # 添加所有节点到图中（包括孤立节点）
            for node in all_nodes:
                db_graph[node] = set()

            # 添加边到邻接表
            for record in result:
                node1, node2 = record["node1"], record["node2"]
                db_graph[node1].add(node2)
                db_graph[node2].add(node1)

            # 使用BFS查找所有连通分量
            visited = set()
            components = []

            for node in all_nodes:
                if node not in visited:
                    component = set()
                    queue = deque([node])

                    while queue:
                        current = queue.popleft()
                        if current not in visited:
                            visited.add(current)
                            component.add(current)

                            for neighbor in db_graph[current]:
                                if neighbor not in visited:
                                    queue.append(neighbor)

                    components.append(component)

            return components

    def display_database_components(self, node_label: str):
        """
        显示数据库中所有连通分量的详细信息

        Args:
            node_label: 要查询的节点标签
        """
        components = self.get_all_database_components(node_label)

        if not components:
            print("数据库中没有找到任何连通分量")
            return

        print(f"数据库中共有 {len(components)} 个连通分量:")

        for i, component in enumerate(components, 1):
            sorted_component = sorted(component)
            node_count = len(component)

            # 计算该连通分量的边数
            edge_count = 0
            with self.driver.session() as session:
                if node_count > 1:
                    edges_query = f"""
                    MATCH (n1:{node_label})-[r:REL]-(n2:{node_label})
                    WHERE n1.name IN $node_names AND n2.name IN $node_names
                    AND n1.name < n2.name
                    RETURN count(r) as edge_count
                    """

                    result = session.run(edges_query, node_names=list(component))
                    record = result.single()
                    if record:
                        edge_count = record["edge_count"]

            print(f"  连通分量 {i}: {sorted_component}")
            print(f"    节点数: {node_count}, 边数: {edge_count}")

            if node_count == 1:
                print(f"    类型: 孤立节点")
            elif edge_count == node_count - 1:
                print(f"    类型: 树状结构")
            elif edge_count == node_count:
                print(f"    类型: 包含一个环的结构")
            else:
                print(f"    类型: 复杂结构")
            print()


# 简化的使用接口
class SimpleGraphMatcher:
    """简化的图匹配接口"""

    def __init__(self, neo4j_uri: str, username: str, password: str, node_label: str):
        """
        初始化简化接口

        Args:
            neo4j_uri: Neo4j数据库URI
            username: 用户名
            password: 密码
            node_label: 要查询的节点标签
        """
        self.matcher = Neo4jGraphMatcher(neo4j_uri, username, password)
        self.node_label = node_label

    def add_edge(self, node1: str, node2: str):
        """
        添加边并执行增量匹配

        Args:
            node1: 第一个节点
            node2: 第二个节点
        """
        # 去除节点名称的前后空白字符
        node1 = node1.strip()
        node2 = node2.strip()

        # 添加边并搜索匹配
        self.matcher.add_edge_and_search(node1, node2, self.node_label)

    def clear(self):
        """清空查询图"""
        self.matcher.clear_query_graph()

    def show_all_database_components(self):
        """显示数据库中所有连通分量"""
        self.matcher.display_database_components(self.node_label)

    def get_all_database_components(self):
        """
        获取数据库中所有连通分量

        Returns:
            所有连通分量的列表
        """
        return self.matcher.get_all_database_components(self.node_label)

    def close(self):
        """关闭连接"""
        self.matcher.close()


if __name__ == "__main__":
    matcher = SimpleGraphMatcher(
        "bolt://192.168.1.130:7687",
        "neo4j",
        "a214a214",
        "1"  # 替换为你的节点标签
    )
    try:
        # 显示数据库中所有连通分量
        print("=== 数据库中所有连通分量 ===")
        matcher.show_all_database_components()

        print("\n=== 开始添加查询边 ===")
        # 现在使用两个独立的参数而不是"X-Y"格式
        matcher.add_edge("QF1-1", "FU1-1")
        matcher.add_edge("FU1-1", "FU2-1")
        matcher.add_edge("D", "E")

    finally:
        matcher.close()