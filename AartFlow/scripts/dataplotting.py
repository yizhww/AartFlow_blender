bl_info = {
    "name": "AartFlow 曲线定长片段提取",
    "author": "AartFlow",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D 视图 > 侧栏 AartFlow 面板",
    "description": "从选中的曲线对象上，按沿程距离提取固定长度的一段片段，生成新的曲线对象",
    "category": "Object",
}

import bpy
from mathutils import Vector
from typing import Dict, List, Tuple, Optional, Set


def _build_ordered_polyline_from_mesh(obj_eval: bpy.types.Object) -> Optional[List[Vector]]:
    """从评估后的曲线对象生成的网格里提取有序折线点列（世界坐标）。

    - 适用于任意曲线类型（Bezier/NURBS/Poly），通过 evaluated 对象转 Mesh 的结果边集合来重建路径。
    - 如果包含多个不相连的子路径，返回其中长度最大的那条。
    """

    depsgraph = bpy.context.evaluated_depsgraph_get()

    # 生成临时网格（保持原对象不变）
    mesh = obj_eval.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
    try:
        if not mesh or len(mesh.vertices) == 0 or len(mesh.edges) == 0:
            return None

        # 邻接表：顶点 -> 相邻顶点列表
        adjacency: Dict[int, List[int]] = {}
        for e in mesh.edges:
            v0, v1 = e.vertices[0], e.vertices[1]
            adjacency.setdefault(v0, []).append(v1)
            adjacency.setdefault(v1, []).append(v0)

        # 按连通分量拆分，逐个重建有序路径
        visited: Set[int] = set()
        all_polylines: List[List[int]] = []

        def walk_component(start_v: int) -> List[int]:
            # 找到度为1的端点，优先用它作为路径起点；没有端点（环）则使用start_v
            component: Set[int] = set()
            stack = [start_v]
            while stack:
                v = stack.pop()
                if v in component:
                    continue
                component.add(v)
                for nb in adjacency.get(v, []):
                    if nb not in component:
                        stack.append(nb)

            endpoints = [v for v in component if len(adjacency.get(v, [])) == 1]
            if endpoints:
                path_start = endpoints[0]
            else:
                # 环：从任意点开始
                path_start = next(iter(component))

            ordered: List[int] = [path_start]
            prev: Optional[int] = None
            curr: int = path_start
            # 在环的情况下，需要遍历 component.size 次；在链的情况下，遇到端点会停止
            for _ in range(len(component) * 2):
                neighbors = adjacency.get(curr, [])
                next_candidates = [n for n in neighbors if n != prev]
                if not next_candidates:
                    break
                nxt = next_candidates[0]
                ordered.append(nxt)
                prev, curr = curr, nxt
                if not endpoints and curr == path_start:
                    # 回到起点，闭环
                    break
            return ordered

        # 遍历所有顶点，构建所有连通路径
        for v_idx in range(len(mesh.vertices)):
            if v_idx in visited or v_idx not in adjacency:
                continue
            comp_order = walk_component(v_idx)
            for vi in comp_order:
                visited.add(vi)
            if len(comp_order) >= 2:
                all_polylines.append(comp_order)

        if not all_polylines:
            return None

        # 选择几何长度最大的那条折线
        mw = obj_eval.matrix_world.copy()

        def polyline_length(vids: List[int]) -> float:
            length = 0.0
            for i in range(1, len(vids)):
                a = mw @ mesh.vertices[vids[i - 1]].co
                b = mw @ mesh.vertices[vids[i]].co
                length += (b - a).length
            return length

        best_vids = max(all_polylines, key=polyline_length)
        world_points = [mw @ mesh.vertices[i].co.copy() for i in best_vids]
        return world_points
    finally:
        # 清理临时网格
        obj_eval.to_mesh_clear()


