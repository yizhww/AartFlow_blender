# AartFlow Blender Add-on

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Blender](https://img.shields.io/badge/Blender-4.2+-orange.svg)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)

AartFlow 是一个高度模块化的 Blender 插件系统，专为 Blender 4.2+ 设计。它通过智能集成器动态发现并整合多个独立脚本模块，为 Blender 用户提供统一、可扩展的工作流解决方案。

## ✨ 主要特性

- 🔧 **模块化架构** - 每个功能模块独立开发，互不干扰
- 🔄 **动态加载** - 自动发现并集成 `scripts/` 目录下的脚本模块
- 🎯 **统一界面** - 所有模块面板整合到 AartFlow 主面板下
- ⚡ **热重载** - 支持开发时实时重载，无需重启 Blender
- 🎨 **代理面板** - 保持原脚本独立性，通过代理机制统一管理
- 📦 **易于扩展** - 添加新功能只需在 `scripts/` 目录放置脚本文件

## 📁 项目结构

```
AartFlow_blender/
├── AartFlow/                          # 插件主目录
│   ├── __init__.py                   # 插件入口点（包含 bl_info）
│   ├── AARTFLOW_integration.py       # 核心集成器
│   ├── manifest.json                 # 插件清单文件
│   ├── README.md                     # 插件详细说明
│   └── scripts/                      # 业务脚本模块目录
│       ├── artrender_front.py        # 渲染前端模块
│       ├── artrender_back.py         # 渲染后端模块
│       ├── objectmeasure.py          # 对象测量工具
│       ├── dataplotting.py           # 数据可视化
│       ├── standardview.py           # 标准视图管理
│       ├── skylightsmanage.py        # 天窗管理
│       ├── skp_drag.py               # SKP 拖拽功能
│       └── open_cmd.py               # 命令行工具
├── LICENSE                           # GPL-3.0 许可证
├── README.md                         # 项目说明文档
└── .gitignore                        # Git 忽略规则
```

## 🚀 快速开始

### 系统要求

- **Blender**: 4.2 或更高版本
- **Python**: 3.10 或更高版本
- **操作系统**: Windows, macOS, Linux

### 安装方法

#### 方法一：ZIP 安装（推荐）

1. 下载最新的 [Release](https://github.com/yizhww/AartFlow_blender/releases)
2. 打开 Blender，进入 `编辑 > 偏好设置 > 插件`
3. 点击 `安装...` 按钮
4. 选择下载的 ZIP 文件
5. 在插件列表中搜索 "AartFlow" 并启用

#### 方法二：手动安装

1. 克隆或下载此仓库
2. 将 `AartFlow/` 目录复制到 Blender 的插件目录：
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender Foundation/Blender/4.2/scripts/addons/`
   - **Linux**: `~/.config/blender/4.2/scripts/addons/`
3. 重启 Blender 或重新加载插件

### 使用方法

1. 安装并启用插件后，在 3D 视图的侧边栏（N 面板）中找到 "AartFlow" 标签
2. 点击 "添加模块..." 按钮选择要集成的脚本文件
3. 或者将脚本文件放入 `AartFlow/scripts/` 目录，插件会自动发现
4. 使用 F5 键快速呼出饼菜单访问常用功能

## 🛠️ 开发指南

### 开发环境设置

1. 克隆仓库到本地
2. 在 Blender 文本编辑器中打开 `AartFlow/__init__.py`
3. 点击 "运行脚本" 进行热重载开发

### 添加新模块

1. 在 `AartFlow/scripts/` 目录下创建新的 Python 文件
2. 确保文件包含 `bpy.types.Panel` 子类定义
3. 插件会自动发现并集成新模块

### 模块开发规范

```python
import bpy

class YOUR_PANEL_NAME(bpy.types.Panel):
    bl_label = "面板名称"
    bl_idname = "VIEW3D_PT_your_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YourCategory"  # 原始分类，集成后会被代理
    
    def draw(self, context):
        layout = self.layout
        # 你的面板内容
        pass

def register():
    bpy.utils.register_class(YOUR_PANEL_NAME)

def unregister():
    bpy.utils.unregister_class(YOUR_PANEL_NAME)

if __name__ == "__main__":
    register()
```

## 📦 打包发布

### 自动打包

在项目根目录执行以下 PowerShell 命令：

```powershell
# 创建 dist 目录
New-Item -ItemType Directory -Force dist | Out-Null

# 打包插件
Compress-Archive -Path "AartFlow\*" -DestinationPath "dist\AartFlow-1.0.0.zip" -Force

# 验证打包结果
Get-ChildItem dist
```

### 手动打包

1. 选择 `AartFlow/` 目录下的所有文件
2. 创建 ZIP 压缩包
3. 重命名为 `AartFlow-版本号.zip`

## 🔧 配置选项

### 模块路径管理

- **查看配置**: 在 AartFlow 面板中点击 "查看配置"
- **重置配置**: 点击 "重置默认" 清空所有模块
- **添加模块**: 使用 "添加模块..." 按钮选择脚本文件
- **刷新模块**: 点击模块旁的刷新按钮重新加载

### 快捷键

- **F5**: 呼出 AartFlow 饼菜单
- **N 面板**: 访问 AartFlow 主面板

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 此仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 使用 Python PEP 8 代码风格
- 添加适当的注释和文档字符串
- 确保新功能不会破坏现有模块
- 测试新功能在 Blender 4.2+ 中的兼容性

## 📄 许可证

本项目采用 [GPL-3.0](LICENSE) 许可证。这意味着：

- ✅ 可以自由使用、修改和分发
- ✅ 可以用于商业项目
- ❌ 衍生作品必须使用相同的 GPL-3.0 许可证
- ❌ 不能移除许可证声明

## 🐛 问题报告

如果您遇到问题或有功能建议，请：

1. 查看 [Issues](https://github.com/yizhww/AartFlow_blender/issues) 是否已有相关问题
2. 创建新的 Issue，详细描述问题
3. 提供 Blender 版本、操作系统和错误日志

## 📞 联系方式

- **GitHub**: [yizhww/AartFlow_blender](https://github.com/yizhww/AartFlow_blender)
- **Issues**: [问题反馈](https://github.com/yizhww/AartFlow_blender/issues)

## 🙏 致谢

感谢所有为 Blender 生态系统做出贡献的开发者和艺术家们！

---

**注意**: 此插件仍在积极开发中，API 可能会发生变化。建议在生产环境中使用前进行充分测试。