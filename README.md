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

## ✨ 核心特性

- **🔧 动态模块发现** - 自动扫描并集成独立脚本模块
- **🎛️ 代理面板系统** - 统一管理分散的功能面板
- **⚡ 热重载开发** - 支持实时调试和代码更新
- **📦 模块化架构** - 每个功能模块独立开发维护
- **🛠️ 开发工具链** - 完整的开发和打包工具

## 🚀 快速开始

1. **安装插件** - 下载并安装 AartFlow 插件
2. **启用模块** - 在 Blender 中启用插件
3. **添加脚本** - 将脚本放入 `scripts/` 目录或手动添加
4. **开始使用** - 在侧边栏找到 AartFlow 面板

## 📚 详细文档

### 🚀 快速开始
- [📥 安装指南](docs/installation.md) - 详细的安装步骤和配置
- [⚡ 快速开始](docs/quick-start.md) - 5分钟快速上手教程

### 📖 用户指南
- [✨ 功能特性](docs/features.md) - 核心功能详细说明
- [📚 使用教程](docs/tutorials.md) - 完整的使用教程和示例
- [🎯 适用场景](docs/use-cases.md) - 项目适用场景和最佳实践

### 🔧 开发指南
- [🛠️ 开发环境](docs/development.md) - 开发环境配置和工具链
- [📝 模块开发](docs/module-development.md) - 如何开发新模块
- [📋 API 参考](docs/api-reference.md) - 详细的 API 文档

### 📦 部署与发布
- [📦 打包发布](docs/packaging.md) - 插件打包和发布流程
- [🏷️ 版本管理](docs/versioning.md) - 版本控制和更新策略

### 🤝 贡献与支持
- [🤝 贡献指南](docs/contributing.md) - 如何参与项目贡献
- [🆘 问题反馈](docs/support.md) - 问题报告和获取帮助
- [📄 许可证](docs/license.md) - 项目许可证信息

## 📁 项目结构

```
AartFlow_blender/
├── README.md                    # 项目说明文档
├── LICENSE                      # GPL-3.0 许可证
├── .gitignore                   # Git 忽略规则
├── texture/                     # 资源文件
│   └── 1.png                   # AartFlow Logo
├── docs/                       # 📚 文档中心
│   ├── README.md               # 文档索引
│   ├── installation.md         # 安装指南
│   ├── features.md             # 功能特性
│   ├── quick-start.md          # 快速开始
│   ├── tutorials.md            # 使用教程
│   ├── use-cases.md            # 适用场景
│   ├── development.md          # 开发指南
│   ├── module-development.md   # 模块开发
│   ├── api-reference.md        # API 参考
│   ├── packaging.md            # 打包发布
│   ├── versioning.md           # 版本管理
│   ├── contributing.md         # 贡献指南
│   ├── support.md              # 问题反馈
│   └── license.md              # 许可证信息
└── AartFlow/                   # 插件主目录
    ├── __init__.py             # 插件入口点
    ├── AARTFLOW_integration.py # 核心集成器
    ├── manifest.json           # 插件清单文件
    ├── README.md               # 插件详细说明
    └── scripts/                # 业务脚本模块目录
        ├── artrender_front.py  # 渲染前端模块
        ├── artrender_back.py   # 渲染后端模块
        ├── objectmeasure.py    # 对象测量工具
        ├── dataplotting.py     # 数据可视化
        ├── standardview.py     # 标准视图管理
        ├── skylightsmanage.py  # 天窗管理
        ├── skp_drag.py         # SKP 拖拽功能
        └── open_cmd.py         # 命令行工具
```

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
- **文档中心**: [docs/](docs/) - 完整的项目文档

## 👥 维护者

- **yizhww** - *项目创建者* - [GitHub](https://github.com/yizhww)

## 🙏 致谢

感谢所有为 Blender 生态系统做出贡献的开发者和艺术家们！

---

<p align="center">
Made with ❤️ for the Blender Community
</p>