def _extract_segment_points(points: List[Vector], start_distance: float, segment_length: float) -> List[Vector]:
    """从有序折线点列里，按沿程距离裁剪出区间 [s, s+L] 的点列，包含端点插值。"""
    if not points or len(points) < 2:
        return []
    total = 0.0
    segs: List[Tuple[Vector, Vector, float]] = []  # (a, b, seg_length)
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        seg_len = (b - a).length
        if seg_len > 0:
            segs.append((a, b, seg_len))
            total += seg_len

    if segment_length <= 0 or total <= 0:
        return []

    s = max(0.0, min(start_distance, total))
    e = max(0.0, min(s + segment_length, total))
    if e <= s:
        return []

    out: List[Vector] = []
    acc = 0.0
    # 查找与插入起点
    for a, b, seg_len in segs:
        if acc + seg_len < s:
            acc += seg_len
            continue
        t = (s - acc) / seg_len if seg_len > 0 else 0.0
        p_start = a.lerp(b, t)
        out.append(p_start)
        break

    # 继续填充中间完整顶点与终点
    acc = 0.0
    added_full = False
    curr_dist = 0.0
    # 重新累积并生成
    acc = 0.0
    dist_from_start = 0.0
    started = False
    for a, b, seg_len in segs:
        if not started:
            if acc + seg_len < s:
                acc += seg_len
                continue
            # 已经把起点插入，当前段从 s 对应的点继续
            t0 = (s - acc) / seg_len if seg_len > 0 else 0.0
            p0 = a.lerp(b, t0)
            seg_left = (b - a).length * (1.0 - t0)
            seg_a = p0
            seg_b = b
            seg_len_effective = (seg_b - seg_a).length
            started = True
            acc_s = 0.0
        else:
            seg_a, seg_b, seg_len_effective = a, b, seg_len

        # 还要在这一段内填充直到 e
        remain = (s + segment_length) - (acc + (s - acc if not added_full else 0.0))
        # 但是上面表达有点拗口，这里直接用 e 控制
        # 当前段起点的全局沿程位置为 curr_start = max(acc, s)
        curr_start = max(acc, s)
        curr_end = acc + seg_len
        if e <= curr_start:
            break
        if e >= curr_end:
            # 当前段完全纳入，加入段末点
            if out and (out[-1] - seg_a).length > 1e-9:
                out.append(seg_a)
            out.append(seg_b)
            acc += seg_len
            continue
        else:
            # 终点落在本段内部，插入终点并结束
            t1 = (e - acc) / seg_len if seg_len > 0 else 0.0
            p_end = a.lerp(b, t1)
            if out and (out[-1] - seg_a).length > 1e-9:
                out.append(seg_a)
            out.append(p_end)
            break

    # 去重相邻重复点
    cleaned: List[Vector] = []
    for p in out:
        if not cleaned or (p - cleaned[-1]).length > 1e-9:
            cleaned.append(p)
    return cleaned


def _create_poly_curve(points: List[Vector], name: str = "Segment") -> Optional[bpy.types.Object]:
    if not points or len(points) < 2:
        return None
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def _total_length(points: List[Vector]) -> float:
    length = 0.0
    for i in range(1, len(points)):
        length += (points[i] - points[i - 1]).length
    return length


def _point_at_arc(points: List[Vector], s: float) -> Vector:
    """返回沿折线距离 s 处的点（s 会在 [0, total] 内钳制）。"""
    if not points or len(points) < 2:
        return Vector((0.0, 0.0, 0.0))
    total = _total_length(points)
    s = max(0.0, min(s, total))
    acc = 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        seg_len = (b - a).length
        if seg_len <= 0:
            continue
        if acc + seg_len >= s:
            t = (s - acc) / seg_len
            return a.lerp(b, t)
        acc += seg_len
    return points[-1].copy()


def _update_poly_curve(obj: bpy.types.Object, points: List[Vector]):
    curve: bpy.types.Curve = obj.data  # type: ignore
    # 清空并重建为单一 POLY spline
    while curve.splines:
        curve.splines.remove(curve.splines[0])
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)


def _create_marker(name: str, location: Vector) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = 0.03
    bpy.context.collection.objects.link(empty)
    empty.location = location
    return empty


