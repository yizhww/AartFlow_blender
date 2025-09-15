import bpy
import os
import sys
import time
import shutil
import traceback
from bpy.utils import register_class, unregister_class
import weakref
from bpy.app.handlers import persistent

bl_info = {
    "name": "Art Renderer Fixed",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "3D View > Sidebar > Art Renderer",
    "description": "逐个渲染指定集合中的物体（修复版）",
    "category": "Render",
}

# 定义场景属性
bpy.types.Scene.target_collection = bpy.props.PointerProperty(
    name="目标集合",
    type=bpy.types.Collection,
    description="选择要逐个渲染的集合"
)

# 详细日志开关（可选）
bpy.types.Scene.art_renderer_verbose = bpy.props.BoolProperty(
    name="详细日志",
    description="输出更多调试信息",
    default=False,
)

# 边界/兼容选项
bpy.types.Scene.art_include_children = bpy.props.BoolProperty(
    name="包含子集合",
    description="递归包含子集合中的对象",
    default=False,
)
bpy.types.Scene.art_exclude_restricted = bpy.props.BoolProperty(
    name="跳过禁止渲染",
    description="忽略原本被设置为不渲染的对象（hide_render=True）",
    default=True,
)

classes = []

_active_op_ref = None

@persistent
def _static_render_complete(scene, depsgraph=None):
    op = _active_op_ref() if _active_op_ref else None
    if op and getattr(op, '_is_active', False):
        try:
            op._on_render_complete(scene, depsgraph)
        except Exception as e:
            print(f"❌ 静态回调调度实例时出错: {e}")

