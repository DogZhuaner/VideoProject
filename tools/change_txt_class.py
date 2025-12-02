import os


# 定义一个函数来修改单个txt文件中的类标签
def modify_labels_in_file(file_path):
    # 读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 修改类标签
    modified_lines = []
    for line in lines:
        parts = line.split()
        # 如果类标签是15，修改为0；如果类标签是16，修改为1
        if parts[0] == '15':
            parts[0] = '0'
        elif parts[0] == '16':
            parts[0] = '1'
        modified_lines.append(" ".join(parts))

    # 获取修改后的文件路径
    modified_file_path = os.path.splitext(file_path)[0]+".txt"

    # 写入修改后的内容
    with open(modified_file_path, 'w') as modified_file:
        modified_file.writelines([line + '\n' for line in modified_lines])

    return modified_file_path


# 批量处理指定目录下的所有txt文件
def batch_modify_labels(directory_path):
    # 获取目录下的所有txt文件
    txt_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]

    modified_files = []
    for txt_file in txt_files:
        file_path = os.path.join(directory_path, txt_file)
        modified_file_path = modify_labels_in_file(file_path)
        modified_files.append(modified_file_path)

    return modified_files


# 批量修改标注文件的路径
directory_path = 'D:\datasets\contact'  # 替换为你的txt文件目录路径
modified_files = batch_modify_labels(directory_path)

# 输出修改后的文件路径
print("修改后的文件路径：")
for file in modified_files:
    print(file)
