#!/usr/bin/env python3
"""
生成批量测试文件
用于测试不同批量大小的处理能力
"""

import pandas as pd
import sys

def create_test_file(count, filename):
    """创建包含指定数量图片链接的测试文件"""

    # 使用多个占位图服务，避免单一服务压力过大
    base_urls = [
        'https://placehold.co/300x200/',
        'https://via.placeholder.com/300x200/',
        'https://dummyimage.com/300x200/',
    ]

    colors = ['00ff87', 'ff6b6b', '4ecdc4', '45b7d1', 'f7dc6f', 'bb8fce', 'f8b739']

    urls = []
    for i in range(count):
        base_url = base_urls[i % len(base_urls)]
        color = colors[i % len(colors)]

        if 'placehold.co' in base_url:
            url = f"{base_url}{color}/ffffff?text=Test+{i+1}"
        elif 'placeholder.com' in base_url:
            url = f"{base_url}/{color}/ffffff?text=Test+{i+1}"
        else:  # dummyimage.com
            url = f"{base_url}{color}/ffffff&text=Test+{i+1}"

        urls.append(url)

    # 创建DataFrame
    df = pd.DataFrame({'image_url': urls})

    # 根据文件扩展名保存
    if filename.endswith('.csv'):
        df.to_csv(filename, index=False)
    elif filename.endswith('.xlsx'):
        df.to_excel(filename, index=False)
    else:
        print(f"❌ 不支持的文件格式: {filename}")
        return False

    print(f"✅ 已创建: {filename}")
    print(f"   包含 {count} 个图片链接")

    # 计算预估时间
    estimated_time = count * 1  # 每张约1秒
    minutes = estimated_time // 60
    seconds = estimated_time % 60
    print(f"   预计检测时间: {minutes}分{seconds}秒")

    return True

def main():
    print("=" * 60)
    print("批量测试文件生成器")
    print("=" * 60)
    print()

    # 预设的测试批量
    presets = {
        '1': (10, 'test_10.xlsx', '快速测试'),
        '2': (50, 'test_50.xlsx', '小批量测试'),
        '3': (100, 'test_100.xlsx', '中批量测试'),
        '4': (200, 'test_200.xlsx', '大批量测试'),
        '5': (500, 'test_500.xlsx', '超大批量测试'),
    }

    print("选择测试文件大小:")
    print()
    for key, (count, filename, desc) in presets.items():
        print(f"  {key}. {desc} - {count}张图片 ({filename})")
    print(f"  6. 自定义数量")
    print()

    choice = input("请选择 (1-6): ").strip()

    if choice in presets:
        count, filename, desc = presets[choice]
        print()
        print(f"正在创建 {desc} ({count}张)...")
        create_test_file(count, filename)
    elif choice == '6':
        try:
            count = int(input("\n请输入图片数量: ").strip())
            if count <= 0:
                print("❌ 数量必须大于0")
                return

            format_choice = input("选择格式 (1=CSV, 2=Excel): ").strip()
            ext = '.csv' if format_choice == '1' else '.xlsx'
            filename = f"test_{count}{ext}"

            print()
            print(f"正在创建 {count}张图片的测试文件...")
            create_test_file(count, filename)
        except ValueError:
            print("❌ 请输入有效的数字")
            return
    else:
        print("❌ 无效的选择")
        return

    print()
    print("=" * 60)
    print("🎯 下一步:")
    print("  1. 访问 http://127.0.0.1:5001")
    print("  2. 切换到【批量检测】选项卡")
    print(f"  3. 上传刚生成的文件: {filename if choice in presets else f'test_{count}{ext}'}")
    print("  4. 等待检测完成")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
