#!/usr/bin/env python3
"""
图片规范检测工具 - Vercel Serverless 版本
"""

from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw
import os
import base64
from io import BytesIO
import traceback

app = Flask(__name__, template_folder='../templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大 16MB

# 安全区域配置
SAFE_AREA = {
    'left': 14,
    'right': 285,
    'top': 24,
    'bottom': 175
}


def check_image_compliance(image_data):
    """
    检查图片是否符合规范
    自动将图片缩放到 300x200 后检测边界
    返回: dict 包含检测结果和详细信息
    """
    result = {
        'compliant': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }

    try:
        img = Image.open(BytesIO(image_data))

        # 保存原始图片信息
        original_width, original_height = img.size
        result['info']['format'] = img.format
        result['info']['mode'] = img.mode
        result['info']['original_width'] = original_width
        result['info']['original_height'] = original_height

        # 检查原始尺寸是否符合
        if original_width != 300 or original_height != 200:
            result['warnings'].append(f"原始图片尺寸为 {original_width}x{original_height}，已自动缩放到 300x200 进行检测")

            # 自动缩放到 300x200
            img = img.resize((300, 200), Image.Resampling.LANCZOS)
            result['info']['resized'] = True
        else:
            result['info']['resized'] = False

        # 检测尺寸（缩放后）
        width, height = img.size
        result['info']['width'] = width
        result['info']['height'] = height

        # 转换为 RGBA 模式进行像素检测
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 像素位置检查
        out_of_bounds_pixels = []

        for y in range(height):
            for x in range(width):
                pixel = img.getpixel((x, y))
                alpha = pixel[3] if len(pixel) == 4 else 255

                # 如果像素不透明，检查是否在安全区域内
                if alpha > 10:
                    if (x < SAFE_AREA['left'] or x > SAFE_AREA['right'] or
                        y < SAFE_AREA['top'] or y > SAFE_AREA['bottom']):
                        out_of_bounds_pixels.append((x, y))

        if out_of_bounds_pixels:
            result['compliant'] = False
            result['errors'].append(f"发现 {len(out_of_bounds_pixels)} 个像素超出安全区域（与红色边框重叠）")
            result['info']['out_of_bounds_count'] = len(out_of_bounds_pixels)

            # 保存前10个超出位置作为示例
            result['info']['out_of_bounds_samples'] = out_of_bounds_pixels[:10]

        # 生成带红色边框的预览图（叠加模板边框）
        preview_img = img.copy().convert('RGBA')

        # 创建红色边框叠加层
        overlay = Image.new('RGBA', (300, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 绘制红色边框区域（半透明红色）
        red_color = (232, 115, 107, 120)  # 半透明红色

        # 上边框
        draw.rectangle([0, 0, 299, SAFE_AREA['top']-1], fill=red_color)
        # 下边框
        draw.rectangle([0, SAFE_AREA['bottom']+1, 299, 199], fill=red_color)
        # 左边框
        draw.rectangle([0, SAFE_AREA['top'], SAFE_AREA['left']-1, SAFE_AREA['bottom']], fill=red_color)
        # 右边框
        draw.rectangle([SAFE_AREA['right']+1, SAFE_AREA['top'], 299, SAFE_AREA['bottom']], fill=red_color)

        # 绘制安全区域的绿色边界线
        green_color = (0, 255, 0, 180)  # 半透明绿色
        # 上边界
        draw.line([SAFE_AREA['left'], SAFE_AREA['top'], SAFE_AREA['right'], SAFE_AREA['top']],
                  fill=green_color, width=2)
        # 下边界
        draw.line([SAFE_AREA['left'], SAFE_AREA['bottom'], SAFE_AREA['right'], SAFE_AREA['bottom']],
                  fill=green_color, width=2)
        # 左边界
        draw.line([SAFE_AREA['left'], SAFE_AREA['top'], SAFE_AREA['left'], SAFE_AREA['bottom']],
                  fill=green_color, width=2)
        # 右边界
        draw.line([SAFE_AREA['right'], SAFE_AREA['top'], SAFE_AREA['right'], SAFE_AREA['bottom']],
                  fill=green_color, width=2)

        # 叠加红色边框到预览图
        preview_img = Image.alpha_composite(preview_img, overlay)

        # 保存预览图
        buffered = BytesIO()
        preview_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        result['info']['resized_image'] = f"data:image/png;base64,{img_str}"

    except Exception as e:
        result['compliant'] = False
        result['errors'].append(f"处理图片时发生错误: {str(e)}")
        result['info']['exception'] = traceback.format_exc()

    return result


@app.route('/')
def index():
    """主页"""
    return render_template('index.html', safe_area=SAFE_AREA)


@app.route('/upload', methods=['POST'])
def upload():
    """处理图片上传和检测"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if file:
        try:
            # 读取图片数据
            image_data = file.read()

            # 检测图片
            result = check_image_compliance(image_data)

            # 添加上传的图片预览
            img_str = base64.b64encode(image_data).decode()
            result['info']['uploaded_image'] = f"data:image/png;base64,{img_str}"

            return jsonify(result)
        except Exception as e:
            return jsonify({
                'error': f'处理失败: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500

    return jsonify({'error': '未知错误'}), 500


# Vercel serverless 函数入口
def handler(request):
    return app(request)


if __name__ == '__main__':
    app.run(debug=True)
