# 安装指南

## 🚀 安装方法

### 方法一：通过 GitHub Releases（推荐）

1. 访问 [Releases](https://github.com/yizhww/AartFlow_blender/releases) 页面
2. 下载最新版本的 `AartFlow-版本号.zip` 文件
3. 打开 Blender，前往 **编辑** > **偏好设置** > **插件**
4. 点击 **安装...** 按钮，选择下载的 ZIP 文件
5. 在插件列表中搜索 "AartFlow" 并启用

### 方法二：手动安装

1. 克隆或下载此仓库到本地
2. 将 `AartFlow/` 目录复制到 Blender 插件目录：
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender Foundation/Blender/4.2/scripts/addons/`
   - **Linux**: `~/.config/blender/4.2/scripts/addons/`
3. 重启 Blender 或重新加载插件

## 📋 系统要求

- **Blender**: 4.2.0 或更高版本
- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10+, macOS 10.15+, Linux

## ✅ 验证安装

安装完成后，在 Blender 中：

1. 打开 3D 视图的侧边栏（按 N 键）
2. 查找 "AartFlow" 标签页
3. 如果看到 AartFlow 面板，说明安装成功

## 🔧 故障排除

### 常见问题

**Q: 插件安装后没有显示面板？**
A: 确保插件已启用，并检查 Blender 版本是否兼容。

**Q: 模块加载失败？**
A: 检查 Python 版本和脚本文件权限。

**Q: 热重载不工作？**
A: 确保在文本编辑器中运行脚本，而不是直接执行。

### 获取帮助

如果遇到问题，请：
1. 查看 [问题反馈](support.md)
2. 在 GitHub Issues 中搜索相关问题
3. 创建新的 Issue 描述您的问题

---

[← 返回文档中心](README.md) | [快速开始 →](quick-start.md)
