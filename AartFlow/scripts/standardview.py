#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正交摄像机快照渲染工具
功能：
1. 一键在选中物体原点生成七个正交摄像机（XYZ、-XYZ 和轴测45°）
2. 为TRACK TO约束的摄像机拍摄快照并保存
"""

import bpy
import mathutils
import math
from bpy.props import FloatVectorProperty, FloatProperty, IntProperty
from bpy.types import Operator, Panel, PropertyGroup


def _update_dynamic_resolution_settings(self, context):
    """当动态相机设置变更时的回调函数"""
    try:
        # 强制UI刷新
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    except Exception as e:
        print(f"动态相机设置更新失败: {e}")

def _update_ortho_scale(self, context):
    """当设置中的正交比例变更时，自动更新与当前选中物体存在 TRACK_TO 约束的正交相机。"""
    try:
        if context is None or not getattr(context, "selected_objects", None):
            return
        if len(context.selected_objects) != 1:
            return

        target_object = context.selected_objects[0]
        new_ortho_scale = float(getattr(self, "ortho_scale", 0.0))

        for obj in bpy.data.objects:
            if obj.type != 'CAMERA':
                continue
            has_track_to = False
            for constraint in obj.constraints:
                if constraint.type == 'TRACK_TO' and constraint.target == target_object:
                    has_track_to = True
                    break
            if not has_track_to:
                continue
            if obj.data and obj.data.type == 'ORTHO':
                obj.data.ortho_scale = new_ortho_scale

        # 刷新视图
        try:
            context.view_layer.update()
        except Exception:
            pass
        if getattr(bpy.context, "screen", None):
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    except Exception as e:
        print(f"实时更新正交比例失败: {e}")

# ----------------------------
# 通用工具函数
# ----------------------------
def _is_standardview_suffix(name: str) -> bool:
    """判断名称是否以标准视图后缀结尾。"""
    try:
        upper = name.upper()
        return upper.endswith(('X', 'X-', 'Y', 'Y-', 'Z', 'Z-', 'ISO45'))
    except Exception:
        return False

def _is_standardview_camera_of_target(obj: bpy.types.Object, target_object: bpy.types.Object) -> bool:
    """判断相机是否属于目标物体的标准视图相机（通过父子关系或约束）。"""
    try:
        if obj is None or obj.type != 'CAMERA':
            return False
        # 父子关系匹配 + 标准后缀
        if getattr(obj, 'parent', None) == target_object and _is_standardview_suffix(obj.name):
            return True
        # 或者存在 TRACK_TO 约束直指目标对象
        for c in obj.constraints:
            if c.type == 'TRACK_TO' and c.target == target_object:
                return True
        return False
    except Exception:
        return False

def _find_standardview_cameras_for_target(target_object: bpy.types.Object) -> list:
    """查找与目标物体相关联的标准视图相机（包含父子关系与TRACK_TO两种方式）。"""
    cameras = []
    try:
        for obj in bpy.data.objects:
            if _is_standardview_camera_of_target(obj, target_object):
                cameras.append(obj)
    except Exception:
        pass
    return cameras

def _find_all_objects_with_standardview_cameras() -> dict:
    """扫描场景中所有具有标准视图相机的对象，返回 {对象: [相机列表]} 的字典。"""
    objects_with_cameras = {}
    try:
        # 遍历所有对象，查找每个对象的标准视图相机
        for obj in bpy.data.objects:
            if obj.type == 'MESH':  # 只考虑网格对象
                cameras = _find_standardview_cameras_for_target(obj)
                if cameras:
                    objects_with_cameras[obj] = cameras
    except Exception:
        pass
    return objects_with_cameras

def _compute_look_at_euler(camera_location, target_location, up_vector=mathutils.Vector((0.0, 1.0, 0.0))):
    """计算使相机朝向目标位置的欧拉角。相机的本地 -Z 轴指向前方。"""
    try:
        cam_loc = mathutils.Vector(camera_location)
        tgt_loc = mathutils.Vector(target_location)
        forward = (tgt_loc - cam_loc)
        if forward.length <= 1e-9:
            return mathutils.Euler((0.0, 0.0, 0.0))
        forward.normalize()
        right = up_vector.cross(forward)
        if right.length <= 1e-9:
            up_vector = mathutils.Vector((0.0, 0.0, 1.0))
            right = up_vector.cross(forward)
        right.normalize()
        true_up = forward.cross(right)
        rot_mat = mathutils.Matrix(((right.x, true_up.x, -forward.x),
                                    (right.y, true_up.y, -forward.y),
                                    (right.z, true_up.z, -forward.z)))
        return rot_mat.to_euler()
    except Exception:
        return mathutils.Euler((0.0, 0.0, 0.0))

class CameraSnapshotSettings(PropertyGroup):
    """摄像机快照设置属性组"""
    
    # 正交比例设置
    ortho_scale: FloatProperty(
        name="正交比例",
        description="正交摄像机的缩放比例",
        default=20.0,
        min=0.1,
        max=1000.0,
        unit='LENGTH',
        update=_update_ortho_scale
    )
    
    # 快照输出路径
    snapshot_output_path: bpy.props.StringProperty(
        name="快照输出路径",
        description="摄像机快照保存的文件夹路径（请输入绝对路径，如：C:\\Users\\PC\\Desktop\\output）",
        default=""
    )
    
    # 环境贴图路径
    environment_map_path: bpy.props.StringProperty(
        name="环境贴图路径",
        description="环境贴图文件路径（支持.hdr, .exr, .png, .jpg等格式）",
        default="",
        maxlen=1024  # 增加最大长度以支持长路径
    )
    
    # 环境贴图强度
    environment_strength: FloatProperty(
        name="环境贴图强度",
        description="环境贴图的光照强度",
        default=1.0,
        min=0.0,
        max=10.0
    )

    # UI 折叠开关（仅用于在单一面板中模拟层级折叠）
    ui_expand_camera: bpy.props.BoolProperty(
        name="展开摄像机管理",
        description="展开/折叠 摄像机管理 区域",
        default=True,
    )
    ui_expand_render: bpy.props.BoolProperty(
        name="展开渲染设置",
        description="展开/折叠 渲染设置 区域",
        default=True,
    )

    # 渲染透明背景
    film_transparent: bpy.props.BoolProperty(
        name="透明背景",
        description="渲染使用透明背景（支持PNG/EXR等带Alpha格式）",
        default=True
    )
    
    # 自定义批注（覆盖整批渲染的 stamp_note）
    stamp_custom_note: bpy.props.StringProperty(
        name="批注文本",
        description="在渲染印章中显示的自定义批注文本（整批渲染统一使用）",
        default=""
    )
    
    # 动态相机设置（分辨率与正交比例联动）
    use_dynamic_resolution: bpy.props.BoolProperty(
        name="动态相机",
        description="根据对象尺寸为每个视图自动计算分辨率并匹配正交比例",
        default=True,
        update=_update_dynamic_resolution_settings
    )
    
    resolution_scale_factor: FloatProperty(
        name="缩放因子(像素/米)",
        description="将对象尺寸（米）转换为分辨率（像素）的缩放因子。如100表示1米=100像素",
        default=100.0,
        min=10.0,
        max=1000.0,
        update=_update_dynamic_resolution_settings
    )
    
    grid_gap_pixels: IntProperty(
        name="网格间距",
        description="六视图合成时图片之间的间距（像素）",
        default=20,
        min=0,
        max=200
    )
    
    auto_cleanup_cameras: bpy.props.BoolProperty(
        name="自动清理临时相机",
        description="渲染完成后自动删除为此次渲染临时创建的相机",
        default=True
    )
    
    # 正交比例偏移系数（留白控制）
    ortho_scale_offset: FloatProperty(
        name="正交比例偏移系数",
        description="正交比例的偏移系数，实际偏移值=系数×基础正交比例。正值增加留白，负值减少留白",
        default=0.0,
        min=-1.0,
        max=2.0,
        precision=3
    )
    
    # 动态对象展开状态存储（用字符串存储对象名称列表）
    expanded_objects: bpy.props.StringProperty(
        name="展开的对象",
        description="内部使用：存储相机清单中展开的对象名称",
        default=""
    )
    
class VIEW3D_OT_create_ortho_cameras(Operator):
    """创建正交摄像机（含六个轴向与一个45°轴测）"""
    bl_idname = "view3d.create_ortho_cameras"
    bl_label = "创建正交摄像机"
    bl_description = "在选中物体原点创建七个正交摄像机（XYZ、-XYZ与轴测45°）"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行创建六个正交摄像机"""
        settings = context.scene.camera_snapshot_settings
        
        # 检查是否有选中的物体
        if not context.selected_objects:
            self.report({'ERROR'}, "请先选择一个物体")
            return {'CANCELLED'}
        
        # 只支持单选：多选时报错
        if len(context.selected_objects) > 1:
            self.report({'ERROR'}, "请只选择一个物体")
            return {'CANCELLED'}
        
        # 获取选中的物体
        target_object = context.selected_objects[0]
        target_location = target_object.location.copy()
        distance = 50.0  # 固定距离50米
        # 动态计算统一正交比例（与渲染阶段一致逻辑）
        dynamic_ortho_scale, _dyn_aspect = _compute_dynamic_scale_and_aspect(target_object, margin=1.03)
        
        # 使用选中物体的局部坐标轴（仅旋转，不含缩放和平移）定义方向
        rot3 = target_object.matrix_world.to_quaternion().to_matrix()
        local_dirs = [
            (mathutils.Vector((1, 0, 0)), "X"),
            (mathutils.Vector((-1, 0, 0)), "X-"),
            (mathutils.Vector((0, 1, 0)), "Y"),
            (mathutils.Vector((0, -1, 0)), "Y-"),
            (mathutils.Vector((0, 0, 1)), "Z"),
            (mathutils.Vector((0, 0, -1)), "Z-"),
            # 轴测方向：位于本地 +X 与 +Y 中间，并沿 +Z 抬升 45°
            (mathutils.Vector((0.5, 0.5, 0.70710678)), "ISO45"),
        ]
        directions = [(rot3 @ v, name) for v, name in local_dirs]

        # 视图标签映射（写入到相机数据自定义属性）
        axis_label_map = {
            "X": "主视图 +x",
            "X-": "后视图 -x",
            "Y": "右视图 +y",
            "Y-": "左视图 -y",
            "Z": "俯视图 +z",
            "Z-": "仰视图 -z",
            "ISO45": "轴测图 45°",
        }
        
        created_cameras = []
        
        try:
            for direction, axis_name in directions:
                # 创建摄像机
                camera_data = bpy.data.cameras.new(name=f"{target_object.name}{axis_name}")
                camera_obj = bpy.data.objects.new(f"{target_object.name}{axis_name}", camera_data)

                # 自定义字符串属性写入到相机数据（object.data）
                try:
                    camera_data["af_view_label"] = axis_label_map.get(axis_name, axis_name)
                except Exception:
                    pass
                
                # 设置摄像机位置：沿物体局部轴（转到世界后）退后固定距离
                camera_obj.location = target_location + direction.normalized() * distance
                
                # 设置摄像机为正交投影
                camera_data.type = 'ORTHO'
                camera_data.ortho_scale = dynamic_ortho_scale  # 动态正交缩放（与渲染阶段统一）
                
                # 将摄像机添加到与目标物体相同的集合（图层）
                linked_to_any_collection = False
                try:
                    for col in getattr(target_object, "users_collection", []) or []:
                        try:
                            col.objects.link(camera_obj)
                            linked_to_any_collection = True
                        except Exception:
                            pass
                except Exception:
                    pass
                if not linked_to_any_collection:
                    # 兜底：若目标物体不在任何集合（极少见），则链接到场景根集合
                    try:
                        context.scene.collection.objects.link(camera_obj)
                    except Exception:
                        pass

                # 设为选中物体的子物体（保持世界变换不变）
                try:
                    camera_obj.parent = target_object
                    camera_obj.matrix_parent_inverse = target_object.matrix_world.inverted()
                except Exception as _e:
                    pass
                
                # 添加朝向：除Z/Z-相机外，使用TRACK_TO；Z/Z-仅设置朝向旋转，不添加约束
                if axis_name.startswith('Z'):
                    try:
                        # 使用目标物体的本地 Y 轴作为相机的上方向，确保相机右轴对齐本地 X、上轴对齐本地 Y，
                        # 这样 Z 视图的横/纵与对象 X/Y 严格一致，实现零留白自适应。
                        local_up_world = rot3 @ mathutils.Vector((0.0, 1.0, 0.0))
                        camera_obj.rotation_euler = _compute_look_at_euler(
                            camera_obj.location, target_location, up_vector=local_up_world
                        )
                    except Exception:
                        pass
                else:
                    track_constraint = camera_obj.constraints.new(type='TRACK_TO')
                    track_constraint.target = target_object
                    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
                    track_constraint.up_axis = 'UP_Y'
                
                created_cameras.append(camera_obj)
            
            # 选择所有创建的摄像机
            bpy.ops.object.select_all(action='DESELECT')
            for camera in created_cameras:
                camera.select_set(True)
            context.view_layer.objects.active = created_cameras[0]
            
            created_count = len(created_cameras)
            self.report({'INFO'}, f"已创建{created_count}个正交摄像机，距离: {distance}")
            
        except Exception as e:
            self.report({'ERROR'}, f"创建摄像机失败: {str(e)}")
            print(f"创建摄像机错误: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class VIEW3D_OT_delete_ortho_cameras(Operator):
    """删除所有正交摄像机"""
    bl_idname = "view3d.delete_ortho_cameras"
    bl_label = "删除正交摄像机"
    bl_description = "删除所有约束到选定物体的正交摄像机"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """删除所有正交摄像机"""
        # 检查是否有选中的物体
        if not context.selected_objects:
            self.report({'ERROR'}, "请先选择一个物体")
            return {'CANCELLED'}
        
        # 检查是否只选择了一个物体
        if len(context.selected_objects) > 1:
            self.report({'ERROR'}, "请只选择一个物体")
            return {'CANCELLED'}
        
        target_object = context.selected_objects[0]
        
        try:
            # 查找与目标物体相关的标准视图相机（包含：TRACK_TO 或 父子关系）
            cameras_to_delete = []

            for obj in bpy.data.objects:
                if _is_standardview_camera_of_target(obj, target_object):
                    cameras_to_delete.append(obj)
            
            if not cameras_to_delete:
                self.report({'INFO'}, f"未找到约束到物体 '{target_object.name}' 的摄像机")
                return {'FINISHED'}
            
            # 直接通过数据 API 删除，避免视图层选择限制
            deleted = 0
            for camera_obj in cameras_to_delete:
                try:
                    camera_data = camera_obj.data if hasattr(camera_obj, 'data') else None
                    bpy.data.objects.remove(camera_obj, do_unlink=True)
                    if camera_data and getattr(camera_data, 'users', 1) == 0:
                        bpy.data.cameras.remove(camera_data)
                    deleted += 1
                except Exception as _e:
                    # 忽略单个删除失败，继续
                    pass

            self.report({'INFO'}, f"已删除 {deleted} 个标准视图摄像机")
                
        except Exception as e:
            self.report({'ERROR'}, f"删除摄像机失败: {str(e)}")
            print(f"删除摄像机错误: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class VIEW3D_OT_browse_environment_path(Operator):
    """浏览环境贴图文件"""
    bl_idname = "view3d.browse_environment_path"
    bl_label = "浏览环境贴图"
    bl_description = "选择环境贴图文件"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="文件路径",
        description="环境贴图文件路径",
        default="",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.hdr;*.exr;*.png;*.jpg;*.jpeg;*.tiff;*.tga",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        """设置环境贴图路径"""
        settings = context.scene.camera_snapshot_settings
        settings.environment_map_path = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """打开文件浏览对话框"""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VIEW3D_OT_browse_output_path(Operator):
    """浏览输出目录"""
    bl_idname = "view3d.browse_output_path"
    bl_label = "浏览输出目录"
    bl_description = "选择快照输出目录"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: bpy.props.StringProperty(
        name="目录路径",
        description="输出目录路径",
        default="",
        subtype='DIR_PATH'
    )
    
    def execute(self, context):
        """设置输出路径"""
        settings = context.scene.camera_snapshot_settings
        settings.snapshot_output_path = self.directory
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """打开目录浏览对话框"""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VIEW3D_OT_toggle_object_cameras(Operator):
    """切换对象相机清单的展开/折叠状态"""
    bl_idname = "view3d.toggle_object_cameras"
    bl_label = "切换对象相机显示"
    bl_description = "展开或折叠指定对象的相机清单"
    bl_options = {'REGISTER'}

    object_name: bpy.props.StringProperty(name="对象名称", default="")

    def execute(self, context):
        settings = context.scene.camera_snapshot_settings
        expanded_list = settings.expanded_objects.split(",") if settings.expanded_objects else []
        
        if self.object_name in expanded_list:
            # 从展开列表中移除
            expanded_list.remove(self.object_name)
        else:
            # 添加到展开列表
            expanded_list.append(self.object_name)
        
        # 更新展开状态
        settings.expanded_objects = ",".join(expanded_list)
        return {'FINISHED'}

class VIEW3D_OT_activate_camera_and_apply_res(Operator):
    """切换活动视图为指定相机，并按规则应用对应分辨率"""
    bl_idname = "view3d.activate_camera_and_apply_res"
    bl_label = "切到该相机并应用分辨率"
    bl_description = "切换到该相机视图，并将全局输出分辨率调整为此相机的计划值"
    bl_options = {'REGISTER', 'UNDO'}

    camera_name: bpy.props.StringProperty(name="相机名称", default="")
    preview_render_visibility: bpy.props.BoolProperty(
        name="按渲染可见集预览",
        description="仅显示本体/或ISO含子物体的集合以对齐渲染预览",
        default=False,
    )

    def execute(self, context):
        try:
            cam = bpy.data.objects.get(self.camera_name)
            if cam is None or cam.type != 'CAMERA':
                self.report({'ERROR'}, f"未找到相机: {self.camera_name}")
                return {'CANCELLED'}

            settings = context.scene.camera_snapshot_settings

            # 推断目标对象：优先 TRACK_TO 目标，其次父对象，最后当前单选对象
            target_object = None
            try:
                for c in getattr(cam, 'constraints', []) or []:
                    if c.type == 'TRACK_TO' and getattr(c, 'target', None) is not None:
                        target_object = c.target
                        break
            except Exception:
                pass
            if target_object is None:
                target_object = getattr(cam, 'parent', None)
            if target_object is None and getattr(context, 'selected_objects', None) and len(context.selected_objects) == 1:
                target_object = context.selected_objects[0]

            # 计算对应分辨率
            axis = _infer_axis_from_camera_name(cam.name)
            res_x = int(context.scene.render.resolution_x)
            res_y = int(context.scene.render.resolution_y)
            if getattr(settings, 'use_dynamic_resolution', False) and target_object is not None:
                if axis == 'ISO45':
                    res_x, res_y = 2000, 2000
                else:
                    try:
                        rx, ry, _ = _compute_view_specific_resolution(target_object, axis, settings.resolution_scale_factor)
                        res_x, res_y = int(rx), int(ry)
                    except Exception:
                        pass

            # 应用分辨率
            context.scene.render.resolution_x = res_x
            context.scene.render.resolution_y = res_y

            # 计算并应用正交比例（带微小安全边距，避免擦边）
            try:
                aspect = float(res_x) / max(1.0, float(res_y))
                if getattr(getattr(cam, 'data', None), 'type', None) == 'ORTHO' and target_object is not None:
                    ortho = _compute_ortho_scale_from_camera(target_object, cam, aspect_ratio=aspect, margin=1.005, scene=context.scene)
                    cam.data.ortho_scale = ortho
            except Exception:
                pass

            # 设置场景相机
            context.scene.camera = cam

            # 可选：按渲染可见集预览（仅本体，ISO含子物体）
            saved_hide = None
            if self.preview_render_visibility and target_object is not None:
                try:
                    include_children = cam.name.endswith("ISO45")
                    allowed = {target_object}
                    if include_children:
                        allowed |= _collect_descendants(target_object)
                    saved_hide = {obj.name: bool(getattr(obj, 'hide_viewport', False)) for obj in bpy.data.objects}
                    for obj in bpy.data.objects:
                        if obj.type == 'CAMERA' or obj in allowed:
                            obj.hide_viewport = False
                        else:
                            obj.hide_viewport = True
                except Exception:
                    saved_hide = None

            # 切换活动视图到相机视角，并绑定到该相机
            try:
                if getattr(context, 'screen', None):
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            for space in area.spaces:
                                if space.type == 'VIEW_3D':
                                    space.camera = cam
                                    region_3d = getattr(space, 'region_3d', None)
                                    if region_3d:
                                        region_3d.view_perspective = 'CAMERA'
                            area.tag_redraw()
                            break
            except Exception:
                pass

            # 刷新依赖图
            try:
                context.view_layer.update()
            except Exception:
                pass

            self.report({'INFO'}, f"已切换到 {cam.name}，分辨率 {res_x}x{res_y}")
            return {'FINISHED'}
        except Exception as e:
            # 恢复可见集
            try:
                if saved_hide is not None:
                    for name, val in saved_hide.items():
                        o = bpy.data.objects.get(name)
                        if o is not None:
                            o.hide_viewport = val
            except Exception:
                pass
            self.report({'ERROR'}, f"切换失败: {str(e)}")
            return {'CANCELLED'}

def setup_environment_map_safe(context, settings):
    """使用临时 World 设置环境贴图，返回创建的临时 World；失败或未设置且找不到默认资源时返回 None"""
    if not settings.environment_map_path:
        # 未选择环境贴图时，尝试自动使用 Blender 自带的 forest.exr
        try:
            default_env = _get_default_forest_exr_path()
            if default_env:
                settings.environment_map_path = default_env
                print(f"未选择HDRI，自动使用默认环境贴图: {default_env}")
            else:
                return None
        except Exception:
            return None

    try:
        import os
        env_path = settings.environment_map_path.strip()

        print(f"使用环境贴图路径: {env_path}")
        if not os.path.exists(env_path):
            print(f"环境贴图文件不存在: {env_path}")
            return None

        temp_world = bpy.data.worlds.new("AF_TempEnv")
        temp_world.use_nodes = True
        nodes = temp_world.node_tree.nodes
        links = temp_world.node_tree.links
        nodes.clear()

        env_tex_node = nodes.new(type='ShaderNodeTexEnvironment')
        env_tex_node.location = (-300, 300)
        background_node = nodes.new(type='ShaderNodeBackground')
        background_node.location = (0, 300)
        background_node.inputs['Strength'].default_value = settings.environment_strength
        output_node = nodes.new(type='ShaderNodeOutputWorld')
        output_node.location = (300, 300)

        env_tex_node.image = bpy.data.images.load(env_path, check_existing=True)
        links.new(env_tex_node.outputs['Color'], background_node.inputs['Color'])
        links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

        # 切换到临时世界
        context.scene.world = temp_world
        print(f"环境贴图临时世界已设置: {temp_world.name}")
        return temp_world

    except Exception as e:
        print(f"设置环境贴图（临时世界）失败: {e}")
        return None

def restore_environment_map_safe(context, original_world, temp_world):
    """恢复原始 World，并尝试清理临时 World"""
    try:
        context.scene.world = original_world
        print("环境设置已恢复")
    except Exception as e:
        print(f"恢复环境设置失败: {e}")

    try:
        if temp_world and temp_world.users == 0:
            bpy.data.worlds.remove(temp_world)
            print("已清理临时环境世界")
    except Exception as e:
        print(f"清理临时环境世界失败: {e}")

def _collect_descendants(root_obj: bpy.types.Object) -> set:
    """递归收集 root_obj 的所有子物体（含多层级）。"""
    descendants = set()
    try:
        def dfs(o):
            for child in getattr(o, 'children', []):
                if child not in descendants:
                    descendants.add(child)
                    dfs(child)
        dfs(root_obj)
    except Exception:
        pass
    return descendants

def _get_default_forest_exr_path() -> str:
    """返回 Blender 资源目录中的默认 HDRI 'forest.exr' 绝对路径，找不到返回空串。"""
    try:
        import os
        # 优先通过 Blender 的资源目录定位（USER/LOCAL/SYSTEM）
        for key in ("USER", "LOCAL", "SYSTEM"):
            base = ""
            try:
                base = bpy.utils.resource_path(key)
            except Exception:
                base = ""
            if base:
                candidate = os.path.join(base, "datafiles", "studiolights", "world", "forest.exr")
                if os.path.exists(candidate):
                    return os.path.abspath(candidate)

        # 兜底：基于二进制路径向上查找常见结构
        try:
            bin_dir = os.path.dirname(getattr(bpy.app, "binary_path", "") or "")
            for up in (bin_dir, os.path.dirname(bin_dir), os.path.dirname(os.path.dirname(bin_dir))):
                if not up:
                    continue
                candidate = os.path.join(up, "datafiles", "studiolights", "world", "forest.exr")
                if os.path.exists(candidate):
                    return os.path.abspath(candidate)
        except Exception:
            pass
    except Exception:
        pass
    return ""

def _get_default_snapshot_dir() -> str:
    """返回默认的快照输出目录（.blend 同目录的 snapshots，未保存文件则桌面/snapshots）。"""
    try:
        import os
        if bpy.data.filepath:
            base_dir = os.path.dirname(bpy.data.filepath)
        else:
            base_dir = os.path.expanduser("~/Desktop")
        return os.path.join(base_dir, "snapshots")
    except Exception:
        return ""

def _ensure_snapshot_output_default(scene: bpy.types.Scene) -> None:
    """为空时为场景写入默认的快照输出目录。"""
    try:
        settings = getattr(scene, "camera_snapshot_settings", None)
        if settings is None:
            return
        if not getattr(settings, "snapshot_output_path", ""):
            default_dir = _get_default_snapshot_dir() or ""
            if default_dir:
                settings.snapshot_output_path = default_dir
    except Exception:
        pass

_af_handlers = {"load_post": None}

def _ensure_stamp_note_default(context: bpy.types.Context) -> None:
    """当批注文本为空时，自动从选中物体或其 data 的自定义属性 'data' 中提取字符串填入。"""
    try:
        if context is None:
            return
        scene = getattr(context, "scene", None)
        if scene is None:
            return
        settings = getattr(scene, "camera_snapshot_settings", None)
        if settings is None:
            return
        current = (getattr(settings, "stamp_custom_note", "") or "").strip()
        if current:
            return
        selected = getattr(context, "selected_objects", None) or []
        if len(selected) != 1:
            return
        obj = selected[0]

        def _to_text(val) -> str:
            if isinstance(val, str):
                return val
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8', 'ignore')
                except Exception:
                    return str(val)
            return str(val)

        def _get_data_prop(container) -> str:
            try:
                if container is None:
                    return ""
                # Blender ID 自定义属性接口
                if hasattr(container, 'keys') and callable(container.keys):
                    if 'data' in container.keys():
                        return _to_text(container.get('data'))
            except Exception:
                return ""
            return ""

        # 优先从对象本身取，其次从对象的数据块（如 Mesh）上取
        note_text = _get_data_prop(obj)
        if not note_text.strip():
            note_text = _get_data_prop(getattr(obj, 'data', None))

        if note_text.strip():
            settings.stamp_custom_note = note_text.strip()
    except Exception:
        pass

# ----------------------------
# 动态正交比例计算
# ----------------------------
def _compute_dynamic_ortho_scale(obj: bpy.types.Object, scene: bpy.types.Scene, margin: float = 1.12) -> float:
    """
    基于对象尺寸计算统一正交比例（视口宽度）。与分辨率无关，仅返回 width。
    内部复用 _compute_dynamic_scale_and_aspect，保证与渲染阶段一致。
    """
    try:
        scale, _aspect = _compute_dynamic_scale_and_aspect(obj, margin=margin)
        return float(scale)
    except Exception:
        return float(getattr(scene.camera_snapshot_settings, "ortho_scale", 20.0))

# ----------------------------
# 动态统一：正交比例 + 输出纵横比/分辨率
# ----------------------------
def _compute_dynamic_scale_and_aspect(obj: bpy.types.Object, margin: float = 1.03) -> tuple:
    """
    基础版动态正交比例计算：为向后兼容保留，现在主要用于UI显示。
    返回 (scale, aspect)。
    """
    try:
        dims = getattr(obj, "dimensions", None)
        if dims is None:
            return 20.0, 16.0 / 9.0

        x = max(float(dims.x), 0.01)
        y = max(float(dims.y), 0.01)
        z = max(float(dims.z), 0.01)

        # 简化计算：取最大的两个尺寸作为基础
        dims_sorted = sorted([x, y, z], reverse=True)
        max_dim = dims_sorted[0]
        second_dim = dims_sorted[1]
        
        # 正交比例 = 最大尺寸 * 安全系数
        scale = max_dim * margin
        aspect = max_dim / second_dim
        
        # 确保合理范围
        scale = max(1.0, min(scale, 500.0))
        aspect = max(0.5, min(aspect, 5.0))

        return float(scale), float(aspect)
    except Exception:
        return 20.0, 16.0 / 9.0

# ----------------------------
# 基于相机姿态的精确正交比例（防裁切）
# ----------------------------
def _compute_ortho_scale_from_camera(
    obj: bpy.types.Object,
    camera_obj: bpy.types.Object,
    aspect_ratio: float,
    margin: float = 1.0,
    scene: bpy.types.Scene = None,
) -> float:
    """
    基于对象尺寸和相机轴向直接计算正交比例：
    - X轴向相机：使用对象Z、Y尺寸中的最大值
    - Y轴向相机：使用对象Z、X尺寸中的最大值  
    - Z轴向相机：使用对象X、Y尺寸中的最大值
    - aspect_ratio: res_x / res_y
    - scene: 场景对象，用于获取正交比例偏移设置
    - 返回值：所需的 ortho_scale（宽度，世界单位）
    """
    try:
        if obj is None or camera_obj is None:
            return 20.0
            
        # 获取对象尺寸
        dims = getattr(obj, "dimensions", None)
        if dims is None:
            return 20.0
            
        x_dim = max(float(dims.x), 0.01)
        y_dim = max(float(dims.y), 0.01)
        z_dim = max(float(dims.z), 0.01)
        
        # 推断相机轴向
        axis = _infer_axis_from_camera_name(camera_obj.name)
        
        if axis.startswith('X'):
            # X轴向相机：使用对象Z、Y尺寸中的最大值
            base_ortho_scale = max(z_dim, y_dim) * margin
        elif axis.startswith('Y'):
            # Y轴向相机：使用对象Z、X尺寸中的最大值
            base_ortho_scale = max(z_dim, x_dim) * margin
        elif axis.startswith('Z'):
            # Z轴向相机：使用对象X、Y尺寸中的最大值
            base_ortho_scale = max(x_dim, y_dim) * margin
        elif axis == 'ISO45':
            # ISO45轴测：使用最大尺寸
            base_ortho_scale = max(x_dim, y_dim, z_dim) * margin
        else:
            # 默认情况：使用最大尺寸
            base_ortho_scale = max(x_dim, y_dim, z_dim) * margin
        
        # 应用正交比例偏移系数（留白控制）
        offset_factor = 0.0
        if scene and hasattr(scene, 'camera_snapshot_settings'):
            offset_factor = getattr(scene.camera_snapshot_settings, 'ortho_scale_offset', 0.0)
        
        # 实际偏移值 = 系数 × 基础正交比例
        actual_offset = offset_factor * base_ortho_scale
        final_ortho_scale = base_ortho_scale + actual_offset
        
        return float(max(1.0, min(final_ortho_scale, 5000.0)))
        
    except Exception as e:
        print(f"计算正交比例失败: {e}")
        return 20.0

def _compute_view_specific_resolution(obj: bpy.types.Object, view_axis: str, scale_factor: float = 100.0) -> tuple:
    """
    根据视图方向和对象XYZ尺寸动态计算特定视图的分辨率。
    
    规则：
    - X轴视图（看向X方向）: 分辨率比例 = Y:Z，分辨率值直接基于尺寸
    - Y轴视图（看向Y方向）: 分辨率比例 = X:Z，分辨率值直接基于尺寸  
    - Z轴视图（看向Z方向）: 分辨率X=物体X尺寸，分辨率Y=物体Y尺寸
    
    Args:
        obj: 目标对象
        view_axis: 视图轴向 ('X', 'X-', 'Y', 'Y-', 'Z', 'Z-')
        scale_factor: 缩放因子，将米转换为像素（默认100，即1米=100像素）
        
    Returns:
        tuple: (resolution_x, resolution_y, aspect_ratio)
    """
    try:
        dims = getattr(obj, "dimensions", None)
        if dims is None:
            return 1920, 1080, 16.0/9.0
            
        x = max(float(dims.x), 0.01)  # 避免除零，最小1cm
        y = max(float(dims.y), 0.01)
        z = max(float(dims.z), 0.01)
        
        # 根据视图方向确定分辨率尺寸（米）
        if view_axis.startswith('X'):
            # X轴视图：X方向=Y尺寸，Y方向=Z尺寸
            dim_x, dim_y = y, z
        elif view_axis.startswith('Y'):
            # Y轴视图：X方向=X尺寸，Y方向=Z尺寸
            dim_x, dim_y = x, z
        elif view_axis.startswith('Z'):
            # Z轴视图：映射 X尺寸→分辨率X，Y尺寸→分辨率Y（直映射）
            dim_x, dim_y = x, y
            # print(f"Z轴视图分辨率映射: X({x:.2f})→分辨率X, Y({y:.2f})→分辨率Y")  # 注释掉重复调试
        else:
            # 默认情况
            dim_x, dim_y = x, y
            
        # 直接将尺寸转换为分辨率（米 × 缩放因子 = 像素）
        res_x = int(dim_x * scale_factor)
        res_y = int(dim_y * scale_factor)
        
        # 确保分辨率为偶数且不小于最小值
        res_x = max(256, res_x + (res_x % 2))
        res_y = max(256, res_y + (res_y % 2))
        
        # 计算纵横比
        aspect_ratio = dim_x / dim_y
        
        # print(f"视图 {view_axis}: 最终分辨率 {res_x}x{res_y}, 纵横比 {aspect_ratio:.3f}")  # 注释掉重复调试
        return int(res_x), int(res_y), float(aspect_ratio)
        
    except Exception as e:
        print(f"视图特定分辨率计算失败: {e}")
        return 1920, 1080, 16.0/9.0

def _compute_dynamic_resolution(obj: bpy.types.Object, scale_factor: float = 100.0, margin: float = 1.03) -> tuple:
    """
    计算所有视图的分辨率信息（用于UI显示）。
    返回一个包含所有视图分辨率的统计信息。
    
    Args:
        obj: 目标对象
        scale_factor: 缩放因子（米到像素的转换比例）
        margin: 边距系数（暂未使用）
        
    Returns:
        tuple: (avg_resolution_x, avg_resolution_y, avg_aspect_ratio)
    """
    try:
        # 计算各个视图的分辨率
        view_axes = ['X', 'Y', 'Z']
        resolutions = []
        
        for axis in view_axes:
            res_x, res_y, aspect = _compute_view_specific_resolution(obj, axis, scale_factor)
            resolutions.append((res_x, res_y, aspect))
            
        # 计算平均值（用于UI显示）
        avg_x = sum(r[0] for r in resolutions) // len(resolutions)
        avg_y = sum(r[1] for r in resolutions) // len(resolutions)
        avg_aspect = sum(r[2] for r in resolutions) / len(resolutions)
        
        return avg_x, avg_y, avg_aspect
        
    except Exception as e:
        print(f"动态分辨率计算失败: {e}")
        return 1920, 1080, 16.0/9.0



def _cleanup_auto_created_cameras(auto_created_cameras: list):
    """清理自动创建的临时相机"""
    if not auto_created_cameras:
        return
        
    try:
        deleted_count = 0
        for camera_obj in auto_created_cameras:
            try:
                if camera_obj and camera_obj.name in bpy.data.objects:
                    camera_data = camera_obj.data if hasattr(camera_obj, 'data') else None
                    print(f"清理自动创建的相机: {camera_obj.name}")
                    
                    # 删除相机对象
                    bpy.data.objects.remove(camera_obj, do_unlink=True)
                    
                    # 删除相机数据（如果没有其他用户）
                    if camera_data and getattr(camera_data, 'users', 1) == 0:
                        bpy.data.cameras.remove(camera_data)
                    
                    deleted_count += 1
            except Exception as e:
                print(f"清理相机失败: {e}")
                continue

        if deleted_count > 0:
            print(f"已清理 {deleted_count} 个自动创建的临时相机")
            
    except Exception as e:
        print(f"清理自动创建相机时发生错误: {e}")

# ----------------------------
# 基于实际相机姿态的统一比例/纵横比计算（最准确）
# ----------------------------
def _infer_axis_from_camera_name(camera_name: str) -> str:
    """
    从相机名称推断视图轴向。
    
    Args:
        camera_name: 相机名称，如 "SuzanneX", "CubeY-", "ObjectISO45"
        
    Returns:
        str: 轴向标识 ('X', 'X-', 'Y', 'Y-', 'Z', 'Z-', 'ISO45')
    """
    try:
        name = camera_name.upper()
        if 'ISO45' in name:
            return 'ISO45'
        elif name.endswith('X-'):
            return 'X-'
        elif name.endswith('X'):
            return 'X'
        elif name.endswith('Y-'):
            return 'Y-'
        elif name.endswith('Y'):
            return 'Y'
        elif name.endswith('Z-'):
            return 'Z-'
        elif name.endswith('Z'):
            return 'Z'
        else:
            return 'X'  # 默认返回X轴
    except Exception:
        return 'X'

            

def _compose_six_view_grid_pillow(
    image_paths: list,
    out_png_path: str,
    cols: int = 3,
    rows: int = 2,
    gap_px: int = 20,  # 默认20像素间距避免重叠
    background_rgba=(0, 0, 0, 0),
    stamp_text: str = "",
    margin_px: int = 16,
) -> str:
    """使用 Pillow 将不同尺寸的图片按网格合成，保持原始分辨率，仅进行对齐操作。返回输出路径。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os

        assert len(image_paths) == cols * rows, "合成网格的图片数量必须等于 cols*rows"

        # 打开所有图片
        opened_images = [Image.open(os.path.abspath(p)).convert("RGBA") for p in image_paths]
        
        # 计算每行每列的最大尺寸，用于确定网格单元大小
        max_col_widths = [0] * cols
        max_row_heights = [0] * rows
        
        for idx, img in enumerate(opened_images):
            col = idx % cols
            row = idx // cols
            w, h = img.size
            max_col_widths[col] = max(max_col_widths[col], w)
            max_row_heights[row] = max(max_row_heights[row], h)
        
        print(f"网格列宽: {max_col_widths}")
        print(f"网格行高: {max_row_heights}")
        
        # 计算画布总尺寸
        canvas_w = sum(max_col_widths) + (cols - 1) * gap_px
        canvas_h = sum(max_row_heights) + (rows - 1) * gap_px
        
        # 创建画布
        out_img = Image.new("RGBA", (canvas_w, canvas_h), background_rgba)
        
        # 计算每个网格位置的起始坐标
        col_starts = [0]
        for w in max_col_widths[:-1]:
            col_starts.append(col_starts[-1] + w + gap_px)
            
        row_starts = [0]
        for h in max_row_heights[:-1]:
            row_starts.append(row_starts[-1] + h + gap_px)
        
        # 放置每张图片（原始尺寸，中心对齐）
        for idx, img in enumerate(opened_images):
            col = idx % cols
            row = idx // cols
            w, h = img.size
            
            # 计算该网格单元的中心对齐位置
            cell_x = col_starts[col]
            cell_y = row_starts[row]
            cell_w = max_col_widths[col]
            cell_h = max_row_heights[row]
            
            # 在单元格内居中放置（保持原始尺寸）
            x = cell_x + (cell_w - w) // 2
            y = cell_y + (cell_h - h) // 2
            
            out_img.paste(img, (x, y), img)
            
            print(f"图片 {idx}: 原始尺寸{w}x{h}, 放置位置({x}, {y}), 网格单元({cell_x}, {cell_y}, {cell_w}x{cell_h})")

        # 在右下角叠加批注文本（若提供）
        if stamp_text:
            try:
                draw = ImageDraw.Draw(out_img)
                # 选择字体：优先中文字体，其次 Arial，最后 Pillow 默认字体
                font = None
                candidate_fonts = [
                    # 优先粗体字体
                    "C:/Windows/Fonts/msyhbd.ttc",   # 微软雅黑 粗体
                    "C:/Windows/Fonts/simhei.ttf",    # 黑体（较粗）
                    "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
                    # 退回常规字体
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/msyh.ttf",
                    "C:/Windows/Fonts/simsun.ttc",
                    "C:/Windows/Fonts/arial.ttf",
                ]
                # 字体大小相对画布较小边，并整体放大 8px，最大 36px
                base_size = max(14, min(36, int(min(canvas_w, canvas_h) * 0.025) + 8))
                for fp in candidate_fonts:
                    if os.path.exists(fp):
                        try:
                            font = ImageFont.truetype(fp, base_size)
                            break
                        except Exception:
                            pass
                if font is None:
                    font = ImageFont.load_default()

                # 计算文本大小并定位到右下角
                try:
                    bbox = draw.textbbox((0, 0), stamp_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                except Exception:
                    text_w, text_h = draw.textsize(stamp_text, font=font)

                tx = max(0, canvas_w - margin_px - text_w)
                ty = max(0, canvas_h - margin_px - text_h)

                # 文字描边（黑色）+ 正文（白色）
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    draw.text((tx + dx, ty + dy), stamp_text, font=font, fill=(0, 0, 0, 255))
                draw.text((tx, ty), stamp_text, font=font, fill=(255, 255, 255, 255))
            except Exception as _e:
                # 文本绘制失败不影响合成
                pass

        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(out_png_path)), exist_ok=True)
        out_img.save(out_png_path)
        return out_png_path
    except Exception as e:
        print(f"Pillow 合成失败: {e}")
        raise

def _compose_iso_left_of_grid_pillow(
    iso_image_path: str,
    grid_image_path: str,
    out_png_path: str,
    gap_px: int = 0,
    background_rgba=(0, 0, 0, 0),
) -> str:
    """将轴测图放在左侧、六视图总图放在右侧进行横向合成。
    轴测图按高度等比缩放至与六视图总图相同高度（即单图分辨率×2）。返回输出路径。
    """
    try:
        from PIL import Image
        import os

        iso_img = Image.open(os.path.abspath(iso_image_path)).convert("RGBA")
        grid_img = Image.open(os.path.abspath(grid_image_path)).convert("RGBA")

        right_w, right_h = grid_img.size
        left_w_raw, left_h_raw = iso_img.size
        if left_h_raw <= 0:
            raise ValueError("ISO 图像高度无效")

        scale = right_h / float(left_h_raw)
        left_w = max(1, int(round(left_w_raw * scale)))
        left_h = right_h
        iso_resized = iso_img.resize((left_w, left_h), Image.LANCZOS)

        canvas_w = left_w + gap_px + right_w
        canvas_h = right_h
        out_img = Image.new("RGBA", (canvas_w, canvas_h), background_rgba)
        out_img.paste(iso_resized, (0, 0), iso_resized)
        out_img.paste(grid_img, (left_w + gap_px, 0), grid_img)

        os.makedirs(os.path.dirname(os.path.abspath(out_png_path)), exist_ok=True)
        out_img.save(out_png_path)
        return out_png_path
    except Exception as e:
        print(f"Pillow 合成（轴测+六视图）失败: {e}")
        raise

def _compose_two_iso_and_grid_pillow(
    iso_with_children_path: str,
    iso_clean_path: str,
    grid_image_path: str,
    out_png_path: str,
    gap_px: int = 0,
    background_rgba=(0, 0, 0, 0),
) -> str:
    """将两张轴测图（左：含子物体，居中：不含子物体）与六视图总图（右）横向合成。
    两张轴测图按高度等比缩放至与六视图总图相同高度。返回输出路径。
    """
    try:
        from PIL import Image
        import os

        iso_with = Image.open(os.path.abspath(iso_with_children_path)).convert("RGBA")
        iso_clean = Image.open(os.path.abspath(iso_clean_path)).convert("RGBA")
        grid_img = Image.open(os.path.abspath(grid_image_path)).convert("RGBA")

        right_w, right_h = grid_img.size

        def _resize_to_h(img, target_h: int):
            w, h = img.size
            if h == target_h:
                return img
            # 等比缩放到目标高度（可能放大）；如要严格避免放大，可在此改为仅缩小策略
            scale = target_h / float(max(1, h))
            new_w = max(1, int(round(w * scale)))
            return img.resize((new_w, target_h), Image.LANCZOS)

        iso_with_r = _resize_to_h(iso_with, right_h)
        iso_clean_r = _resize_to_h(iso_clean, right_h)

        left_w1, _ = iso_with_r.size
        left_w2, _ = iso_clean_r.size

        canvas_w = left_w1 + gap_px + left_w2 + gap_px + right_w
        canvas_h = right_h
        out_img = Image.new("RGBA", (canvas_w, canvas_h), background_rgba)

        x = 0
        out_img.paste(iso_with_r, (x, 0), iso_with_r)
        x += left_w1 + gap_px
        out_img.paste(iso_clean_r, (x, 0), iso_clean_r)
        x += left_w2 + gap_px
        out_img.paste(grid_img, (x, 0), grid_img)

        os.makedirs(os.path.dirname(os.path.abspath(out_png_path)), exist_ok=True)
        out_img.save(out_png_path)
        return out_png_path
    except Exception as e:
        print(f"Pillow 合成（两轴测+六视图）失败: {e}")
        raise

def _pillow_draw_center_bottom_text(
    image_path: str,
    text: str,
    margin_px: int = 16,
    min_font_px: int = 14,
    max_font_px: int = 36,
) -> None:
    """在单张图片的底部居中绘制文本，并向上偏移一些。原地覆盖保存。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os

        img = Image.open(os.path.abspath(image_path)).convert("RGBA")
        W, H = img.size
        draw = ImageDraw.Draw(img)

        # 选择字体（优先中文字体）
        font = None
        candidate_fonts = [
            # 优先粗体字体
            "C:/Windows/Fonts/msyhbd.ttc",   # 微软雅黑 粗体
            "C:/Windows/Fonts/simhei.ttf",    # 黑体（较粗）
            "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
            # 退回常规字体
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyh.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ]
        # 放大 8px，并提升上限至 36px
        base_size = max(min_font_px, min(max_font_px, int(min(W, H) * 0.035) + 8))
        for fp in candidate_fonts:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, base_size)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        # 计算文本尺寸与位置
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = draw.textsize(text, font=font)

        x = max(0, int((W - text_w) / 2))
        # 在底边基础上再向上偏移，避免太贴边：offset 约为 3.0 倍字体大小，至少 32px
        upward_offset = max(30, int(base_size * 4.0))
        y = max(0, H - margin_px - upward_offset - text_h)

        # 文字描边（黑色）+ 正文（白色）
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

        img.save(image_path)
    except Exception as e:
        print(f"Pillow 单图标注失败: {e}")

class VIEW3D_OT_render_camera_snapshots(Operator):
    """渲染摄像机快照"""
    bl_idname = "view3d.render_camera_snapshots"
    bl_label = "渲染摄像机快照"
    bl_description = "为约束到选定物体的摄像机拍摄快照并保存"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行摄像机快照渲染"""
        settings = context.scene.camera_snapshot_settings
        # 确保默认快照输出路径在属性中被写入（与环境贴图默认逻辑一致）
        try:
            _ensure_snapshot_output_default(context.scene)
            _ensure_stamp_note_default(context)
        except Exception:
            pass
        
        # 检查是否有选中的物体
        if not context.selected_objects:
            self.report({'ERROR'}, "请先选择一个物体")
            return {'CANCELLED'}
        
        # 检查是否只选择了一个物体
        if len(context.selected_objects) > 1:
            self.report({'ERROR'}, "请只选择一个物体")
            return {'CANCELLED'}
        
        # 检查输出路径（与默认环境贴图逻辑保持一致：为空则写回属性并提示）
        output_path = settings.snapshot_output_path
        if not output_path:
            # 使用统一的默认路径助手
            output_path = _get_default_snapshot_dir()
            try:
                settings.snapshot_output_path = output_path
            except Exception:
                pass
            self.report({'INFO'}, f"使用默认路径: {output_path}")
        
        # 验证输出路径
        import os
        try:
            output_path_abs = output_path.strip()
            os.makedirs(output_path_abs, exist_ok=True)
            print(f"使用路径: {output_path_abs}")
        except Exception as e:
            self.report({'ERROR'}, f"输出路径无效: {str(e)}")
            return {'CANCELLED'}
        
        target_object = context.selected_objects[0]
        object_name = target_object.name
        
        # 查找目标物体的标准视图相机（兼容：TRACK_TO 约束和父子关系）
        cameras_to_render = _find_standardview_cameras_for_target(target_object)
        print(f"总共找到 {len(cameras_to_render)} 个标准视图摄像机")
        
        # 记录是否自动创建了相机，用于渲染完成后清理
        auto_created_cameras = []
        cameras_auto_created = False
        
        if not cameras_to_render:
            # 自动创建正交摄像机后重试
            try:
                print("未找到现有相机，开始自动创建...")
                bpy.ops.view3d.create_ortho_cameras()
                cameras_auto_created = True
                
                # 重新扫描并记录新创建的相机（同时兼容父子关系的Z/Z-相机）
                cameras_to_render = []
                for obj in bpy.data.objects:
                    if _is_standardview_camera_of_target(obj, target_object):
                        cameras_to_render.append(obj)
                        auto_created_cameras.append(obj)
                        print(f"自动创建后找到标准视图相机: {obj.name}")
            except Exception as _e:
                print(f"自动创建相机失败: {_e}")
                pass

            if not cameras_to_render:
                self.report({'ERROR'}, f"未找到TRACK TO约束到物体 '{object_name}' 的摄像机（已尝试自动创建但失败）")
                return {'CANCELLED'}
            else:
                self.report({'INFO'}, f"已自动创建 {len(auto_created_cameras)} 个正交摄像机并继续渲染")
        
        # 保存原始渲染设置
        original_camera = context.scene.camera
        original_render_engine = context.scene.render.engine
        original_resolution_x = context.scene.render.resolution_x
        original_resolution_y = context.scene.render.resolution_y
        original_filepath = context.scene.render.filepath
        original_world = context.scene.world
        temp_world = None
        original_film_transparent = context.scene.render.film_transparent
        # 保存原始渲染印章配置（所有常见的印章开关 + 样式）
        r = context.scene.render
        stamp_bool_names = [
            "use_stamp",
            "use_stamp_time",
            "use_stamp_date",
            "use_stamp_render_time",
            "use_stamp_frame",
            "use_stamp_scene",
            "use_stamp_memory",
            "use_stamp_hostname",
            "use_stamp_camera",
            "use_stamp_lens",
            "use_stamp_filename",
            "use_stamp_note",
            "use_stamp_sequencer_strip_meta",
            "use_stamp_strip_metadata",
        ]
        original_stamp = {"__bools__": {}, "__styles__": {}}
        for name in stamp_bool_names:
            if hasattr(r, name):
                original_stamp["__bools__"][name] = getattr(r, name)
        # 样式与文本
        original_stamp["__styles__"]["stamp_note_text"] = getattr(r, "stamp_note_text", "")
        if hasattr(r, "stamp_font_size"):
            original_stamp["__styles__"]["stamp_font_size"] = r.stamp_font_size
        if hasattr(r, "stamp_foreground"):
            original_stamp["__styles__"]["stamp_foreground"] = tuple(r.stamp_foreground)
        if hasattr(r, "stamp_background"):
            original_stamp["__styles__"]["stamp_background"] = tuple(r.stamp_background)
        
        # 记录所有对象的原始 hide_render 状态，便于渲染后恢复
        original_hide_render_map = {obj.name: bool(getattr(obj, "hide_render", False)) for obj in bpy.data.objects}
        
        rendered_count = 0
        
        try:
            # 设置环境贴图（临时 World）
            temp_world = setup_environment_map_safe(context, settings)
            if temp_world:
                print("环境贴图已设置（临时世界）")
            else:
                print("未设置环境贴图或设置失败（继续渲染）")

            # 计算基础信息用于显示（已简化，避免未定义函数引用）
            base_scale, dyn_aspect = _compute_dynamic_scale_and_aspect(
                target_object,
                margin=1.03,
            )

            # 应用动态相机设置（每个相机有独立分辨率/正交比例）
            print(f"动态相机检查: use_dynamic_resolution = {settings.use_dynamic_resolution}")
            if settings.use_dynamic_resolution:
                print(f"启用动态相机: 对象={target_object.name}, 缩放因子={settings.resolution_scale_factor}")
                print("注意：每个相机会使用其视图特定的分辨率与正交比例")
            else:
                print(f"使用固定分辨率: {context.scene.render.resolution_x}x{context.scene.render.resolution_y}")
            
            print(f"统一纵横比(仅报告): {dyn_aspect:.4f}")
            
            # 根据设置开启/关闭透明背景
            context.scene.render.film_transparent = settings.film_transparent

            # 配置渲染印章：按需完全关闭（在 Pillow 合成阶段叠加批注文本）
            try:
                if hasattr(r, "use_stamp"):
                    r.use_stamp = False
                if hasattr(r, "use_stamp_camera"):
                    r.use_stamp_camera = False
                if hasattr(r, "use_stamp_note"):
                    r.use_stamp_note = False
            except Exception:
                pass

            # 预先收集子物体集合，供不同相机按需选择
            descendants_set = _collect_descendants(target_object)
            
            rendered_outputs = []  # (camera_name, filepath)

            for camera_obj in cameras_to_render:
                print(f"\n开始处理摄像机: {camera_obj.name}")
                
                # 逐相机控制可见集：
                # - 六视图：仅渲染选中物体本体（不含子物体）
                # - 轴测图 ISO45：渲染选中物体及其所有子物体
                try:
                    include_children = camera_obj.name.endswith("ISO45")
                    allowed_set = {target_object} | (descendants_set if include_children else set())
                    for obj in bpy.data.objects:
                        try:
                            if obj.type == 'CAMERA' or obj in allowed_set:
                                obj.hide_render = False
                            else:
                                obj.hide_render = True
                        except Exception:
                            pass
                except Exception:
                    pass

                # 设置当前摄像机为渲染摄像机
                context.scene.camera = camera_obj
                context.view_layer.update()
                
                # 生成文件名
                filename = f"{camera_obj.name}.png"
                filepath = os.path.join(output_path_abs, filename)
                
                print(f"正在渲染到: {filepath}")
                
                # 按全局设置使用渲染引擎（不再改动，引擎在操作开始时已记录）
                render_engine = original_render_engine
                context.scene.render.engine = render_engine
                context.scene.render.filepath = filepath
                
                # 应用每个视图特定的动态相机分辨率
                if settings.use_dynamic_resolution:
                    try:
                        # ISO45 也参与动态相机：使用对象最大边作为正方形边
                        if camera_obj.name.endswith("ISO45"):
                            dims = getattr(target_object, 'dimensions', None)
                            if dims is not None:
                                max_edge = max(float(dims.x), float(dims.y), float(dims.z))
                                side = int(max_edge * settings.resolution_scale_factor)
                                side = max(256, side + (side % 2))
                                context.scene.render.resolution_x = side
                                context.scene.render.resolution_y = side
                                print(f"相机 {camera_obj.name} (轴测图): 应用动态方形分辨率 {side}x{side}")
                            else:
                                context.scene.render.resolution_x = 2000
                                context.scene.render.resolution_y = 2000
                                print(f"相机 {camera_obj.name} (轴测图): 无尺寸信息，退回 2000x2000")
                        else:
                            # 六视图使用动态相机分辨率
                            axis = _infer_axis_from_camera_name(camera_obj.name)
                            # print(f"渲染: 相机 {camera_obj.name} 推断轴向: {axis}")  # 注释掉重复调试
                            if axis:
                                # print(f"渲染: 开始计算 {axis} 轴视图分辨率，对象: {target_object.name}")  # 注释掉重复调试
                                view_res_x, view_res_y, view_aspect = _compute_view_specific_resolution(
                                    target_object, axis, settings.resolution_scale_factor
                                )
                                context.scene.render.resolution_x = view_res_x
                                context.scene.render.resolution_y = view_res_y
                                print(f"相机 {camera_obj.name} ({axis}轴): 分辨率 {view_res_x}x{view_res_y}")
                                # print(f"渲染: 确认设置 - scene.render.resolution_x={context.scene.render.resolution_x}, resolution_y={context.scene.render.resolution_y}")  # 注释掉重复调试
                            else:
                                print(f"相机 {camera_obj.name}: 无法识别轴向，使用默认分辨率")
                    except Exception as e:
                        print(f"相机 {camera_obj.name}: 动态分辨率应用失败: {e}")
                
                # 计算并应用视图特定的正交比例（动态相机的一部分）
                original_cam_scale = None
                try:
                    if getattr(camera_obj.data, 'type', None) == 'ORTHO':
                        original_cam_scale = camera_obj.data.ortho_scale
                        
                        # 推断相机轴向并计算对应的正交比例
                        axis = _infer_axis_from_camera_name(camera_obj.name)
                        # 传入当前分辨率纵横比，确保横纵两向都不被裁切
                        try:
                            current_ar = float(context.scene.render.resolution_x) / max(1.0, float(context.scene.render.resolution_y))
                        except Exception:
                            current_ar = 1.0
                        # 优先用真实相机姿态计算，避免数值误差与朝向误判
                        # 按轴向分别计算正交比例，确保三个轴向自适应
                        view_specific_scale = _compute_ortho_scale_from_camera(
                            target_object, camera_obj, aspect_ratio=current_ar, margin=1.005, scene=context.scene
                        )
                        
                        camera_obj.data.ortho_scale = view_specific_scale
                except Exception as e:
                    print(f"相机 {camera_obj.name}: 正交比例设置失败: {e}")
                    pass

                # 直接使用Python渲染
                bpy.ops.render.render(write_still=True)

                # 渲染后恢复相机正交比例
                try:
                    if original_cam_scale is not None:
                        camera_obj.data.ortho_scale = original_cam_scale
                except Exception:
                    pass
                
                rendered_count += 1
                rendered_outputs.append((camera_obj.name, filepath))
                print(f"渲染成功: {filepath}")

                # 渲染完成后，用 Pillow 在该单图底部居中标注该相机的视图标签（来自相机数据自定义属性）
                # 轴测图 ISO45 不叠加文字
                try:
                    if not camera_obj.name.endswith("ISO45"):
                        view_label = camera_obj.data.get("af_view_label", "")
                        if isinstance(view_label, str):
                            view_label = view_label.strip()
                        if view_label and view_label != "轴测图 45°":
                            _pillow_draw_center_bottom_text(filepath, view_label)
                except Exception as _e:
                    pass

                # 如为 ISO45，再额外渲染一张"干净轴测"（不包含子物体），用于最终三图横向合成
                if camera_obj.name.endswith("ISO45"):
                    try:
                        # 重新设置相机正交比例，确保两次渲染一致
                        iso_ortho_scale = None
                        try:
                            if getattr(camera_obj.data, 'type', None) == 'ORTHO':
                                axis = _infer_axis_from_camera_name(camera_obj.name)
                                # 使用和前一次一致的纵横比、margin，确保两次ISO一致
                                current_ar = float(context.scene.render.resolution_x) / max(1.0, float(context.scene.render.resolution_y))
                                iso_ortho_scale = _compute_ortho_scale_from_camera(
                                    target_object, camera_obj, aspect_ratio=current_ar, margin=1.005, scene=context.scene
                                )
                                camera_obj.data.ortho_scale = iso_ortho_scale
                        except Exception as e:
                            print(f"干净轴测渲染: 正交比例设置失败: {e}")
                        
                        # 暂存当前 hide_render 状态
                        saved_hide = {obj.name: bool(getattr(obj, "hide_render", False)) for obj in bpy.data.objects}
                        # 仅渲染目标物体本体
                        for obj2 in bpy.data.objects:
                            try:
                                if obj2.type == 'CAMERA' or obj2 == target_object:
                                    obj2.hide_render = False
                                else:
                                    obj2.hide_render = True
                            except Exception:
                                pass
                        # 生成文件名（clean）
                        filename2 = f"{camera_obj.name}_clean.png"
                        filepath2 = os.path.join(output_path_abs, filename2)
                        context.scene.render.filepath = filepath2
                        bpy.ops.render.render(write_still=True)
                        print(f"渲染成功(干净轴测): {filepath2}")
                        rendered_outputs.append((f"{camera_obj.name}_CLEAN", filepath2))
                    except Exception as _e:
                        print(f"干净轴测渲染失败: {_e}")
                    finally:
                        # 恢复 hide_render
                        for name, hidden in saved_hide.items():
                            objx = bpy.data.objects.get(name)
                            if objx is not None:
                                try:
                                    objx.hide_render = hidden
                                except Exception:
                                    pass

            # 使用 Pillow 合成六视图总图（3列×2行布局：第一行XYZ，第二行-X-Y-Z），若不足6张则跳过
            try:
                # 合成顺序：3列×2行布局
                # 第一行：+X, +Y, +Z
                # 第二行：-X, -Y, -Z  
                axis_order = ["X", "Y", "Z", "X-", "Y-", "Z-"]
                axis_to_path = {}
                for cam_name, path in rendered_outputs:
                    axis = _infer_axis_from_camera_name(cam_name)
                    if axis and axis not in axis_to_path:
                        axis_to_path[axis] = path

                image_paths = [axis_to_path[a] for a in axis_order if a in axis_to_path]
                if len(image_paths) == 6:
                    comp_name = f"{target_object.name}_sixview.png"
                    composite_path = os.path.join(output_path_abs, comp_name)
                    _compose_six_view_grid_pillow(
                        image_paths=image_paths,
                        out_png_path=composite_path,
                        cols=3,
                        rows=2,
                        gap_px=settings.grid_gap_pixels,  # 使用用户设置的间距
                        background_rgba=(0, 0, 0, 0 if settings.film_transparent else 255),
                        stamp_text=settings.stamp_custom_note.strip() if hasattr(settings, 'stamp_custom_note') else "",
                    )
                    print(f"六视图总图已输出: {composite_path}")
                    # 若存在轴测图，则在左侧拼接生成最终图
                    try:
                        iso_path = None
                        iso_clean_path = None
                        for cam_name, path in rendered_outputs:
                            if cam_name.endswith("ISO45"):
                                iso_path = path
                                break
                        for cam_name, path in rendered_outputs:
                            if cam_name.endswith("ISO45_CLEAN"):
                                iso_clean_path = path
                                break
                        if iso_path:
                            comp_name2 = f"{target_object.name}_sixview_iso.png"
                            composite_path2 = os.path.join(output_path_abs, comp_name2)
                            if iso_clean_path:
                                _compose_two_iso_and_grid_pillow(
                                    iso_with_children_path=iso_path,
                                    iso_clean_path=iso_clean_path,
                                    grid_image_path=composite_path,
                                    out_png_path=composite_path2,
                                    gap_px=0,
                                    background_rgba=(0, 0, 0, 0 if settings.film_transparent else 255),
                                )
                            else:
                                _compose_iso_left_of_grid_pillow(
                                    iso_image_path=iso_path,
                                    grid_image_path=composite_path,
                                    out_png_path=composite_path2,
                                    gap_px=0,
                                    background_rgba=(0, 0, 0, 0 if settings.film_transparent else 255),
                                )
                            print(f"六视图+轴测图总图已输出: {composite_path2}")
                    except Exception as e:
                        print(f"六视图+轴测图合成失败: {e}")
                else:
                    print(f"合成跳过：找到 {len(image_paths)} 张可识别轴向的图片，需 6 张")
            except Exception as e:
                print(f"六视图合成失败: {e}")
            
            # 恢复原始设置
            context.scene.camera = original_camera
            context.scene.render.engine = original_render_engine
            context.scene.render.resolution_x = original_resolution_x
            context.scene.render.resolution_y = original_resolution_y
            context.scene.render.filepath = original_filepath
            restore_environment_map_safe(context, original_world, temp_world)
            # 恢复透明背景设置
            context.scene.render.film_transparent = original_film_transparent
            # 恢复渲染印章配置
            try:
                for name, value in original_stamp["__bools__"].items():
                    try:
                        setattr(r, name, value)
                    except Exception:
                        pass
                if "stamp_note_text" in original_stamp["__styles__"]:
                    r.stamp_note_text = original_stamp["__styles__"]["stamp_note_text"]
                if "stamp_font_size" in original_stamp["__styles__"] and hasattr(r, "stamp_font_size"):
                    r.stamp_font_size = original_stamp["__styles__"]["stamp_font_size"]
                if "stamp_foreground" in original_stamp["__styles__"] and hasattr(r, "stamp_foreground"):
                    r.stamp_foreground = original_stamp["__styles__"]["stamp_foreground"]
                if "stamp_background" in original_stamp["__styles__"] and hasattr(r, "stamp_background"):
                    r.stamp_background = original_stamp["__styles__"]["stamp_background"]
            except Exception:
                pass
            # 恢复所有对象的 hide_render 状态
            for name, hidden in original_hide_render_map.items():
                obj = bpy.data.objects.get(name)
                if obj is not None:
                    try:
                        obj.hide_render = hidden
                    except Exception:
                        pass
            
            # 清理自动创建的临时相机（根据用户设置）
            if cameras_auto_created and auto_created_cameras and settings.auto_cleanup_cameras:
                _cleanup_auto_created_cameras(auto_created_cameras)
                self.report({'INFO'}, f"已成功渲染 {rendered_count} 个摄像机快照到: {output_path_abs}，并清理了 {len(auto_created_cameras)} 个临时相机")
            elif cameras_auto_created and auto_created_cameras:
                self.report({'INFO'}, f"已成功渲染 {rendered_count} 个摄像机快照到: {output_path_abs}，保留了 {len(auto_created_cameras)} 个临时相机")
            else:
                self.report({'INFO'}, f"已成功渲染 {rendered_count} 个摄像机快照到: {output_path_abs}")
            
        except Exception as e:
            # 恢复原始设置
            context.scene.camera = original_camera
            context.scene.render.engine = original_render_engine
            context.scene.render.resolution_x = original_resolution_x
            context.scene.render.resolution_y = original_resolution_y
            context.scene.render.filepath = original_filepath
            restore_environment_map_safe(context, original_world, temp_world)
            # 恢复透明背景设置
            context.scene.render.film_transparent = original_film_transparent
            # 恢复渲染印章配置
            try:
                for name, value in original_stamp["__bools__"].items():
                    try:
                        setattr(r, name, value)
                    except Exception:
                        pass
                if "stamp_note_text" in original_stamp["__styles__"]:
                    r.stamp_note_text = original_stamp["__styles__"]["stamp_note_text"]
                if "stamp_font_size" in original_stamp["__styles__"] and hasattr(r, "stamp_font_size"):
                    r.stamp_font_size = original_stamp["__styles__"]["stamp_font_size"]
                if "stamp_foreground" in original_stamp["__styles__"] and hasattr(r, "stamp_foreground"):
                    r.stamp_foreground = original_stamp["__styles__"]["stamp_foreground"]
                if "stamp_background" in original_stamp["__styles__"] and hasattr(r, "stamp_background"):
                    r.stamp_background = original_stamp["__styles__"]["stamp_background"]
            except Exception:
                pass
            # 恢复所有对象的 hide_render 状态
            for name, hidden in original_hide_render_map.items():
                obj = bpy.data.objects.get(name)
                if obj is not None:
                    try:
                        obj.hide_render = hidden
                    except Exception:
                        pass
            
            # 即使渲染失败也要清理自动创建的临时相机（根据用户设置）
            if cameras_auto_created and auto_created_cameras and settings.auto_cleanup_cameras:
                _cleanup_auto_created_cameras(auto_created_cameras)
                self.report({'ERROR'}, f"渲染失败: {str(e)}，已清理 {len(auto_created_cameras)} 个临时相机")
            elif cameras_auto_created and auto_created_cameras:
                self.report({'ERROR'}, f"渲染失败: {str(e)}，保留了 {len(auto_created_cameras)} 个临时相机")
            else:
                self.report({'ERROR'}, f"渲染失败: {str(e)}")
                
            print(f"渲染错误: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class VIEW3D_PT_standardview_root(Panel):
    """标准视图渲染父面板（用于归类子面板）"""
    bl_label = "standardview"
    bl_idname = "VIEW3D_PT_standardview_root"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "standardview"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.camera_snapshot_settings

        # -----------------
        # 摄像机管理（折叠区）
        # -----------------
        box_cam = layout.box()
        row = box_cam.row(align=True)
        icon = 'TRIA_DOWN' if settings.ui_expand_camera else 'TRIA_RIGHT'
        row.prop(settings, "ui_expand_camera", text="", icon=icon, emboss=False)
        row.label(text="摄像机管理")
        if settings.ui_expand_camera:
            # 正交比例
            row = box_cam.row()
            row.prop(settings, "ortho_scale", text="正交比例")
            
            # 正交比例偏移系数（留白控制）
            row = box_cam.row()
            row.prop(settings, "ortho_scale_offset", text="正交比例偏移系数")

            # 按钮：创建/删除
            row = box_cam.row()
            row.operator("view3d.create_ortho_cameras", text="创建", icon='ADD')
            row.operator("view3d.delete_ortho_cameras", text="删除", icon='REMOVE')

            # 相机清单（封装为独立 box）：显示场景中所有具有标准视图相机的对象
            try:
                box_cam_list = box_cam.box()
                row = box_cam_list.row()
                row.enabled = False
                row.label(text="相机清单（按对象分组）")

                # 获取场景中所有具有标准视图相机的对象
                objects_with_cameras = _find_all_objects_with_standardview_cameras()
                expanded_list = settings.expanded_objects.split(",") if settings.expanded_objects else []

                if objects_with_cameras:
                    for target_object, cams in objects_with_cameras.items():
                        # 对象标题行：显示对象名称和展开/折叠按钮
                        obj_row = box_cam_list.row(align=True)
                        is_expanded = target_object.name in expanded_list
                        icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
                        
                        # 展开/折叠按钮
                        op = obj_row.operator("view3d.toggle_object_cameras", text="", icon=icon, emboss=False)
                        op.object_name = target_object.name
                        
                        # 对象名称
                        obj_row.label(text=f"{target_object.name} ({len(cams)}个相机)")
                        
                        # 如果展开，显示该对象的相机列表
                        if is_expanded:
                            # 轴向排序优先：X, X-, Y, Y-, Z, Z-, ISO45；其余按名称
                            order = {"X": 0, "X-": 1, "Y": 2, "Y-": 3, "Z": 4, "Z-": 5, "ISO45": 6}
                            def _sort_key(c):
                                ax = _infer_axis_from_camera_name(getattr(c, 'name', ''))
                                return (order.get(ax, 99), getattr(c, 'name', ''))
                            cams_sorted = sorted(cams, key=_sort_key)

                            for cam in cams_sorted:
                                try:
                                    axis = _infer_axis_from_camera_name(cam.name)
                                    # 分辨率选择：动态分辨率→各轴规则；ISO45固定；否则用当前场景设置
                                    if settings.use_dynamic_resolution:
                                        if axis == 'ISO45':
                                            # ISO45 也参与动态相机：使用对象最大边作为正方形边
                                            dims = getattr(target_object, 'dimensions', None)
                                            if dims is not None:
                                                max_edge = max(float(dims.x), float(dims.y), float(dims.z))
                                                side = int(max_edge * settings.resolution_scale_factor)
                                                side = max(256, side + (side % 2))
                                                res_x, res_y = side, side
                                            else:
                                                res_x, res_y = 2000, 2000
                                        else:
                                            rx, ry, _ar = _compute_view_specific_resolution(
                                                target_object, axis, settings.resolution_scale_factor
                                            )
                                            res_x, res_y = int(rx), int(ry)
                                    else:
                                        res_x = int(context.scene.render.resolution_x)
                                        res_y = int(context.scene.render.resolution_y)

                                    aspect = float(res_x) / max(1.0, float(res_y))
                                    ortho = None
                                    if getattr(getattr(cam, 'data', None), 'type', None) == 'ORTHO':
                                        # 按轴向分别计算正交比例
                                        ortho = _compute_ortho_scale_from_camera(
                                            target_object, cam, aspect_ratio=aspect, margin=1.005, scene=context.scene
                                        )

                                    # 标签优先用自定义中文标签
                                    label_txt = getattr(getattr(cam, 'data', None), 'get', lambda *a, **k: None)("af_view_label")
                                    if not isinstance(label_txt, str) or not label_txt.strip():
                                        label_txt = cam.name

                                    # 相机信息行：缩进显示
                                    cam_row = box_cam_list.row(align=True)
                                    col_l = cam_row.column()
                                    col_l.enabled = False
                                    if ortho is not None:
                                        col_l.label(text=f"  {label_txt}: ortho={ortho:.2f}, 分辨率={res_x}x{res_y}")
                                    else:
                                        col_l.label(text=f"  {label_txt}: 分辨率={res_x}x{res_y}")
                                    
                                    # 激活按钮
                                    col_r = cam_row.column()
                                    op = col_r.operator("view3d.activate_camera_and_apply_res", text="", icon='VIEW_CAMERA')
                                    op.camera_name = cam.name

                                except Exception:
                                    # 单个相机信息计算失败不影响其他相机显示
                                    r2 = box_cam_list.row()
                                    r2.enabled = False
                                    r2.label(text=f"  {getattr(cam,'name','<相机>')}: 信息计算失败")
                else:
                    row = box_cam_list.row()
                    row.enabled = False
                    row.label(text="(场景中未找到标准视图相机)")
            except Exception as e:
                row = box_cam.box().row()
                row.enabled = False
                row.label(text=f"相机清单生成失败: {str(e)}")

        # -----------------
        # 渲染设置（折叠区）
        # -----------------
        # 确保默认值与自动填充逻辑与原来一致
        try:
            _ensure_snapshot_output_default(context.scene)
            _ensure_stamp_note_default(context)
        except Exception:
            pass

        box_render = layout.box()
        row = box_render.row(align=True)
        icon = 'TRIA_DOWN' if settings.ui_expand_render else 'TRIA_RIGHT'
        row.prop(settings, "ui_expand_render", text="", icon=icon, emboss=False)
        row.label(text="渲染设置")
        if settings.ui_expand_render:
            # 若未设置环境贴图且存在默认 forest.exr，则自动填入
            try:
                if not settings.environment_map_path:
                    default_env = _get_default_forest_exr_path()
                    if default_env:
                        settings.environment_map_path = default_env
            except Exception:
                pass

            # 输出路径
            row = box_render.row()
            row.prop(settings, "snapshot_output_path", text="输出路径")
            row.operator("view3d.browse_output_path", text="", icon='FILE_FOLDER')

            # 环境贴图
            row = box_render.row()
            row.prop(settings, "environment_map_path", text="环境贴图")
            row.operator("view3d.browse_environment_path", text="", icon='FILE_FOLDER')

            # 透明背景
            row = box_render.row()
            row.prop(settings, "film_transparent", text="透明背景")
            
            # 自动清理临时相机
            row = box_render.row()
            row.prop(settings, "auto_cleanup_cameras", text="自动清理临时相机")

            # 动态相机
            row = box_render.row()
            row.prop(settings, "use_dynamic_resolution", text="动态相机")
            
            if settings.use_dynamic_resolution:
                # 缩放因子（像素/米）
                row = box_render.row()
                row.prop(settings, "resolution_scale_factor", text="缩放因子(像素/米)")
                
                # 六视图网格间距
                row = box_render.row()
                row.prop(settings, "grid_gap_pixels", text="六视图间距(像素)")
                
                # 相机清单已移动至上方“摄像机管理”板块

            # 批注文本
            row = box_render.row()
            row.prop(settings, "stamp_custom_note", text="批注文本")

            # 渲染按钮
            box_render.operator("view3d.render_camera_snapshots", text="渲染快照")

def register():
    """注册所有类和属性"""
    bpy.utils.register_class(CameraSnapshotSettings)
    bpy.utils.register_class(VIEW3D_OT_create_ortho_cameras)
    bpy.utils.register_class(VIEW3D_OT_delete_ortho_cameras)
    # VIEW3D_OT_update_ortho_scale 不再需要
    bpy.utils.register_class(VIEW3D_OT_browse_environment_path)
    bpy.utils.register_class(VIEW3D_OT_browse_output_path)
    bpy.utils.register_class(VIEW3D_OT_toggle_object_cameras)
    bpy.utils.register_class(VIEW3D_OT_activate_camera_and_apply_res)
    bpy.utils.register_class(VIEW3D_OT_render_camera_snapshots)
    # 父面板需先注册
    bpy.utils.register_class(VIEW3D_PT_standardview_root)
    # 子面板不再注册，改为在父面板中用 box() 模拟层级
    
    # 注册场景属性
    bpy.types.Scene.camera_snapshot_settings = bpy.props.PointerProperty(type=CameraSnapshotSettings)

    # 在文件加载后确保默认输出路径被写入设置，便于在 Python 属性与 UI 中显示
    try:
        def _on_load_post(_dummy):
            try:
                _ensure_snapshot_output_default(bpy.context.scene)
            except Exception:
                pass
        # 记录并注册处理器，避免重复添加
        global _af_handlers
        if _af_handlers.get("load_post") is None:
            bpy.app.handlers.load_post.append(_on_load_post)
            _af_handlers["load_post"] = _on_load_post
        # 立即尝试为当前场景写入（适用于脚本在已打开文件中加载的情形）
        _ensure_snapshot_output_default(bpy.context.scene)
    except Exception:
        pass

def unregister():
    """注销所有类和属性"""
    bpy.utils.unregister_class(VIEW3D_PT_standardview_root)
    bpy.utils.unregister_class(VIEW3D_OT_render_camera_snapshots)
    bpy.utils.unregister_class(VIEW3D_OT_activate_camera_and_apply_res)
    bpy.utils.unregister_class(VIEW3D_OT_toggle_object_cameras)
    bpy.utils.unregister_class(VIEW3D_OT_browse_output_path)
    bpy.utils.unregister_class(VIEW3D_OT_browse_environment_path)
    # VIEW3D_OT_update_ortho_scale 不再需要
    bpy.utils.unregister_class(VIEW3D_OT_delete_ortho_cameras)
    bpy.utils.unregister_class(VIEW3D_OT_create_ortho_cameras)
    bpy.utils.unregister_class(CameraSnapshotSettings)
    
    # 注销场景属性
    del bpy.types.Scene.camera_snapshot_settings

    # 注销处理器
    try:
        global _af_handlers
        cb = _af_handlers.get("load_post")
        if cb and cb in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(cb)
        _af_handlers["load_post"] = None
    except Exception:
        pass

# 如果直接运行此脚本
if __name__ == "__main__":
    # 先尝试注销，避免重复注册错误
    try:
        unregister()
    except:
        pass
    
    # 注册插件
    register()
    print("正交摄像机快照渲染工具已加载完成！")
