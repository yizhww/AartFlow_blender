# -*- coding: utf-8 -*-
"""
世界着色器管理（skylightsmanage）

功能概览：
- 列出并快速切换场景中的 World 数据块
- 为指定/全部 World 配置环境贴图（Environment Texture）与强度（Background Strength）
- 一键创建基础 World 节点（Environment → Background → World Output）
- 复制选定 World、清理未被使用的 World

面板位置：View3D > Sidebar > skylightsmanage
"""

import bpy
import os


# 已去除环境贴图相关的辅助函数（仅保留世界管理）


def _enum_world_items(self, context):
    """为 EnumProperty 提供动态世界列表。"""
    try:
        return [(w.name, w.name, "") for w in bpy.data.worlds]
    except Exception:
        return []


def _get_selected_world_name(context) -> str:
    """稳健地解析当前选择的世界名称；若未设置则回退到场景世界或第一个世界。"""
    try:
        s = getattr(context.scene, 'skylights_settings', None)
        if s is not None:
            val = getattr(s, 'world_enum', "")
            if isinstance(val, str) and val:
                return val
    except Exception:
        pass
    try:
        if getattr(context.scene, 'world', None) is not None:
            return context.scene.world.name
    except Exception:
        pass
    try:
        if len(bpy.data.worlds) > 0:
            return bpy.data.worlds[0].name
    except Exception:
        pass
    return ""


def _setup_default_world_nodes(world: bpy.types.World) -> None:
    """为给定 World 构建默认节点：天空纹理( Nishita ) → 背景 → 世界输出。
    若已有节点则尽量复用，不重复创建连接。
    """
    try:
        if world is None:
            return
        world.use_nodes = True
        nt = world.node_tree
        nodes = nt.nodes
        links = nt.links

        # 获取/创建输出与背景
        out_node = next((n for n in nodes if n.type == 'OUTPUT_WORLD'), None)
        if out_node is None:
            out_node = nodes.new('ShaderNodeOutputWorld')
            out_node.location = (400, 0)

        bg_node = next((n for n in nodes if n.type == 'BACKGROUND'), None)
        if bg_node is None:
            bg_node = nodes.new('ShaderNodeBackground')
            bg_node.location = (150, 0)

        sky_node = next((n for n in nodes if n.type == 'TEX_SKY'), None)
        if sky_node is None:
            sky_node = nodes.new('ShaderNodeTexSky')
            sky_node.location = (-150, 0)
            # 设为 Nishita（若属性存在）
            try:
                if hasattr(sky_node, 'sky_type'):
                    sky_node.sky_type = 'NISHITA'
            except Exception:
                pass

        def _ensure_link(from_socket, to_socket):
            if from_socket is None or to_socket is None:
                return
            for l in links:
                if l.from_socket == from_socket and l.to_socket == to_socket:
                    return
            links.new(from_socket, to_socket)

        _ensure_link(sky_node.outputs.get('Color'), bg_node.inputs.get('Color'))
        _ensure_link(bg_node.outputs.get('Background'), out_node.inputs.get('Surface'))
    except Exception:
        pass


class SkylightsSettings(bpy.types.PropertyGroup):
    """面板设置/输入（仅世界管理）"""

    # 使用普通赋值以兼容编辑器静态检查器
    world_enum = bpy.props.EnumProperty(
        name="世界",
        description="选择要操作的世界",
        items=_enum_world_items,
    )


class SKYLIGHTS_OT_set_scene_world(bpy.types.Operator):
    """将选定世界设为当前场景世界"""
    bl_idname = "skylights.set_scene_world"
    bl_label = "设为场景世界"
    bl_options = {'REGISTER', 'UNDO'}

    world_name = bpy.props.StringProperty()

    def execute(self, context):
        name_prop = getattr(self, "world_name", "")
        wname = name_prop if isinstance(name_prop, str) and name_prop else _get_selected_world_name(context)
        w = bpy.data.worlds.get(wname)
        if w is None:
            self.report({'ERROR'}, "未找到指定世界")
            return {'CANCELLED'}
        context.scene.world = w
        self.report({'INFO'}, f"已设置场景世界：{w.name}")
        return {'FINISHED'}