class AF_OT_interactive_curve_segment(bpy.types.Operator):
    bl_idname = "aartflow.interactive_curve_segment"
    bl_label = "交互截取曲线片段"
    bl_description = "设定片段长度后，通过鼠标在曲线上滑动起点，始终保持两端点沿程距离等于给定长度，回车确认、ESC取消"
    bl_options = {'REGISTER', 'UNDO'}

    segment_length: bpy.props.FloatProperty(  # type: ignore
        name="片段长度",
        description="要截取的曲线片段长度",
        min=0.0,
        default=1.0,
        unit='LENGTH',
    )

    # 运行期状态（不注册为属性）
    _points: List[Vector] = []
    _total: float = 0.0
    _start_s: float = 0.0
    _preview_obj: Optional[bpy.types.Object] = None
    _marker_a: Optional[bpy.types.Object] = None
    _marker_b: Optional[bpy.types.Object] = None
    _last_mouse_x: int = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type in {'CURVE', 'MESH'}

    def invoke(self, context: bpy.types.Context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, "segment_length")

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, '未找到活动对象')
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        points = _build_ordered_polyline_from_mesh(obj_eval)
        if not points or len(points) < 2:
            self.report({'ERROR'}, '无法从对象生成有效折线，请检查几何是否为单条折线')
            return {'CANCELLED'}

        self._points = points
        self._total = _total_length(points)
        if self.segment_length <= 0.0:
            self.report({'ERROR'}, '片段长度必须大于 0')
            return {'CANCELLED'}
        if self.segment_length >= self._total:
            self.segment_length = max(0.0, self._total - 1e-6)

        # 创建预览对象与端点标记
        seg_pts = _extract_segment_points(self._points, 0.0, self.segment_length)
        self._preview_obj = _create_poly_curve(seg_pts, name=f"{obj.name}_seg_preview")
        a = _point_at_arc(self._points, 0.0)
        b = _point_at_arc(self._points, self.segment_length)
        self._marker_a = _create_marker(f"{obj.name}_seg_A", a)
        self._marker_b = _create_marker(f"{obj.name}_seg_B", b)

        # 首次鼠标同步标记，避免跳变
        self._first_mouse_sync = True  # type: ignore
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _update_preview(self, context: bpy.types.Context):
        s = max(0.0, min(self._start_s, max(0.0, self._total - self.segment_length)))
        seg_pts = _extract_segment_points(self._points, s, self.segment_length)
        if self._preview_obj and seg_pts and len(seg_pts) >= 2:
            _update_poly_curve(self._preview_obj, seg_pts)
        if self._marker_a:
            self._marker_a.location = _point_at_arc(self._points, s)
        if self._marker_b:
            self._marker_b.location = _point_at_arc(self._points, s + self.segment_length)

    def modal(self, context: bpy.types.Context, event):
        if event.type == 'MOUSEMOVE':
            # 首次同步当前鼠标位置，避免进入后第一次移动造成跳变
            if getattr(self, '_first_mouse_sync', False):  # type: ignore
                self._last_mouse_x = event.mouse_x
                self._first_mouse_sync = False  # type: ignore
                return {'RUNNING_MODAL'}
            region = context.region
            width = max(1, getattr(region, 'width', 1000))
            lpix = self._total / float(width)
            dx = event.mouse_x - self._last_mouse_x
            self._start_s += dx * lpix
            self._start_s = max(0.0, min(self._start_s, max(0.0, self._total - self.segment_length)))
            self._last_mouse_x = event.mouse_x
            self._update_preview(context)
            return {'RUNNING_MODAL'}

        if event.type in {'WHEELUPMOUSE', 'NUMPAD_PLUS'} and event.value == 'PRESS':
            self._start_s = min(self._start_s + self._total * 0.01, max(0.0, self._total - self.segment_length))
            self._update_preview(context)
            return {'RUNNING_MODAL'}
        if event.type in {'WHEELDOWNMOUSE', 'NUMPAD_MINUS'} and event.value == 'PRESS':
            self._start_s = max(self._start_s - self._total * 0.01, 0.0)
            self._update_preview(context)
            return {'RUNNING_MODAL'}

        if event.type in {'LEFTMOUSE', 'RET', 'SPACE'} and event.value == 'PRESS':
            # 确认：将预览对象转为最终对象，保留端点标记
            if self._preview_obj:
                self._preview_obj.name = self._preview_obj.name.replace('_preview', '')
            return {'FINISHED'}

        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            # 取消：删除预览与标记
            if self._preview_obj:
                bpy.data.objects.remove(self._preview_obj, do_unlink=True)
                self._preview_obj = None
            if self._marker_a:
                bpy.data.objects.remove(self._marker_a, do_unlink=True)
                self._marker_a = None
            if self._marker_b:
                bpy.data.objects.remove(self._marker_b, do_unlink=True)
                self._marker_b = None
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class AF_OT_get_curve_length(bpy.types.Operator):
    bl_idname = "aartflow.get_curve_length"
    bl_label = "获取曲线长度"
    bl_description = "计算并显示当前选中曲线/折线网格的沿程总长度"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type in {'CURVE', 'MESH'}

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        points = _build_ordered_polyline_from_mesh(obj_eval)
        if not points or len(points) < 2:
            self.report({'ERROR'}, '无法从对象生成有效折线，请检查几何是否为单条折线')
            return {'CANCELLED'}
        length = _total_length(points)
        try:
            context.window_manager.clipboard = f"{length}"
        except Exception:
            pass
        msg = f"曲线长度：{length:.6f}"
        self.report({'INFO'}, msg)
        bpy.context.window_manager.popup_menu(
            lambda self2, ctx, m=msg: self2.layout.label(text=m),
            title="曲线长度", icon='INFO')
        return {'FINISHED'}


class AF_PT_curve_segment_panel(bpy.types.Panel):
    bl_label = "曲线定长提取"
    bl_idname = "AF_PT_curve_segment_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AartFlow'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="选中一个曲线或网格对象（单条折线）")
        col.operator(AF_OT_interactive_curve_segment.bl_idname, text="交互截取…")
        col.operator(AF_OT_get_curve_length.bl_idname, text="获取曲线长度")


classes = (
    AF_OT_interactive_curve_segment,
    AF_OT_get_curve_length,
    AF_PT_curve_segment_panel,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()


