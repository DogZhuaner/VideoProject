from global_config import Global_Config
import os
import shutil
import pandas as pd


def validate_and_move_files():
    """
    比较 new 和 old 目录下的 merge_result.csv，
    校验状态变化是否符合规则，通过则覆盖 old 文件。
    返回：如果检测到并通过校验，返回变化的两个触点名列表 [name1, name2]，
          否则返回 None。
    """
    # 使用 Global_Config 中定义的路径
    old_dir = Global_Config.old_result_csv_path
    new_dir = Global_Config.result_csv_path
    old_file_path = os.path.join(old_dir, 'merge_result.csv')
    new_file_path = os.path.join(new_dir, 'merge_result.csv')

    # 第一步：检查 old 目录下是否存在 merge_result.csv 文件
    if not os.path.exists(old_file_path):
        # 如果 old 不存在，但 new 中存在，则直接复制过去后结束
        if os.path.exists(new_file_path):
            shutil.copy(new_file_path, old_file_path)  # 将文件从 new 复制到 old 目录
        return [],[]  # 结束程序

    # 第二步：加载 CSV 文件（不使用表头，按列序号处理）
    old_df = pd.read_csv(old_file_path, header=None)
    new_df = pd.read_csv(new_file_path, header=None)

    # 第三步：只取第一列和第二列
    old_df = old_df[[0, 1]]
    new_df = new_df[[0, 1]]

    # 给列命名，方便后续操作（第一列当作触点名，第二列当作状态）
    old_df.columns = ['触点名', '状态']
    new_df.columns = ['触点名', '状态']

    # 按触点名合并 old 和 new，比较状态是否发生变化
    merged = pd.merge(old_df, new_df, on='触点名', suffixes=('_old', '_new'))

    # 找出状态不同的行
    diff_df = merged[merged['状态_old'] != merged['状态_new']]

    # 如果完全没有变化
    if len(diff_df) == 0:
        print("没有检测到更新")
        return [],[]

    # 第四步：根据条件判断是新增触点还是撤回触点
    added_contacts = []
    removed_contacts = []
    delete_from_union = []

    for _, row in diff_df.iterrows():
        old_state = row['状态_old']
        new_state = row['状态_new']
        name = row['触点名']

        # 新增触点的条件
        #两个触点从empty变为wired
        if (old_state == 'empty' and new_state in ['wired']) or \
           (old_state == 'wired' and new_state =='wired2'):
            added_contacts.append(name)

        # 撤回触点的条件
        if (old_state == 'wired' and new_state == 'empty') or \
           (old_state == 'wired2' and new_state == 'wired'):
            removed_contacts.append(name)

        if (old_state == 'wired' and new_state == 'empty'):
            delete_from_union.append(name)


    # 判断是否符合新增触点的条件
    if len(added_contacts) == 2:
        print(f"新增接线触点是：{added_contacts[0]} 和 {added_contacts[1]}")
        #赋值全局变量，当前接线的两个触点
        Global_Config.current_A = added_contacts[0]
        Global_Config.current_B = added_contacts[1]

        #设置接线状态
        Global_Config.wired_status = "add"

        # 如果是新增触点，直接返回
        return added_contacts,delete_from_union

    # 判断是否符合撤回触点的条件
    if len(removed_contacts) == 2:
        print(f"撤回触点是：{removed_contacts[0]} 和 {removed_contacts[1]}")
        # 如果是撤回触点，直接返回
        Global_Config.current_A = removed_contacts[0]
        Global_Config.current_B = removed_contacts[1]

        # 设置接线状态
        Global_Config.wired_status = "sub"

        return removed_contacts,delete_from_union

    #新增的和撤回的触点都为0
    if len(removed_contacts)==0 and len(added_contacts)==0:
        print("没有新增或撤回触点。")
        return [],[]

    print("接线步骤识别出错！")
    Global_Config.wired_status = "error"
    return [],[]

# 通过 main 直接使用
if __name__ == "__main__":
    result = validate_and_move_files()
    print(result)