class SKYLIGHTS_OT_create_world(bpy.types.Operator):
    """创建一个带基础节点的 World，并可选设置为当前场景世界"""
    bl_idname = "skylights.create_world"
    bl_label = "新建世界"
    bl_options = {'REGISTER', 'UNDO'}

    set_as_scene = bpy.props.BoolProperty(name="设为场景世界", default=True)

    def execute(self, context):
        w = bpy.data.worlds.new("AF_World")
        _setup_default_world_nodes(w)
        if self.set_as_scene:
            context.scene.world = w
        self.report({'INFO'}, f"已创建世界：{w.name}")
        return {'FINISHED'}


class SKYLIGHTS_OT_duplicate_world(bpy.types.Operator):
    """复制当前选定世界为一个新 World"""
    bl_idname = "skylights.duplicate_world"
    bl_label = "复制选定世界"
    bl_options = {'REGISTER', 'UNDO'}

    world_name = bpy.props.StringProperty()

    def execute(self, context):
        name_prop = getattr(self, "world_name", "")
        wname = name_prop if isinstance(name_prop, str) and name_prop else _get_selected_world_name(context)
        src = bpy.data.worlds.get(wname)
        if src is None:
            self.report({'ERROR'}, "未找到指定世界")
            return {'CANCELLED'}
        new = src.copy()
        # 拷贝节点树（.copy() 已复制 node_tree 数据块的用户引用）
        try:
            context.scene.world = new
        except Exception:
            pass
        self.report({'INFO'}, f"已复制世界并设为当前：{src.name} → {new.name}")
        return {'FINISHED'}


class SKYLIGHTS_OT_cleanup_unused(bpy.types.Operator):
    """删除未被任何场景/数据使用的 World"""
    bl_idname = "skylights.cleanup_unused"
    bl_label = "清理未使用世界"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed = 0
        for w in list(bpy.data.worlds):
            try:
                if w.users == 0:
                    bpy.data.worlds.remove(w)
                    removed += 1
            except Exception:
                pass
        self.report({'INFO'}, f"已清理 {removed} 个未使用世界")
        return {'FINISHED'}


class SKYLIGHTS_OT_open_world_shader(bpy.types.Operator):
    """打开 Shader Editor 并切换到 世界(World) 着色器"""
    bl_idname = "skylights.open_world_shader"
    bl_label = "打开世界着色器"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        # 确保场景世界存在
        if scene.world is None:
            try:
                scene.world = bpy.data.worlds.new("World")
            except Exception:
                pass
        try:
            if scene.world is not None:
                scene.world.use_nodes = True
                # 确保默认节点存在，便于直接编辑
                _setup_default_world_nodes(scene.world)
        except Exception:
            pass

        # 找到一个可用区域：优先"最左下"，并尽量不占用唯一的 3D/属性/大纲
        target_area = None
        target_window = None
        try:
            # 先收集所有区域与类型计数
            all_areas = []  # (window, area, (x, y))
            type_counts = {}
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    try:
                        ax = int(getattr(area, 'x', 1_000_000))
                        ay = int(getattr(area, 'y', 1_000_000))
                    except Exception:
                        ax, ay = (1_000_000, 1_000_000)
                    all_areas.append((window, area, (ax, ay)))
                    t = getattr(area, 'type', '') or ''
                    type_counts[t] = type_counts.get(t, 0) + 1

            # 若已有节点编辑器，则选"最左下"的节点编辑器
            node_areas = [(w, a, pos) for (w, a, pos) in all_areas if getattr(a, 'type', '') == 'NODE_EDITOR']
            if node_areas:
                node_areas.sort(key=lambda it: (it[2][0], it[2][1]))
                target_window, target_area, _ = node_areas[0]
            else:
                # 否则，从所有区域按"最左下"排序，挑第一个不会使 3D/属性/大纲 其中某一类归零的区域
                all_areas.sort(key=lambda it: (it[2][0], it[2][1]))
                protected = {'VIEW_3D', 'PROPERTIES', 'OUTLINER'}
                chosen = None
                for w, a, pos in all_areas:
                    at = getattr(a, 'type', '') or ''
                    if at in protected and type_counts.get(at, 0) <= 1:
                        # 这是该类型的唯一一个，跳过以避免占用
                        continue
                    chosen = (w, a)
                    break
                if chosen is None:
                    # 仍未找到，则只能占用最左下的那个
                    if all_areas:
                        chosen = (all_areas[0][0], all_areas[0][1])
                if chosen is not None:
                    target_window, target_area = chosen
        except Exception:
            target_area = None

        if target_area is None:
            self.report({'ERROR'}, "未找到可用的区域以打开世界着色器")
            return {'CANCELLED'}

        # 切换并配置为 Shader Editor(World)
        try:
            target_area.type = 'NODE_EDITOR'
        except Exception:
            pass
        try:
            for space in target_area.spaces:
                if space.type == 'NODE_EDITOR':
                    # Shader 节点树
                    if hasattr(space, 'tree_type'):
                        space.tree_type = 'ShaderNodeTree'
                    if hasattr(space, 'shader_type'):
                        space.shader_type = 'WORLD'
                    if hasattr(space, 'id') and scene.world is not None:
                        space.id = scene.world
                    break
            target_area.tag_redraw()
        except Exception:
            pass

        self.report({'INFO'}, "已打开世界着色器")
        return {'FINISHED'}


