import json
from global_config import Global_Config


def load_json(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def compare_subgraphs(subgraph1, subgraph2):
    """比较两个连通图是否相同（忽略顺序）"""
    return set(subgraph1) == set(subgraph2)


def match_subgraphs():
    """将两个文件中的连通图进行匹配"""
    # 直接在代码中硬编码文件路径
    union_find_file = Global_Config.union_find_json_path
    rule_file = Global_Config.rule_json_path

    # 加载两个文件的数据
    union_find_data = load_json(union_find_file)
    rule_data = load_json(rule_file)

    # 存储匹配结果
    matched_results = []

    # 遍历union_find中的每个连通图
    for union_find_subgraph in union_find_data:
        union_find_nodes = union_find_subgraph['nodes']  # 获取当前连通图的节点列表
        # 遍历rule中的每个连通图
        for rule_item in rule_data:
            rule_nodes = rule_item['nodes']  # 获取规则中的节点列表
            # 比较当前连通图的节点和规则的节点是否匹配
            if compare_subgraphs(union_find_nodes, rule_nodes):
                # 找到匹配的连通图，保存匹配结果（序号，分值）
                matched_results.append({
                    '匹配序号': rule_item['id'],
                    '分值': rule_item['score'],
                    '节点': rule_item['nodes']  # 添加节点信息
                })
    Global_Config.total_score = sum(item['分值'] for item in matched_results)
    print(matched_results)
    print(Global_Config.total_score)


    return matched_results


if __name__ == '__main__':
    print(match_subgraphs())
    print(Global_Config.total_score)