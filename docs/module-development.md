# AartFlow 脚本模块开发规范

## 📋 目录
- [文件结构规范](#文件结构规范)
- [命名规范](#命名规范)
- [代码组织规范](#代码组织规范)
- [类定义规范](#类定义规范)
- [属性定义规范](#属性定义规范)
- [错误处理规范](#错误处理规范)
- [文档注释规范](#文档注释规范)
- [注册与注销规范](#注册与注销规范)
- [示例模板](#示例模板)

---

## 文件结构规范

### 1. 文件命名和位置
```python
# 文件位置：AartFlow/scripts/模块名称.py
# 文件命名：使用帕斯卡命名法，反映模块主要功能

# 示例文件路径：
AartFlow/scripts/artRenderBack.py
AartFlow/scripts/objectMeasure.py
AartFlow/scripts/standardView.py
```

### 2. 文件头部结构
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块功能描述
详细说明模块的主要功能和用途
"""

import bpy
# 其他必要的导入
from bpy.types import Operator, Panel
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy.utils import register_class, unregister_class

# bl_info 元数据（必须）
bl_info = {
    "name": "模块名称",
    "author": "AartFlow",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "3D 视图 > 侧栏 > 面板名称",
    "description": "模块功能描述",
    "category": "模块分类",
}
```

### 3. 代码组织顺序
1. **导入语句** - 标准库 → 第三方库 → Blender API
2. **bl_info 元数据**
3. **全局变量和常量**
4. **工具函数** (以 `_` 开头)
5. **属性定义** (bpy.types.Scene 属性)
6. **类定义** (Operator → Panel)
7. **注册/注销函数**

---

## 命名规范

### 1. 文件命名规范
```python
# 脚本模块文件命名：使用帕斯卡命名法（PascalCase）
# 格式：模块功能名称.py

# 示例：
artRenderBack.py          # 艺术渲染后端模块
artRenderFront.py         # 艺术渲染前端模块
dataPlotting.py           # 数据绘制模块
objectMeasure.py          # 对象测量模块
openCmd.py              # 命令打开模块
skpDrag.py              # SKP拖拽模块
skylightsManage.py       # 天空光管理模块
standardView.py          # 标准视图模块

# 命名规则：
# - 使用帕斯卡命名法（PascalCase）
# - 文件名应简洁明了，反映模块主要功能
# - 避免使用下划线分隔（除非必要）
# - 使用小写字母开头，后续单词首字母大写
# - 文件名长度控制在20个字符以内
# - 避免使用缩写，除非是通用缩写（如cmd、skp等）
```

### 2. 类命名规范
```python
# Operator 类
class AF_OT_module_action(bpy.types.Operator):
    """操作符描述"""
    bl_idname = "af.module_action"  # 使用 af. 前缀
    bl_label = "操作名称"
    bl_options = {'REGISTER', 'UNDO'}

# Panel 类  
class AF_PT_module_panel(bpy.types.Panel):
    """面板描述"""
    bl_label = "面板名称"
    bl_idname = "AF_PT_module_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"  # 统一使用 AartFlow 分类

# PropertyGroup 类
class ModuleSettings(bpy.types.PropertyGroup):
    """设置属性组"""
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

# 工具函数：使用模块前缀
def _module_utility_function():
    """模块工具函数"""
    pass
```

### 4. 变量命名规范
```python
# 常量：全大写，下划线分隔
DEFAULT_VALUE = 1.0
MAX_ITERATIONS = 100

# 全局变量：小写，下划线分隔
module_state = {}
active_handlers = []

# 局部变量：小写，下划线分隔
current_object = None
render_count = 0
```

---

## 代码组织规范

### 1. 模块化设计
```python
# 将复杂功能拆分为独立的函数
def _setup_rendering_environment(context):
    """设置渲染环境"""
    pass

def _cleanup_rendering_environment(context):
    """清理渲染环境"""
    pass

def _process_render_results(results):
    """处理渲染结果"""
    pass
```

### 2. 状态管理
```python
# 使用类属性管理状态
class AF_OT_module_operator(bpy.types.Operator):
    bl_idname = "af.module_operator"
    
    # 运行时状态变量（不注册为属性）
    _is_active = False
    _current_step = 0
    _render_results = []
```

### 3. 错误处理模式
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

## 类定义规范

### 1. Operator 类规范
```python
class AF_OT_module_operator(bpy.types.Operator):
    """操作符描述"""
    bl_idname = "af.module_operator"
    bl_label = "操作名称"
    bl_description = "详细的操作描述"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 属性定义
    input_value: bpy.props.FloatProperty(
        name="输入值",
        description="输入参数描述",
        default=1.0,
        min=0.0,
        max=100.0
    )
    
    @classmethod
    def poll(cls, context):
        """操作可用性检查"""
        return context.active_object is not None
    
    def invoke(self, context, event):
        """交互式调用"""
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        """属性对话框绘制"""
        layout = self.layout
        layout.prop(self, "input_value")
    
    def execute(self, context):
        """执行操作"""
        # 实现逻辑
        return {'FINISHED'}
```

### 2. Panel 类规范
```python
class AF_PT_module_panel(bpy.types.Panel):
    """面板描述"""
    bl_label = "面板标题"
    bl_idname = "AF_PT_module_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_context = "objectmode"
    
    def draw(self, context):
        """绘制面板内容"""
        layout = self.layout
        scene = context.scene
        
        # 使用 box 进行分组
        box = layout.box()
        box.label(text="设置区域")
        box.prop(scene, "module_setting")
        
        # 操作按钮
        layout.operator("af.module_operator", text="执行操作")
```

---

## 属性定义规范

### 1. 场景属性定义
```python
# 使用模块前缀避免冲突
bpy.types.Scene.af_module_setting = bpy.props.BoolProperty(
    name="模块设置",
    description="模块设置描述",
    default=True
)

# 复杂属性使用 PropertyGroup
class ModuleSettings(bpy.types.PropertyGroup):
    """模块设置属性组"""
    
    setting_value: bpy.props.FloatProperty(
        name="设置值",
        description="设置值描述",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    setting_enabled: bpy.props.BoolProperty(
        name="启用设置",
        description="是否启用此设置",
        default=True
    )

# 注册属性组
bpy.types.Scene.af_module_settings = bpy.props.PointerProperty(
    type=ModuleSettings
)
```

### 2. 属性更新回调
```python
def _update_module_setting(self, context):
    """属性更新回调"""
    try:
        # 更新逻辑
        self._refresh_ui(context)
    except Exception as e:
        print(f"更新设置失败: {e}")

# 在属性定义中使用
bpy.types.Scene.af_module_setting = bpy.props.FloatProperty(
    name="模块设置",
    description="模块设置描述",
    default=1.0,
    update=_update_module_setting
)
```

---

## 错误处理规范

### 1. 异常处理模式
```python
def execute(self, context):
    """执行操作"""
    try:
        # 主要逻辑
        return self._perform_main_action(context)
    except ValueError as e:
        self.report({'ERROR'}, f"参数错误: {e}")
        return {'CANCELLED'}
    except RuntimeError as e:
        self.report({'ERROR'}, f"运行时错误: {e}")
        return {'CANCELLED'}
    except Exception as e:
        # 记录详细错误信息
        import traceback
        print(f"未预期错误: {e}")
        print(traceback.format_exc())
        self.report({'ERROR'}, f"操作失败: {e}")
        return {'CANCELLED'}
```

### 2. 状态恢复模式
```python
def execute(self, context):
    """执行操作"""
    # 保存原始状态
    original_state = self._save_original_state(context)
    
    try:
        # 执行操作
        return self._perform_action(context)
    finally:
        # 确保状态恢复
        self._restore_original_state(context, original_state)
```

---

## 文档注释规范

### 1. 模块级文档
```python
"""
模块名称

详细描述模块的功能、用途和使用方法。

功能特性:
- 功能1: 描述
- 功能2: 描述

使用说明:
1. 步骤1
2. 步骤2

注意事项:
- 注意事项1
- 注意事项2
"""
```

### 2. 类和函数文档
```python
def calculate_dimensions(obj, precision=2):
    """
    计算对象的尺寸信息
    
    Args:
        obj (bpy.types.Object): 要计算尺寸的对象
        precision (int): 小数位数精度，默认为2
        
    Returns:
        dict: 包含长宽高信息的字典，格式为 {'length': float, 'width': float, 'height': float}
        
    Raises:
        ValueError: 当对象类型不支持时抛出
        RuntimeError: 当计算过程中发生错误时抛出
    """
    pass
```

---

## 注册与注销规范

### 1. 类列表管理
```python
# 定义类列表
classes = [
    AF_OT_module_operator,
    AF_PT_module_panel,
    ModuleSettings,
]

def register():
    """注册所有类和属性"""
    # 注册类
    for cls in classes:
        try:
            unregister_class(cls)
        except RuntimeError:
            pass
        register_class(cls)
    
    # 注册属性
    bpy.types.Scene.af_module_settings = bpy.props.PointerProperty(
        type=ModuleSettings
    )

def unregister():
    """注销所有类和属性"""
    # 注销类（逆序）
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except RuntimeError:
            pass
    
    # 清理属性
    if hasattr(bpy.types.Scene, "af_module_settings"):
        del bpy.types.Scene.af_module_settings

if __name__ == "__main__":
    register()
```

### 2. 处理器管理
```python
# 全局处理器存储
_handlers = {}

def register():
    """注册处理器"""
    global _handlers
    
    # 注册事件处理器
    if "load_post" not in _handlers:
        _handlers["load_post"] = _on_load_post
        bpy.app.handlers.load_post.append(_handlers["load_post"])

def unregister():
    """注销处理器"""
    global _handlers
    
    # 移除事件处理器
    if "load_post" in _handlers:
        bpy.app.handlers.load_post.remove(_handlers["load_post"])
        del _handlers["load_post"]
```

---

## 示例模板

### 完整模块模板

**文件名示例：** `exampleModule.py` (使用帕斯卡命名法)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例模块

这是一个完整的模块开发模板，展示了所有规范的用法。
"""

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "示例模块",
    "author": "AartFlow",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "3D 视图 > 侧栏 > 示例面板",
    "description": "模块功能描述",
    "category": "Example",
}

# 全局常量
DEFAULT_VALUE = 1.0
MAX_ITERATIONS = 100

# 全局变量
module_state = {}

# 工具函数
def _calculate_something(value):
    """计算某个值"""
    return value * 2

# 属性组
class ExampleSettings(bpy.types.PropertyGroup):
    """示例设置属性组"""
    
    setting_value: FloatProperty(
        name="设置值",
        description="示例设置值",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    setting_enabled: BoolProperty(
        name="启用",
        description="是否启用设置",
        default=True
    )

# 操作符
class AF_OT_example_operator(bpy.types.Operator):
    """示例操作符"""
    bl_idname = "af.example_operator"
    bl_label = "执行示例操作"
    bl_description = "执行示例操作的详细描述"
    bl_options = {'REGISTER', 'UNDO'}
    
    input_text: StringProperty(
        name="输入文本",
        description="输入文本参数",
        default="示例文本"
    )
    
    @classmethod
    def poll(cls, context):
        """检查操作是否可用"""
        return context.active_object is not None
    
    def execute(self, context):
        """执行操作"""
        try:
            # 获取设置
            settings = context.scene.af_example_settings
            
            # 执行主要逻辑
            result = _calculate_something(float(settings.setting_value))
            
            # 报告结果
            self.report({'INFO'}, f"计算结果: {result}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"操作失败: {e}")
            return {'CANCELLED'}

# 面板
class AF_PT_example_panel(bpy.types.Panel):
    """示例面板"""
    bl_label = "示例面板"
    bl_idname = "AF_PT_example_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_context = "objectmode"
    
    def draw(self, context):
        """绘制面板"""
        layout = self.layout
        scene = context.scene
        
        # 设置区域
        box = layout.box()
        box.label(text="设置")
        box.prop(scene.af_example_settings, "setting_value")
        box.prop(scene.af_example_settings, "setting_enabled")
        
        # 操作区域
        layout.separator()
        layout.operator("af.example_operator", text="执行操作")

# 类列表
classes = [
    ExampleSettings,
    AF_OT_example_operator,
    AF_PT_example_panel,
]

def register():
    """注册模块"""
    for cls in classes:
        register_class(cls)
    
    # 注册场景属性
    bpy.types.Scene.af_example_settings = bpy.props.PointerProperty(
        type=ExampleSettings
    )

def unregister():
    """注销模块"""
    for cls in reversed(classes):
        unregister_class(cls)
    
    # 清理场景属性
    if hasattr(bpy.types.Scene, "af_example_settings"):
        del bpy.types.Scene.af_example_settings

if __name__ == "__main__":
    register()
```

---

## 📝 开发检查清单

### 开发前检查
- [ ] 确认模块功能需求
- [ ] 选择合适的命名规范
- [ ] 设计合理的类结构

### 开发中检查
- [ ] 遵循命名规范
- [ ] 添加适当的错误处理
- [ ] 编写清晰的文档注释
- [ ] 使用统一的代码风格

### 开发后检查
- [ ] 测试所有功能
- [ ] 检查内存泄漏
- [ ] 验证注册/注销流程
- [ ] 更新文档

---

[← 返回文档中心](README.md) | [API 参考 →](api-reference.md)