class ArtRendererOperatorFront(bpy.types.Operator):
    """逐个渲染指定集合中的物体（修复版）"""
    bl_idname = "render.art_render_collection_fixed"
    bl_label = "artrender_front"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.target_collection is not None

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        # 初始化批量渲染
        self._timer = None
        self._render_cb = None
        self._is_active = False
        self._render_done = False
        self._next_start_time = None
        self._progress_started = False
        self.instance_id = time.monotonic_ns()
        self.scene = context.scene
        self.target_collection = self.scene.target_collection
        self.verbose = bool(getattr(self.scene, 'art_renderer_verbose', False))
        self.include_children = bool(getattr(self.scene, 'art_include_children', False))
        self.exclude_restricted = bool(getattr(self.scene, 'art_exclude_restricted', True))
        
        if not self.target_collection:
            self.report({'ERROR'}, "请先选择目标集合")
            return {'CANCELLED'}
        
        # 获取集合中的所有网格物体（支持递归与跳过禁止渲染对象）
        self.mesh_objects = self._collect_mesh_objects(self.target_collection, self.include_children, self.exclude_restricted)
        
        if not self.mesh_objects:
            self.report({'WARNING'}, f"集合 '{self.target_collection.name}' 中没有有效网格物体")
            return {'CANCELLED'}
        
        # 统计需要渲染的物体数量
        self.total_objects = len(self.mesh_objects)
        self.report({'INFO'}, f"准备批量渲染集合 '{self.target_collection.name}' 中的 {self.total_objects} 个物体")
        if self.verbose:
            print(f"📊 批量渲染准备 - 集合: {self.target_collection.name}, 物体数量: {self.total_objects}")
            print(f"📊 物体列表: {[obj.name for obj in self.mesh_objects]}")
        
        # 保存原始渲染可见性（仅限待渲染对象）
        self.original_visibility = {}
        for obj in self.mesh_objects:
            if obj and obj.name in bpy.data.objects:
                self.original_visibility[obj.name] = {'hide_render': obj.hide_render}
        
        # 设置输出路径
        global_filepath = bpy.path.abspath(self.scene.render.filepath)
        self.original_filepath = self.scene.render.filepath
        self.global_dir = os.path.dirname(global_filepath)

        # 输出扩展与格式一致性
        fmt = (self.scene.render.image_settings.file_format or '').upper()
        fmt_to_ext = {
            'PNG': '.png',
            'JPEG': '.jpg', 'JPG': '.jpg',
            'BMP': '.bmp',
            'TIFF': '.tif',
            'TARGA': '.tga', 'TARGA_RAW': '.tga',
            'OPEN_EXR': '.exr', 'OPEN_EXR_MULTILAYER': '.exr',
            'WEBP': '.webp',
            'HDR': '.hdr',
        }
        self.global_ext = fmt_to_ext.get(fmt, os.path.splitext(global_filepath)[1] or '.png')
        
        if not self.global_dir:
            self.global_dir = os.path.join(os.path.expanduser("~"), "Desktop", "New Folder")
        
        if not os.path.exists(self.global_dir):
            os.makedirs(self.global_dir, exist_ok=True)
        
        # 初始化状态
        self.current_index = 0
        self.rendered_count = 0
        self.render_state = 'idle'  # 'idle', 'rendering', 'completed'
        self.render_complete_flag = False
        self.is_batch_complete = False  # 新增：批量渲染完成标志
        
        # 检查渲染引擎
        if self.scene.render.engine != 'CYCLES':
            self.report({'ERROR'}, f"当前渲染引擎为 {self.scene.render.engine}，请切换到Cycles引擎以获得最佳支持")
            return {'CANCELLED'}
        
        # 初始化完成标志（实例内）
        self._render_done = False

        # 重建回调列表：强力清理全部回调，仅注册静态回调，避免旧签名残留
        try:
            handlers = bpy.app.handlers.render_complete
            handlers.clear()
            if _static_render_complete not in handlers:
                handlers.append(_static_render_complete)
            if self.verbose:
                print(f"🔧 回调已重建（强力清理），当前数量: {len(handlers)}")
        except Exception as e:
            print(f"⚠️ 重建回调列表失败: {e}")

        # 设定活动实例弱引用
        global _active_op_ref
        _active_op_ref = weakref.ref(self)

        # 仅在 invoke 中添加模态处理器与计时器
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)
        self._is_active = True

        # 进度条
        try:
            wm.progress_begin(0, self.total_objects)
            wm.progress_update(0)
            self._progress_started = True
        except Exception:
            pass

        # 开始第一个渲染
        self.start_next_render(context)
        return {'RUNNING_MODAL'}

    def start_next_render(self, context):
        """开始渲染下一个物体 - 优化版本（不在此添加模态处理器）"""
        if self.verbose:
            print(f"🚀 start_next_render 被调用，当前索引: {self.current_index}")
        
        # 检查是否完成所有渲染
        if self.current_index >= len(self.mesh_objects):
            self.is_batch_complete = True
            self.finish_batch_render()
            self.report({'INFO'}, f"批量渲染完成，共渲染 {self.rendered_count} 个物体")
            return
        
        obj = self.mesh_objects[self.current_index]
        
        # 验证物体有效性
        if not obj or obj.name not in bpy.data.objects:
            print(f"❌ 物体不存在或无效：{obj.name if obj else 'None'}")
            self.report({'ERROR'}, f"物体不存在或无效")
            self.finish_batch_render()
            return {'CANCELLED'}
        
        try:
            # 只在第一次渲染或上次渲染失败时进行清理
            if self.current_index == 0 or self.render_state == 'rendering':
                self.cleanup_previous_render()
            
            # 设置物体可见性（安全切换）
            for collection_obj in self.mesh_objects:
                try:
                    if (collection_obj and collection_obj.name in bpy.data.objects and 
                        collection_obj.type == 'MESH' and collection_obj.data):
                        collection_obj.hide_render = True
                except Exception:
                    pass
            try:
                if obj and obj.name in bpy.data.objects and obj.type == 'MESH' and obj.data:
                    obj.hide_render = False
            except Exception:
                pass
            
            # 设置输出文件路径
            safe_name = "".join(c for c in obj.name if c.isalnum() or c in ('-', '_')).rstrip()
            if not safe_name:
                safe_name = f"object_{self.current_index + 1}"
            
            output_filepath = os.path.join(self.global_dir, f"{safe_name}_{self.current_index + 1:03d}{self.global_ext}")
            output_filepath = os.path.normpath(output_filepath)
            self.scene.render.filepath = output_filepath
            
            # 验证输出目录
            output_dir = os.path.dirname(output_filepath)
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    print(f"✅ 创建输出目录: {output_dir}")
                except Exception as dir_error:
                    print(f"❌ 创建输出目录失败: {dir_error}")
                    self.report({'ERROR'}, f"无法创建输出目录: {dir_error}")
                    self.finish_batch_render()
                    return {'CANCELLED'}
            
            # 开始渲染
            if self.verbose:
                print(f"▶️ 渲染 {self.current_index + 1}/{self.total_objects}: {obj.name}")
            self.render_state = 'rendering'
            
            # 添加额外的安全检查（移除阻塞 sleep）
            try:
                # 确保场景状态正常
                try:
                    bpy.context.view_layer.update()
                except:
                    pass
                
                # 检查渲染引擎状态
                if not hasattr(bpy.context.scene, 'render') or not bpy.context.scene.render:
                    print(f"❌ 渲染场景无效: {obj.name}")
                    self.current_index += 1
                    self.start_next_render(context)
                    return
                
                # 检查物体是否仍然有效
                if not obj or obj.name not in bpy.data.objects:
                    print(f"❌ 物体已无效: {obj.name}")
                    self.current_index += 1
                    self.start_next_render(context)
                    return
                
                # 开始渲染 - 简化版本
                try:
                    # 使用后台渲染以避免依赖视图状态
                    result = bpy.ops.render.render('INVOKE_DEFAULT', use_viewport=False, write_still=True)
                    
                    if result == {'FINISHED'} or result == {'RUNNING_MODAL'}:
                        # 渲染启动成功
                        if self.verbose:
                            print(f"✅ 渲染启动成功: {obj.name}")
                        return
                    elif result == {'CANCELLED'}:
                        print(f"❌ 渲染启动失败: {obj.name}")
                        self.report({'ERROR'}, f"渲染启动失败：{obj.name}")
                        # 跳过这个物体，继续下一个
                        self.current_index += 1
                        self.start_next_render(context)
                        return
                    else:
                        print(f"❌ 渲染启动失败: {obj.name} (未知结果: {result})")
                        self.report({'ERROR'}, f"渲染启动失败：{obj.name}")
                        # 跳过这个物体，继续下一个
                        self.current_index += 1
                        self.start_next_render(context)
                        return
                        
                except Exception as render_error:
                    print(f"❌ 渲染操作异常: {render_error}")
                    self.report({'ERROR'}, f"渲染操作异常: {render_error}")
                    # 跳过这个物体，继续下一个
                    self.current_index += 1
                    self.start_next_render(context)
                    return
                    
            except Exception as render_error:
                print(f"❌ 渲染操作失败: {render_error}")
                self.report({'ERROR'}, f"渲染操作失败: {render_error}")
                # 跳过这个物体，继续下一个
                self.current_index += 1
                self.start_next_render(context)
                return
            
        except Exception as e:
            print(f"❌ 开始渲染时出错：{e}")
            self.report({'ERROR'}, f"开始渲染时出错：{e}")
            # 跳过这个物体，继续下一个
            self.current_index += 1
            self.start_next_render(context)
            return

    def cleanup_previous_render(self):
        """简化的状态清理（无阻塞）"""
        
        # 重置渲染状态
        self.render_state = 'idle'
        
        # 重置全局标志（仅兼容旧逻辑，不再使用）
        if hasattr(bpy, 'render_complete_flag'):
            bpy.render_complete_flag = False
        
        # 强制更新场景状态
        try:
            bpy.context.view_layer.update()
        except Exception as e:
            pass
        
        # 清理渲染界面
        self.cleanup_render_interface()

    def modal(self, context, event):
        """模态处理函数 - 以计时器事件驱动状态轮询"""
        try:
            # ESC 立即取消
            if event.type == 'ESC':
                self.report({'ERROR'}, "用户取消渲染")
                self.finish_batch_render()
                return {'CANCELLED'}

            # 检查批量渲染是否已完成
            if self.is_batch_complete:
                return {'FINISHED'}
            
            # 仅处理计时器事件
            if event.type != 'TIMER':
                return {'PASS_THROUGH'}

            # 检测渲染完成
            if (self._render_done and self.render_state == 'rendering'):
                
                # 渲染完成，重置标志
                self._render_done = False
                self.render_state = 'completed'
                # 稍作延迟，等待内部清理完成
                self._next_start_time = time.time() + 0.2
                
                # 检查是否还有更多物体需要渲染
                if self.current_index < len(self.mesh_objects):
                    # 开始下一个渲染 - 重新启动模态处理器
                    print(f"🔄 准备开始下一个渲染进程: {self.current_index + 1}")
                else:
                    # 所有物体都渲染完成
                    self.is_batch_complete = True
                    self.finish_batch_render()
                    self.report({'INFO'}, f"批量渲染完成，共渲染 {self.rendered_count} 个物体")
                    return {'FINISHED'}

            # 若已完成且设定了下一次启动时间，到点后启动
            if self.render_state == 'completed' and self._next_start_time is not None:
                if time.time() >= self._next_start_time:
                    self._next_start_time = None
                    self.start_next_render(context)
                    return {'RUNNING_MODAL'}
                else:
                    return {'PASS_THROUGH'}
            
            # 在渲染过程中，忽略所有用户交互事件（除了ESC取消）
            if self.render_state == 'rendering':
                # 渲染中忽略其他事件
                return {'PASS_THROUGH'}
            
            # 如果当前状态是idle或completed，继续等待
            return {'PASS_THROUGH'}
        
        except Exception as e:
            print(f"❌ 模态处理时出错: {e}")
            # 简单退出，不调用复杂的完成处理
            self.is_batch_complete = True
            return {'CANCELLED'}

    def _on_render_complete(self, scene, depsgraph=None):
        """实例内部的渲染完成处理，由静态回调转调。"""
        try:
            # 多实例令牌校验
            if not getattr(self, '_is_active', False):
                return
            # 验证当前索引是否有效
            if self.current_index >= len(self.mesh_objects):
                print(f"⚠️ 当前索引超出范围: {self.current_index} >= {len(self.mesh_objects)}")
                self._render_done = True
                return
            
            obj = self.mesh_objects[self.current_index]
            
            # 验证物体是否仍然有效
            if not obj or obj.name not in bpy.data.objects:
                print(f"⚠️ 物体已无效: {obj.name if obj else 'None'}")
                self.current_index += 1
                self._render_done = True
                return
            # 如果当前对象被设置为不渲染且用户选择跳过，则直接跳过
            if self.exclude_restricted and getattr(obj, 'hide_render', False):
                self.current_index += 1
                self._render_done = True
                return
            
            # write_still=True 已自动保存，这里仅统计与推进
            self.rendered_count += 1
            try:
                bpy.context.window_manager.progress_update(self.rendered_count)
            except Exception:
                pass
            if self.verbose:
                progress = (self.rendered_count / len(self.mesh_objects)) * 100
                print(f"📈 渲染进度: {self.rendered_count}/{len(self.mesh_objects)} ({progress:.1f}%)")

            # 清理并推进
            self.cleanup_render_interface()
            self.current_index += 1
            
        except Exception as e:
            print(f"❌ 渲染完成回调处理时出错: {e}")
            # 即使出错也要清理界面并移动到下一个物体
            try:
                self.cleanup_render_interface()
                self.current_index += 1
            except:
                pass
        
        # 标记渲染完成，由模态计时器推进
        self._render_done = True

    def _collect_mesh_objects(self, collection, include_children=False, exclude_restricted=True):
        """收集集合中的 MESH 对象，支持递归与按需跳过禁止渲染对象。"""
        result = []
        try:
            for obj in getattr(collection, 'objects', []):
                try:
                    if not obj:
                        continue
                    if obj.type != 'MESH' or not getattr(obj, 'data', None):
                        continue
                    if exclude_restricted and getattr(obj, 'hide_render', False):
                        continue
                    result.append(obj)
                except Exception:
                    continue
            if include_children:
                for child in getattr(collection, 'children', []):
                    result.extend(self._collect_mesh_objects(child, True, exclude_restricted))
        except Exception:
            pass
        return result

    # （不再需要 _remove_old_handlers，改为静态回调模式）

    def cleanup_render_interface(self):
        """清理渲染界面和状态"""
        try:
            # 最小化 UI 干预：找到首个 IMAGE_EDITOR，将其 image 置空后退出
            done = False
            for window in bpy.context.window_manager.windows:
                if done:
                    break
                for area in window.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        for space in area.spaces:
                            if space.type == 'IMAGE_EDITOR':
                                try:
                                    space.image = None
                                except Exception:
                                    pass
                                done = True
                                break
                    if done:
                        break
                if done:
                    break
            # 不再清空 Render Result 的像素，避免重负载

            # 强制更新界面
            try:
                bpy.context.view_layer.update()
            except:
                pass
                
        except Exception as e:
            # 静默处理错误，不输出错误信息
            pass



    def finish_batch_render(self):
        """完成批量渲染 - 最简安全版本（恢复状态与清理资源）"""
        try:
            print("🏁 开始批量渲染完成处理...")
            
            # 第一步：重置基本状态
            self.render_state = 'idle'
            self.is_batch_complete = True
            self._is_active = False
            
            # 第二步：显示完成信息
            print(f"🎉 总结：成功渲染了 {self.rendered_count} 个物体")
            print("🎉 所有渲染文件已保存完毕")
            
            # 第三步：恢复用户状态
            try:
                if hasattr(self, 'original_filepath'):
                    self.scene.render.filepath = self.original_filepath
                if hasattr(self, 'original_visibility'):
                    for obj_name, state in self.original_visibility.items():
                        obj = bpy.data.objects.get(obj_name)
                        if obj and 'hide_render' in state:
                            obj.hide_render = state['hide_render']
            except Exception:
                pass

            # 第四步：清理计时器（不移除静态回调）
            try:
                wm = bpy.context.window_manager
                if self._timer:
                    wm.event_timer_remove(self._timer)
                    self._timer = None
            except Exception:
                pass
            # 结束进度条
            try:
                if self._progress_started:
                    bpy.context.window_manager.progress_end()
                    self._progress_started = False
            except Exception:
                pass
            
            print("✅ 批量渲染完成处理成功")
            
        except Exception as e:
            print(f"🏁 完成处理时出错: {e}")
            # 即使出错也要确保基本状态
            try:
                self.render_state = 'idle'
                self.is_batch_complete = True
            except:
                pass

