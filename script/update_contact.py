import json
import os
from script.compare_csv import validate_and_move_files
from global_config import Global_Config
import shutil

old_dir = Global_Config.old_result_csv_path
new_dir = Global_Config.result_csv_path
old_file_path = os.path.join(old_dir, 'merge_result.csv')
new_file_path = os.path.join(new_dir, 'merge_result.csv')

class UnionFind:

    def __init__(self):
        self.parent = {}
        self.size = {}

    def find(self, x):
        """查找 x 的根节点"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]

    def union(self, x, y):
        """合并 x 和 y 所在的连通图"""
        rootX = self.find(x)
        rootY = self.find(y)

        if rootX != rootY:
            if self.size[rootX] > self.size[rootY]:
                self.parent[rootY] = rootX
                self.size[rootX] += self.size[rootY]
            else:
                self.parent[rootX] = rootY
                self.size[rootY] += self.size[rootX]

    def add(self, x):
        """初始化触点"""
        if x not in self.parent:
            self.parent[x] = x
            self.size[x] = 1

    def remove_node(self, node_name):
        """
        删除单个节点：
        - 如果不存在：返回 False
        - 如果存在：从所有连通分量中移除该节点，然后重建并查集，返回 True
        """
        if node_name not in self.parent:
            return False

        components = self.get_all_components()

        new_components = []
        for comp in components:
            filtered = [n for n in comp if n != node_name]
            if filtered:
                new_components.append(filtered)

        # 重建并查集
        self.parent = {}
        self.size = {}

        for comp in new_components:
            for n in comp:
                self.add(n)
            if len(comp) >= 2:
                first = comp[0]
                for other in comp[1:]:
                    self.union(first, other)

        return True

    def get_all_components(self):
        """返回所有连通分量（以列表或集合的形式）"""
        components = {}
        for node in self.parent:
            root = self.find(node)
            if root not in components:
                components[root] = []
            components[root].append(node)

        # 返回连通图的列表形式，每个连通图用一个列表表示
        return list(components.values())

    def save_to_file(self, filepath):
        """将并查集保存到文件"""
        with open(filepath, 'w') as f:
            components = self.get_all_components()

            # 创建带标号的字典形式：每个连通图使用字典表示，包含 id 和 nodes
            numbered_components = [{"id": i + 1, "nodes": component} for i, component in enumerate(components)]

            # 保存为 JSON 格式
            json.dump(numbered_components, f, indent=4)
            shutil.copy(new_file_path, old_file_path)  # 覆盖 old 文件

    def load_from_file(self, filepath):
        """从文件加载并查集"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                components = json.load(f)
                # 现在每个 component 是字典格式，包含 "id" 和 "nodes"
                for component in components:
                    for touchpoint in component["nodes"]:
                        if touchpoint not in self.parent:
                            self.add(touchpoint)
                    # 合并每个连通分量中的触点
                    for i in range(1, len(component["nodes"])):
                        self.union(component["nodes"][0], component["nodes"][i])
        else:
            print(f"{filepath} 不存在，创建一个新的并查集文件。")
            self.save_to_file(filepath)


# 定义并查集实例和文件路径
uf = UnionFind()
save_path = Global_Config.union_find_json_path  # 文件保存路径


def update_connected_components(add_pairs, remove_nodes=None):
    """
    根据 Global_Config.wired_status 更新并查集：
    - wired_status == 'add'：把 add_pairs 中的触点连成一组
    - wired_status == 'sub'：把 remove_nodes（若为空则用 add_pairs）中的触点从并查集中删除

    :param add_pairs: list，validate_and_move_files 返回的第一个列表，
                      例如 ['KM1-13', 'KM1-53']
    :param remove_nodes: list 或 None，validate_and_move_files 返回的第二个列表，
                         例如 ['KM1-13'] 或 ['KM1-13', 'KM1-53']
    """
    wired_status = Global_Config.wired_status

    if remove_nodes is None:
        remove_nodes = []

    # 两个列表都空，直接不处理
    if (not add_pairs) and (not remove_nodes):
        print("没有新的触点信息，跳过更新操作。")
        return None

    if wired_status not in ("add", "sub"):
        print(f"未知的 wired_status: {wired_status}，不进行任何操作。")
        return None

    # 先加载之前保存的并查集状态
    uf.load_from_file(save_path)

    # ------------------ 新增连线模式 ------------------
    if wired_status == "add":
        if not add_pairs:
            print("wired_status 为 add，但 add_pairs 为空，跳过。")
        else:
            # 假设一次传入的是一组要连起来的触点，例如 ['KM1-13', 'KM1-53']
            # 也支持多于两个，比如 ['A','B','C'] 就是 A-B、A-C 都连起来
            print(f"新增连线触点组：{add_pairs}")

            # 先把所有节点 add 进去
            for n in add_pairs:
                uf.add(n)

            if len(add_pairs) >= 2:
                first = add_pairs[0]
                for other in add_pairs[1:]:
                    uf.union(first, other)

    # ------------------ 撤销连线 / 删除节点模式 ------------------
    elif wired_status == "sub":
        # 优先使用 remove_nodes，如果 remove_nodes 为空，就用 add_pairs 当作要删的节点
        targets = remove_nodes if remove_nodes else add_pairs
        print(f"删除节点列表：{targets}")

        for node in targets:
            success = uf.remove_node(node)
            if not success:
                print(f"并查集中不存在节点：{node}，无法删除。")

    # 调试查看当前所有连通图
    components = uf.get_all_components()
    print("当前所有连通图：", components)
    largest_component = max(components, key=len) if components else []

    # 保存当前的并查集状态到文件
    uf.save_to_file(save_path)

    return largest_component


# 示例使用
if __name__ == "__main__":
    # 现在 validate_and_move_files() 返回两个列表
   # add_pairs, remove_nodes = validate_and_move_files()
    #update_connected_components(add_pairs, remove_nodes)
    update_connected_components(*validate_and_move_files())
