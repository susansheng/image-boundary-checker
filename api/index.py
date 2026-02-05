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
import pandas as pd
import requests
from urllib.parse import urlparse

app = Flask(__name__, template_folder='../templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大 16MB

# 安全区域配置
SAFE_AREA = {
    'left': 14,
    'right': 285,
    'top': 24,
    'bottom': 175
}


def generate_template_image():
    """
    生成模板图片：300x200，带红色边框标识安全区域
    """
    # 创建白色背景图片
    img = Image.new('RGB', (300, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 红色
    red_color = (232, 115, 107)

    # 绘制红色边框区域
    # 上边框
    draw.rectangle([0, 0, 299, SAFE_AREA['top']-1], fill=red_color)
    # 下边框
    draw.rectangle([0, SAFE_AREA['bottom']+1, 299, 199], fill=red_color)
    # 左边框
    draw.rectangle([0, SAFE_AREA['top'], SAFE_AREA['left']-1, SAFE_AREA['bottom']], fill=red_color)
    # 右边框
    draw.rectangle([SAFE_AREA['right']+1, SAFE_AREA['top'], 299, SAFE_AREA['bottom']], fill=red_color)

    # 转换为 base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


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


@app.route('/template')
def get_template():
    """获取模板图片"""
    try:
        template_image = generate_template_image()
        return jsonify({
            'success': True,
            'image': template_image,
            'safe_area': SAFE_AREA
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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


@app.route('/batch_upload', methods=['POST'])
def batch_upload():
    """处理批量上传：读取表格并检测多张图片"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    try:
        # 读取表格文件
        filename = file.filename.lower()

        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'error': '不支持的文件格式，请上传 CSV 或 Excel 文件'}), 400

        # 查找包含图片链接的列
        image_column = None
        possible_columns = ['url', 'image_url', 'img_url', 'link', 'image', 'img', '图片', '图片链接', '链接']

        # 首先尝试精确匹配（不区分大小写）
        for col in df.columns:
            if col.lower() in [pc.lower() for pc in possible_columns]:
                image_column = col
                break

        # 如果没找到，尝试模糊匹配
        if image_column is None:
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['url', 'link', 'image', 'img', '图片', '链接']):
                    image_column = col
                    break

        # 如果还是没找到，使用第一列
        if image_column is None:
            if len(df.columns) > 0:
                image_column = df.columns[0]
            else:
                return jsonify({'error': '表格为空或没有找到图片链接列'}), 400

        # 提取图片URL列表
        image_urls = df[image_column].dropna().tolist()

        if not image_urls:
            return jsonify({'error': f'在列 "{image_column}" 中没有找到有效的图片链接'}), 400

        # 批量检测
        results = []
        total = len(image_urls)
        success_count = 0
        failed_count = 0
        compliant_count = 0
        non_compliant_count = 0

        for idx, url in enumerate(image_urls, 1):
            result_item = {
                'index': idx,
                'url': str(url),
                'status': 'pending'
            }

            try:
                # 下载图片
                response = requests.get(str(url), timeout=10)
                response.raise_for_status()

                # 检测图片
                image_data = response.content
                check_result = check_image_compliance(image_data)

                result_item['status'] = 'success'
                result_item['compliant'] = check_result['compliant']
                result_item['errors'] = check_result['errors']
                result_item['warnings'] = check_result['warnings']
                result_item['info'] = {
                    'width': check_result['info'].get('width'),
                    'height': check_result['info'].get('height'),
                    'original_width': check_result['info'].get('original_width'),
                    'original_height': check_result['info'].get('original_height'),
                    'resized': check_result['info'].get('resized'),
                    'out_of_bounds_count': check_result['info'].get('out_of_bounds_count', 0)
                }

                # 添加缩略图（缩小版本以节省带宽）
                if 'resized_image' in check_result['info']:
                    result_item['preview'] = check_result['info']['resized_image']

                success_count += 1
                if check_result['compliant']:
                    compliant_count += 1
                else:
                    non_compliant_count += 1

            except requests.exceptions.RequestException as e:
                result_item['status'] = 'failed'
                result_item['error'] = f'下载图片失败: {str(e)}'
                failed_count += 1
            except Exception as e:
                result_item['status'] = 'failed'
                result_item['error'] = f'检测失败: {str(e)}'
                failed_count += 1

            results.append(result_item)

        # 返回批量检测结果
        return jsonify({
            'success': True,
            'summary': {
                'total': total,
                'success': success_count,
                'failed': failed_count,
                'compliant': compliant_count,
                'non_compliant': non_compliant_count
            },
            'column_used': image_column,
            'results': results
        })

    except Exception as e:
        return jsonify({
            'error': f'处理表格失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


# Flask app 会被 Vercel 自动检测和使用
# 不需要额外的 handler 函数
