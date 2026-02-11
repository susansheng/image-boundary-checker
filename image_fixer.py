#!/usr/bin/env python3
"""
图片自动修复模块
提供智能裁剪和边距添加等修复策略
"""

from PIL import Image, ImageDraw
import numpy as np
import re
from urllib.parse import urlparse, parse_qs
from io import BytesIO

# 安全区域配置（与 web_validator.py 一致）
SAFE_AREA = {
    'left': 14,
    'right': 285,
    'top': 24,
    'bottom': 175
}


def find_content_bounds(img):
    """
    找到图片中所有不透明像素的边界框

    Args:
        img: PIL Image对象（RGBA模式，300x200尺寸）

    Returns:
        tuple: (min_x, min_y, max_x, max_y) 内容边界框
    """
    width, height = img.size
    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))
            alpha = pixel[3] if len(pixel) == 4 else 255

            # 如果像素不透明，更新边界
            if alpha > 10:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    # 如果没有找到任何内容，返回整个图片区域
    if min_x == width and min_y == height:
        return (0, 0, width - 1, height - 1)

    return (min_x, min_y, max_x, max_y)


def calculate_optimal_crop_box(content_bounds, safe_area):
    """
    计算最佳裁剪框，确保内容在安全区域内

    Args:
        content_bounds: (min_x, min_y, max_x, max_y) 内容边界
        safe_area: 安全区域字典

    Returns:
        tuple: (left, top, right, bottom) 裁剪框坐标（在300x200尺寸上）
    """
    min_x, min_y, max_x, max_y = content_bounds

    # 计算内容的宽度和高度
    content_width = max_x - min_x + 1
    content_height = max_y - min_y + 1

    # 安全区域的尺寸
    safe_width = safe_area['right'] - safe_area['left']
    safe_height = safe_area['bottom'] - safe_area['top']

    # 如果内容已经在安全区域内，不需要裁剪
    if (min_x >= safe_area['left'] and max_x <= safe_area['right'] and
        min_y >= safe_area['top'] and max_y <= safe_area['bottom']):
        return (0, 0, 300, 200)

    # 计算需要裁剪的区域
    # 策略：居中裁剪，确保内容在安全区域内

    # 计算目标区域（安全区域）
    target_center_x = (safe_area['left'] + safe_area['right']) // 2
    target_center_y = (safe_area['top'] + safe_area['bottom']) // 2

    # 计算内容中心
    content_center_x = (min_x + max_x) // 2
    content_center_y = (min_y + max_y) // 2

    # 计算偏移量（将内容中心移动到安全区域中心）
    offset_x = target_center_x - content_center_x
    offset_y = target_center_y - content_center_y

    # 计算新的裁剪框
    crop_left = max(0, -offset_x)
    crop_top = max(0, -offset_y)
    crop_right = min(300, 300 - offset_x)
    crop_bottom = min(200, 200 - offset_y)

    return (crop_left, crop_top, crop_right, crop_bottom)


def smart_crop_to_safe_area(img):
    """
    智能裁剪：在原图上找到最佳裁剪区域，确保内容在安全区域内

    Args:
        img: PIL Image对象（原始尺寸）

    Returns:
        PIL Image对象（修复后，保持原始尺寸）
    """
    original_width, original_height = img.size

    # 1. 缩放到300×200进行检测
    test_img = img.resize((300, 200), Image.Resampling.LANCZOS)
    if test_img.mode != 'RGBA':
        test_img = test_img.convert('RGBA')

    # 2. 找到内容边界
    content_bounds = find_content_bounds(test_img)

    # 3. 计算最佳裁剪框（在300×200尺寸上）
    crop_box_300x200 = calculate_optimal_crop_box(content_bounds, SAFE_AREA)

    # 4. 映射回原图尺寸
    scale_x = original_width / 300
    scale_y = original_height / 200
    crop_box_original = (
        int(crop_box_300x200[0] * scale_x),
        int(crop_box_300x200[1] * scale_y),
        int(crop_box_300x200[2] * scale_x),
        int(crop_box_300x200[3] * scale_y)
    )

    # 5. 在原图上裁剪
    cropped = img.crop(crop_box_original)

    # 6. 调整回原图尺寸（居中放置）
    # 检查图片是否有透明通道
    has_alpha = img.mode == 'RGBA' or img.mode == 'LA'

    if has_alpha:
        result = Image.new('RGBA', (original_width, original_height), (255, 255, 255, 0))
    else:
        result = Image.new('RGB', (original_width, original_height), (255, 255, 255))

    paste_x = (original_width - cropped.width) // 2
    paste_y = (original_height - cropped.height) // 2

    if has_alpha and cropped.mode != 'RGBA':
        cropped = cropped.convert('RGBA')

    result.paste(cropped, (paste_x, paste_y))

    return result


