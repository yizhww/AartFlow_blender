# API 参考

## 📋 API 文档

### 核心集成器 API

#### AARTFLOW_integration.py

**主要类和方法：**

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
```

### 模块开发 API

#### 标准模块结构

```python
import bpy

class ModulePanel(bpy.types.Panel):
    """标准模块面板基类"""
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        """绘制面板内容"""
        pass

def register():
    """注册模块"""
    bpy.utils.register_class(ModulePanel)

def unregister():
    """注销模块"""
    bpy.utils.unregister_class(ModulePanel)
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
```

---

[← 返回文档中心](README.md) | [打包发布 →](packaging.md)
