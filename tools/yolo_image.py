import os
import cv2
import numpy as np
from ultralytics import YOLO

from global_config import Global_Config

# ========== 参数设置 ==========
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = Global_Config.contact  # 替换为你的模型路径
input_dir = Global_Config.split_path  # 输入图片目录
output_dir = 'result'  # 结果保存目录
imgsz = 1280  # 输入图像大小
conf_thresh = 0.5  # 置信度阈值

# 框样式参数
box_thickness = 2
font_scale = 0.6
font_thickness = 2


# 创建丰富的颜色列表（BGR格式）
def generate_colors(num_classes):
    """为每个类别生成不同的颜色"""
    colors = []
    np.random.seed(42)  # 固定随机种子，确保颜色一致
    for i in range(num_classes):
        # 生成随机颜色，但避免太暗的颜色
        color = tuple(map(int, np.random.randint(50, 255, 3)))
        colors.append(color)
    return colors


# 预定义一些常用颜色（BGR格式）
predefined_colors = [
    (0, 255, 0),  # 绿色
    (255, 0, 0),  # 蓝色
    (0, 0, 255),  # 红色
    (255, 255, 0),  # 青色
    (255, 0, 255),  # 品红色
    (0, 255, 255),  # 黄色
    (128, 0, 128),  # 紫色
    (255, 165, 0),  # 橙色
    (0, 128, 255),  # 橙红色
    (128, 128, 0),  # 橄榄色
    (0, 128, 128),  # 青绿色
    (128, 128, 128),  # 灰色
    (255, 192, 203),  # 粉色
    (255, 20, 147),  # 深粉色
    (0, 191, 255),  # 深天蓝
    (34, 139, 34),  # 森林绿
    (255, 140, 0),  # 深橙色
]

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 加载模型
model = YOLO(model_path)

# 获取类别数量并生成颜色
num_classes = len(model.names)
if num_classes <= len(predefined_colors):
    class_colors = predefined_colors[:num_classes]
else:
    # 如果类别数超过预定义颜色，生成额外颜色
    class_colors = predefined_colors + generate_colors(num_classes - len(predefined_colors))
print(Global_Config.split_path)
print(f"检测到 {num_classes} 个类别，已分配不同颜色")
for i, (class_id, class_name) in enumerate(model.names.items()):
    color = class_colors[i]
    print(f"类别 {class_id}: {class_name} -> 颜色 RGB{color[::-1]}")  # 显示RGB格式

# 获取所有图片文件
image_files = [f for f in os.listdir(input_dir) if
               f.lower().endswith(('.jpg', '.jpeg', '.png')) and f.startswith('region')]

for file in image_files:
    input_path = os.path.join(input_dir, file)
    output_path = os.path.join(output_dir, file)

    # 预测
    results = model.predict(source=input_path, save=False, imgsz=imgsz, conf=conf_thresh,agnostic_nms=True)
    r = results[0]
    image = r.orig_img.copy()

    # 统计每个类别的检测数量
    class_counts = {}

    for box in r.boxes:
        cls_id = int(box.cls)
        conf = float(box.conf)
        class_name = model.names[cls_id]
        label = f"{class_name} {conf:.2f}"
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # 根据类别选择颜色
        box_color = class_colors[cls_id % len(class_colors)]

        # 统计类别数量
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

        # 画检测框
        cv2.rectangle(image, (x1, y1), (x2, y2), box_color, box_thickness)



    # 保存结果
    cv2.imwrite(output_path, image)
    print(f"✅ 已保存: {output_path} | 检测到 {len(r.boxes)} 个目标")
    if class_counts:
        count_str = " | ".join([f"{name}: {count}" for name, count in class_counts.items()])
        print(f"   📊 类别统计: {count_str}")

print(f"\n🎉 所有图片处理完成！输出目录: {output_dir}")
print(f"🎨 使用了 {len(class_colors)} 种不同颜色区分类别")