def add_padding_to_safe_area(img):
    """
    添加边距：在原图四周添加白边或透明边，将内容推入安全区域

    Args:
        img: PIL Image对象（原始尺寸）

    Returns:
        PIL Image对象（修复后，保持原始尺寸）
    """
    original_width, original_height = img.size

    # 1. 缩放到300×200进行检测
    test_img = img.resize((300, 200), Image.Resampling.LANCZOS)
    if test_img.mode != 'RGBA':
        test_img = test_img.convert('RGBA')

    # 2. 找到内容边界
    content_bounds = find_content_bounds(test_img)
    min_x, min_y, max_x, max_y = content_bounds

    # 3. 计算需要添加的边距（在300×200尺寸上）
    padding_left = max(0, SAFE_AREA['left'] - min_x)
    padding_right = max(0, max_x - SAFE_AREA['right'])
    padding_top = max(0, SAFE_AREA['top'] - min_y)
    padding_bottom = max(0, max_y - SAFE_AREA['bottom'])

    # 4. 映射回原图尺寸
    scale_x = original_width / 300
    scale_y = original_height / 200

    padding_left_original = int(padding_left * scale_x)
    padding_right_original = int(padding_right * scale_x)
    padding_top_original = int(padding_top * scale_y)
    padding_bottom_original = int(padding_bottom * scale_y)

    # 5. 创建新图片（带边距）
    new_width = original_width + padding_left_original + padding_right_original
    new_height = original_height + padding_top_original + padding_bottom_original

    # 检查图片是否有透明通道
    has_alpha = img.mode == 'RGBA' or img.mode == 'LA'

    if has_alpha:
        result = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 0))
    else:
        result = Image.new('RGB', (new_width, new_height), (255, 255, 255))

    # 6. 将原图粘贴到中心
    if has_alpha and img.mode != 'RGBA':
        img = img.convert('RGBA')

    result.paste(img, (padding_left_original, padding_top_original))

    # 7. 缩放回原始尺寸
    result = result.resize((original_width, original_height), Image.Resampling.LANCZOS)

    return result


def extract_filename_from_url(url):
    """
    从URL中提取文件名：取最后一个斜杠到扩展名之间的部分

    例：https://example.com/path/my_image.jpg → my_image

    Args:
        url: 图片URL

    Returns:
        str: 文件名（不含扩展名）
    """
    try:
        parsed = urlparse(url)
        path = parsed.path

        if path:
            filename = path.split('/')[-1]
            name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
            name_without_ext = name_without_ext.strip()
            if name_without_ext:
                return sanitize_filename(name_without_ext)

        return 'image_fixed'

    except Exception:
        return 'image_fixed'