class SKYLIGHTS_OT_world_context_menu(bpy.types.Operator):
    """世界右键菜单操作符"""
    bl_idname = "skylights.world_context_menu"
    bl_label = "世界操作"
    bl_options = {'REGISTER', 'UNDO'}

    world_name = bpy.props.StringProperty()
    action = bpy.props.StringProperty()

    def execute(self, context):
        world_name = self.world_name
        action = self.action
        
        if not world_name:
            self.report({'ERROR'}, "未指定世界名称")
            return {'CANCELLED'}
            
        world = bpy.data.worlds.get(world_name)
        if world is None:
            self.report({'ERROR'}, f"未找到世界：{world_name}")
            return {'CANCELLED'}

        if action == "set_scene":
            context.scene.world = world
            self.report({'INFO'}, f"已设置场景世界：{world.name}")
        elif action == "duplicate":
            new_world = world.copy()
            context.scene.world = new_world
            self.report({'INFO'}, f"已复制世界：{world.name} → {new_world.name}")
        elif action == "delete":
            if world.users > 0:
                self.report({'WARNING'}, f"世界 {world.name} 正在被使用，无法删除")
                return {'CANCELLED'}
            bpy.data.worlds.remove(world)
            self.report({'INFO'}, f"已删除世界：{world.name}")
        elif action == "open_shader":
            # 临时设置为场景世界并打开着色器
            old_world = context.scene.world
            context.scene.world = world
            bpy.ops.skylights.open_world_shader()
            # 恢复原来的场景世界
            context.scene.world = old_world
            self.report({'INFO'}, f"已打开世界着色器：{world.name}")
        elif action == "rename":
            # 这里可以打开重命名对话框，暂时用简单的重命名
            new_name = f"{world.name}_copy"
            world.name = new_name
            self.report({'INFO'}, f"已重命名世界：{world.name}")
        else:
            self.report({'ERROR'}, f"未知操作：{action}")
            return {'CANCELLED'}

        return {'FINISHED'}


