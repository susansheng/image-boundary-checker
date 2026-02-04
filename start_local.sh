#!/bin/bash
# 图片边界验收工具 - 本地启动脚本

echo "=========================================="
echo "  图片边界验收工具 - 本地版本"
echo "=========================================="
echo ""
echo "🔒 数据安全: 所有处理都在本地完成，不会上传到服务器"
echo ""
echo "正在启动本地服务器..."
echo ""

cd "/Users/sxsheng/Documents/代码/图片边界验收工具"
python3 web_validator.py
