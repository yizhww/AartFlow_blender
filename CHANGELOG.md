# 更新日志

本文档记录了AartFlow Blender插件的主要版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- [ ] 添加更多渲染选项
- [ ] 优化性能
- [ ] 增加更多测量工具

## [1.0.1] - 2025-09-16

### 变更
- 重构所有脚本模块文件名为帕斯卡命名法（PascalCase）
  - `artrender_back.py` → `artRenderBack.py`
  - `artrender_front.py` → `artRenderFront.py`
  - `dataplotting.py` → `dataPlotting.py`
  - `objectmeasure.py` → `objectMeasure.py`
  - `open_cmd.py` → `openCmd.py`
  - `skp_drag.py` → `skpDrag.py`
  - `skylightsmanage.py` → `skylightsManage.py`
  - `standardview.py` → `standardView.py`

### 新增
- 添加自动化打包脚本 (`package.ps1`)
- 补充完整的开发规范文档 (`docs/development-standards.md`)
- 更新模块开发规范，添加文件命名规范

### 修复
- 修复Blender扩展库索引文件 (`index.json`) 版本信息
- 更新所有文档和引用以匹配新的文件名
- 修复内部函数和变量命名一致性

### 文档
- 更新所有文档中的文件名引用
- 补充开发标准和规范文档
- 更新项目结构说明

## [1.0.0] - 2025-09-15

### 新增
- 初始发布版本
- 模块化Blender插件集成系统
- 艺术渲染功能模块
- 对象测量和尺寸标注工具
- 数据可视化和图表生成
- 标准视图管理和相机控制
- 天窗管理和光照控制
- SKP文件拖拽导入功能
- 命令行工具和外部程序调用

### 技术特性
- 松耦合的模块化架构
- 统一的用户界面集成
- 自动化的插件管理
- 完整的错误处理机制
- 详细的文档和API参考

---

## 版本说明

### 版本号格式
使用语义化版本控制：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增  
- **PATCH**: 向下兼容的问题修正

### 变更类型
- **新增**: 新功能和特性
- **变更**: 对现有功能的更改
- **弃用**: 即将移除的功能
- **移除**: 在此版本中移除的功能
- **修复**: 任何bug修复
- **安全**: 安全问题修复

### 更新频率
- **主版本**: 重大架构变更时发布
- **次版本**: 每月或重要功能完成时发布
- **补丁版本**: 根据bug修复需要随时发布

---

[← 返回文档中心](README.md) | [开发规范 →](docs/development-standards.md)