class SKYLIGHTS_OT_show_world_menu(bpy.types.Operator):
    """显示世界右键菜单"""
    bl_idname = "skylights.show_world_menu"
    bl_label = "世界操作菜单"
    bl_options = {'REGISTER'}

    world_name = bpy.props.StringProperty()

    def execute(self, context):
        # 在Blender中，我们需要通过bpy.ops.wm.call_menu来调用菜单
        # 这里我们直接执行操作，或者可以打开一个对话框
        return {'FINISHED'}

    def invoke(self, context, event):
        # 使用invoke来显示菜单
        world_name = self.world_name
        if not world_name:
            self.report({'ERROR'}, "未指定世界名称")
            return {'CANCELLED'}
            
        world = bpy.data.worlds.get(world_name)
        if world is None:
            self.report({'ERROR'}, f"未找到世界：{world_name}")
            return {'CANCELLED'}

        # 创建一个简单的操作选择对话框
        def draw_menu(self, context):
            layout = self.layout
            layout.label(text=f"世界操作: {world_name}")
            layout.separator()
            
            op = layout.operator("skylights.world_context_menu", text="设为场景世界", icon='WORLD')
            op.world_name = world_name
            op.action = "set_scene"

            op = layout.operator("skylights.world_context_menu", text="打开着色器", icon='NODETREE')
            op.world_name = world_name
            op.action = "open_shader"

            layout.separator()

            op = layout.operator("skylights.world_context_menu", text="复制世界", icon='DUPLICATE')
            op.world_name = world_name
            op.action = "duplicate"

            op = layout.operator("skylights.world_context_menu", text="重命名", icon='RENAME')
            op.world_name = world_name
            op.action = "rename"

            layout.separator()

            if world.users == 0:
                op = layout.operator("skylights.world_context_menu", text="删除世界", icon='TRASH')
                op.world_name = world_name
                op.action = "delete"
            else:
                layout.label(text="世界正在使用中", icon='INFO')

        # 注册临时菜单
        menu_class = type(f"SKYLIGHTS_MT_temp_{world_name}", (bpy.types.Menu,), {
            "bl_label": f"世界操作: {world_name}",
            "bl_idname": f"SKYLIGHTS_MT_temp_{world_name}",
            "draw": draw_menu
        })
        
        try:
            bpy.utils.register_class(menu_class)
            bpy.ops.wm.call_menu(name=menu_class.bl_idname)
        finally:
            try:
                bpy.utils.unregister_class(menu_class)
            except:
                pass

        return {'FINISHED'}


class SKYLIGHTS_MT_world_context_menu(bpy.types.Menu):
    """世界右键菜单"""
    bl_label = "世界操作"
    bl_idname = "SKYLIGHTS_MT_world_context_menu"

    def draw(self, context):
        layout = self.layout
        layout.label(text="请选择世界进行操作")


class VIEW3D_PT_skylightsmanage(bpy.types.Panel):
    """世界着色器管理面板"""
    bl_label = "skylightsmanage"
    bl_idname = "VIEW3D_PT_skylightsmanage"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "skylightsmanage"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.skylights_settings

        # 世界选择/操作
        box_world = layout.box()
        row = box_world.row()
        row.prop(settings, "world_enum", text="世界")
        # 同行：新建 / 打开 / 清理
        row = box_world.row(align=True)
        row.operator("skylights.create_world", text="新建", icon='ADD')
        row.operator("skylights.open_world_shader", text="打开", icon='NODETREE')
        row.operator("skylights.cleanup_unused", text="清理", icon='TRASH')

        # 世界清单
        box_list = layout.box()
        try:
            for w in bpy.data.worlds:
                row = box_list.row(align=True)
                # 世界名称按钮（左键设为场景世界）
                op = row.operator("skylights.world_context_menu", text=w.name, icon='WORLD_DATA')
                op.world_name = w.name
                op.action = "set_scene"
                
                # 右键菜单按钮
                op = row.operator("skylights.show_world_menu", text="", icon='DOWNARROW_HLT')
                op.world_name = w.name
        except Exception:
            box_list.label(text="读取世界列表失败")

        # 清理按钮已与“新建/打开”同行


classes = [
    SkylightsSettings,
    SKYLIGHTS_OT_set_scene_world,
    SKYLIGHTS_OT_create_world,
    SKYLIGHTS_OT_duplicate_world,
    SKYLIGHTS_OT_cleanup_unused,
    SKYLIGHTS_OT_open_world_shader,
    SKYLIGHTS_OT_world_context_menu,
    SKYLIGHTS_OT_show_world_menu,
    SKYLIGHTS_MT_world_context_menu,
    VIEW3D_PT_skylightsmanage,
]


def register():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)
    bpy.types.Scene.skylights_settings = bpy.props.PointerProperty(type=SkylightsSettings)


def unregister():
    try:
        del bpy.types.Scene.skylights_settings
    except Exception:
        pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("[skylightsmanage] 已加载：N 面板 > skylightsmanage")


