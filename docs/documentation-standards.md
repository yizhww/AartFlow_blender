# AartFlow 文档规范

![Documentation Standards](https://img.shields.io/badge/Documentation-Standards-blue?style=flat-square&logo=markdown)
![Version-1.0.0](https://img.shields.io/badge/Version-1.0.0-green?style=flat-square)
![Status-Active](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

<p align="center">
<strong>统一、清晰、易维护的文档编写标准</strong>
</p>

## 📋 目录

- [文档结构规范](#文档结构规范)
- [Markdown 格式规范](#markdown-格式规范)
- [内容编写规范](#内容编写规范)
- [视觉设计规范](#视觉设计规范)
- [文档维护规范](#文档维护规范)
- [模板和示例](#模板和示例)

---

## 文档结构规范

### 1. 文档层级结构

```
docs/
├── README.md                    # 文档中心首页
├── installation.md              # 安装指南
├── quick-start.md               # 快速开始
├── features.md                  # 功能特性
├── tutorials.md                 # 教程指南
├── api-reference.md             # API 参考
├── development.md               # 开发指南
├── module-development.md        # 模块开发
├── development-standards.md     # 开发标准
├── documentation-standards.md   # 文档规范（本文件）
├── contributing-and-support.md  # 贡献与支持
├── license.md                   # 许可证
└── versioning.md                # 版本管理
```

### 2. 文档头部结构

每个文档必须包含以下标准头部：

```markdown
# 文档标题

![相关徽章](https://img.shields.io/badge/类型-值-颜色?style=flat-square&logo=图标)

<p align="center">
<strong>文档副标题或简短描述</strong>
</p>

## 📋 目录

- [章节1](#章节1)
- [章节2](#章节2)
- [子章节2.1](#子章节21)

---
```

### 3. 文档尾部结构

```markdown
---

## 相关链接

- [返回文档中心](./README.md)
- [上一章节](./previous-doc.md) | [下一章节](./next-doc.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
```

---

## Markdown 格式规范

### 1. 标题层级

```markdown
# 一级标题（文档标题）
## 二级标题（主要章节）
### 三级标题（子章节）
#### 四级标题（详细说明）
##### 五级标题（特殊情况）
```

### 2. 代码块规范

#### 语言标识
```markdown
```python
# Python 代码
def example_function():
    pass
```

```bash
# Shell 命令
git commit -m "feat: add new feature"
```

```powershell
# PowerShell 命令
Get-Item .\dist\*.zip
```
```

#### 行内代码
```markdown
使用 `bpy.types.Operator` 类来创建操作器
```

### 3. 列表规范

#### 有序列表
```markdown
1. 第一项
2. 第二项
   1. 子项 2.1
   2. 子项 2.2
3. 第三项
```

#### 无序列表
```markdown
- 主要功能
  - 子功能 1
  - 子功能 2
- 次要功能
- 其他功能
```

#### 任务列表
```markdown
- [x] 已完成的任务
- [ ] 待完成的任务
- [ ] 另一个待完成的任务
```

### 4. 表格规范

```markdown
| 列标题1 | 列标题2 | 列标题3 |
|---------|---------|---------|
| 数据1   | 数据2   | 数据3   |
| 数据4   | 数据5   | 数据6   |
```

### 5. 链接和引用

```markdown
# 内部链接
[链接文本](./target-file.md)
[链接文本](./target-file.md#锚点)

# 外部链接
[链接文本](https://example.com)

# 图片
![图片描述](./path/to/image.png)

# 引用
> 这是一个引用块
> 可以跨越多行
```

---

## 内容编写规范

### 1. 语言风格

- **语言**: 中文为主，技术术语可保留英文
- **语调**: 专业、友好、易懂
- **人称**: 使用第二人称"你"或"您"
- **时态**: 使用现在时，描述当前状态

### 2. 技术文档要求

#### 代码示例
```markdown
# 好的示例
def calculate_dimensions(obj):
    """计算对象尺寸"""
    return obj.dimensions

# 避免的示例
def calc(obj):  # 函数名不够描述性
    return obj.dimensions  # 缺少文档字符串
```

#### 错误处理说明
```markdown
**常见错误**:
- `ModuleNotFoundError`: 缺少依赖模块
- `AttributeError`: 对象属性不存在

**解决方案**:
1. 检查模块是否正确安装
2. 验证对象类型和属性
```

### 3. 用户指南要求

#### 步骤说明
```markdown
### 安装步骤

1. **下载插件**
   - 访问 [GitHub 发布页面](https://github.com/user/repo/releases)
   - 下载最新版本的 `.zip` 文件

2. **安装到 Blender**
   - 打开 Blender
   - 进入 `编辑 > 偏好设置 > 扩展`
   - 点击 `安装...` 选择下载的文件

3. **启用插件**
   - 在扩展列表中找到 AartFlow
   - 勾选启用复选框
```

### 4. 开发文档要求

#### API 文档
```markdown
## AF_OT_module_action

**类名**: `AF_OT_module_action`  
**继承**: `bpy.types.Operator`  
**描述**: 执行模块相关操作

### 属性

| 属性名 | 类型 | 描述 |
|--------|------|------|
| `module_name` | `StringProperty` | 模块名称 |
| `action` | `StringProperty` | 执行的操作类型 |

### 方法

#### `execute(context)`
执行操作的主要方法。

**参数**:
- `context` (bpy.types.Context): Blender 上下文对象

**返回值**:
- `{'FINISHED'}`: 操作成功完成
- `{'CANCELLED'}`: 操作被取消

**示例**:
```python
bpy.ops.af.module_action(module_name="test", action="refresh")
```
```

---

## 视觉设计规范

### 1. 徽章使用

#### 状态徽章
```markdown
![Version](https://img.shields.io/badge/Version-1.0.0-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-GPL--3.0-green?style=flat-square)
```

#### 技术徽章
```markdown
![Blender](https://img.shields.io/badge/Blender-4.2+-orange?style=flat-square&logo=blender)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
```

### 2. 分隔线使用

```markdown
---  # 主要章节分隔
***  # 子章节分隔（较少使用）
```

### 3. 强调和突出

```markdown
**粗体文本** - 重要概念
*斜体文本* - 强调或引用
`代码文本` - 技术术语或代码
> 引用文本 - 重要说明或引用
```

### 4. 图标使用

```markdown
## 📋 目录
## 🚀 快速开始
## ⚙️ 配置
## 🐛 故障排除
## 📚 参考
## ❓ 常见问题
```

---

## 文档维护规范

### 1. 更新频率

- **功能文档**: 随功能更新同步更新
- **API 文档**: 随代码变更同步更新
- **教程文档**: 每季度检查一次
- **规范文档**: 半年检查一次

### 2. 版本控制

```markdown
## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-01-16 | 初始版本，建立文档规范 |
| 1.0.1 | 2025-01-16 | 补充视觉设计规范 |
```

### 3. 质量检查清单

- [ ] 文档结构符合规范
- [ ] 所有链接有效
- [ ] 代码示例可运行
- [ ] 图片显示正常
- [ ] 拼写和语法正确
- [ ] 格式统一一致

### 4. 协作规范

#### 文档修改流程
1. 创建功能分支
2. 修改文档内容
3. 自我检查质量
4. 提交 Pull Request
5. 代码审查
6. 合并到主分支

#### 审查要点
- 内容准确性
- 格式规范性
- 语言流畅性
- 结构逻辑性

---

## 模板和示例

### 1. 功能文档模板

```markdown
# 功能名称

![功能徽章](https://img.shields.io/badge/功能-状态-颜色?style=flat-square)

<p align="center">
<strong>功能简短描述</strong>
</p>

## 📋 目录

- [概述](#概述)
- [使用方法](#使用方法)
- [配置选项](#配置选项)
- [示例](#示例)
- [故障排除](#故障排除)

---

## 概述

功能详细描述...

## 使用方法

### 基本使用

1. 步骤一
2. 步骤二
3. 步骤三

### 高级使用

...

## 配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| option1 | string | "default" | 选项描述 |

## 示例

```python
# 代码示例
```

## 故障排除

**常见问题**:
- 问题1: 解决方案1
- 问题2: 解决方案2

---

## 相关链接

- [返回文档中心](./README.md)
- [API 参考](./api-reference.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
```

### 2. 教程文档模板

```markdown
# 教程标题

![教程徽章](https://img.shields.io/badge/教程-级别-颜色?style=flat-square)

<p align="center">
<strong>教程简短描述</strong>
</p>

## 📋 目录

- [前置条件](#前置条件)
- [学习目标](#学习目标)
- [教程步骤](#教程步骤)
- [总结](#总结)
- [下一步](#下一步)

---

## 前置条件

- 条件1
- 条件2
- 条件3

## 学习目标

完成本教程后，你将能够：
- 目标1
- 目标2
- 目标3

## 教程步骤

### 步骤 1: 标题

详细说明...

**操作**:
1. 操作1
2. 操作2

**结果**: 预期结果

### 步骤 2: 标题

...

## 总结

本教程学习了...

## 下一步

- [相关教程1](./tutorial1.md)
- [相关教程2](./tutorial2.md)
- [API 参考](./api-reference.md)

---

## 相关链接

- [返回文档中心](./README.md)
- [所有教程](./tutorials.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
```

---

## 工具推荐

### 1. 编辑工具
- **Visual Studio Code**: 推荐，支持 Markdown 预览
- **Typora**: 专业 Markdown 编辑器
- **Mark Text**: 开源 Markdown 编辑器

### 2. 检查工具
- **markdownlint**: Markdown 语法检查
- **Vale**: 写作风格检查
- **LinkChecker**: 链接有效性检查

### 3. 生成工具
- **MkDocs**: 静态站点生成器
- **GitBook**: 在线文档平台
- **Sphinx**: Python 文档生成工具

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-01-16 | 初始版本，建立文档规范体系 |

---

## 相关链接

- [返回文档中心](./README.md)
- [开发标准](./development-standards.md)
- [贡献与支持](./contributing-and-support.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
