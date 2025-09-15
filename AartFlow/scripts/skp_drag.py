bl_info = {
    "name": "SKP 拖拽处理器 (最终版)",
    "author": "AartFlow",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D 视图 > 拖拽处理",
    "description": "最终版SKP文件拖拽处理器，支持真实拖拽事件",
    "category": "Import",
}

import bpy
import os
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent
from bpy.types import FileHandler
from bpy_extras.io_utils import ImportHelper

# 全局变量存储拖拽的文件路径
skp_drag_filepath = ""


def process_skp_file(filepath):
    """处理SKP文件的基础函数（简化版，占位）"""
    # 在此对 filepath 进行后续处理（留空，按需扩展）
    return None


class AF_OT_skp_drag_handler(bpy.types.Operator):
    """SKP拖拽处理器"""
    bl_idname = "af.skp_drag_handler"
    bl_label = "SKP拖拽处理器"
    bl_description = "处理拖拽到3D视图的SKP文件"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(
        name="文件路径",
        description="SKP文件路径",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        """执行拖拽处理"""
        global skp_drag_filepath
        
        filepath = self.filepath
        if not filepath:
            self.report({'WARNING'}, "未选择文件")
            return {'CANCELLED'}

        # 检查文件是否存在
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"文件不存在: {filepath}")
            return {'CANCELLED'}

        # 检查文件扩展名
        if not filepath.lower().endswith('.skp'):
            self.report({'ERROR'}, "只支持 .skp 文件")
            return {'CANCELLED'}

        # 处理文件路径
        file_path = os.path.abspath(filepath)
        skp_drag_filepath = file_path
        
        print(f"🟢 [SKP 拖拽处理器] 检测到 SKP 文件: {file_path}")
        self.report({'INFO'}, f"已接收 SKP 文件: {os.path.basename(file_path)}")
        
        # 处理文件
        process_skp_file(file_path)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        """调用操作"""
        # 使用文件选择器作为备选方案
        context.window_manager.fileselect_add(self)
        print("🟢 打开文件选择器")
        return {'RUNNING_MODAL'}


## 已弃用：模态拖拽监听会引发未知事件类型警告，改用 FileHandler


class AF_OT_skp_file_selector(bpy.types.Operator):
    """SKP文件选择器"""
    bl_idname = "af.skp_file_selector"
    bl_label = "选择SKP文件"
    bl_description = "选择SKP文件进行处理"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(
        name="文件路径",
        description="SKP文件路径",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        """执行文件选择"""
        global skp_drag_filepath
        
        filepath = self.filepath
        if not filepath:
            self.report({'WARNING'}, "未选择文件")
            return {'CANCELLED'}

        # 检查文件是否存在
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"文件不存在: {filepath}")
            return {'CANCELLED'}

        # 检查文件扩展名
        if not filepath.lower().endswith('.skp'):
            self.report({'ERROR'}, "只支持 .skp 文件")
            return {'CANCELLED'}

        # 处理文件路径
        file_path = os.path.abspath(filepath)
        skp_drag_filepath = file_path
        
        print(f"🟢 [SKP 拖拽处理器] 检测到 SKP 文件: {file_path}")
        self.report({'INFO'}, f"已接收 SKP 文件: {os.path.basename(file_path)}")
        
        # 处理文件
        process_skp_file(file_path)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        """调用操作"""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class AF_OT_get_skp_path(bpy.types.Operator):
    """获取当前SKP文件路径（已不在面板暴露）"""
    bl_idname = "af.get_skp_path"
    bl_label = "获取文件路径"
    bl_description = "获取当前SKP文件路径"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'CANCELLED'}


class AF_PT_skp_panel(bpy.types.Panel):
    """SKP处理面板"""
    bl_label = "SKP 拖拽处理"
    bl_idname = "AF_PT_skp_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"

    def draw(self, context):
        layout = self.layout
        
        # 仅保留一个选择 SU 文件按钮
        layout.operator("af.skp_file_selector", text="选择 SU 文件", icon='FILEBROWSER')


class AF_FH_skp(FileHandler):
    bl_idname = "AF_FH_skp"
    bl_label = "AartFlow SKP Drop"
    bl_file_extensions = ".skp"
    bl_import_operator = "af.skp_drop_import"

    @classmethod
    def poll_drop(cls, context):
        area = context.area
        if not area:
            return False
        if area.type == 'VIEW_3D':
            return True
        if area.type == 'OUTLINER' and area.spaces.active.display_mode == 'VIEW_LAYER':
            return True
        return False

    # 不重载 execute，交由 bl_import_operator = af.skp_drop_import 处理


class AF_OT_skp_drop_import(bpy.types.Operator, ImportHelper):
    bl_idname = "af.skp_drop_import"
    bl_label = "Import SKP From Drop"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        global skp_drag_filepath
        # 解析路径：优先 filepath，其次 files+directory
        filepath_value = self.filepath
        if not isinstance(filepath_value, str):
            filepath_value = ""
        resolved_path = filepath_value
        if not resolved_path:
            dir_value = self.directory if isinstance(self.directory, str) else ""
            if dir_value and self.files:
                try:
                    first = self.files[0].name
                    resolved_path = os.path.join(dir_value, first)
                except Exception:
                    resolved_path = ""
        if not resolved_path:
            self.report({'WARNING'}, "未获取到拖拽路径")
            return {'CANCELLED'}
        filepath = os.path.abspath(resolved_path)
        if not filepath.lower().endswith('.skp'):
            self.report({'WARNING'}, f"非SKP: {filepath}")
            return {'CANCELLED'}
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"文件不存在: {filepath}")
            return {'CANCELLED'}
        skp_drag_filepath = filepath
        print(f"🟢 [SKP Drop] {skp_drag_filepath}")
        process_skp_file(skp_drag_filepath)
        return {'FINISHED'}


@persistent
def handle_drop_files(scene):
    """全局拖拽处理函数"""
    # 这个函数会在场景更新时被调用
    # 可以在这里添加全局的拖拽处理逻辑
    pass


def register():
    """注册插件"""
    register_class(AF_OT_skp_drop_import)
    register_class(AF_OT_skp_file_selector)
    register_class(AF_PT_skp_panel)
    register_class(AF_FH_skp)
    
    # 注册全局拖拽处理函数（保留，无实际逻辑）
    bpy.app.handlers.depsgraph_update_post.append(handle_drop_files)
    
    print("🟢 [SKP 拖拽处理器] 插件已注册")


def unregister():
    """注销插件"""
    # 移除全局拖拽处理函数
    if handle_drop_files in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(handle_drop_files)

    # 无 KeyMap 需要移除
    
    unregister_class(AF_PT_skp_panel)
    unregister_class(AF_OT_skp_file_selector)
    unregister_class(AF_OT_skp_drop_import)
    unregister_class(AF_FH_skp)
    
    print("🔴 [SKP 拖拽处理器] 插件已注销")


if __name__ == "__main__":
    register()
