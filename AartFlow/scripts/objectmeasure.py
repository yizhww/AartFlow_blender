#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格测量工具
获取当前选中网格的长宽高和面积
参照Blender原生绘制方法：
1. 获取对象的边界框数据
2. 根据display_bounds_type计算相应的几何体
3. 应用对象的变换矩阵a
"""

import bpy
import os
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy.props import StringProperty
from bpy.types import Operator, Panel
import blf
# 注：本脚本依赖 Blender 的 Python 环境（bpy/gpu/blf 等模块），在外部linter可能会提示“无法解析导入”。

# 全局变量
measurement_results = []  # 存储测量结果
show_3d_annotations = False  # 控制3D标注显示
measurement_draw_handler = None  # 测量绘制处理器
bounding_box_draw_handler = None  # 边界框绘制处理器
object_annotation_states = {}  # 跟踪每个物体的标注显示状态 {object_name: bool}
object_collapse_states = {}  # 跟踪每个物体的折叠状态 {object_name: bool}
object_area_states = {}  # 跟踪每个物体的面积状态 {object_name: {'current_area': float, 'recorded_length': float, 'recorded_width': float, 'recorded_height': float, 'is_expired': bool}}

# 通用常量与绘图工具
# 12条包围盒边（连接8个顶点）
EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # 底面
    (4, 5), (5, 6), (6, 7), (7, 4),  # 顶面
    (0, 4), (1, 5), (2, 6), (3, 7)   # 垂直边
]

def gpu_draw_line(start, end, color):
    """通用直线绘制（供各处理器复用）。"""
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": [start, end]})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def gpu_calc_adaptive_dash_length(start, end, context):
    """根据视口与距离计算自适应虚线段长度。"""
    if not context:
        return 0.05
    try:
        region = context.region
        rv3d = context.region_data
        if not region or not rv3d:
            return 0.05
        mid_point = (start + end) / 2
        camera_location = rv3d.view_matrix.inverted().translation
        distance = (mid_point - camera_location).length
        view_distance = rv3d.view_distance
        base_length = 0.02
        distance_factor = max(0.1, min(2.0, distance / 10.0))
        scale_factor = max(0.5, min(2.0, view_distance / 10.0))
        adaptive_length = base_length * distance_factor * scale_factor
        return max(0.005, min(0.2, adaptive_length))
    except:
        return 0.05

def gpu_draw_dashed_line(start, end, color, context, min_segments=5):
    """通用虚线绘制，自动按视口密度分段。"""
    direction = end - start
    length = direction.length
    if length == 0:
        return
    direction.normalize()
    dash_len = gpu_calc_adaptive_dash_length(start, end, context)
    dash_count = max(min_segments, int(length / (dash_len * 2)))
    actual_dash_len = length / (dash_count * 2)
    for i in range(dash_count):
        dash_start = start + direction * (i * actual_dash_len * 2)
        dash_end = dash_start + direction * actual_dash_len
        if (dash_end - start).length > length:
            dash_end = end
        gpu_draw_line(dash_start, dash_end, color)

def build_all_edges(corners):
    """基于给定顶点构建12条边及其向量: [((i,j), vector), ...]。"""
    return [
        (edge, corners[edge[1]] - corners[edge[0]])
        for edge in EDGES
    ]

# 在文件开头添加全局的平行边分组函数
def group_parallel_edges(edges_list):
    """
    将所有边按平行关系分组，每组应该包含4条平行边
    
    Args:
        edges_list: 边列表，每个元素为 (edge_indices, edge_vector)
        
    Returns:
        list: 平行边组列表，每组包含平行的边
    """
    parallel_groups = []
    used_indices = set()
    
    for i, (indices1, vector1) in enumerate(edges_list):
        if indices1 in used_indices:
            continue
        
        # 开始一个新的平行边组
        current_group = [(indices1, vector1)]
        used_indices.add(indices1)
        
        # 寻找与当前边平行的其他边
        for j, (indices2, vector2) in enumerate(edges_list):
            if j == i or indices2 in used_indices:
                continue
            
            # 检查两个向量是否平行（点积的绝对值接近1）
            if vector1.length > 0 and vector2.length > 0:  # 避免零向量
                v1_normalized = vector1.normalized()
                v2_normalized = vector2.normalized()
                alignment = abs(v1_normalized.dot(v2_normalized))
                
                # 如果夹角余弦接近1或-1，说明平行或反平行
                if abs(alignment - 1.0) < 0.01:  # 允许0.01的误差
                    current_group.append((indices2, vector2))
                    used_indices.add(indices2)
        
        # 矩形应该每组有4条边
        if len(current_group) >= 2:  # 至少2条边算一组
            parallel_groups.append(current_group)
    
    return parallel_groups

def select_representative_edge(group, target_axis=None):
    """
    从平行边组中选择代表边
    
    Args:
        group: 平行边组
        target_axis: 目标轴方向（可选）
        
    Returns:
        tuple: (edge_indices, edge_length, alignment)
    """
    if not group:
        return None, 0, 0
    
    # 如果指定了目标轴，选择与目标轴最对齐的边
    if target_axis:
        max_alignment = -1
        best_edge = None
        best_length = 0
        
        for edge_indices, edge_vector in group:
            if edge_vector.length > 0:
                alignment = abs(edge_vector.normalized().dot(target_axis))
                if alignment > max_alignment:
                    max_alignment = alignment
                    best_edge = edge_indices
                    best_length = edge_vector.length
        
        return best_edge, best_length, max_alignment
    else:
        # 如果没有指定目标轴，选择最长的边
        best_edge = None
        best_length = 0
        
        for edge_indices, edge_vector in group:
            if edge_vector.length > best_length:
                best_length = edge_vector.length
                best_edge = edge_indices
        
        return best_edge, best_length, 0

def check_edges_not_parallel(edge1_indices, edge2_indices, edge3_indices, world_corners):
    """已废弃：未使用。保留占位避免外部误引用。"""
    return False

class BoundingBoxDrawHandler:
    """独立的边界框绘制处理器（仅绘制虚线包围盒，不受测量功能影响）"""
    
    def __init__(self):
        self.draw_handler = None
    
    def draw_bounding_box_lines(self, context):
        """绘制所有选中网格对象的边界框 - 独立于测量系统"""
        # 获取所有选中的网格对象
        selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            return
        
        # 设置绘制参数
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1.5)  # 增加边界框线宽，让虚线更清晰
        
        for obj in selected_objects:
            # 检查该物体的标注是否应该显示
            global object_annotation_states
            if obj.name in object_annotation_states and not object_annotation_states[obj.name]:
                continue  # 跳过被隐藏的物体
            
            # 获取对象的边界框顶点
            bbox_corners = [Vector(corner) for corner in obj.bound_box]
            if not bbox_corners or len(bbox_corners) != 8:
                continue
            
            # 将边界框顶点转换为世界坐标
            world_corners = [obj.matrix_world @ corner for corner in bbox_corners]
            
            # 绘制边界框的12条边（灰色虚线）
            self.draw_bounding_box(world_corners, (0.8, 0.8, 0.8, 0.6), context)  # 半透明灰色
        
        gpu.state.blend_set('NONE')
    
    def draw_bounding_box(self, corners, color, context=None):
        """绘制边界框的12条边（虚线，视口自适应）"""
        for a, b in EDGES:
            start = corners[a]
            end = corners[b]
            gpu_draw_dashed_line(start, end, color, context)
    
    
    def start(self, context):
        """启动边界框绘制"""
        if self.draw_handler:
            self.stop()
        
        # 添加绘制处理器 - 在测量线之前绘制
        self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_bounding_box_lines, (context,), 'WINDOW', 'POST_VIEW'
        )
    
    def stop(self):
        """停止边界框绘制"""
        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None

class MeasurementDrawHandler:
    """测量绘制处理器 - 负责绘制测量线和文本标注
    
    优化特性：
    - 只在边界框真正变化时才进行动态检测
    - 静态状态下使用缓存数据，避免重复计算
    - 智能检测边界框变化，包括位置、缩放、旋转等
    - 提供状态监控，显示静态/动态对象数量
    - 静态方法优化：绘制完成后停止处理器，减少性能开销
    - 静态数据持久化：确保视图刷新时数据不丢失
    """
    
    def __init__(self):
        self.draw_handler = None
        self.text_handler = None
        self.static_draw_handler = None  # 预留：静态数据绘制处理器（当前未使用）
        self.static_text_handler = None  # 预留：静态文本绘制处理器（当前未使用）
        # 添加缓存机制
        self.cached_data = {}  # 存储每个对象的缓存数据
        self.last_update_time = 0  # 上次更新时间
        self.static_objects = set()  # 记录当前处于静态状态的对象
        self.dynamic_objects = set()  # 记录当前处于动态状态的对象
        self.static_draw_completed = False  # 标记静态绘制是否完成
        self.static_draw_frames = 0  # 静态绘制帧数计数
        self.static_draw_data = []  # 存储静态绘制的数据
    
    def draw_measurement_lines(self, context):
        """绘制测量线和边界框 - 3D空间，所有数据都使用动态方法"""
        if not measurement_results or not show_3d_annotations:
            return
        
        # 设置绘制参数
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(4.0)  # 加粗测量线
        
        for item in measurement_results:
            obj = bpy.data.objects.get(item['name'])
            if not obj or obj.type != 'MESH':
                continue
            
            # 检查该物体的标注是否应该显示
            global object_annotation_states
            if obj.name in object_annotation_states and not object_annotation_states[obj.name]:
                continue  # 跳过被隐藏的物体
            
            # 所有数据都使用动态方法绘制
            self._draw_dynamic_measurements(obj, item)
        
        gpu.state.blend_set('NONE')
    
    def _draw_static_persistent_data(self, context):
        """绘制静态持久化数据，确保视图刷新时数据不丢失"""
        if not self.static_draw_data:
            return
        
        # 设置绘制参数
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(4.0)
        
        # 绘制所有静态数据
        for draw_item in self.static_draw_data:
            if draw_item['type'] == 'line':
                self.draw_line(draw_item['start'], draw_item['end'], draw_item['color'])
            elif draw_item['type'] == 'text':
                self.draw_text_3d(draw_item['text'], draw_item['location'], context, draw_item['color'])
        
        gpu.state.blend_set('NONE')
    

    def _draw_dynamic_measurements(self, obj, item):
        """动态方法：每次都重新计算边界框和测量数据"""
        # 每次都重新获取当前边界框顶点
        current_bbox_corners = self.get_current_bbox_corners(obj, item['dimensions'])
        if current_bbox_corners and len(current_bbox_corners) == 8:
            # 绘制测量线（实线，更突出）- 使用动态边界框数据
            self.draw_measurement_dimensions_dynamic(obj, current_bbox_corners, item['dimensions'])
        
        # 记录动态状态
        self.dynamic_objects.add(obj.name)
        if obj.name in self.static_objects:
            self.static_objects.remove(obj.name)
    
    
    def _is_area_expired(self, obj, item):
        """更新面积数据状态 - 基于长宽高数据变化检测并更新状态"""
        global object_area_states
        
        # 如果对象没有面积状态记录，说明还没有初始化，返回False（正常状态）
        if obj.name not in object_area_states:
            return False
        
        # 获取面积状态记录
        area_state = object_area_states[obj.name]
        
        # 如果面积状态已经是过期状态，直接返回True
        if area_state.get('state') == 'expired':
            return True
        
        # 获取当前的长宽高数据
        current_bbox_corners = self.get_current_bbox_corners(obj, item['dimensions'])
        if not current_bbox_corners or len(current_bbox_corners) != 8:
            return False
        
        # 计算当前的长宽高
        edges_data = item['dimensions'].get('edges_data', {})
        current_dimensions = self.calculate_current_dimensions(current_bbox_corners, edges_data)
        current_length = current_dimensions.get('length', 0)
        current_width = current_dimensions.get('width', 0)
        current_height = current_dimensions.get('height', 0)
        
        # 获取记录的长宽高数据
        recorded_length = area_state.get('recorded_length', 0)
        recorded_width = area_state.get('recorded_width', 0)
        recorded_height = area_state.get('recorded_height', 0)
        
        # 检查是否有任何尺寸发生变化（使用容差避免浮点数精度问题）
        tolerance = 0.001  # 1毫米容差
        length_changed = abs(current_length - recorded_length) > tolerance
        width_changed = abs(current_width - recorded_width) > tolerance
        height_changed = abs(current_height - recorded_height) > tolerance
        
        # 只有当长宽高任意一个发生变化时，面积才过期
        is_expired = length_changed or width_changed or height_changed
        
        # 更新面积状态记录
        if is_expired:
            area_state['state'] = 'expired'
            area_state['is_expired'] = True
        else:
            area_state['state'] = 'current'
            area_state['is_expired'] = False
        
        return is_expired
    
    def _update_cache(self, obj, current_bbox_corners, original_dimensions):
        """更新对象的缓存数据 - 只在边界框真正变化时更新"""
        current_matrix_hash = hash(str(obj.matrix_world))
        current_bbox = [Vector(corner) for corner in obj.bound_box]
        bbox_hash = hash(str(current_bbox))
        
        # 检查是否真的需要更新缓存
        if obj.name in self.cached_data:
            cached = self.cached_data[obj.name]
            cached_bbox_hash = cached.get('bbox_hash')
            
            # 如果边界框哈希相同，只更新矩阵哈希（避免不必要的重新计算）
            if cached_bbox_hash == bbox_hash:
                cached['matrix_hash'] = current_matrix_hash
                cached['update_time'] = bpy.context.scene.frame_current
                return
        
        # 边界框发生变化，更新完整缓存
        self.cached_data[obj.name] = {
            'matrix_hash': current_matrix_hash,
            'bbox_hash': bbox_hash,
            'bbox_corners': current_bbox_corners,
            'dimensions': original_dimensions,
            'update_time': bpy.context.scene.frame_current,
            'last_bbox_change_time': bpy.context.scene.frame_current  # 记录边界框最后变化时间
        }
    
    def clear_cache(self):
        """清除所有缓存数据"""
        self.cached_data.clear()
        self.last_update_time = 0
        self.static_objects.clear()
        self.dynamic_objects.clear()
        # 重置静态绘制状态
        self.static_draw_completed = False
        self.static_draw_frames = 0
        # 清除静态绘制数据
        self.static_draw_data.clear()
    
    def get_status_info(self):
        """获取当前测量状态信息"""
        return {
            'static_objects': list(self.static_objects),
            'dynamic_objects': list(self.dynamic_objects),
            'cached_objects': list(self.cached_data.keys()),
            'total_objects': len(self.static_objects) + len(self.dynamic_objects)
        }
    
    def get_current_bbox_corners(self, obj, original_dimensions):
        """
        动态获取对象的当前边界框顶点数据
        支持实时更新，参照原生边界框的动态变化
        """
        bbox_corners = [Vector(corner) for corner in obj.bound_box]
        if not bbox_corners or len(bbox_corners) != 8:
            return None
        
        # 将边界框顶点转换为世界坐标（包含缩放）
        world_corners = [obj.matrix_world @ corner for corner in bbox_corners]
        return world_corners

    def draw_measurement_dimensions_dynamic(self, obj, current_bbox_corners, original_dimensions):
        """绘制测量尺寸线 - 基于动态12条边计算的长宽高数据"""
        if not current_bbox_corners or len(current_bbox_corners) != 8:
            return
        
        # 获取12条边的数据（使用原始定义）
        edges_data = original_dimensions.get('edges_data', {})
        
        # 动态计算当前尺寸，包括三条边分析 - 长宽高分析完成
        current_dimensions = self.calculate_current_dimensions(current_bbox_corners, edges_data)
        
        # 从分析结果中获取最终确定的边索引
        final_edges = current_dimensions.get('final_edges', {})
        length_edge_indices = final_edges.get('length_edge_indices', (0, 1))
        width_edge_indices = final_edges.get('width_edge_indices', (1, 2))
        height_edge_indices = final_edges.get('height_edge_indices', (0, 4))
        

        
        # 基于分析结果绘制三条彩色实线
        # 1. 绘制长度线 (X轴) - 柔和红色
        length_start = current_bbox_corners[length_edge_indices[0]]
        length_end = current_bbox_corners[length_edge_indices[1]]
        gpu_draw_line(length_start, length_end, (1.0, 0.0, 0.0, 0.9))  # 纯红

        # 2. 绘制宽度线 (Y轴) - 柔和绿色
        width_start = current_bbox_corners[width_edge_indices[0]]
        width_end = current_bbox_corners[width_edge_indices[1]]
        gpu_draw_line(width_start, width_end, (0.0, 1.0, 0.0, 0.9))  # 纯绿

        # 3. 绘制高度线 (Z轴) - 使用分析后的高度边
        height_start = current_bbox_corners[height_edge_indices[0]]
        height_end = current_bbox_corners[height_edge_indices[1]]
        gpu_draw_line(height_start, height_end, (0.0, 0.0, 1.0, 0.9))  # 纯蓝
           
    def draw_measurement_text(self, context):
        """绘制测量文本标注 - 2D屏幕空间。
        规则：
        - 全局显示开启时：可见物体显示完整三项文本；被隐藏的物体仅显示“名称（隐藏）”。
        - 全局显示关闭时：所有已测量物体仅显示“名称（隐藏）”。
        """
        if not measurement_results:
            return
        
        # 设置文本绘制参数
        blf.size(0, 16)  # 增加字体大小，让文本更粗更清晰
        
        for item in measurement_results:
            obj = bpy.data.objects.get(item['name'])
            if not obj or obj.type != 'MESH':
                continue
            
            global object_annotation_states, show_3d_annotations
            is_obj_visible = object_annotation_states.get(obj.name, True)

            if show_3d_annotations and is_obj_visible:
                # 显示完整文本
                self._draw_dynamic_text_calculation(obj, context, item)
            else:
                # 仅显示名称（隐藏）
                current_bbox_corners = self.get_current_bbox_corners(obj, item['dimensions'])
                if current_bbox_corners and len(current_bbox_corners) == 8:
                    bbox_top_center = Vector((
                        sum(corner.x for corner in current_bbox_corners) / 8,
                        sum(corner.y for corner in current_bbox_corners) / 8,
                        max(corner.z for corner in current_bbox_corners) + 0.2
                    ))
                else:
                    bbox_top_center = obj.location
                self.draw_text_3d(f"名称: {obj.name}（隐藏）", bbox_top_center, context, (0.8, 0.8, 0.8, 1.0))
    
    
    def _draw_dynamic_text_calculation(self, obj, context, item):
        """动态文本计算逻辑"""
        current_bbox_corners = self.get_current_bbox_corners(obj, item['dimensions'])
        if current_bbox_corners and len(current_bbox_corners) == 8:
            # 获取12条边的数据
            edges_data = item['dimensions'].get('edges_data', {})
            
            # 动态计算当前测量数据，包括最终确定的边索引
            current_dimensions = self.calculate_current_dimensions(current_bbox_corners, edges_data)
            
            # 从分析结果中获取最终确定的边索引
            final_edges = current_dimensions.get('final_edges', {})
            length_edge_indices = final_edges.get('length_edge_indices', (0, 1))
            width_edge_indices = final_edges.get('width_edge_indices', (1, 2))
            height_edge_indices = final_edges.get('height_edge_indices', (0, 4))
            
            # 获取当前测量数据
            current_length = current_dimensions.get('length', 0)
            current_width = current_dimensions.get('width', 0)
            current_height = current_dimensions.get('height', 0)
            
            # 基于最终确定的边索引计算文本位置
            # 长度线文本 (X轴) - 红色，显示在长度边中点
            length_start = current_bbox_corners[length_edge_indices[0]]
            length_end = current_bbox_corners[length_edge_indices[1]]
            length_mid = (length_start + length_end) / 2
            self.draw_text_3d(f"长度: {current_length:.2f}m", length_mid, context, (1.0, 0.0, 0.0, 1.0))
            
            # 宽度线文本 (Y轴) - 绿色，显示在宽度边中点
            width_start = current_bbox_corners[width_edge_indices[0]]
            width_end = current_bbox_corners[width_edge_indices[1]]
            width_mid = (width_start + width_end) / 2
            self.draw_text_3d(f"宽度: {current_width:.2f}m", width_mid, context, (0.0, 1.0, 0.0, 1.0))
            
            # 高度线文本 (Z轴) - 蓝色，显示在高度边中点
            height_start = current_bbox_corners[height_edge_indices[0]]
            height_end = current_bbox_corners[height_edge_indices[1]]
            height_mid = (height_start + height_end) / 2
            self.draw_text_3d(f"高度: {current_height:.2f}m", height_mid, context, (0.0, 0.0, 1.0, 1.0))
            
            # 物体名称 - 显示在边界框上方
            # 计算边界框的顶部中心位置
            bbox_top_center = Vector((
                sum(corner.x for corner in current_bbox_corners) / 8,
                sum(corner.y for corner in current_bbox_corners) / 8,
                max(corner.z for corner in current_bbox_corners) + 0.2  # 在最高点上方0.2米
            ))
            self.draw_text_3d(f"名称: {obj.name}", bbox_top_center, context, (1.0, 1.0, 0.0, 1.0))  # 黄色显示物体名称
            
            # 面积文本 - 显示在对象中心位置（根据状态显示不同文本）
            obj_center = obj.location
            static_area = edges_data.get('static_area', 0)  # 使用静态缓存的表面积
            
            # 更新面积状态（这会触发状态检测和更新）
            self._is_area_expired(obj, item)
            
            # 获取更新后的面积状态
            global object_area_states
            area_state = object_area_states.get(obj.name, {})
            state = area_state.get('state', 'initial')
            
            # 根据状态显示不同的文本和颜色
            if state == 'expired':
                area_text = f"面积: {static_area:.2f}m2 (过期)"
                area_color = (1.0, 0.5, 0.0, 1.0)  # 橙色表示过期
            else:  # current状态
                area_text = f"面积: {static_area:.2f}m2"
                area_color = (1.0, 1.0, 1.0, 1.0)  # 白色表示正常
            
            self.draw_text_3d(area_text, obj_center, context, area_color)
    
    def _draw_cached_text(self, obj, context):
        """使用缓存数据绘制文本 - 已废弃，现在所有文本都使用动态计算"""
        # 这个方法现在不再使用，所有文本都通过动态计算获取
        pass
    
    def calculate_current_dimensions(self, current_bbox_corners, edges_data, obj=None):
        """
        动态计算当前尺寸 - 基于实时边界框顶点数据
        使用固定的边索引，但重新验证高度边与Z轴的一致性
        """
        if not current_bbox_corners or len(current_bbox_corners) != 8:
            return {}
        
        # 从原始数据中获取固定的边索引（选定了要测量的三条边，分析完就固定住）
        final_edges = edges_data.get('final_edges', {})
        length_edge_indices = final_edges.get('length_edge_indices', (0, 1))
        width_edge_indices = final_edges.get('width_edge_indices', (1, 2))
        height_edge_indices = final_edges.get('height_edge_indices', (0, 4))
        
        # 改进：按边的方向自动分组，找出三组平行边
        world_z_axis = Vector((0, 0, 1))  # 世界坐标Z轴方向
        
        # 定义所有12条边
        all_edges = build_all_edges(current_bbox_corners)
        
        # 使用全局的平行边分组函数
        
        # 获取三组平行边
        parallel_groups = group_parallel_edges(all_edges)
        
        # 使用全局的代表边选择函数
        
        # 确保我们有三组平行边
        if len(parallel_groups) >= 3:
            # 为每组计算与Z轴的对齐度，并选择代表边
            group_representatives = []
            
            for group in parallel_groups:
                edge_indices, edge_length, z_alignment = select_representative_edge(group, world_z_axis)
                if edge_indices:
                    group_representatives.append((edge_indices, edge_length, z_alignment, group))
            
            # 确保我们有三个有效的代表边
            if len(group_representatives) >= 3:
                # 选择与Z轴最对齐的作为高度
                group_representatives.sort(key=lambda x: x[2], reverse=True)  # 按Z轴对齐度排序
                
                # 高度：Z轴对齐度最高的组
                height_edge_indices = group_representatives[0][0]
                bbox_height = group_representatives[0][1]
                
                # 长度和宽度：剩下两组按边长度排序
                remaining_groups = group_representatives[1:3]
                remaining_groups.sort(key=lambda x: x[1], reverse=True)  # 按边长度排序
                
                length_edge_indices = remaining_groups[0][0]
                bbox_length = remaining_groups[0][1]
                
                width_edge_indices = remaining_groups[1][0]
                bbox_width = remaining_groups[1][1]
                
                # 更新原始数据中的边索引
                if 'final_edges' in edges_data:
                    edges_data['final_edges']['height_edge_indices'] = height_edge_indices
                    edges_data['final_edges']['length_edge_indices'] = length_edge_indices
                    edges_data['final_edges']['width_edge_indices'] = width_edge_indices
            else:
                # 回退到原来的逻辑
                bbox_length = (current_bbox_corners[length_edge_indices[1]] - current_bbox_corners[length_edge_indices[0]]).length
                bbox_width = (current_bbox_corners[width_edge_indices[1]] - current_bbox_corners[width_edge_indices[0]]).length
                bbox_height = (current_bbox_corners[height_edge_indices[1]] - current_bbox_corners[height_edge_indices[0]]).length
        else:
            # 回退到原来的逻辑
            bbox_length = (current_bbox_corners[length_edge_indices[1]] - current_bbox_corners[length_edge_indices[0]]).length
            bbox_width = (current_bbox_corners[width_edge_indices[1]] - current_bbox_corners[width_edge_indices[0]]).length
            bbox_height = (current_bbox_corners[height_edge_indices[1]] - current_bbox_corners[height_edge_indices[0]]).length
        
        # 计算边界框的边界范围（用于绘制）
        world_min_x = min(corner.x for corner in current_bbox_corners)
        world_max_x = max(corner.x for corner in current_bbox_corners)
        world_min_y = min(corner.y for corner in current_bbox_corners)
        world_max_y = max(corner.y for corner in current_bbox_corners)
        world_min_z = min(corner.z for corner in current_bbox_corners)
        world_max_z = max(corner.z for corner in current_bbox_corners)
        
        # 表面积计算已独立，只提供静态方法
        # 在动态方法中使用缓存的表面积数据，避免性能消耗
        area = edges_data.get('static_area', 0)  # 使用静态缓存的表面积
        area_info = edges_data.get('area_info', {})
        
        return {
            'length': bbox_length,  # 基于固定边索引计算的长度
            'width': bbox_width,    # 基于固定边索引计算的宽度
            'height': bbox_height,  # 基于验证后的高度边索引计算的高度
            'area': area,  # 从原始数据获取的表面积
            'area_info': area_info,  # 保持原始表面积信息
            'volume': bbox_length * bbox_width * bbox_height,
            'bounds': {
                'min_x': world_min_x, 'max_x': world_max_x,
                'min_y': world_min_y, 'max_y': world_max_y,
                'min_z': world_min_z, 'max_z': world_max_z
            },
            'bounds_type': 'DYNAMIC_BOUNDING_BOX',  # 表示这是动态计算的边界框
            'bbox_corners': current_bbox_corners,  # 存储当前边界框顶点
            'edges_data': edges_data,  # 保持原始边数据
            'final_edges': {  # 保持固定的边索引（可能已更新高度边索引）
                'length_edge_indices': length_edge_indices,
                'width_edge_indices': width_edge_indices,
                'height_edge_indices': height_edge_indices
            },
            'analysis_info': edges_data.get('analysis_info', {})  # 保持原始分析信息
        }
    
    def draw_line(self, start, end, color):
        """委托到通用绘图函数。"""
        gpu_draw_line(start, end, color)
    
    def draw_rounded_rect(self, x, y, width, height, radius, color):
        """绘制圆角矩形 - 简化版本，使用普通矩形作为背景"""
        # 使用GPU绘制矩形背景（简化版本，避免复杂的圆角计算）
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        # 创建矩形的顶点（简化为普通矩形）
        vertices = [
            (x, y),                    # 左下角
            (x + width, y),            # 右下角
            (x + width, y + height),   # 右上角
            (x, y + height)            # 左上角
        ]
        
        # 创建三角形索引（两个三角形组成矩形）
        # 注意：索引必须是元组或列表的列表，每个内部列表代表一个三角形
        indices = [(0, 1, 2), (0, 2, 3)]
        
        # 绘制矩形
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    
    def draw_text_3d(self, text, location, context, color):
        """在3D空间中绘制文本（带半透明矩形背景）"""
        # 导入view3d_utils
        from bpy_extras import view3d_utils
        
        # 获取3D点的2D投影
        region = context.region
        rv3d = context.region_data
        
        # 将3D坐标转换为2D屏幕坐标
        coord = view3d_utils.location_3d_to_region_2d(region, rv3d, location)
        
        if coord:
            # 计算文本尺寸
            blf.size(0, 16)  # 确保字体大小一致
            text_width, text_height = blf.dimensions(0, text)
            
            # 计算背景矩形的位置和尺寸
            padding = 8  # 文本周围的内边距
            bg_width = text_width + padding * 2
            bg_height = text_height + padding * 2
            bg_x = coord.x - bg_width / 2
            bg_y = coord.y - bg_height / 2
            
            # 绘制半透明矩形背景
            bg_color = (0.1, 0.1, 0.1, 0.8)  # 深灰色半透明背景
            
            # 设置GPU状态
            gpu.state.blend_set('ALPHA')
            
            # 绘制背景
            self.draw_rounded_rect(bg_x, bg_y, bg_width, bg_height, 0, bg_color)
            
            # 重置GPU状态
            gpu.state.blend_set('NONE')
            
            # 设置文本颜色
            blf.color(0, *color)
            
            # 绘制文本
            blf.position(0, coord.x - text_width / 2, coord.y - text_height / 2, 0)
            blf.draw(0, text)
        else:
            # 如果坐标转换失败，静默处理而不是抛出异常
            # 这通常发生在对象在视口外或相机后面时
            pass
    
    def start(self, context):
        """启动测量绘制"""
        if self.draw_handler:
            self.stop()
        
        # 添加绘制处理器 - 在边界框之后绘制
        self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                self.draw_measurement_lines, (context,), 'WINDOW', 'POST_VIEW'
            )
        
        # 添加文本绘制处理器
        self.text_handler = bpy.types.SpaceView3D.draw_handler_add(
                self.draw_measurement_text, (context,), 'WINDOW', 'POST_PIXEL'
            )
    
    def stop(self):
        """停止测量绘制"""
        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None
        
        if self.text_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.text_handler, 'WINDOW')
            self.text_handler = None

def calculate_surface_area_3d_print_style(obj):
    """
    参照3D print box方法计算表面积
    使用bmesh进行更精确的计算，考虑对象变换
    
    Args:
        obj: Blender对象
        
    Returns:
        dict: 包含表面积信息的字典
    """
    if obj.type != 'MESH':
        return None
    
    # 创建bmesh实例
    bm = bmesh.new()
    
    try:
        # 从网格数据创建bmesh
        bm.from_mesh(obj.data)
        
        # 应用对象的变换矩阵到bmesh
        bm.transform(obj.matrix_world)
        
        # 计算表面积
        total_area = 0.0
        face_areas = []
        
        # 遍历所有面
        for face in bm.faces:
            # 计算面的面积
            face_area = face.calc_area()
            total_area += face_area
            face_areas.append(face_area)
        
        # 计算统计信息
        if face_areas:
            min_face_area = min(face_areas)
            max_face_area = max(face_areas)
            avg_face_area = sum(face_areas) / len(face_areas)
        else:
            min_face_area = max_face_area = avg_face_area = 0.0
        
        # 计算网格复杂度指标
        vertex_count = len(bm.verts)
        face_count = len(bm.faces)
        edge_count = len(bm.edges)
        
        # 计算表面积与体积比（如果体积可用）
        volume = calculate_mesh_volume(bm)
        area_volume_ratio = total_area / volume if volume > 0 else 0
        
        return {
            'total_area': total_area,
            'face_count': face_count,
            'vertex_count': vertex_count,
            'edge_count': edge_count,
            'min_face_area': min_face_area,
            'max_face_area': max_face_area,
            'avg_face_area': avg_face_area,
            'volume': volume,
            'area_volume_ratio': area_volume_ratio,
            'face_areas': face_areas,
            'calculation_method': 'BMESH_3D_PRINT_STYLE'
        }
        
    finally:
        # 清理bmesh
        bm.free()

def calculate_mesh_volume(bm):
    """
    计算网格体积（使用bmesh）
    
    Args:
        bm: bmesh对象
        
    Returns:
        float: 网格体积
    """
    try:
        # 使用bmesh计算体积
        volume = bm.calc_volume()
        return abs(volume)  # 确保体积为正数
    except:
        # 如果bmesh计算失败，返回0
        return 0.0

# ==================== 数据获取策略说明 ====================
# 表面积：使用改进的bmesh方法，只在初始测量时计算一次，通过手动刷新更新
# 原因：表面积计算非常消耗性能，特别是在动态更新时
# 其他数据（长度、宽度、高度、体积）：使用动态方法，实时计算
# 原因：这些数据计算简单，可以实时更新，提供更准确的信息
# 
# 解决方案：
# 1. 表面积：在初始测量时使用bmesh计算一次，存储到 static_area 字段，通过手动刷新更新
# 2. 其他数据：每次更新时重新计算，确保实时准确性
# 3. 性能平衡：在保证准确性的同时，避免表面积重复计算
# ====================================================

def get_mesh_dimensions(obj):
    """
    获取网格对象的尺寸信息
    基于边界框的12条边计算长宽高：
    1. 获取对象的边界框数据 (obj.bound_box)
    2. 应用对象的变换矩阵
    3. 基于12条边计算长宽高数据
    4. 分析并固定长宽高对应的边索引（后续变换时只更新数值，不重新选择边）
    5. 使用改进的表面积计算方法（基于bmesh）
    
    Args:
        obj: Blender对象
        
    Returns:
        dict: 包含长宽高和面积信息的字典，以及固定的边索引
    """
    if obj.type != 'MESH':
        return None
    
    # 获取边界框数据（与原生边界框相同的数据源）
    bbox_corners = [Vector(corner) for corner in obj.bound_box]
    
    if not bbox_corners or len(bbox_corners) != 8:
        return None
    
    # 将边界框顶点转换为世界坐标（包含缩放）
    world_corners = [obj.matrix_world @ corner for corner in bbox_corners]
    bounds_type = 'BOUNDING_BOX'
    
    # 基于12条边计算长宽高数据
    edges = EDGES
    
    # 从12条边计算长宽高
    # 长度 (X轴) - 使用底面边 (0,1) 和顶面边 (4,5)
    length_edge1 = (world_corners[1] - world_corners[0]).length  # 底面边 (0,1)
    length_edge2 = (world_corners[5] - world_corners[4]).length  # 顶面边 (4,5)
    bbox_length = max(length_edge1, length_edge2)  # 取较大值确保准确性
    
    # 宽度 (Y轴) - 使用底面边 (1,2) 和顶面边 (5,6)
    width_edge1 = (world_corners[2] - world_corners[1]).length  # 底面边 (1,2)
    width_edge2 = (world_corners[6] - world_corners[5]).length  # 顶面边 (5,6)
    bbox_width = max(width_edge1, width_edge2)  # 取较大值确保准确性
    
    # 改进：按边的方向自动分组，找出三组平行边
    world_z_axis = Vector((0, 0, 1))  # 世界坐标Z轴方向
    
    # 定义所有12条边
    all_edges = build_all_edges(world_corners)
    
    # 使用全局的平行边分组函数
    parallel_groups = group_parallel_edges(all_edges)
    
    # 确保我们有三组平行边
    if len(parallel_groups) >= 3:
        # 为每组计算与Z轴的对齐度，并选择代表边
        group_representatives = []
        
        for group in parallel_groups:
            edge_indices, edge_length, z_alignment = select_representative_edge(group, world_z_axis)
            if edge_indices:
                group_representatives.append((edge_indices, edge_length, z_alignment, group))
        
        # 确保我们有三个有效的代表边
        if len(group_representatives) >= 3:
            # 选择与Z轴最对齐的作为高度
            group_representatives.sort(key=lambda x: x[2], reverse=True)  # 按Z轴对齐度排序
            
            # 高度：Z轴对齐度最高的组
            height_edge_indices = group_representatives[0][0]
            bbox_height = group_representatives[0][1]
            
            # 长度和宽度：剩下两组按边长度排序
            remaining_groups = group_representatives[1:3]
            remaining_groups.sort(key=lambda x: x[1], reverse=True)  # 按边长度排序
            
            length_edge_indices = remaining_groups[0][0]
            bbox_length = remaining_groups[0][1]
            
            width_edge_indices = remaining_groups[1][0]
            bbox_width = remaining_groups[1][1]
            
            selected_height_edge = height_edge_indices
        else:
            # 回退到原来的逻辑
            bbox_length = max(length_edge1, length_edge2)
            bbox_width = max(width_edge1, width_edge2)
            # 从所有边中选择最长的作为默认高度
            height_edges = [edge_vector.length for _, edge_vector in all_edges]
            bbox_height = max(height_edges)
            selected_height_edge = all_edges[height_edges.index(bbox_height)][0]
    else:
        # 回退到原来的逻辑
        bbox_length = max(length_edge1, length_edge2)
        bbox_width = max(width_edge1, width_edge2)
        # 从所有边中选择最长的作为默认高度
        height_edges = [edge_vector.length for _, edge_vector in all_edges]
        bbox_height = max(height_edges)
        selected_height_edge = all_edges[height_edges.index(bbox_height)][0]
    
    # 分析测量的三条边，选择与Z轴方向最一致的作为高度
    # 确定最终的三条边：长度边、宽度边、高度边
    if length_edge1 >= length_edge2:
        final_length_edge = ((0, 1), world_corners[1] - world_corners[0])
    else:
        final_length_edge = ((4, 5), world_corners[5] - world_corners[4])
    
    if width_edge1 >= width_edge2:
        final_width_edge = ((1, 2), world_corners[2] - world_corners[1])
    else:
        final_width_edge = ((5, 6), world_corners[6] - world_corners[5])
    
    final_height_edge = (selected_height_edge, world_corners[selected_height_edge[1]] - world_corners[selected_height_edge[0]])
    
    # 分析三条边与Z轴的对齐度
    three_edges_data = [
        ("长度", final_length_edge),
        ("宽度", final_width_edge),
        ("高度", final_height_edge)
    ]
    
    max_z_alignment = -1
    best_height_edge = None
    best_height_length = 0
    best_edge_name = ""
    
    for edge_name, (edge_indices, edge_vector) in three_edges_data:
        if edge_vector.length > 0:  # 避免零向量
            # 计算边向量与世界Z轴的夹角余弦值（点积除以长度）
            alignment = abs(edge_vector.normalized().dot(world_z_axis))
            if alignment > max_z_alignment:
                max_z_alignment = alignment
                best_height_edge = edge_indices
                best_height_length = edge_vector.length
                best_edge_name = edge_name
    
    # 初始化最终边索引
    final_length_edge_indices = final_length_edge[0]
    final_width_edge_indices = final_width_edge[0]
    final_height_edge_indices = selected_height_edge
    
    # 如果找到更合适的边作为高度，更新高度值并重新分配剩余两条边
    if best_height_edge and best_edge_name != "高度":
        bbox_height = best_height_length
        final_height_edge_indices = best_height_edge
        
        # 更新高度后，需要将剩下两条边也同步更新（长的那条是长度，小的那条宽度）
        # 收集剩余两条边的数据
        remaining_edges = []
        for edge_name, (edge_indices, edge_vector) in three_edges_data:
            if edge_name != best_edge_name:  # 排除已选为高度的边
                remaining_edges.append((edge_name, edge_indices, edge_vector.length))
        
        # 按长度排序，长的为长度，短的为宽度
        remaining_edges.sort(key=lambda x: x[2], reverse=True)
        
        if len(remaining_edges) >= 2:
            new_length_name, new_length_edge, new_length_value = remaining_edges[0]
            new_width_name, new_width_edge, new_width_value = remaining_edges[1]
            
            # 更新长度和宽度值及边索引
            bbox_length = new_length_value
            bbox_width = new_width_value
            final_length_edge_indices = new_length_edge
            final_width_edge_indices = new_width_edge
    
    # 计算边界框的边界范围（用于绘制）
    world_min_x = min(corner.x for corner in world_corners)
    world_max_x = max(corner.x for corner in world_corners)
    world_min_y = min(corner.y for corner in world_corners)
    world_max_y = max(corner.y for corner in world_corners)
    world_min_z = min(corner.z for corner in world_corners)
    world_max_z = max(corner.z for corner in world_corners)
    
    # 使用改进的表面积计算方法（参照3D print box）
    surface_area_data = calculate_surface_area_3d_print_style(obj)
    if surface_area_data:
        area = surface_area_data['total_area']
        area_info = surface_area_data
    else:
        # 如果计算失败，设置默认值
        area = 0.0
        area_info = {
            'total_area': area,
            'calculation_method': 'CALCULATION_FAILED'
        }
    
    # 直接返回结果（已在上文按Z轴对齐判断选定高度边）
    return {
        'name': obj.name,
        'length': bbox_length,
        'width': bbox_width,
        'height': bbox_height,
        'area': area,
        'volume': bbox_length * bbox_width * bbox_height,
        'bounds': {
            'min_x': world_min_x, 'max_x': world_max_x,
            'min_y': world_min_y, 'max_y': world_max_y,
            'min_z': world_min_z, 'max_z': world_max_z
        },
        'bounds_type': bounds_type,
        'bbox_corners': world_corners,
        'edges_data': {
            'edges': edges,
            'length_edges': [(0, 1), (4, 5)],
            'width_edges': [(1, 2), (5, 6)],
            'height_edges': [(0, 4), (1, 5), (2, 6), (3, 7)],
            'selected_height_edge': selected_height_edge,
            'static_area': area,
            'area_info': area_info
        },
        'final_edges': {
            'length_edge_indices': final_length_edge_indices,
            'width_edge_indices': final_width_edge_indices,
            'height_edge_indices': final_height_edge_indices
        },
        'analysis_info': {
            'max_z_alignment': max_z_alignment,
            'best_edge_name': best_edge_name,
            'height_edge_verification': 'Z_AXIS_ALIGNED'
        }
    }

def get_selected_mesh_measurements():
    """
    获取当前选中网格的测量信息
    
    Returns:
        list: 包含所有选中网格测量信息的列表
    """
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    
    if not selected_objects:
        return []
    
    measurements = []
    
    for obj in selected_objects:
        dims = get_mesh_dimensions(obj)
        if dims:
            measurements.append({
                'name': obj.name,
                'dimensions': dims
            })
    
    return measurements

def print_measurements(measurements):
    """
    打印测量结果
    
    Args:
        measurements: 测量结果列表
    """
    if not measurements:
        return
    
    for item in measurements:
        obj_name = item['name']
        dims = item['dimensions']
        
        print(f"对象: {obj_name} - 长度: {dims['length']:.2f}m, 宽度: {dims['width']:.2f}m, 高度: {dims['height']:.2f}m, 面积: {dims['area']:.2f}m², 体积: {dims['volume']:.2f}m³")
        
# ==================== 操作符类 ====================

class OBJECT_OT_measure_mesh(Operator):
    """测量选中网格对象的尺寸"""
    bl_idname = "object.measure_mesh"
    bl_label = "测量网格"
    bl_description = "测量选中网格对象的长宽高和面积"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """执行测量操作"""
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "请选择至少一个网格对象")
            return {'CANCELLED'}
        
        # 获取测量数据
        new_measurements = get_selected_mesh_measurements()
        
        if not new_measurements:
            self.report({'ERROR'}, "无法获取测量数据")
            return {'CANCELLED'}
        
        # 已在 get_mesh_dimensions 中完成Z轴对齐，无需再次处理
        
        # 获取现有的测量结果
        global measurement_results, show_3d_annotations, object_annotation_states
        
        # 创建现有物体名称的集合，用于检查重复
        existing_object_names = {item.get('name') for item in measurement_results if item and 'name' in item}
        
        # 过滤出新的测量数据（避免重复添加）
        added_measurements = []
        for measurement in new_measurements:
            if measurement and 'name' in measurement:
                if measurement['name'] not in existing_object_names:
                    added_measurements.append(measurement)
                    existing_object_names.add(measurement['name'])
        
        if not added_measurements:
            self.report({'INFO'}, "选中的物体已经测量过了")
            return {'FINISHED'}
        
        # 将新测量数据追加到现有结果中
        measurement_results.extend(added_measurements)
        
        # 打印新添加的测量结果
        print_measurements(added_measurements)
        
        # 存储测量结果到场景属性中
        context.scene['mesh_measurements'] = measurement_results
        
        # 启用3D标注显示
        context.scene['show_3d_annotations'] = True
        show_3d_annotations = True
        
        # 设置新测量物体的标注状态为显示，并初始化面积状态
        global object_area_states
        for measurement in added_measurements:
            if measurement and 'name' in measurement:
                object_annotation_states[measurement['name']] = True
                # 初始化面积状态，记录当前长宽高，设置为当前状态
                dims = measurement['dimensions']
                object_area_states[measurement['name']] = {
                    'current_area': dims.get('area', 0),
                    'recorded_length': dims.get('length', 0),
                    'recorded_width': dims.get('width', 0),
                    'recorded_height': dims.get('height', 0),
                    'is_expired': False,
                    'state': 'current'  # 当前状态，表示面积数据有效
                }
        
        # 启动测量绘制处理器，确保测量后视口能显示标注
        global measurement_draw_handler
        if measurement_draw_handler is None:
            measurement_draw_handler = MeasurementDrawHandler()
        measurement_draw_handler.start(context)
        
        # 启动边界框绘制处理器，确保测量后能显示边界框虚线
        global bounding_box_draw_handler
        if bounding_box_draw_handler is None:
            bounding_box_draw_handler = BoundingBoxDrawHandler()
        bounding_box_draw_handler.start(context)
        
        
        self.report({'INFO'}, f"已测量 {len(added_measurements)} 个新对象，总计 {len(measurement_results)} 个对象")
        return {'FINISHED'}

class OBJECT_OT_toggle_3d_annotations(Operator):
    """切换3D视口标注显示状态"""
    bl_idname = "object.toggle_3d_annotations"
    bl_label = "切换3D标注"
    bl_description = "显示或隐藏3D视口中的测量标注"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global show_3d_annotations, object_annotation_states
        
        # 获取选中的物体
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            # 如果没有选中物体，则切换全局状态
            show_3d_annotations = not show_3d_annotations
            status = "显示" if show_3d_annotations else "隐藏"
            self.report({'INFO'}, f"3D视口标注已{status}（全局）")
        else:
            # 针对选中的物体进行操作
            for obj in selected_objects:
                if obj.name not in object_annotation_states:
                    object_annotation_states[obj.name] = True  # 默认显示
                
                # 切换该物体的标注状态
                object_annotation_states[obj.name] = not object_annotation_states[obj.name]
            
            # 统计显示和隐藏的物体数量
            visible_count = sum(1 for state in object_annotation_states.values() if state)
            hidden_count = len(object_annotation_states) - visible_count
            
            self.report({'INFO'}, f"已切换 {len(selected_objects)} 个物体的标注状态（显示: {visible_count}, 隐藏: {hidden_count}）")
        
        # 刷新界面
        context.area.tag_redraw()
        
        return {'FINISHED'}

class OBJECT_OT_clear_measurements(Operator):
    """清除测量结果"""
    bl_idname = "object.clear_measurements"
    bl_label = "清除结果"
    bl_description = "清除当前的测量结果"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global measurement_results, show_3d_annotations, measurement_draw_handler, bounding_box_draw_handler, object_annotation_states, object_area_states
        
        # 获取选中的物体
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            # 如果没有选中物体，则清除所有测量结果
            measurement_results.clear()
            object_annotation_states.clear()
            object_area_states.clear()
            
            # 清除测量绘制缓存
            if measurement_draw_handler:
                measurement_draw_handler.clear_cache()
                measurement_draw_handler.stop()
                measurement_draw_handler = None
            
            # 停止边界框绘制
            if bounding_box_draw_handler:
                bounding_box_draw_handler.stop()
                bounding_box_draw_handler = None
            
            # 隐藏3D标注
            show_3d_annotations = False
            
            self.report({'INFO'}, "所有测量结果已清除")
        else:
            # 针对选中的物体进行操作
            cleared_count = 0
            for obj in selected_objects:
                obj_name = obj.name
                
                # 从测量结果中移除该物体
                measurement_results = [item for item in measurement_results if item.get('name') != obj_name]
                
                # 从标注状态中移除该物体
                if obj_name in object_annotation_states:
                    del object_annotation_states[obj_name]
                
                # 从面积状态中移除该物体
                if obj_name in object_area_states:
                    del object_area_states[obj_name]
                    cleared_count += 1
            
            # 清除测量绘制缓存中对应物体的数据
            if measurement_draw_handler:
                measurement_draw_handler.clear_cache()
            
            self.report({'INFO'}, f"已清除 {cleared_count} 个物体的测量结果")
        
        # 刷新界面
        context.area.tag_redraw()
        
        return {'FINISHED'}

class OBJECT_OT_refresh_expired_areas(Operator):
    """刷新过期面积数据"""
    bl_idname = "object.refresh_expired_areas"
    bl_label = "刷新面积"
    bl_description = "重新计算并刷新选中物体的过期面积数据"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global measurement_draw_handler, object_area_states, measurement_results
        
        # 获取选中的物体
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "请选择至少一个网格对象")
            return {'CANCELLED'}
        
        refreshed_count = 0
        
        for obj in selected_objects:
            obj_name = obj.name
            
            # 检查该物体是否有过期的面积数据
            if obj_name not in object_area_states:
                continue
                
            area_state = object_area_states[obj_name]
            if area_state.get('state') != 'expired':
                continue
            
            # 重新计算面积数据
            new_dimensions = get_mesh_dimensions(obj)
            if not new_dimensions:
                continue
            
            # 更新测量结果中的面积数据
            for measurement in measurement_results:
                if measurement and measurement.get('name') == obj_name:
                    # 更新面积数据
                    measurement['dimensions']['area'] = new_dimensions['area']
                    measurement['dimensions']['edges_data']['static_area'] = new_dimensions['area']
                    measurement['dimensions']['edges_data']['area_info'] = new_dimensions['edges_data']['area_info']
                    break
            
            # 获取当前的长宽高数据用于记录
            current_bbox_corners = measurement_draw_handler.get_current_bbox_corners(obj, new_dimensions)
            if current_bbox_corners:
                current_dimensions = measurement_draw_handler.calculate_current_dimensions(
                    current_bbox_corners, new_dimensions.get('edges_data', {})
                )
                current_length = current_dimensions.get('length', 0)
                current_width = current_dimensions.get('width', 0)
                current_height = current_dimensions.get('height', 0)
            else:
                current_length = new_dimensions.get('length', 0)
                current_width = new_dimensions.get('width', 0)
                current_height = new_dimensions.get('height', 0)
            
            # 更新面积状态记录
            object_area_states[obj_name] = {
                'current_area': new_dimensions['area'],
                'recorded_length': current_length,
                'recorded_width': current_width,
                'recorded_height': current_height,
                'is_expired': False,
                'state': 'current'  # 设置为当前状态，表示面积数据有效
            }
            
            refreshed_count += 1
        
        # 清除缓存
        if measurement_draw_handler:
            measurement_draw_handler.clear_cache()
        
        if refreshed_count > 0:
            self.report({'INFO'}, f"已刷新 {refreshed_count} 个物体的面积数据")
        else:
            self.report({'INFO'}, "没有找到需要刷新的过期面积数据")
        
        # 刷新界面
        context.area.tag_redraw()
        
        return {'FINISHED'}

def _ensure_collection(collection_name: str):
    """确保目标集合存在并返回它。"""
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    return coll

def _ensure_emission_material(mat_name: str, color=(1.0, 1.0, 1.0, 1.0), strength: float = 3.0):
    """获取或创建一个纯色材质（仅 RGB 直连 Output，不使用 BSDF/Emission）。

    结构：ShaderNodeRGB → Material Output(Surface)
    同步设置视图显示颜色。"""
    mat = bpy.data.materials.get(mat_name)
    # 统一为 RGBA
    col = tuple(color) if len(color) == 4 else (color[0], color[1], color[2], 1.0)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        # 重建简洁的 RGB -> Output 网络
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        rgb = nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = col
        # 连接：RGB -> Surface（直接连输出表面）
        try:
            links.new(rgb.outputs[0], out.inputs["Surface"])
        except Exception:
            # 某些版本可能拒绝不同类型直连，退化为添加发光节点
            emit = nodes.new("ShaderNodeEmission")
            links.new(rgb.outputs[0], emit.inputs["Color"])
            links.new(emit.outputs["Emission"], out.inputs["Surface"])
        # 渲染设置
        mat.blend_method = 'OPAQUE'
        mat.shadow_method = 'NONE'
        mat.use_backface_culling = True
        # 视图显示颜色（Viewport Display）
        mat.diffuse_color = col
    else:
        # 更新为 RGB -> Output，如果不是该结构则重建
        if mat.use_nodes and mat.node_tree:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            # 简单策略：总是重建为目标结构，避免历史材质形态复杂导致不一致
            for n in list(nodes):
                nodes.remove(n)
            out = nodes.new("ShaderNodeOutputMaterial")
            rgb = nodes.new("ShaderNodeRGB")
            rgb.outputs[0].default_value = col
            try:
                links.new(rgb.outputs[0], out.inputs["Surface"])
            except Exception:
                emit = nodes.new("ShaderNodeEmission")
                links.new(rgb.outputs[0], emit.inputs["Color"])
                links.new(emit.outputs["Emission"], out.inputs["Surface"])
        mat.diffuse_color = col
    return mat

def _ensure_principled_gray_alpha_material(mat_name: str, alpha: float = 1.0):
    """获取或创建一个灰色原理化BSDF材质，Alpha=alpha。

    节点结构：Principled BSDF → Material Output(Surface)
    渲染设置启用透明混合以生效Alpha。
    """
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # 重建为 Principled → Output
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    # 灰色基色
    try:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    except Exception:
        pass
    # 设置Alpha
    try:
        bsdf.inputs["Alpha"].default_value = float(alpha)
    except Exception:
        pass
    try:
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    except Exception:
        try:
            links.new(bsdf.outputs[0], out.inputs[0])
        except Exception:
            pass
    # 若alpha<1启用透明混合，否则使用不透明
    try:
        mat.blend_method = 'BLEND' if float(alpha) < 1.0 else 'OPAQUE'
    except Exception:
        pass
    return mat

def _ensure_bold_font_datablock():
    """确保加载并返回一个粗体字体(Font)数据块。

    优先尝试常见的 Windows 粗体字体；若 `bpy.ops.font.open` 失败，则回退到 `bpy.data.fonts.load`。
    返回可直接赋给 `Curve.font`/`Curve.font_bold` 的 Font 对象；失败返回 None。
    """
    candidate_paths = [
        r"C:\\Windows\\Fonts\\msyhbd.ttc",   # 微软雅黑 粗体（若存在）
        r"C:\\Windows\\Fonts\\simhei.ttf",   # 黑体
        r"C:\\Windows\\Fonts\\arialbd.ttf", # Arial Bold
    ]
    for path in candidate_paths:
        if not os.path.exists(path):
            continue
        # 优先通过 ops 载入（满足用户“使用 bpy.ops.font.open()”的需求）
        try:
            bpy.ops.font.open(filepath=path)
        except Exception:
            pass
        # 在已载入字体中查找同一路径的 Font
        try:
            for f in bpy.data.fonts:
                if getattr(f, 'filepath', None) and os.path.normcase(os.path.abspath(f.filepath)) == os.path.normcase(os.path.abspath(path)):
                    return f
        except Exception:
            pass
        # 回退直接 load
        try:
            return bpy.data.fonts.load(path)
        except Exception:
            pass
    return None

def _create_curve_segment(obj_name: str, start, end, color=(1.0, 1.0, 1.0, 1.0), bevel: float = 0.003):
    """创建一条两点的3D曲线线段，并附加发光材质。"""
    crv = bpy.data.curves.new(name=obj_name, type='CURVE')
    crv.dimensions = '3D'
    spline = crv.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (start.x, start.y, start.z, 1.0)
    spline.points[1].co = (end.x, end.y, end.z, 1.0)
    crv.bevel_depth = bevel

    obj = bpy.data.objects.new(obj_name, crv)
    mat = _ensure_emission_material(f"Mat_{obj_name}", color=color, strength=3.0)
    obj.data.materials.append(mat)
    return obj

def _create_text_label(obj_name: str, text: str, location, color=(1.0, 1.0, 1.0, 1.0), size: float = 0.2, face_camera: bool = True):
    """创建文本(FONT)对象作为标注，赋予纯色材质，可选朝向相机。"""
    cu = bpy.data.curves.new(name=obj_name, type='FONT')
    cu.body = text
    cu.size = size
    # 使用粗体字体：通过 bpy.ops.font.open 加载常见粗体字形，并赋给 font/font_bold
    try:
        bold_font = _ensure_bold_font_datablock()
        if bold_font is not None:
            cu.font = bold_font
            cu.font_bold = bold_font
    except Exception:
        pass
    # 模拟粗体：适度增加偏移和挤出厚度（随字号按比例放大）
    try:
        cu.offset = max(0.0, 0.00 * size)
    except Exception:
        pass
    try:
        cu.extrude = max(0.0, 0.25 * size)
    except Exception:
        pass
    # 居中对齐，文本在中点更自然
    try:
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
    except Exception:
        pass
    obj = bpy.data.objects.new(obj_name, cu)
    obj.location = location
    mat = _ensure_emission_material(f"Mat_{obj_name}", color=color)
    obj.data.materials.append(mat)
    if face_camera:
        try:
            _attach_face_camera_geonodes(
                obj,
                bpy.context.scene.camera if getattr(bpy.context.scene, "camera", None) else None,
                axis='Z'
            )
            # 校验是否成功创建了几何节点修改器
            if not any(
                (m.type == 'NODES' and getattr(m, 'node_group', None) and m.name == 'AF_FaceCamera')
                for m in obj.modifiers
            ):
                raise RuntimeError('AF_FaceCamera 未挂载成功')
        except Exception:
            # 回退到约束方案（兜底）
            try:
                cam = getattr(bpy.context.scene, 'camera', None)
                if cam is None:
                    for ob in bpy.data.objects:
                        if ob.type == 'CAMERA':
                            cam = ob
                            break
                if cam is not None:
                    c = obj.constraints.new('TRACK_TO')
                    c.target = cam
                    c.track_axis = 'TRACK_Z'
                    c.up_axis = 'UP_Y'
            except Exception:
                pass
    return obj

def _compute_label_position(p0, p1, sign: float = 1.0, scale: float = 0.08, min_offset: float = 0.05):
    """根据线段与相机方向计算文本位置，尽量放置在物体“上侧”，避免与线重叠。

    规则：
    - 以线段中点为基准
    - 使用 线方向 × 视线方向 得到侧向偏移方向（屏幕视角下垂直于线）
    - 将侧向偏移方向的 z 分量调整为非负（尽可能朝世界 +Z），使文本趋向于位于对象之上
    - 偏移距离与线长成比例，且不小于最小偏移
    - 额外增加少量世界 +Z 偏移，避免极端角度下仍落到对象下侧
    - sign 用于让不同标签分布在两侧，避免相互遮挡
    """
    mid = (p0 + p1) / 2
    direction = (p1 - p0)
    length = direction.length
    if length == 0:
        return mid
    direction.normalize()

    # 视线方向
    cam = bpy.context.scene.camera
    if cam is not None:
        view_vec = (mid - cam.matrix_world.translation)
        if view_vec.length > 0:
            view_vec.normalize()
        else:
            view_vec = Vector((0, 0, 1))
    else:
        view_vec = Vector((0, 0, 1))

    # 侧向偏移方向：线方向 × 视线方向
    lateral = direction.cross(view_vec)
    if lateral.length == 0:
        # 退化时，改用与世界Z叉乘的结果
        lateral = direction.cross(Vector((0, 0, 1)))
    if lateral.length == 0:
        return mid
    lateral.normalize()
    # 尽量让偏移朝世界+Z方向（上方）
    if lateral.z < 0:
        lateral = -lateral

    offset = max(min_offset, scale * length)
    pos = mid + lateral * (sign * offset)
    # 加一点固定的世界+Z上移，避免极端相机角度下仍显得偏下
    pos = pos + Vector((0.0, 0.0, max(0.0, 0.5 * min_offset)))
    return pos

def _ensure_face_camera_node_group():
    """确保/重建几何节点组 AF_FaceCamera 并返回。

    目标结构（与截图一致，最小可用方案）：
    - 组输入: 仅 `Geometry`
    - 输入节点: `Active Camera` → `Object Info`
    - `Object Info.Rotation` → `Transform Geometry.Rotation`
    - `Group Input.Geometry` → `Transform Geometry.Geometry` → `Group Output.Geometry`

    兼容性：若无法创建 `Active Camera` 节点，则直接把场景相机赋给 `Object Info` 的对象输入。
    """
    group_name = "AF_FaceCamera"
    ng = bpy.data.node_groups.get(group_name)
    if ng and ng.bl_idname == 'GeometryNodeTree':
        # 清空并重建，保持 ID 不变
        try:
            try:
                ng.interface.clear()
            except Exception:
                try:
                    for item in list(getattr(ng.interface, 'items_tree', [])):
                        ng.interface.remove(item)
                except Exception:
                    pass
            ng.nodes.clear()
        except Exception:
            pass
    else:
        ng = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    nodes = ng.nodes
    links = ng.links

    # 定义接口：仅 Geometry in/out
    iface = ng.interface
    def _new_iface_socket(name, in_out, socket_type):
        try:
            return iface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
        except Exception:
            return None

    _new_iface_socket('Geometry', 'INPUT', 'NodeSocketGeometry')
    _new_iface_socket('Geometry', 'OUTPUT', 'NodeSocketGeometry')

    # IO 节点
    n_in = nodes.new('NodeGroupInput')
    n_out = nodes.new('NodeGroupOutput')
    n_in.location = (-600, 0)
    n_out.location = (300, 0)

    # 构建简化网络
    # 活动摄像机（优先 ActiveCamera，其次 SceneCamera）
    active_cam = None
    for type_name in ('GeometryNodeInputActiveCamera', 'GeometryNodeInputSceneCamera'):
        try:
            active_cam = nodes.new(type_name)
            active_cam.location = (-600, -180)
            break
        except Exception:
            active_cam = None
            continue

    # 对象信息（读取相机的旋转）
    obj_info = nodes.new('GeometryNodeObjectInfo')
    obj_info.location = (-350, -180)
    try:
        obj_info.as_instance = False
    except Exception:
        pass

    # 变换几何体
    try:
        transform = nodes.new('GeometryNodeTransformGeometry')
    except Exception:
        transform = nodes.new('GeometryNodeTransform')
    transform.location = (-120, 0)

    # 连接：Group In Geometry → Transform Geometry
    try:
        links.new(n_in.outputs['Geometry'], transform.inputs['Geometry'])
    except Exception:
        links.new(n_in.outputs[0], transform.inputs[0])

    # 连接：相机 → 对象信息
    if active_cam is not None:
        # 兼容不同版本输出口命名
        linked = False
        for out_name in ('Active Camera', 'Camera'):
            if not linked:
                try:
                    links.new(active_cam.outputs[out_name], obj_info.inputs['Object'])
                    linked = True
                except Exception:
                    pass
        if not linked:
            # 兜底按索引
            try:
                links.new(active_cam.outputs[0], obj_info.inputs[0])
                linked = True
            except Exception:
                pass
    else:
        # 无活动摄像机节点可用时，直接使用场景相机
        try:
            obj_info.inputs['Object'].default_value = bpy.context.scene.camera
        except Exception:
            pass

    # 连接：对象信息 Rotation → Transform Geometry Rotation
    try:
        links.new(obj_info.outputs['Rotation'], transform.inputs['Rotation'])
    except Exception:
        try:
            links.new(obj_info.outputs[1], transform.inputs[2])
        except Exception:
            pass

    # 连接：Transform Geometry → Group Output
    try:
        links.new(transform.outputs['Geometry'], n_out.inputs['Geometry'])
    except Exception:
        links.new(transform.outputs[0], n_out.inputs[0])

    return ng

def _attach_face_camera_geonodes(text_obj, camera_obj, axis: str = 'Z'):
    """将 AF_FaceCamera 节点组以几何节点修改器挂到文本对象上。"""
    ng = _ensure_face_camera_node_group()
    # 兜底获取相机
    cam = camera_obj
    if cam is None:
        cam = bpy.context.scene.camera
    if cam is None:
        for ob in bpy.data.objects:
            if ob.type == 'CAMERA':
                cam = ob
                break
    if cam is None:
        print('[AF_FaceCamera] 未找到相机，跳过几何节点挂载。')
        return
    mod = text_obj.modifiers.new(name='AF_FaceCamera', type='NODES')
    mod.node_group = ng
    # 输入按顺序：Geometry, Camera, Self, Axis, Up
    # 设置对象输入
    def _set_any(m, keys, value):
        for k in keys:
            try:
                m[k] = value
                return True
            except Exception:
                continue
        return False

    axis_map = {'X': 0, 'Y': 1, 'Z': 2}
    _set_any(mod, ('Input_2','Socket_2'), cam)
    _set_any(mod, ('Input_3','Socket_3'), text_obj)
    _set_any(mod, ('Input_4','Socket_4'), axis_map.get(axis.upper(), 2))
    _set_any(mod, ('Input_5','Socket_5'), (0.0, 0.0, 1.0))
    _set_any(mod, ('Input_6','Socket_6'), True)
    _set_any(mod, ('Input_7','Socket_7'), False)
    _set_any(mod, ('Input_8','Socket_8'), 0.0)
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass

class OBJECT_OT_bake_annotation_curves(Operator):
    """将当前选中物体的边界框烘焙为对应方体网格，便于渲染/导出"""
    bl_idname = "object.bake_annotation_curves"
    bl_label = "烘焙边界框方体"
    bl_description = "把测量对象的边界框转为方体网格并放入集合"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name: bpy.props.StringProperty(
        name="集合名",
        description="用于承载烘焙标注曲线的集合",
        default="Measurement_Annotations"
    )

    line_bevel: bpy.props.FloatProperty(
        name="线径",
        description="测量线的曲线圆角半径（粗细）",
        default=0.01,
        min=0.01,
        max=0.05
    )

    text_size: bpy.props.FloatProperty(
        name="文字大小",
        description="烘焙文本的字号（世界单位）",
        default=0.2,
        min=0.01,
        max=5.0
    )

    text_face_camera: bpy.props.BoolProperty(
        name="文字朝向相机",
        description="给文本添加朝向相机约束以保持可读",
        default=True
    )

    label_offset_scale: bpy.props.FloatProperty(
        name="文字偏移比例",
        description="文本相对于线段长度的侧向偏移比例，避免与线重叠",
        default=0.08,
        min=0.0,
        max=1.0
    )

    label_min_offset: bpy.props.FloatProperty(
        name="文字最小偏移",
        description="文本与线段的最小距离（世界单位）",
        default=0.05,
        min=0.0,
        max=1.0
    )
    
    def execute(self, context):
        global measurement_results, measurement_draw_handler

        # 如果还没有测量数据，则先对选中对象执行一次测量
        if not measurement_results:
            bpy.ops.object.measure_mesh('INVOKE_DEFAULT')
            if not measurement_results:
                self.report({'WARNING'}, "没有可烘焙的标注数据")
            return {'CANCELLED'}
        
        # 改为：将烘焙对象链接到源对象所在的集合中（若无则退回到场景根集合）

        baked_count = 0
        for item in measurement_results:
            obj = bpy.data.objects.get(item.get('name'))
            if obj is None or obj.type != 'MESH':
                continue

            # 获取动态边界框与最终三边
            corners = measurement_draw_handler.get_current_bbox_corners(obj, item['dimensions'])
            if not corners:
                continue

            dims = measurement_draw_handler.calculate_current_dimensions(
                corners, item['dimensions'].get('edges_data', {})
            )
            final_edges = dims.get('final_edges', {})
            le = final_edges.get('length_edge_indices', (0, 1))
            we = final_edges.get('width_edge_indices', (1, 2))
            he = final_edges.get('height_edge_indices', (0, 4))

            # 分组一个父对象，便于整体管理
            root = bpy.data.objects.new(f"Annot_{obj.name}", None)
            root.empty_display_type = 'PLAIN_AXES'

            # 源对象所在集合（可能有多个）；若无则退回到场景根集合
            src_colls = list(obj.users_collection)
            if not src_colls:
                src_colls = [bpy.context.scene.collection]

            # 链接根对象到与源对象相同的集合
            for coll in src_colls:
                try:
                    coll.objects.link(root)
                except Exception:
                    pass

            # 设置父子关系：Annot_<obj> 作为源对象的子物体
            root.parent = obj
            try:
                root.matrix_parent_inverse = obj.matrix_world.inverted()
            except Exception:
                pass

            # 生成“边界框方体”网格对象
            try:
                length_val = dims.get('length', 0.0)
                width_val  = dims.get('width', 0.0)
                height_val = dims.get('height', 0.0)
                area_val_for_prop = dims.get('area', 0.0) or dims.get('edges_data', {}).get('static_area', 0.0)
                obj["data"] = f'DATA"{obj.name}  L:{length_val:.2f}m  W:{width_val:.2f}m  H:{height_val:.2f}m  A:{area_val_for_prop:.2f}㎡"'
            except Exception:
                pass

            # 使用当前 world 空间 8 个角点创建方体网格
            try:
                mesh = bpy.data.meshes.new(f"{obj.name}_bbox_mesh")
                verts = [(v.x, v.y, v.z) for v in corners]
                faces = [
                    (0, 1, 2, 3),  # 底面
                    (4, 5, 6, 7),  # 顶面
                    (0, 1, 5, 4),  # 侧面1
                    (1, 2, 6, 5),  # 侧面2
                    (2, 3, 7, 6),  # 侧面3
                    (3, 0, 4, 7)   # 侧面4
                ]
                mesh.from_pydata(verts, [], faces)
                try:
                    mesh.validate(clean_customdata=True)
                except Exception:
                    pass
                mesh.update()
                
                # 统一并校正法线朝向：确保六个四边面法线朝外
                try:
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    # 先计算一致法线
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
                    bm.normal_update()
                    # 判断整体朝向是否内翻：若面法线与(面心-网格中心)的点积累计为负，则整体反转
                    if len(bm.verts) > 0 and len(bm.faces) > 0:
                        center = Vector((0.0, 0.0, 0.0))
                        for v in bm.verts:
                            center += v.co
                        center /= len(bm.verts)
                        acc = 0.0
                        for f in bm.faces:
                            fc = f.calc_center_median()
                            acc += f.normal.dot(fc - center)
                        if acc < 0.0:
                            try:
                                bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
                            except Exception:
                                for f in bm.faces:
                                    f.normal_flip()
                    bm.normal_update()
                    bm.to_mesh(mesh)
                    bm.free()
                except Exception:
                    pass

                bbox_obj = bpy.data.objects.new(f"{obj.name}_bbox", mesh)

                # 赋予灰色原理化BSDF，Alpha=1
                try:
                    mat = _ensure_principled_gray_alpha_material(f"Mat_BBox_{obj.name}", alpha=1.0)
                    bbox_obj.data.materials.append(mat)
                except Exception:
                    pass

                # 不需要实体化修改器：移除SOLIDIFY逻辑
                

                # 添加线框修改器，实现方体线框化显示（厚度固定0.1m）
                try:
                    wire = bbox_obj.modifiers.new(name='BBox_Wire', type='WIREFRAME')
                    # 固定厚度为0.1m
                    try:
                        wire.thickness = 0.1
                    except Exception:
                        pass
                    # 常用参数：均匀偏移、替换面为线框
                    try:
                        wire.use_even_offset = True
                    except Exception:
                        pass
                    try:
                        # 替换原始面，仅保留线框几何
                        wire.use_replace = True
                    except Exception:
                        pass
                except Exception:
                    pass

                # 链接到源对象集合并设父子关系
                for coll in src_colls:
                    try:
                        coll.objects.link(bbox_obj)
                    except Exception:
                        pass
                bbox_obj.parent = root

                # 为所有平行边创建对应的 L/W/H 文本，放置在每条边的中点
                try:
                    all_edges = build_all_edges(corners)
                    parallel_groups = group_parallel_edges(all_edges)
                    # 找到与 L/W/H 三组对应的分组索引
                    group_map = {}
                    for gi, group in enumerate(parallel_groups):
                        edge_indices_list = [ei for (ei, _) in group]
                        if le in edge_indices_list:
                            group_map[gi] = ('L', (1.0, 0.0, 0.0, 1.0), dims.get('length', 0.0), '长度')
                        elif we in edge_indices_list:
                            group_map[gi] = ('W', (0.0, 1.0, 0.0, 1.0), dims.get('width', 0.0), '宽度')
                        elif he in edge_indices_list:
                            group_map[gi] = ('H', (0.0, 0.0, 1.0, 1.0), dims.get('height', 0.0), '高度')
                    # 遍历三组并在每条边中点生成对应文本
                    for gi, group in enumerate(parallel_groups):
                        if gi not in group_map:
                            continue
                        letter, color, value, cname = group_map[gi]
                        for (edge_indices, _) in group:
                            i, j = edge_indices
                            mid = (corners[i] + corners[j]) / 2
                            label = f"{letter}({cname}): {value:.2f}m"
                            txt = _create_text_label(
                                f"{obj.name}_{letter}_{i}_{j}",
                                label,
                                mid,
                                color=color,
                                size=float(self.text_size) * 2.5,
                                face_camera=bool(self.text_face_camera)
                            )
                            for coll in src_colls:
                                try:
                                    coll.objects.link(txt)
                                except Exception:
                                    pass
                            txt.parent = root
                            # 若尚未存在 AF_FaceCamera 修改器，则挂载（避免重复）
                            try:
                                has_face_cam = any(
                                    (m.type == 'NODES' and getattr(m, 'node_group', None) and m.name == 'AF_FaceCamera')
                                    for m in txt.modifiers
                                )
                                if not has_face_cam:
                                    _attach_face_camera_geonodes(
                                        txt,
                                        context.scene.camera if getattr(context.scene, "camera", None) else None,
                                        axis='Z'
                                    )
                            except Exception:
                                pass
                except Exception:
                    pass

                # 生成六面方向文本：与对象局部坐标系一致（按局部 ±X/±Y/±Z 在世界中的方向选择面）
                try:
                    face_defs = [
                        (0, 1, 2, 3),  # 底面
                        (4, 5, 6, 7),  # 顶面
                        (0, 1, 5, 4),  # 侧面1
                        (1, 2, 6, 5),  # 侧面2
                        (2, 3, 7, 6),  # 侧面3
                        (3, 0, 4, 7),  # 侧面4
                    ]

                    # 盒心（用于将法线统一为外向）
                    bbox_center = sum(corners, Vector((0.0, 0.0, 0.0))) / 8.0

                    face_centers = []
                    face_normals = []
                    for a, b, c, d in face_defs:
                        v0, v1, v2, v3 = corners[a], corners[b], corners[c], corners[d]
                        center = (v0 + v1 + v2 + v3) / 4
                        n = (v1 - v0).cross(v2 - v0)
                        if n.length > 0:
                            n.normalize()
                        # 保证外向
                        if (center - bbox_center).dot(n) < 0:
                            n = -n
                        face_centers.append(center)
                        face_normals.append(n)

                    # 对象局部坐标轴在世界空间的方向
                    local_to_world = obj.matrix_world.to_3x3()
                    x_axis = (local_to_world @ Vector((1.0, 0.0, 0.0))).normalized()
                    y_axis = (local_to_world @ Vector((0.0, 1.0, 0.0))).normalized()
                    z_axis = (local_to_world @ Vector((0.0, 0.0, 1.0))).normalized()

                    axis_map = {
                        "+X": x_axis,
                        "-X": -x_axis,
                        "+Y": y_axis,
                        "-Y": -y_axis,
                        "+Z": z_axis,
                        "-Z": -z_axis,
                    }

                    # 为每个标签选择与其轴向最对齐的面
                    label_to_index = {}
                    for lab, axis_vec in axis_map.items():
                        best_i = -1
                        best_dot = -1.0
                        for i, n in enumerate(face_normals):
                            d = n.dot(axis_vec)
                            if d > best_dot:
                                best_dot = d
                                best_i = i
                        label_to_index[lab] = best_i

                    # 去重：避免极端情况下同一面被分配给两个标签
                    used = set()
                    for lab in ("+X", "-X", "+Y", "-Y", "+Z", "-Z"):
                        i = label_to_index.get(lab, -1)
                        if i < 0:
                            continue
                        # 若已被占用，跳过（理论上不会在正交盒发生）
                        if i in used:
                            continue
                        used.add(i)
                        center = face_centers[i]
                        txt = _create_text_label(
                            f"{obj.name}_face_{lab}",
                            lab,
                            center,
                            color=(1.0, 1.0, 1.0, 1.0),
                            size=float(self.text_size) * 2.5,
                            face_camera=bool(self.text_face_camera),
                        )
                        for coll in src_colls:
                            try:
                                coll.objects.link(txt)
                            except Exception:
                                pass
                        txt.parent = root
                        # 若尚未存在 AF_FaceCamera 修改器，则挂载（避免重复）
                        try:
                            has_face_cam = any(
                                (m.type == 'NODES' and getattr(m, 'node_group', None) and m.name == 'AF_FaceCamera')
                                for m in txt.modifiers
                            )
                            if not has_face_cam:
                                _attach_face_camera_geonodes(
                                    txt,
                                    context.scene.camera if getattr(context.scene, "camera", None) else None,
                                    axis='Z'
                                )
                        except Exception:
                            pass
                except Exception:
                    pass

                # 视图显示：仅线框
                try:
                    bbox_obj.display_type = 'WIRE'
                except Exception:
                    pass
            except Exception:
                pass

            baked_count += 1

        self.report({'INFO'}, f"已烘焙 {baked_count} 个对象的边界框方体到源对象集合")
        return {'FINISHED'}

class OBJECT_OT_remove_annotation_curves(Operator):
    """移除选中物体对应的烘焙对象（按名称查找 Annot_前缀的根对象）"""
    bl_idname = "object.remove_annotation_curves"
    bl_label = "移除烘焙对象"
    bl_description = "删除选中物体的烘焙对象及其子对象"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "请选择至少一个网格对象")
            return {'CANCELLED'}

        removed_count = 0
        for src in selected_objects:
            root_name = f"Annot_{src.name}"
            root = bpy.data.objects.get(root_name)
            if root is None:
                continue

            # 收集并移除子对象
            children = [o for o in bpy.data.objects if o.parent == root]
            for child in children:
                try:
                    bpy.data.objects.remove(child, do_unlink=True)
                except Exception:
                    pass
            # 最后移除根对象
            try:
                bpy.data.objects.remove(root, do_unlink=True)
                removed_count += 1
            except Exception:
                pass

        if removed_count:
            self.report({'INFO'}, f"已移除 {removed_count} 个物体的烘焙对象")
        else:
            self.report({'INFO'}, "选中物体未发现已烘焙对象")
        return {'FINISHED'}

# ==================== 面板类与调试辅助 ====================

class OBJECT_OT_build_face_camera_ng(Operator):
    """手动创建/重建 AF_FaceCamera 节点组（调试辅助）"""
    bl_idname = "object.build_face_camera_ng"
    bl_label = "创建AF_FaceCamera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            ng = _ensure_face_camera_node_group()
            # Blender 4.x: 统计接口输入/输出需要通过 interface
            try:
                iface_items = list(getattr(ng.interface, 'items_tree', []))
                input_count = sum(1 for it in iface_items if getattr(it, 'in_out', None) == 'INPUT')
                output_count = sum(1 for it in iface_items if getattr(it, 'in_out', None) == 'OUTPUT')
            except Exception:
                input_count = output_count = 0
            msg = f"节点组 {ng.name} 构建完成：节点数={len(ng.nodes)}, 输入={input_count}, 输出={output_count}"
            print('[AF_FaceCamera]', msg)
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"创建失败: {e}")
            return {'CANCELLED'}

class OBJECT_OT_attach_face_camera_to_texts(Operator):
    """给选中文本对象挂载 AF_FaceCamera（调试辅助）"""
    bl_idname = "object.attach_face_camera_to_texts"
    bl_label = "挂到选中文本"
    bl_options = {'REGISTER', 'UNDO'}

    axis: bpy.props.EnumProperty(
        name="轴向",
        items=(('X','X',''),('Y','Y',''),('Z','Z','')),
        default='Z'
    )

    def execute(self, context):
        _ensure_face_camera_node_group()
        cam = context.scene.camera
        attached = 0
        for obj in context.selected_objects:
            if obj.type == 'FONT':
                try:
                    _attach_face_camera_geonodes(obj, cam, axis=self.axis)
                    attached += 1
                except Exception as e:
                    print('[AF_FaceCamera] 挂载失败:', obj.name, e)
        if attached:
            self.report({'INFO'}, f"已挂载到 {attached} 个文本对象")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "未选中文本对象")
            return {'CANCELLED'}

class OBJECT_PT_mesh_measurements(Panel):
    """网格测量工具面板"""
    bl_label = "objectmeasure"
    bl_idname = "OBJECT_PT_mesh_measurements"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "objectmeasure"
    
    def draw(self, context):
        layout = self.layout
        
        # 操作按钮 - 放在同一行
        row = layout.row()
        row.operator("object.measure_mesh", text="测量", icon='DRIVER_DISTANCE')
        row.operator("object.clear_measurements", text="清除", icon='X')
        row.operator("object.refresh_expired_areas", text="刷新", icon='FILE_REFRESH')
        
        # 3D标注控制 - 放在同一行
        icon = 'HIDE_OFF' if show_3d_annotations else 'HIDE_ON'
        text = "隐藏" if show_3d_annotations else "显示"
        row.operator("object.toggle_3d_annotations", text=text, icon=icon)
        
        # 烘焙/移除曲线标注（根据当前选择状态切换显示）
        row2 = layout.row()
        # 选区内若有任一对象存在名为 Annot_<obj> 的根对象，则显示移除按钮
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        has_baked = False
        for o in selected_meshes:
            if bpy.data.objects.get(f"Annot_{o.name}") is not None:
                has_baked = True
                break
        if has_baked:
            row2.operator("object.remove_annotation_curves", text="移除烘焙对象", icon='TRASH')
        else:
            row2.operator("object.bake_annotation_curves", text="烘焙边界框方体", icon='OUTLINER_COLLECTION')
        # 调试辅助按钮已移除（仍可通过搜索菜单调用对应操作符）
        

# ==================== 注册函数 ====================

def register():
    """注册所有类和属性"""
    bpy.utils.register_class(OBJECT_OT_measure_mesh)
    bpy.utils.register_class(OBJECT_OT_clear_measurements)
    bpy.utils.register_class(OBJECT_OT_toggle_3d_annotations)
    bpy.utils.register_class(OBJECT_OT_refresh_expired_areas)
    bpy.utils.register_class(OBJECT_OT_bake_annotation_curves)
    bpy.utils.register_class(OBJECT_OT_remove_annotation_curves)
    bpy.utils.register_class(OBJECT_OT_build_face_camera_ng)
    bpy.utils.register_class(OBJECT_OT_attach_face_camera_to_texts)
    bpy.utils.register_class(OBJECT_PT_mesh_measurements)

def unregister():
    """注销所有类和属性"""
    global measurement_draw_handler, bounding_box_draw_handler, object_annotation_states, object_collapse_states, object_area_states
    
    # 停止测量绘制并清除缓存
    if measurement_draw_handler is not None:
        measurement_draw_handler.clear_cache()
        measurement_draw_handler.stop()
        measurement_draw_handler = None
    
    # 停止边界框绘制
    if bounding_box_draw_handler is not None:
        bounding_box_draw_handler.stop()
        bounding_box_draw_handler = None
    
    # 清理物体状态
    object_annotation_states.clear()
    object_collapse_states.clear()
    object_area_states.clear()
    
    bpy.utils.unregister_class(OBJECT_PT_mesh_measurements)
    bpy.utils.unregister_class(OBJECT_OT_attach_face_camera_to_texts)
    bpy.utils.unregister_class(OBJECT_OT_build_face_camera_ng)
    bpy.utils.unregister_class(OBJECT_OT_toggle_3d_annotations)
    bpy.utils.unregister_class(OBJECT_OT_clear_measurements)
    bpy.utils.unregister_class(OBJECT_OT_measure_mesh)
    bpy.utils.unregister_class(OBJECT_OT_refresh_expired_areas)
    bpy.utils.unregister_class(OBJECT_OT_bake_annotation_curves)
    bpy.utils.unregister_class(OBJECT_OT_remove_annotation_curves)

# 如果直接运行此脚本
if __name__ == "__main__":
    # 先尝试注销，避免重复注册错误
    try:
        unregister()
    except:
        pass
    
    # 注册插件
    register()