def sanitize_filename(filename):
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        str: 清理后的文件名
    """
    # 移除特殊字符，只保留字母、数字、下划线、连字符
    cleaned = re.sub(r'[^\w\-]', '_', filename)

    # 移除开头和结尾的下划线
    cleaned = cleaned.strip('_')

    # 限制长度
    if len(cleaned) > 50:
        cleaned = cleaned[:50]

    return cleaned if cleaned else 'image'


def is_watermark_pixel(x, y, alpha, img_width, img_height):
    """
    判断像素是否为水印

    规则：alpha < 50 且在右下角区域

    Args:
        x, y: 像素坐标
        alpha: 透明度值
        img_width, img_height: 图片尺寸

    Returns:
        bool: True表示是水印
    """
    # 半透明判定
    if alpha >= 50:
        return False

    # 右下角区域判定（右下1/4区域）
    right_threshold = img_width * 0.75
    bottom_threshold = img_height * 0.75

    if x >= right_threshold and y >= bottom_threshold:
        return True

    return False


def find_car_bounds_exclude_watermark(img):
    """
    找到车图边界，排除右下角水印

    Args:
        img: PIL Image对象（RGBA模式，300x200尺寸）

    Returns:
        tuple: (min_x, min_y, max_x, max_y) 车图边界框（不含水印）
    """
    width, height = img.size
    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))
            alpha = pixel[3] if len(pixel) == 4 else 255

            # 检查是否为水印
            if is_watermark_pixel(x, y, alpha, width, height):
                continue

            # 如果是不透明的车图像素（alpha > 200）
            if alpha > 200:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    # 如果没有找到车图内容，返回整个图片区域
    if min_x == width and min_y == height:
        return (0, 0, width - 1, height - 1)

    return (min_x, min_y, max_x, max_y)


def smart_fit_to_safe_area(img):
    """
    智能适配：居中调整 + 等比缩放（放大或缩小），排除水印干扰

    策略：
    1. 识别并排除右下角半透明水印
    2. 计算车图实际边界
    3. 尝试居中调整
    4. 如果超出安全区 → 等比缩小至完全贴住安全线
    5. 如果未撑满安全区 → 等比放大至完全贴住安全线
    6. 优先级：缩放倍数越小越好（高车贴上下，长车贴左右）

    Args:
        img: PIL Image对象（原始尺寸）

    Returns:
        PIL Image对象（修复后，保持原始尺寸）
    """
    original_width, original_height = img.size

    # 1. 缩放到300×200进行分析
    test_img = img.resize((300, 200), Image.Resampling.LANCZOS)
    if test_img.mode != 'RGBA':
        test_img = test_img.convert('RGBA')

    # 2. 找到车图边界（排除水印）
    car_bounds = find_car_bounds_exclude_watermark(test_img)
    min_x, min_y, max_x, max_y = car_bounds

    # 计算车图尺寸
    car_width = max_x - min_x + 1
    car_height = max_y - min_y + 1

    # 安全区域尺寸
    safe_width = SAFE_AREA['right'] - SAFE_AREA['left']  # 271
    safe_height = SAFE_AREA['bottom'] - SAFE_AREA['top']  # 151

    # 3. 计算居中位置
    safe_center_x = (SAFE_AREA['left'] + SAFE_AREA['right']) // 2
    safe_center_y = (SAFE_AREA['top'] + SAFE_AREA['bottom']) // 2

    car_center_x = (min_x + max_x) // 2
    car_center_y = (min_y + max_y) // 2

    # 计算偏移量
    offset_x = safe_center_x - car_center_x
    offset_y = safe_center_y - car_center_y

    # 4. 检查居中后是否超出或过小
    new_min_x = min_x + offset_x
    new_max_x = max_x + offset_x
    new_min_y = min_y + offset_y
    new_max_y = max_y + offset_y

    # 计算需要的缩放比例
    scale_ratio = 1.0

    # 检查是否超出安全区
    is_overflow = (new_min_x < SAFE_AREA['left'] or new_max_x > SAFE_AREA['right'] or
                   new_min_y < SAFE_AREA['top'] or new_max_y > SAFE_AREA['bottom'])

    # 检查是否过小（未撑满安全区）
    is_too_small = (car_width < safe_width * 0.98 and car_height < safe_height * 0.98)

    if is_overflow or is_too_small:
        # 计算宽度和高度的缩放比例
        target_width = 264
        target_height = 144
        width_scale = target_width / car_width
        height_scale = target_height / car_height

        # 无论缩小还是放大，都取较小的比例（确保不超出，同时至少一边压住安全线）
        scale_ratio = min(width_scale, height_scale)

    # 5. 应用变换到原图
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 映射回原图尺寸
    scale_x = original_width / 300
    scale_y = original_height / 200

    # 创建结果图片
    result = Image.new('RGBA', (original_width, original_height), (255, 255, 255, 0))

    if scale_ratio != 1.0:
        # 需要缩放（缩小或放大）
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 居中放置：让车图内容中心对准安全区域中心
        paste_x = int(scale_x * (safe_center_x - car_center_x * scale_ratio))
        paste_y = int(scale_y * (safe_center_y - car_center_y * scale_ratio))
        result.paste(scaled_img, (paste_x, paste_y))
    else:
        # 只需要偏移，不需要缩放
        offset_x_original = int(offset_x * scale_x)
        offset_y_original = int(offset_y * scale_y)

        # 计算粘贴位置
        paste_x = offset_x_original
        paste_y = offset_y_original

        # 创建临时画布进行偏移
        temp = Image.new('RGBA', (original_width, original_height), (255, 255, 255, 0))
        temp.paste(img, (paste_x, paste_y))
        result = temp

    return result


def remove_watermark(img, alpha_threshold=200, brightness_threshold=250,
                     x_fraction=0.65, y_fraction=0.50):
    """
    去除右下角半透明白色水印

    策略：在指定区域内，将"半透明 + 高亮度（白色）"的像素设为完全透明。
    通过亮度过滤区分水印（白色文字）和车影（深色），确保车图不受影响。

    Args:
        img: PIL Image 对象
        alpha_threshold: alpha 上限，低于此值且满足亮度条件的像素视为水印（默认 200）
        brightness_threshold: 亮度下限，高于此值视为白色水印像素（默认 250）
        x_fraction: 水印区域 X 起始比例（默认 0.65，即右侧 35%）
        y_fraction: 水印区域 Y 起始比例（默认 0.50，即下半部分）

    Returns:
        PIL Image: 去除水印后的图片（原始尺寸）
    """
    img = img.copy().convert('RGBA')
    pixels = np.array(img)
    h, w = pixels.shape[:2]

    y_start = int(h * y_fraction)
    x_start = int(w * x_fraction)

    region = pixels[y_start:, x_start:]
    alpha = region[:, :, 3]
    rgb = region[:, :, :3]
    brightness = np.mean(rgb, axis=2)

    # 水印 = 半透明 + 白色（高亮度）
    mask = (alpha > 0) & (alpha < alpha_threshold) & (brightness > brightness_threshold)
    region[mask] = [0, 0, 0, 0]

    pixels[y_start:, x_start:] = region

    return Image.fromarray(pixels)


def get_fix_description(strategy):
    """
    获取修复策略的描述

    Args:
        strategy: 修复策略名称

    Returns:
        str: 策略描述
    """
    descriptions = {
        'smart_crop': '智能裁剪：找到最佳内容区域并调整',
        'add_padding': '添加边距：在图片周围添加白边',
        'smart_fit': '智能适配：识别水印，居中+缩放至安全区（推荐）'
    }
    return descriptions.get(strategy, '未知策略')
