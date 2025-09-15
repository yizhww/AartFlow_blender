# 模块开发指南

## 📝 开发新模块

### 1. 创建模块文件
在 `AartFlow/scripts/` 目录下创建新的 Python 文件

### 2. 模块开发规范
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

### 3. 模块要求
- 必须包含 `bpy.types.Panel` 子类
- 必须实现 `register()` 和 `unregister()` 函数
- 建议添加适当的错误处理

---

[← 返回文档中心](README.md) | [API 参考 →](api-reference.md)
