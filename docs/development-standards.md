# AartFlow 开发规范

## 📋 目录
- [代码规范](#代码规范)
- [文件命名规范](#文件命名规范)
- [Git工作流规范](#git工作流规范)
- [版本管理规范](#版本管理规范)
- [打包发布规范](#打包发布规范)
- [文档规范](#文档规范)
- [测试规范](#测试规范)

---

## 代码规范

### 1. Python代码风格
- 遵循PEP 8编码规范
- 使用4个空格缩进，不使用Tab
- 行长度限制为88字符（Black格式化器标准）
- 使用有意义的变量名和函数名

### 2. Blender API使用规范
```python
# 正确的导入顺序
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy.utils import register_class, unregister_class

# 类命名规范
class AF_OT_module_action(bpy.types.Operator):
    bl_idname = "af.module_action"  # 使用 af. 前缀
    bl_label = "操作名称"
    bl_options = {'REGISTER', 'UNDO'}
```

### 3. 错误处理规范
```python
def execute(self, context):
    """执行操作"""
    try:
        # 主要逻辑
        result = self._perform_action(context)
        
        if result:
            self.report({'INFO'}, "操作成功完成")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "操作未完成")
            return {'CANCELLED'}
            
    except Exception as e:
        self.report({'ERROR'}, f"操作失败: {e}")
        return {'CANCELLED'}
```

---

## 文件命名规范

### 1. 脚本模块文件
- **命名方式**: 帕斯卡命名法（PascalCase）
- **格式**: `模块功能名称.py`
- **示例**: 
  - `artRenderBack.py` - 艺术渲染后端模块
  - `objectMeasure.py` - 对象测量模块
  - `standardView.py` - 标准视图模块

### 2. 类命名规范
```python
# Operator 类
class AF_OT_module_action(bpy.types.Operator):
    bl_idname = "af.module_action"

# Panel 类
class AF_PT_module_panel(bpy.types.Panel):
    bl_idname = "AF_PT_module_panel"
    bl_category = "AartFlow"  # 统一使用 AartFlow 分类

# PropertyGroup 类
class ModuleSettings(bpy.types.PropertyGroup):
    pass
```

### 3. 函数命名规范
```python
# 公共函数：使用动词开头，描述性命名
def calculate_mesh_dimensions(obj):
    """计算网格尺寸"""
    pass

# 私有函数：使用下划线前缀
def _get_object_bounds(obj):
    """获取对象边界"""
    pass
```

---

## Git工作流规范

### 1. 分支管理
- **main**: 主分支，用于发布稳定版本
- **develop**: 开发分支，用于集成功能
- **feature/***: 功能分支，用于开发新功能
- **hotfix/***: 热修复分支，用于紧急修复

### 2. 提交信息规范
```bash
# 格式：类型(范围): 简短描述
# 类型：
# - feat: 新功能
# - fix: 修复bug
# - docs: 文档更新
# - style: 代码格式调整
# - refactor: 重构
# - test: 测试相关
# - chore: 构建过程或辅助工具的变动

# 示例：
git commit -m "feat(scripts): 添加新的测量工具模块"
git commit -m "fix(render): 修复渲染引擎内存泄漏问题"
git commit -m "docs(api): 更新API文档"
```

### 3. 提交前检查
- [ ] 代码通过语法检查
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 遵循命名规范

---

## 版本管理规范

### 1. 语义化版本控制
使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

### 2. 版本更新流程
```bash
# 1. 更新版本号
# 在 manifest.json 中更新版本号

# 2. 更新 index.json
# 更新版本号、文件大小、哈希值

# 3. 创建Git标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 4. 推送到远程仓库
git push origin main --tags
```

### 3. 变更日志
在每次发布时更新CHANGELOG.md：
```markdown
## [1.0.1] - 2025-09-16

### Changed
- 重构所有模块文件名为帕斯卡命名法
- 更新模块开发规范文档

### Fixed
- 修复Blender扩展库索引文件
```

---

## 打包发布规范

### 1. 打包前检查清单
- [ ] 所有模块文件已重命名为帕斯卡命名法
- [ ] 代码通过语法检查
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] 所有引用已更新

### 2. 打包脚本使用
```powershell
# 使用打包脚本
.\package.ps1 -Version "1.0.1"

# 脚本会自动：
# - 验证必要文件
# - 创建ZIP文件
# - 计算文件大小
# - 清理临时文件
```

### 3. 发布流程
```bash
# 1. 重新打包
.\package.ps1 -Version "1.0.1"

# 2. 更新index.json
# 更新版本号、文件大小、哈希值

# 3. 提交更改
git add .
git commit -m "release: 发布版本 1.0.1"

# 4. 创建发布标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 5. 推送到远程仓库
git push origin main --tags
```

---

## 文档规范

### 1. 文档结构
```
docs/
├── README.md                 # 项目总览
├── installation.md          # 安装指南
├── quick-start.md           # 快速开始
├── features.md              # 功能特性
├── api-reference.md         # API参考
├── development.md           # 开发指南
├── module-development.md    # 模块开发规范
├── development-standards.md # 开发标准（本文件）
└── contributing.md          # 贡献指南
```

### 2. 文档编写规范
- 使用Markdown格式
- 包含目录结构
- 使用emoji增强可读性
- 代码示例使用语法高亮
- 保持文档与代码同步更新

### 3. 注释规范
```python
def calculate_dimensions(obj, precision=2):
    """
    计算对象的尺寸信息
    
    Args:
        obj (bpy.types.Object): 要计算尺寸的对象
        precision (int): 小数位数精度，默认为2
        
    Returns:
        dict: 包含长宽高信息的字典
        
    Raises:
        ValueError: 当对象类型不支持时抛出
    """
    pass
```

---

## 测试规范

### 1. 单元测试
- 为每个模块编写单元测试
- 测试覆盖率应达到80%以上
- 使用pytest框架

### 2. 集成测试
- 测试模块间的集成
- 测试与Blender API的交互
- 验证用户界面功能

### 3. 测试文件命名
```
tests/
├── test_artRender.py
├── test_objectMeasure.py
├── test_standardView.py
└── test_integration.py
```

---

## 质量保证

### 1. 代码审查
- 所有代码变更必须经过审查
- 审查重点：功能正确性、代码质量、安全性
- 使用Pull Request流程

### 2. 持续集成
- 自动化测试
- 代码质量检查
- 自动打包部署

### 3. 性能监控
- 监控内存使用
- 检查渲染性能
- 优化用户体验

---

## 工具和资源

### 1. 开发工具
- **IDE**: Visual Studio Code / PyCharm
- **版本控制**: Git
- **代码格式化**: Black
- **代码检查**: Flake8, Pylint

### 2. 参考资源
- [Blender Python API文档](https://docs.blender.org/api/current/)
- [PEP 8 Python编码规范](https://www.python.org/dev/peps/pep-0008/)
- [语义化版本控制](https://semver.org/)

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-09-15 | 初始版本，建立基础开发规范 |
| 1.0.1 | 2025-09-16 | 补充完整开发标准，更新文件命名规范 |

---

[← 返回文档中心](README.md) | [模块开发规范 →](module-development.md)
