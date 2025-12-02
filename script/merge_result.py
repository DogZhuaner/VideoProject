import os
import csv
from global_config import Global_Config
def merge_txt_files(dir_a, dir_b, output_dir, output_name="merge_result.csv"):
    merged_rows = []

    # 找到两个目录下的公共文件名
    files_a = set(f for f in os.listdir(dir_a) if f.endswith(".txt"))
    files_b = set(f for f in os.listdir(dir_b) if f.endswith(".txt"))
    common_files = files_a & files_b

    if not common_files:
        print("⚠️ 没有找到同名的 txt 文件")
        return

    for filename in common_files:
        path_a = os.path.join(dir_a, filename)
        path_b = os.path.join(dir_b, filename)

        with open(path_a, "r", encoding="utf-8") as fa, \
             open(path_b, "r", encoding="utf-8") as fb:
            lines_a = [line.strip() for line in fa if line.strip()]
            lines_b = [line.strip() for line in fb if line.strip()]

        len_a, len_b = len(lines_a), len(lines_b)
        print(f"📄 文件 {filename}: 目录A={len_a} 行, 目录B={len_b} 行")

        if len_a != len_b:
            print(f"⚠️ 警告: {filename} 两个文件行数不一致，将按较少的 {min(len_a, len_b)} 行进行合并")

        # 按最短行数进行合并
        min_len = min(len_a, len_b)
        for la, lb in zip(lines_a[:min_len], lines_b[:min_len]):
            # B 文件按空格拆分，只取第一列
            lb_cols = lb.split()
            second_col = lb_cols[0] if lb_cols else ""

            # 只保留前两列
            merged_rows.append([la, second_col])

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_name)

    # 保存到 CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(merged_rows)

    print(f"✅ 合并完成，结果保存为 {output_path}")


# 示例调用
if __name__ == '__main__':
 merge_txt_files(Global_Config.label_6area_path, Global_Config.predict_txt_path, Global_Config.result_csv_path)   # 会生成 output/merge_result.csv
