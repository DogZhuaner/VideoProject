import cv2
import json
import os
import global_config


def split_image_by_regions(image_path, json_path, output_dir="output_regions"):
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")

    # 读取json文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 创建输出文件夹
    os.makedirs(output_dir, exist_ok=True)

    # 遍历每个区域
    for idx, region in enumerate(data["regions"], start=1):
        coords = region.get("coordinates")  # [x1, y1, x2, y2]
        if not coords or len(coords) != 4:
            print(f"跳过区域 {idx}，无效坐标")
            continue

        x1, y1, x2, y2 = coords
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        # 裁剪区域
        roi = image[y1:y2, x1:x2]

        if roi.size == 0:
            print(f"跳过区域 {idx}，裁剪结果为空")
            continue

        # 旋转裁剪区域 90度
        rotated_roi = cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)

        # 按编号保存，region_001, region_002 ...
        save_name = f"region_{idx:03d}.png"
        save_path = os.path.join(output_dir, save_name)
        cv2.imwrite(save_path, rotated_roi, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # 不压缩
        print(f"已保存: {save_path}")

    print("所有区域裁剪并旋转完成！")

if __name__ == "__main__":
    split_image_by_regions(global_config.Global_Config.live_capture_path, global_config.Global_Config.region_json_path, global_config.Global_Config.split_path)
