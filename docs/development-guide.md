# AartFlow 开发指南

![Development Guide](https://img.shields.io/badge/Development-Guide-orange?style=flat-square&logo=code)
![Version-1.0.0](https://img.shields.io/badge/Version-1.0.0-green?style=flat-square)
![Status-Active](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

<p align="center">
<strong>从环境配置到模块开发的完整开发指南</strong>
</p>

## 📋 目录

- [🔧 环境配置](#-环境配置)
- [🚀 快速开发](#-快速开发)
- [📝 模块开发](#-模块开发)
- [🏗️ 项目结构](#️-项目结构)
- [📚 API 参考](#-api-参考)
- [🧪 测试指南](#-测试指南)
- [📦 打包发布](#-打包发布)
- [📋 开发规范](#-开发规范)
- [📝 文档规范](#-文档规范)

---

## 🔧 环境配置

### 环境要求

- **Blender**: 4.2.0 或更高版本
- **Python**: 3.10 或更高版本
- **开发工具**: 任意文本编辑器或 IDE（推荐 VS Code）

### 开发环境设置

#### 1. 克隆仓库
```bash
git clone https://github.com/yizhww/AartFlow_blender.git
cd AartFlow_blender
```

#### 2. 开发环境配置
1. 在 Blender 文本编辑器中打开 `AartFlow/__init__.py`
2. 点击 "运行脚本" 进行热重载开发
3. 修改代码后重新运行即可看到效果

#### 3. 调试技巧
- 使用 `print()` 语句输出调试信息
- 在控制台中查看错误和警告
- 使用 Blender 的内置调试工具
- 启用详细日志记录

---

## 🚀 快速开发

### 开发工作流

#### 1. 热重载开发
```python
# 在文本编辑器中运行脚本
if __name__ == "__main__":
    # 先卸载之前的版本
    try:
        unregister()
    except:
        pass
    
    # 重新注册
    register()
    print("模块已重新加载")
```

#### 2. 模块测试
1. 创建测试场景
2. 加载测试模块
3. 验证功能正常
4. 检查错误日志

#### 3. 调试工具
- **控制台输出**: 使用 `print()` 查看变量值
- **错误追踪**: 查看 Blender 控制台的错误信息
- **断点调试**: 在关键位置添加断点
- **性能监控**: 监控内存和 CPU 使用

---

## 📝 模块开发

### 模块开发规范

#### 1. 创建模块文件
在 `AartFlow/scripts/` 目录下创建新的 Python 文件

#### 2. 标准模块结构
```python
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, BoolProperty

class YOUR_OT_operator(bpy.types.Operator):
    """操作器类"""
    bl_idname = "your.operator"
    bl_label = "操作名称"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 操作逻辑
        return {'FINISHED'}

class YOUR_PT_panel(bpy.types.Panel):
    """面板类"""
    bl_label = "面板名称"
    bl_idname = "VIEW3D_PT_your_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YourCategory"  # 原始分类，集成后会被代理
    
    def draw(self, context):
        layout = self.layout
        # 面板内容
        layout.operator("your.operator")

class YOUR_PG_properties(bpy.types.PropertyGroup):
    """属性组类"""
    name: StringProperty(name="名称")
    value: FloatProperty(name="值")

def register():
    """注册函数"""
    bpy.utils.register_class(YOUR_OT_operator)
    bpy.utils.register_class(YOUR_PT_panel)
    bpy.utils.register_class(YOUR_PG_properties)
    
    # 注册属性到场景
    bpy.types.Scene.your_properties = bpy.props.PointerProperty(type=YOUR_PG_properties)

def unregister():
    """注销函数"""
    bpy.utils.unregister_class(YOUR_OT_operator)
    bpy.utils.unregister_class(YOUR_PT_panel)
    bpy.utils.unregister_class(YOUR_PG_properties)
    
    # 删除属性
    del bpy.types.Scene.your_properties

if __name__ == "__main__":
    register()
```

#### 3. 模块要求
- 必须包含 `bpy.types.Panel` 子类
- 必须实现 `register()` 和 `unregister()` 函数
- 建议添加适当的错误处理
- 遵循项目命名规范

### 模块开发最佳实践

#### 1. 命名规范
```python
# 操作器命名
class AF_OT_your_action(bpy.types.Operator):
    bl_idname = "af.your_action"

# 面板命名
class VIEW3D_PT_your_panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_your_panel"

# 属性组命名
class AF_PG_your_properties(bpy.types.PropertyGroup):
    pass
```

#### 2. 错误处理
```python
def execute(self, context):
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

#### 3. 用户界面设计
```python
def draw(self, context):
    layout = self.layout
    
    # 标题
    box = layout.box()
    box.label(text="模块标题", icon='INFO')
    
    # 操作按钮
    row = layout.row()
    row.operator("af.your_action", text="执行操作")
    
    # 属性设置
    col = layout.column()
    col.prop(context.scene.your_properties, "name")
    col.prop(context.scene.your_properties, "value")
```

---

## 🏗️ 项目结构

### 完整项目结构

```
AartFlow_blender/
├── README.md                           # 项目说明文档
├── LICENSE                             # GPL-3.0 许可证
├── .gitignore                          # Git 忽略规则
├── index.json                          # 扩展库索引文件
├── texture/                            # 资源文件
│   └── 1.png                          # AartFlow Logo
├── docs/                              # 文档中心
│   ├── README.md                      # 文档索引
│   ├── user-guide.md                  # 用户指南
│   ├── development-guide.md           # 开发指南（本文件）
│   ├── contributing-and-support.md    # 贡献与支持
│   └── license.md                     # 许可证信息
├── dist/                              # 发布包目录
│   └── AartFlow-1.0.1.zip            # 发布包
└── AartFlow/                          # 插件主目录
    ├── __init__.py                    # 插件入口点
    ├── AARTFLOW_integration.py        # 核心集成器
    ├── manifest.json                  # 插件清单文件
    ├── blender_manifest.toml          # Blender 扩展清单
    ├── README.md                      # 插件详细说明
    └── scripts/                       # 业务脚本模块目录
        ├── artRenderFront.py         # 渲染前端模块
        ├── artRenderBack.py          # 渲染后端模块
        ├── objectMeasure.py           # 对象测量工具
        ├── dataPlotting.py            # 数据可视化
        ├── standardView.py            # 标准视图管理
        ├── skylightsManage.py         # 天窗管理
        ├── skpDrag.py                # SKP 拖拽功能
        └── openCmd.py                # 命令行工具
```

### 核心文件说明

#### 插件入口文件
- **`__init__.py`**: 插件主入口，包含 `bl_info` 和注册函数
- **`AARTFLOW_integration.py`**: 核心集成器，负责模块发现和管理
- **`manifest.json`**: 插件元数据，包含版本、作者等信息
- **`blender_manifest.toml`**: Blender 扩展系统清单文件

#### 模块目录
- **`scripts/`**: 存放所有业务模块脚本
- 每个模块都是独立的 Python 文件
- 模块间通过集成器统一管理

---

## 📚 API 参考

### 核心集成器 API

#### AARTFLOW_integration.py

**主要功能类：**

```python
class AartFlowIntegration:
    """AartFlow 核心集成器"""
    
    def register_modules(self):
        """注册所有模块"""
        pass
    
    def unregister_modules(self):
        """注销所有模块"""
        pass
    
    def refresh_modules(self):
        """刷新模块列表"""
        pass
    
    def add_module(self, module_path):
        """添加新模块"""
        pass
    
    def remove_module(self, module_name):
        """移除模块"""
        pass
```

**主要面板类：**

```python
class VIEW3D_PT_aartflow_root(bpy.types.Panel):
    """AartFlow 主面板"""
    bl_label = "AartFlow"
    bl_idname = "VIEW3D_PT_aartflow_root"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"

class VIEW3D_PT_aartflow_modules(bpy.types.Panel):
    """集成模块容器面板"""
    bl_label = "集成模块"
    bl_idname = "VIEW3D_PT_aartflow_modules"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_parent_id = "VIEW3D_PT_aartflow_root"
```

### 模块开发 API

#### 标准模块结构

```python
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, BoolProperty

class ModulePanel(bpy.types.Panel):
    """标准模块面板基类"""
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        """绘制面板内容"""
        layout = self.layout
        # 面板内容实现

class ModuleOperator(bpy.types.Operator):
    """标准操作器基类"""
    
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行操作"""
        return {'FINISHED'}

def register():
    """注册模块"""
    bpy.utils.register_class(ModulePanel)
    bpy.utils.register_class(ModuleOperator)

def unregister():
    """注销模块"""
    bpy.utils.unregister_class(ModulePanel)
    bpy.utils.unregister_class(ModuleOperator)
```

### 工具函数

#### 常用工具函数

```python
def get_selected_objects():
    """获取选中的对象"""
    return bpy.context.selected_objects

def create_camera(name="Camera"):
    """创建相机"""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = name
    return camera

def get_object_bounds(obj):
    """获取对象边界"""
    return obj.bound_box

def calculate_mesh_dimensions(obj):
    """计算网格尺寸"""
    return obj.dimensions

def set_render_settings(engine="CYCLES"):
    """设置渲染引擎"""
    bpy.context.scene.render.engine = engine
```

---

## 🧪 测试指南

### 单元测试

```python
import unittest
import bpy

class TestYourModule(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 设置测试场景
        bpy.ops.mesh.primitive_cube_add()
        self.test_object = bpy.context.object
    
    def test_panel_creation(self):
        """测试面板创建"""
        # 验证面板是否正确注册
        self.assertIn('VIEW3D_PT_your_panel', bpy.types.__dict__)
    
    def test_operator_execution(self):
        """测试操作器执行"""
        # 测试操作器功能
        result = bpy.ops.your.operator()
        self.assertEqual(result, {'FINISHED'})
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试数据
        bpy.ops.object.delete()
```

### 集成测试

#### 1. 模块加载测试
```python
def test_module_loading():
    """测试模块加载"""
    # 加载模块
    import your_module
    your_module.register()
    
    # 验证模块是否正确加载
    assert 'VIEW3D_PT_your_panel' in bpy.types.__dict__
    
    # 清理
    your_module.unregister()
```

#### 2. 功能集成测试
```python
def test_module_integration():
    """测试模块集成"""
    # 在 Blender 中加载插件
    # 测试各个模块的功能
    # 验证模块间的交互
    pass
```

### 性能测试

```python
import time

def test_performance():
    """性能测试"""
    start_time = time.time()
    
    # 执行测试操作
    for i in range(1000):
        # 测试代码
        pass
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 验证性能要求
    assert execution_time < 1.0  # 应在1秒内完成
```

---

## 📦 打包发布

### 自动打包

```powershell
# 创建 dist 目录
New-Item -ItemType Directory -Force dist | Out-Null

# 打包插件
Compress-Archive -Path "AartFlow\*" -DestinationPath "dist\AartFlow-1.0.1.zip" -Force

# 验证打包结果
Get-ChildItem dist

# 计算文件哈希
$hash = (Get-FileHash "dist\AartFlow-1.0.1.zip" -Algorithm SHA256).Hash
Write-Host "SHA256: $hash"
```

### 版本管理

#### 1. 更新版本号
```python
# __init__.py
bl_info = {
    "version": (1, 0, 1),  # 更新版本号
    # 其他信息...
}
```

```json
// manifest.json
{
    "version": "1.0.1",  // 更新版本号
    // 其他信息...
}
```

#### 2. 创建发布标签
```bash
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin main --tags
```

#### 3. 更新索引文件
```json
// index.json
{
    "version": "1.0.1",
    "archive_size": 89169,
    "archive_hash": "sha256:fcdfe79eb26af6a0c6163ebf98ddf7538fa80affd67be366d077959f05cc527d"
}
```

### 发布流程

1. **开发完成** - 确保所有功能正常
2. **测试验证** - 运行完整测试套件
3. **版本更新** - 更新所有版本号
4. **打包发布** - 创建发布包
5. **索引更新** - 更新扩展库索引
6. **标签发布** - 创建 Git 标签
7. **文档更新** - 更新相关文档

---

## 📋 开发规范

### 代码规范

#### 1. Python代码风格
- 遵循PEP 8编码规范
- 使用4个空格缩进，不使用Tab
- 行长度限制为88字符（Black格式化器标准）
- 使用有意义的变量名和函数名

#### 2. Blender API使用规范
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

#### 3. 错误处理规范
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

### 文件命名规范

#### 1. 脚本模块文件
- **命名方式**: 帕斯卡命名法（PascalCase）
- **格式**: `模块功能名称.py`
- **示例**: 
  - `artRenderBack.py` - 艺术渲染后端模块
  - `objectMeasure.py` - 对象测量模块
  - `standardView.py` - 标准视图模块

#### 2. 类命名规范
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

#### 3. 函数命名规范
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

### Git工作流规范

#### 1. 分支管理
- **main**: 主分支，用于发布稳定版本
- **develop**: 开发分支，用于集成功能
- **feature/***: 功能分支，用于开发新功能
- **hotfix/***: 热修复分支，用于紧急修复

#### 2. 提交信息规范
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

#### 3. 提交前检查
- [ ] 代码通过语法检查
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 遵循命名规范

### 版本管理规范

#### 1. 语义化版本控制
使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

#### 2. 版本更新流程
```bash
# 1. 更新版本号
# 在 manifest.json 中更新版本号

# 打包 ZIP（必须先打包，再更新 index.json）
./package.ps1 -Version "1.0.1"

# 2. 更新 index.json
# 更新版本号、文件大小、哈希值

# 3. 创建Git标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 4. 推送到远程仓库
git push origin main --tags
```

#### 3. 版本一致性校验与常见错误

##### Package version mismatch（remote: "X", archive: "Y"）

- **错误现象**: 安装时报错 `Package version mismatch (remote: "X", archive: "Y")`。
- **根因**: 远端索引文件 `index.json` 中的 `data[0].version` 与压缩包内部 `manifest.json.version` 不一致，或 `archive_url` 指向了旧包。
- **自检清单**:
  - 确认 `index.json` 中：
    - `version` 与目标版本一致
    - `archive_url` 指向最新包（建议使用 `raw.githubusercontent` 指向仓库 `dist`）
    - `archive_size` 与 `archive_hash` 与实际压缩包一致
  - 解压或读取压缩包内的 `manifest.json`，确认其中 `version` 与 `index.json` 一致
  - 资源发布/缓存：若通过 GitHub Pages 提供索引，变更后可能有缓存延时，等待数分钟或强制刷新

**校验示例（PowerShell）**

```powershell
# 1) 读取压缩包内部 manifest.json 的版本
$zip = "dist/AartFlow-1.0.1.zip"
$dst = "tmp_check"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $dst -Force
# 兼容两种布局：根目录或 AartFlow/ 目录
$manifestPath = @("$dst/manifest.json", "$dst/AartFlow/manifest.json") | Where-Object { Test-Path $_ } | Select-Object -First 1
$manifest = Get-Content $manifestPath | ConvertFrom-Json
Write-Host "archive manifest version = $($manifest.version)"

# 2) 计算压缩包大小与 SHA256（用于写入 index.json）
$size = (Get-Item $zip).Length
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
Write-Host "archive_size = $size"
Write-Host "archive_hash = sha256:$hash"

# 3) 快速验证下载链接可用（返回 200 即正常）
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/dist/AartFlow-1.0.1.zip" -Method Head -UseBasicParsing | Select-Object -ExpandProperty StatusCode
```

##### Archive size mismatch（大小不一致）

- **错误现象**: `Archive size mismatch "<id>", expected <expected>, was <actual>`。
- **根因**:
  - `index.json` 中的 `archive_size` 与真实 ZIP 大小（字节）不一致（常见于打包后未同步更新索引）。
  - 远端缓存返回旧 ZIP，导致大小与本地不同。
- **自检清单**:
  - 本地计算 ZIP 大小：
    ```powershell
    (Get-Item dist/AartFlow-1.0.1.zip).Length
    ```
  - 对比 `index.json` 的 `archive_size` 数值是否一致（单位均为字节）。
  - 如使用 Pages/CDN，等待缓存或改用原始链接二次确认：
    ```powershell
    iwr https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/dist/AartFlow-1.0.1.zip -OutFile _tmp.zip
    (Get-Item _tmp.zip).Length
    Remove-Item _tmp.zip -Force
    ```
- **修复建议**:
  - 以本地实际 ZIP 为准，更新 `index.json.archive_size`（与 `archive_hash` 一并更新）。
  - 严格遵循发布顺序：先打包 → 再更新 `index.json` → 再提交推送。
  - 必要时在 `archive_url` 添加查询参数（如 `?t=<timestamp>`）以绕过缓存。

### 打包发布规范

#### 1. 打包前检查清单
- [ ] 所有模块文件已重命名为帕斯卡命名法
- [ ] 代码通过语法检查
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] 所有引用已更新

#### 2. 打包脚本使用
```powershell
# 使用打包脚本
.\package.ps1 -Version "1.0.1"

# 脚本会自动：
# - 验证必要文件
# - 创建ZIP文件
# - 计算文件大小
# - 清理临时文件
```

#### 3. 发布流程
注意：发布顺序必须为"先打包 → 再更新 index.json → 再提交推送"，否则容易出现 Archive size/hash mismatch。
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

## 📝 文档规范

### 文档结构规范

#### 1. 文档层级结构
```
docs/
├── README.md                    # 文档中心首页
├── user-guide.md                # 用户指南
├── development-guide.md         # 开发指南（本文件）
├── contributing-and-support.md  # 贡献与支持
└── license.md                   # 许可证
```

#### 2. 文档头部结构
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

#### 3. 文档尾部结构
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

### Markdown 格式规范

#### 1. 标题层级
```markdown
# 一级标题（文档标题）
## 二级标题（主要章节）
### 三级标题（子章节）
#### 四级标题（详细说明）
##### 五级标题（特殊情况）
```

#### 2. 代码块规范
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

#### 3. 列表规范
```markdown
# 有序列表
1. 第一项
2. 第二项
   1. 子项 2.1
   2. 子项 2.2
3. 第三项

# 无序列表
- 主要功能
  - 子功能 1
  - 子功能 2
- 次要功能
- 其他功能

# 任务列表
- [x] 已完成的任务
- [ ] 待完成的任务
- [ ] 另一个待完成的任务
```

#### 4. 表格规范
```markdown
| 列标题1 | 列标题2 | 列标题3 |
|---------|---------|---------|
| 数据1   | 数据2   | 数据3   |
| 数据4   | 数据5   | 数据6   |
```

### 内容编写规范

#### 1. 语言风格
- **语言**: 中文为主，技术术语可保留英文
- **语调**: 专业、友好、易懂
- **人称**: 使用第二人称"你"或"您"
- **时态**: 使用现在时，描述当前状态

#### 2. 技术文档要求

##### 代码示例
```markdown
# 好的示例
def calculate_dimensions(obj):
    """计算对象尺寸"""
    return obj.dimensions

# 避免的示例
def calc(obj):  # 函数名不够描述性
    return obj.dimensions  # 缺少文档字符串
```

##### 错误处理说明
```markdown
**常见错误**:
- `ModuleNotFoundError`: 缺少依赖模块
- `AttributeError`: 对象属性不存在

**解决方案**:
1. 检查模块是否正确安装
2. 验证对象类型和属性
```

#### 3. 用户指南要求

##### 步骤说明
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

#### 4. 开发文档要求

##### API 文档
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

### 视觉设计规范

#### 1. 徽章使用
```markdown
![Version](https://img.shields.io/badge/Version-1.0.0-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-GPL--3.0-green?style=flat-square)
```

#### 2. 分隔线使用
```markdown
---  # 主要章节分隔
***  # 子章节分隔（较少使用）
```

#### 3. 强调和突出
```markdown
**粗体文本** - 重要概念
*斜体文本* - 强调或引用
`代码文本` - 技术术语或代码
> 引用文本 - 重要说明或引用
```

#### 4. 图标使用
```markdown
## 📋 目录
## 🚀 快速开始
## ⚙️ 配置
## 🐛 故障排除
## 📚 参考
## ❓ 常见问题
```

### 文档维护规范

#### 1. 更新频率
- **功能文档**: 随功能更新同步更新
- **API 文档**: 随代码变更同步更新
- **教程文档**: 每季度检查一次
- **规范文档**: 半年检查一次

#### 2. 版本控制
```markdown
## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-01-16 | 初始版本，建立文档规范 |
| 1.0.1 | 2025-01-16 | 补充视觉设计规范 |
```

#### 3. 质量检查清单
- [ ] 文档结构符合规范
- [ ] 所有链接有效
- [ ] 代码示例可运行
- [ ] 图片显示正常
- [ ] 拼写和语法正确
- [ ] 格式统一一致

#### 4. 协作规范

##### 文档修改流程
1. 创建功能分支
2. 修改文档内容
3. 自我检查质量
4. 提交 Pull Request
5. 代码审查
6. 合并到主分支

##### 审查要点
- 内容准确性
- 格式规范性
- 语言流畅性
- 结构逻辑性

---

## 相关链接

- [返回文档中心](README.md)
- [用户指南](user-guide.md)
- [贡献与支持](contributing-and-support.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>