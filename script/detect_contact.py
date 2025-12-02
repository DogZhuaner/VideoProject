import os
import cv2
from ultralytics import YOLO
from global_config import Global_Config

def detect_and_save(input_dir, output_dir, model_path, classes_to_detect):
    # 加载YOLO模型
    model = YOLO(model_path)

    # 获取输入目录下的所有图片文件
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    for image_file in image_files:
        image_path = os.path.join(input_dir, image_file)
        output_txt_path = os.path.join(output_dir, os.path.splitext(image_file)[0] + '.txt')

        # 读取图片
        image = cv2.imread(image_path)

        # 使用YOLO进行目标检测
        results = model(image,imgsz=1280, conf=0.4,agnostic_nms=True)
        result = results[0]

        # 获取检测框，类别，置信度
        boxes = result.boxes
        labels = result.names
        confs = boxes.conf
        cls = boxes.cls

        # 筛选只包含empty或wired的目标
        filtered_boxes = []
        for i in range(len(cls)):
            if labels[int(cls[i])] in classes_to_detect:
                filtered_boxes.append({
                    "label": labels[int(cls[i])],
                    "confidence": confs[i].item(),
                    "box": boxes.xywh[i].cpu().numpy()
                })

        # 根据y坐标排序
        filtered_boxes.sort(key=lambda x: x['box'][1])  # 按y坐标排序（box[1]是y中心点）

        # 保存检测结果到txt文件
        with open(output_txt_path, 'w') as f:
            for box in filtered_boxes:
                label = box['label']
                confidence = box['confidence']
                x, y, w, h = box['box']  # xywh
                # 格式：label x_center y_center width height confidence
                f.write(f"{label} {x:.2f} {y:.2f} {w:.2f} {h:.2f} {confidence:.2f}\n")

if __name__ == "__main__":
    # 配置目录路径和YOLO权重路径
    input_dir = Global_Config.split_path  # 输入图片的目录
    output_dir = Global_Config.predict_txt_path  # 输出txt文件的目录
    model_path = Global_Config.contact  # 训练好的YOLO模型权重路径

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 执行检测
    detect_and_save(input_dir, output_dir, model_path, ["empty", "wired","wired2"])
