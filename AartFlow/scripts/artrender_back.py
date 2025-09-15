import bpy
import os

bl_info = {
    "name": "Art Renderer",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Sidebar > Art Renderer",
    "description": "逐个渲染指定集合中的物体",
    "category": "Render",
}

# 定义场景属性
bpy.types.Scene.target_collection = bpy.props.PointerProperty(
    name="目标集合",
    type=bpy.types.Collection,
    description="选择要逐个渲染的集合"
)

classes = []

class ArtRendererOperator(bpy.types.Operator):
    """逐个渲染指定集合中的物体"""
    bl_idname = "render.art_render_collection"
    bl_label = "逐个渲染集合"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.target_collection is not None

    def execute(self, context):
        """执行批量渲染"""
        scene = context.scene
        target_collection = scene.target_collection
        
        if not target_collection:
            self.report({'ERROR'}, "请先选择目标集合")
            return {'CANCELLED'}
        
        # 获取集合中的所有网格物体
        mesh_objects = [obj for obj in target_collection.objects if obj.type == 'MESH' and obj.data]
        
        if not mesh_objects:
            self.report({'WARNING'}, f"集合 '{target_collection.name}' 中没有有效网格物体")
            return {'CANCELLED'}
        
        # 保存原始渲染可见性
        original_visibility = {}
        for obj in target_collection.objects:
            original_visibility[obj.name] = {'hide_render': obj.hide_render}
        
        # 设置输出路径
        global_filepath = bpy.path.abspath(scene.render.filepath)
        original_filepath = scene.render.filepath
        global_dir = os.path.dirname(global_filepath)
        global_ext = os.path.splitext(global_filepath)[1] or '.png'
        
        if not global_dir:
            global_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Blender_Renders")
        
        if not os.path.exists(global_dir):
            os.makedirs(global_dir, exist_ok=True)
        
        rendered_count = 0
        
        try:
            # 逐个渲染每个物体
            for i, obj in enumerate(mesh_objects):
                if not obj or obj.name not in bpy.data.objects:
                    continue
                
                # 隐藏所有物体，只显示当前物体
                for collection_obj in mesh_objects:
                    if collection_obj and collection_obj.name in bpy.data.objects:
                        collection_obj.hide_render = True
                obj.hide_render = False
                
                # 设置输出文件名
                safe_name = "".join(c for c in obj.name if c.isalnum() or c in ('-', '_')).rstrip()
                if not safe_name:
                    safe_name = f"object_{i + 1}"
                
                output_filepath = os.path.join(global_dir, f"{safe_name}{global_ext}")
                # 确保路径格式正确（Windows路径分隔符）
                output_filepath = os.path.normpath(output_filepath)
                scene.render.filepath = output_filepath
                
                # 开始渲染
                self.report({'INFO'}, f"正在渲染第 {i + 1} 个物体: {obj.name}")
                
                # 直接渲染并保存
                bpy.ops.render.render(write_still=True)
                
                rendered_count += 1
                self.report({'INFO'}, f"成功渲染并保存 {obj.name} 到 {output_filepath}")
            
            # 恢复原始渲染可见性
            for obj_name, visibility in original_visibility.items():
                obj = bpy.data.objects.get(obj_name)
                if obj:
                    obj.hide_render = visibility['hide_render']
            
            # 恢复原始文件路径
            scene.render.filepath = original_filepath
            
            self.report({'INFO'}, f"批量渲染完成，共渲染 {rendered_count} 个物体")
            return {'FINISHED'}
            
        except Exception as e:
            # 发生错误时也要恢复设置
            try:
                for obj_name, visibility in original_visibility.items():
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        obj.hide_render = visibility['hide_render']
                scene.render.filepath = original_filepath
            except:
                pass
            
            self.report({'ERROR'}, f"渲染过程中出错: {e}")
            return {'CANCELLED'}

classes.append(ArtRendererOperator)

class VIEW3D_PT_ArtRendererPanel(bpy.types.Panel):
    """3D视图侧边栏中的Art Renderer面板"""
    bl_label = "artrender_back"
    bl_idname = "VIEW3D_PT_art_renderer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'artrender_back'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 选择集合
        layout.prop(scene, "target_collection", text="选择集合")
        
        # 分隔线
        layout.separator()
        
        # 渲染按钮
        layout.operator(
            "render.art_render_collection",
            icon='RENDER_STILL',
            text="批量渲染集合"
        )

classes.append(VIEW3D_PT_ArtRendererPanel)

def register():
    """注册插件中的所有类"""
    from bpy.utils import register_class, unregister_class
    for cls in classes:
        try:
            unregister_class(cls)
        except RuntimeError:
            pass
        register_class(cls)

def unregister():
    """注销插件中的所有类"""
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    # 清理自定义属性
    if hasattr(bpy.types.Scene, "target_collection"):
        del bpy.types.Scene.target_collection

if __name__ == "__main__":
    register() 