classes.append(ArtRendererOperatorFront)

class VIEW3D_PT_ArtRendererPanelFixed(bpy.types.Panel):
    """3D视图侧边栏中的Art Renderer面"""
    bl_label = "artrender_front"
    bl_idname = "VIEW3D_PT_art_renderer_fixed"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'artrender_front'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 检查渲染引擎
        if scene.render.engine != 'CYCLES':
            layout.label(text="⚠️ 请切换到Cycles渲染引擎", icon='ERROR')
            layout.label(text="以获得最佳批量渲染支持")
            layout.separator()
        
        # 选择集合
        layout.prop(scene, "target_collection", text="选择集合")
        # 选项
        layout.prop(scene, "art_include_children", text="包含子集合")
        layout.prop(scene, "art_exclude_restricted", text="跳过禁止渲染")
        
        # 分隔线
        layout.separator()
        
        # 渲染按钮
        layout.operator(
            "render.art_render_collection_fixed",
            icon='RENDER_STILL',
            text="批量渲染集合（修复版）"
        )

classes.append(VIEW3D_PT_ArtRendererPanelFixed)

def register():
    """注册插件中的所有类"""
    for cls in classes:
        try:
            unregister_class(cls)
        except RuntimeError:
            pass
        register_class(cls)

def unregister():
    """注销插件中的所有类"""
    for cls in reversed(classes):
        unregister_class(cls)
    
    # 清理自定义属性
    if hasattr(bpy.types.Scene, "target_collection"):
        del bpy.types.Scene.target_collection

if __name__ == "__main__":
    register() 