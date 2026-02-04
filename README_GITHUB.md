# 🖼️ 图片边界验收工具

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/image-boundary-checker)

一个自动化的图片规范检测工具，用于验证图片内容是否符合特定的边界要求。

## ✨ 核心功能

- 🎯 **智能自动缩放** - 支持任意尺寸图片，自动缩放到 300×200 进行检测
- 🔍 **逐像素检测** - 精确检测图片内容是否在安全区域内
- 🎨 **可视化边界** - 红色边框叠加显示，直观展示超出边界的部分
- 📊 **详细报告** - 显示原始尺寸、缩放信息、超出像素数等
- 🌐 **Web 界面** - 支持拖拽上传，实时预览检测结果

## 🎬 演示

[在线演示](https://your-deployment-url.vercel.app)

### 功能预览

**上传图片 → 自动检测 → 可视化结果**

- 🟢 绿色边界线：标记安全区域边界
- 🔴 红色半透明区域：标记禁区（内容不能超出）
- ✅ 实时显示检测结果和详细信息

## 📋 检测规范

### 尺寸要求
- 自动缩放到：300px × 200px

### 安全区域边界
图片内容（非透明像素）必须在以下区域内：
- 左边界：14px
- 右边界：285px
- 上边界：24px
- 下边界：175px

## 🚀 快速开始

### 在线使用

直接访问：[https://your-deployment-url.vercel.app](https://your-deployment-url.vercel.app)

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/image-boundary-checker.git
cd image-boundary-checker

# 安装依赖
pip install -r requirements.txt

# 运行本地服务器
python3 web_validator.py

# 访问 http://localhost:5000
```

### 部署到 Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/image-boundary-checker)

或查看详细部署指南：[DEPLOYMENT.md](./DEPLOYMENT.md)

## 📊 使用示例

### 1. 上传图片

拖拽或点击上传区域选择图片

### 2. 查看结果

**符合规范 ✅**
```
✓ 检测通过
图片完全符合规范要求！

原始尺寸: 600 × 400 像素
检测尺寸: 300 × 200 像素（已缩放）
```

**不符合规范 ❌**
```
✗ 检测未通过

发现以下问题：
✗ 发现 1500 个像素超出安全区域（与红色边框重叠）

原始尺寸: 800 × 600 像素
检测尺寸: 300 × 200 像素（已缩放）
超出像素数: 1500
```

### 3. 可视化预览

左侧显示原始图片，右侧显示叠加红色边框后的检测预览，一眼看出哪里超出边界。

## 🛠️ 技术栈

- **后端**: Python 3.9+, Flask
- **图像处理**: Pillow (PIL)
- **前端**: HTML5, CSS3, JavaScript
- **部署**: Vercel Serverless Functions

## 📁 项目结构

```
image-boundary-checker/
├── api/
│   └── index.py              # Vercel serverless 入口
├── templates/
│   └── index.html            # Web 界面
├── test_*.png                # 测试图片
├── demo_*.png                # 演示图片
├── vercel.json               # Vercel 配置
├── requirements.txt          # Python 依赖
├── README.md                 # 项目说明（本文件）
├── DEPLOYMENT.md             # 部署指南
└── .gitignore               # Git 忽略文件
```

## 🎯 典型应用场景

- 📦 **电商平台** - 商品图片规范检测
- 📱 **社交媒体** - 用户头像边界验证
- 🎨 **设计工具** - 设计稿规范检查
- 📝 **内容管理** - 图片上传验证
- 🔍 **批量检测** - 图片质量审核

## 🔧 配置说明

### 调整安全区域边界

修改 `api/index.py` 中的配置：

```python
SAFE_AREA = {
    'left': 14,
    'right': 285,
    'top': 24,
    'bottom': 175
}
```

### 调整文件大小限制

```python
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB
```

## 📖 详细文档

- [部署指南](./DEPLOYMENT.md) - 如何部署到 Vercel 和 GitHub
- [边界检测原理](./边界检测原理详解.md) - 详细的检测算法说明
- [自动缩放功能](./自动缩放功能说明.md) - 自动缩放功能详解
- [模板边框叠加](./模板边框叠加功能说明.md) - 可视化功能说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

由 Claude Code 辅助开发

---

**Star ⭐ 这个项目如果它对你有帮助！**

## 🔗 相关链接

- [在线演示](https://your-deployment-url.vercel.app)
- [问题反馈](https://github.com/YOUR_USERNAME/image-boundary-checker/issues)
- [部署文档](./DEPLOYMENT.md)
