# AartFlow Blender Add-on

![AartFlow Logo](texture/1.png)

<p align="center">
<strong>基于模块化架构的 Blender 插件集成系统</strong>
</p>

<p align="center">
<img src="https://img.shields.io/badge/Blender-4.2+-orange?style=flat-square&logo=blender" alt="Blender Version">
<img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python Version">
<img src="https://img.shields.io/badge/License-GPL--3.0-green?style=flat-square" alt="License">
</p>

## 📖 项目概述

AartFlow 是一个高度模块化的 Blender 插件系统，专为 Blender 4.2+ 设计。它通过智能集成器动态发现并整合多个独立脚本模块，为 Blender 用户提供统一、可扩展的工作流解决方案。项目采用代理面板机制，保持各模块的独立性，同时提供统一的用户界面。

## ✨ 功能特性

### 🔧 核心集成功能

- **动态模块发现**
  - 自动扫描 `scripts/` 目录下的 Python 脚本
  - 智能识别包含 `bpy.types.Panel` 的模块
  - 支持热重载，开发时无需重启 Blender

- **代理面板系统**
  - 将分散的模块面板统一整合到 AartFlow 主面板
  - 保持原脚本的完整功能和独立性
  - 避免面板冲突和重复注册问题

- **模块管理工具**
  - 可视化模块添加、移除和刷新
  - 模块路径配置和状态查看
  - 一键重置和批量操作

### 🛠️ 开发工具链

- **热重载开发** - 支持实时调试和代码更新
- **模块化架构** - 每个功能模块独立开发维护
- **统一接口** - 标准化的模块开发规范
- **自动打包** - PowerShell 脚本自动化打包发布

## 🚀 安装与使用

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

### 快速开始

1. 安装并启用插件后，在 3D 视图的侧边栏（N 面板）中找到 "AartFlow" 标签
2. 点击 "添加模块..." 按钮选择要集成的脚本文件
3. 或者将脚本文件放入 `AartFlow/scripts/` 目录，插件会自动发现
4. 使用 **F5** 键快速呼出饼菜单访问常用功能

## 📁 项目结构

```
AartFlow_blender/
├── README.md                           # 项目说明文档
├── LICENSE                             # GPL-3.0 许可证
├── .gitignore                          # Git 忽略规则
├── 1.png                               # AartFlow Logo
└── AartFlow/                           # 插件主目录
    ├── __init__.py                     # 插件入口点（包含 bl_info）
    ├── AARTFLOW_integration.py         # 核心集成器
    ├── manifest.json                   # 插件清单文件
    ├── README.md                       # 插件详细说明
    └── scripts/                        # 业务脚本模块目录
        ├── artrender_front.py          # 渲染前端模块
        ├── artrender_back.py           # 渲染后端模块
        ├── objectmeasure.py            # 对象测量工具
        ├── dataplotting.py             # 数据可视化
        ├── standardview.py             # 标准视图管理
        ├── skylightsmanage.py          # 天窗管理
        ├── skp_drag.py                 # SKP 拖拽功能
        └── open_cmd.py                 # 命令行工具
```

## 🔧 开发指南

### 环境要求

- **Blender**: 4.2.0 或更高版本
- **Python**: 3.10 或更高版本
- **开发工具**: 任意文本编辑器或 IDE

### 本地开发

1. 克隆仓库：
   ```bash
   git clone https://github.com/yizhww/AartFlow_blender.git
   cd AartFlow_blender
   ```

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

## 🎯 适用场景

- **插件开发**：需要整合多个独立功能的 Blender 插件
- **工作流优化**：统一管理分散的工具和脚本
- **团队协作**：模块化开发，便于多人协作维护
- **功能扩展**：快速添加新功能而不影响现有代码
- **教学培训**：学习 Blender 插件开发的最佳实践

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

## 🛡️ 技术栈

### DCC 软件
- ![Blender](https://img.shields.io/badge/Blender-F5792A?style=flat-square&logo=blender&logoColor=white)
- ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)

### 编程语言
- ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

### 开发工具
- ![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?style=flat-square&logo=powershell&logoColor=white)
- ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)

## 📚 资源链接

- **GitHub 仓库**: [AartFlow_blender](https://github.com/yizhww/AartFlow_blender)
- **问题反馈**: [Issues](https://github.com/yizhww/AartFlow_blender/issues)
- **Releases**: [下载页面](https://github.com/yizhww/AartFlow_blender/releases)

## 📄 许可证

本项目采用 [GPL-3.0](LICENSE) 许可证。这意味着：

- ✅ 可以自由使用、修改和分发
- ✅ 可以用于商业项目
- ❌ 衍生作品必须使用相同的 GPL-3.0 许可证
- ❌ 不能移除许可证声明

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 使用 Python PEP 8 代码风格
- 添加适当的注释和文档字符串
- 确保新功能不会破坏现有模块
- 测试新功能在 Blender 4.2+ 中的兼容性

## 👥 维护者

- **yizhww** - *项目创建者* - [GitHub](https://github.com/yizhww)

## 🙏 致谢

感谢所有为 Blender 生态系统做出贡献的开发者和艺术家们！

---

<p align="center">
Made with ❤️ for the Blender Community
</p>