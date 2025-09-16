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
│   ├── development-guide.md           # 开发指南
│   ├── project-management.md          # 项目管理
│   ├── development-standards.md       # 开发标准
│   ├── documentation-standards.md     # 文档规范
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

## 相关链接

- [返回文档中心](README.md)
- [用户指南](user-guide.md)
- [项目管理](project-management.md)
- [开发标准](development-standards.md)
- [贡献与支持](contributing-and-support.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
