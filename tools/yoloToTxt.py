import os
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt

# 加载训练好的YOLO模型权重
model_path = 'D:/Project/video2.0/weights/contact.pt'  # 替换为你的YOLO权重文件路径
model = YOLO(model_path)

# 指定目录下的图片
image_directory = 'D:/datasets/contact'  # 替换为你的图片文件夹路径

# 获取所有图片文件
image_files = [f for f in os.listdir(image_directory) if f.endswith(('.jpg', '.jpeg', '.png'))]

# 循环处理每张图片
for image_file in image_files:
    image_path = os.path.join(image_directory, image_file)

    # 读取图片
    img = cv2.imread(image_path)

    # 使用YOLO模型进行目标检测
    results = model(image_path)

    # 提取检测结果
    # results[0].boxes 是包含检测框、类别和置信度的对象
    boxes = results[0].boxes.xyxy.cpu().numpy()  # 获取框的坐标（x1, y1, x2, y2）
    labels = results[0].boxes.cls.cpu().numpy().astype(int)  # 获取类别索引
    conf = results[0].boxes.conf.cpu().numpy()  # 获取置信度

    # 保存检测结果到txt文件
    txt_filename = os.path.splitext(image_file)[0] + '.txt'  # 获取与图片同名的txt文件
    txt_path = os.path.join(image_directory, txt_filename)

    with open(txt_path, 'w') as f:
        for box, label, confidence in zip(boxes, labels, conf):
            if confidence > 0.5:  # 可以调整置信度阈值
                x1, y1, x2, y2 = map(int, box)
                # 将检测框格式转换为yolo格式：class_id x_center y_center width height
                width = x2 - x1
                height = y2 - y1
                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                # 将坐标归一化到[0, 1]范围
                x_center /= img.shape[1]
                y_center /= img.shape[0]
                width /= img.shape[1]
                height /= img.shape[0]
                # 将检测结果写入txt文件
                f.write(f'{label} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n')

    # 可视化检测结果
    for box, label, confidence in zip(boxes, labels, conf):
        if confidence > 0.5:  # 可以调整置信度阈值
            x1, y1, x2, y2 = map(int, box)
            img = cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            img = cv2.putText(img, f'{label} {confidence:.2f}', (x1, y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # 显示结果图片
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis('off')  # 不显示坐标轴
    plt.show()
