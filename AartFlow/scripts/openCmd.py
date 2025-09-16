bl_info = {
    "name": "Open PowerShell (AartFlow)",
    "author": "AartFlow",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > AartFlow",
    "description": "一键在当前项目目录打开 Windows PowerShell",
    "category": "System",
}

import os
import subprocess

import bpy


class ARTFLOW_OT_open_powershell(bpy.types.Operator):
    bl_idname = "artflow.open_powershell"
    bl_label = "打开 PowerShell"
    bl_description = "在指定目录打开一个新的 Windows PowerShell 窗口"
    bl_options = {"REGISTER", "INTERNAL"}

    # 添加属性用于输入工作目录
    work_dir: bpy.props.StringProperty(
        name="工作目录",
        description="PowerShell 启动的工作目录路径",
        default="",
        subtype='DIR_PATH'
    )

    def invoke(self, context, event):
        # 设置默认值为当前 .blend 所在目录或当前工作目录
        if not self.work_dir:
            self.work_dir = bpy.path.abspath("//") or os.getcwd()
        
        # 显示属性对话框
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "work_dir")
        
        # 显示一些快捷按钮
        row = layout.row(align=True)
        row.operator("artflow.set_current_blend_dir", text="当前文件目录", icon='FILE_BLEND')
        row.operator("artflow.set_project_dir", text="项目目录", icon='FOLDER_REDIRECT')
        row.operator("artflow.browse_dir", text="浏览", icon='FILEBROWSER')

    def execute(self, context):
        try:
            # 优先使用场景属性中的工作目录
            scene = context.scene
            if hasattr(scene, 'artflow_work_dir') and scene.artflow_work_dir.strip():
                cwd = scene.artflow_work_dir.strip()
            else:
                # 使用操作符属性中的目录
                cwd = self.work_dir.strip()
            
            # 如果都为空，使用默认目录
            if not cwd:
                cwd = bpy.path.abspath("//") or os.getcwd()
            
            # 检查目录是否存在
            if not os.path.exists(cwd):
                self.report({"ERROR"}, f"目录不存在: {cwd}")
                return {"CANCELLED"}
            
            if not os.path.isdir(cwd):
                self.report({"ERROR"}, f"路径不是目录: {cwd}")
                return {"CANCELLED"}

            if os.name == "nt":
                # 在 Windows 上创建新的控制台窗口
                CREATE_NEW_CONSOLE = 0x00000010
                subprocess.Popen(["powershell.exe"], creationflags=CREATE_NEW_CONSOLE, cwd=cwd)
            else:
                # 非 Windows 环境的兜底（一般用不到）
                subprocess.Popen(["x-terminal-emulator"], cwd=cwd)

            self.report({"INFO"}, f"已打开 PowerShell，目录: {cwd}")
            return {"FINISHED"}
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, f"打开 PowerShell 失败: {exc}")
            return {"CANCELLED"}


class ARTFLOW_OT_set_current_blend_dir(bpy.types.Operator):
    bl_idname = "artflow.set_current_blend_dir"
    bl_label = "设置为当前文件目录"
    bl_description = "将工作目录设置为当前 .blend 文件所在目录"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        # 获取当前打开的 PowerShell 操作符并设置其工作目录
        if hasattr(context, 'operator') and context.operator and hasattr(context.operator, 'work_dir'):
            context.operator.work_dir = bpy.path.abspath("//") or os.getcwd()
            self.report({"INFO"}, f"已设置为当前文件目录: {context.operator.work_dir}")
        else:
            # 如果没有操作符上下文，设置场景属性作为备用
            context.scene.artflow_work_dir = bpy.path.abspath("//") or os.getcwd()
            self.report({"INFO"}, f"已设置为当前文件目录: {context.scene.artflow_work_dir}")
        return {"FINISHED"}


class ARTFLOW_OT_set_project_dir(bpy.types.Operator):
    bl_idname = "artflow.set_project_dir"
    bl_label = "设置为项目目录"
    bl_description = "将工作目录设置为项目根目录"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        # 尝试找到项目根目录（包含 .git 或其他项目标识的目录）
        current_dir = bpy.path.abspath("//") or os.getcwd()
        project_dir = current_dir
        
        # 向上查找项目根目录
        while project_dir != os.path.dirname(project_dir):
            if any(os.path.exists(os.path.join(project_dir, marker)) for marker in ['.git', 'pyproject.toml', 'Cargo.toml', 'package.json']):
                break
            project_dir = os.path.dirname(project_dir)
        
        # 获取当前打开的 PowerShell 操作符并设置其工作目录
        if hasattr(context, 'operator') and context.operator and hasattr(context.operator, 'work_dir'):
            context.operator.work_dir = project_dir
            self.report({"INFO"}, f"已设置为项目根目录: {context.operator.work_dir}")
        else:
            # 如果没有操作符上下文，设置场景属性作为备用
            context.scene.artflow_work_dir = project_dir
            self.report({"INFO"}, f"已设置为项目根目录: {project_dir}")
        return {"FINISHED"}


class ARTFLOW_OT_browse_dir(bpy.types.Operator):
    bl_idname = "artflow.browse_dir"
    bl_label = "浏览目录"
    bl_description = "打开文件浏览器选择目录"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: bpy.props.StringProperty(
        name="目录",
        description="选择的目录路径",
        subtype='DIR_PATH'
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # 获取当前打开的 PowerShell 操作符并设置其工作目录
        if hasattr(context, 'operator') and context.operator and hasattr(context.operator, 'work_dir'):
            context.operator.work_dir = self.directory
            self.report({"INFO"}, f"已选择目录: {context.operator.work_dir}")
        else:
            # 如果没有操作符上下文，设置场景属性作为备用
            context.scene.artflow_work_dir = self.directory
            self.report({"INFO"}, f"已选择目录: {self.directory}")
        return {"FINISHED"}


class ARTFLOW_PT_powershell_panel(bpy.types.Panel):
    bl_label = "PowerShell 工具"
    bl_idname = "ARTFLOW_PT_powershell_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"

    def draw(self, context):
        layout = self.layout
        
        # 打开 PowerShell 按钮
        layout.operator(ARTFLOW_OT_open_powershell.bl_idname, text="打开 PowerShell", icon='CONSOLE')
        


def _menu_func(self, context):
    self.layout.operator(ARTFLOW_OT_open_powershell.bl_idname, text="打开 PowerShell")


classes = (
    ARTFLOW_OT_open_powershell,
    ARTFLOW_OT_set_current_blend_dir,
    ARTFLOW_OT_set_project_dir,
    ARTFLOW_OT_browse_dir,
    ARTFLOW_PT_powershell_panel,
)


def register():
    # 注册场景属性
    bpy.types.Scene.artflow_work_dir = bpy.props.StringProperty(
        name="工作目录",
        description="PowerShell 启动的工作目录路径",
        default="",
        subtype='DIR_PATH'
    )
    
    for cls in classes:
        bpy.utils.register_class(cls)
    # 顶部菜单 Window 下添加入口，避免干扰现有面板布局
    bpy.types.TOPBAR_MT_window.append(_menu_func)


def unregister():
    bpy.types.TOPBAR_MT_window.remove(_menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 清理场景属性
    if hasattr(bpy.types.Scene, 'artflow_work_dir'):
        del bpy.types.Scene.artflow_work_dir


if __name__ == "__main__":
    register()


