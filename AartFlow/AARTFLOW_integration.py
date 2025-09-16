import bpy

class AF_OT_module_popup(bpy.types.Operator):
    bl_idname = "af.module_popup"
    bl_label = "Module Panel"
    bl_description = "Show selected module panels in a popup"

    module_name: bpy.props.StringProperty(name="module")
    module_list: bpy.props.StringProperty(name="module_list", description="semicolon joined module names", default="")

    def execute(self, context):
        # 将弹窗改为“可手动开关”的固定面板：写入 WM 属性
        wm = context.window_manager
        names = []
        try:
            if self.module_list:
                names = [s for s in self.module_list.split(';') if s]
            elif self.module_name:
                names = [self.module_name]
        except Exception:
            pass
        try:
            wm.af_popup_modules = ';'.join(names)
            wm.af_popup_enabled = True
        except Exception:
            # 若属性尚未注册则先注册一次
            try:
                bpy.types.WindowManager.af_popup_enabled = bpy.props.BoolProperty(name="AF Popup", default=True)
                bpy.types.WindowManager.af_popup_modules = bpy.props.StringProperty(name="AF Popup Modules", default=';'.join(names))
            except Exception:
                pass
        _refresh_ui()
        self.report({'INFO'}, 'AartFlow Modules Popup: ON (N 面板 > AartFlow)')
        return {'FINISHED'}

class AF_OT_module_dialog(bpy.types.Operator):
    bl_idname = "af.module_dialog"
    bl_label = "Module Dialog"
    bl_description = "Show selected modules in a temporary dialog"
    bl_options = {'REGISTER', 'UNDO'}

    module_name: bpy.props.StringProperty(name="module")
    module_list: bpy.props.StringProperty(name="module_list", description="semicolon joined module names", default="")

    def invoke(self, context, event):
        width = 420
        return context.window_manager.invoke_props_dialog(self, width=width)

    def draw(self, context):
        layout = self.layout
        names = []
        try:
            if self.module_list:
                names = [s for s in self.module_list.split(';') if s]
            elif self.module_name:
                names = [self.module_name]
        except Exception:
            pass

        if not names:
            layout.label(text="No module")
            return

        for name in names:
            header = layout.box(); header.label(text=name)
            panels = _get_panels_for_module(name)
            if not panels:
                header.label(text="No panels found")
                continue
            for panel_cls in panels:
                try:
                    show_ok = True
                    try:
                        if hasattr(panel_cls, 'poll') and callable(panel_cls.poll):
                            show_ok = bool(panel_cls.poll(context))
                    except Exception:
                        show_ok = True
                    if not show_ok:
                        continue
                    frame = layout.box()
                    frame.label(text=str(getattr(panel_cls, 'bl_label', panel_cls.__name__)))
                    Shim = type('AF_PopupShim', (), {})
                    shim = Shim(); shim.layout = frame.column()
                    panel_cls.draw(shim, context)
                except Exception as e:
                    err = layout.box(); err.label(text=f"Panel error: {e}", icon='ERROR')

    def execute(self, context):
        return {'FINISHED'}

class AF_OT_close_module_popup(bpy.types.Operator):
    bl_idname = "af.close_module_popup"
    bl_label = "Close Modules Popup"
    bl_description = "Hide AartFlow modules popup panel"

    def execute(self, context):
        try:
            context.window_manager.af_popup_enabled = False
            _refresh_ui()
        except Exception:
            pass
        return {'FINISHED'}

class VIEW3D_PT_aartflow_popup(bpy.types.Panel):
    bl_label = "Modules Popup"
    bl_idname = "VIEW3D_PT_aartflow_popup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_parent_id = "VIEW3D_PT_aartflow_root"

    @classmethod
    def poll(cls, context):
        try:
            return bool(getattr(context.window_manager, 'af_popup_enabled', False))
        except Exception:
            return False

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        names = []
        try:
            raw = getattr(wm, 'af_popup_modules', '') or ''
            names = [s for s in raw.split(';') if s]
        except Exception:
            names = []

        row = layout.row()
        row.operator("af.close_module_popup", icon='CANCEL', text="Close")
        if not names:
            layout.label(text="No module selected")
            return

        for name in names:
            header = layout.box()
            header.label(text=name)
            panels = _get_panels_for_module(name)
            if not panels:
                header.label(text="No panels found")
                continue
            for panel_cls in panels:
                try:
                    show_ok = True
                    try:
                        if hasattr(panel_cls, 'poll') and callable(panel_cls.poll):
                            show_ok = bool(panel_cls.poll(context))
                    except Exception:
                        show_ok = True
                    if not show_ok:
                        continue
                    frame = layout.box()
                    frame.label(text=str(getattr(panel_cls, 'bl_label', panel_cls.__name__)))
                    Shim = type('AF_PopupShim', (), {})
                    shim = Shim()
                    shim.layout = frame.column()
                    panel_cls.draw(shim, context)
                except Exception as e:
                    err = layout.box()
                    err.label(text=f"Panel error: {e}", icon='ERROR')
# -*- coding: utf-8 -*-
# 仅包含整合逻辑：动态加载外部业务模块，复用并重注册其原面板为子面板，不包含任何业务 UI 代码。

# 插件信息已移至 __init__.py

# 在非 Blender 环境下防护导入 bpy，仅在缺少模块时提示
try:
    import bpy  # type: ignore
except ModuleNotFoundError:
    print("[AARTFLOW] 未检测到 bpy：请在 Blender 内运行或使用 blender.exe --python 调用此脚本。")
    raise
import importlib
import importlib.machinery
import importlib.util
import sys
import os
from types import FunctionType
import types

# 外部业务脚本绝对路径（全局配置参数）
_MODULE_PATHS = {}

# 合规的扩展命名空间前缀（与 blender_manifest.toml 的 id 对应）
_EXT_NAMESPACE_PREFIX = "bl_ext.aartflow_blender"

def _ensure_ext_namespace_packages():
    """确保 bl_ext 以及 bl_ext.<id> 作为包存在于 sys.modules。"""
    try:
        if 'bl_ext' not in sys.modules:
            bl_ext_pkg = types.ModuleType('bl_ext')
            setattr(bl_ext_pkg, '__path__', [])
            sys.modules['bl_ext'] = bl_ext_pkg
        ns_name = _EXT_NAMESPACE_PREFIX
        if ns_name not in sys.modules:
            ns_pkg = types.ModuleType(ns_name)
            setattr(ns_pkg, '__path__', [])
            sys.modules[ns_name] = ns_pkg
    except Exception:
        pass

# 自动发现并加载 scripts 目录中的脚本
def _discover_script_modules():
    """自动发现并加载 scripts 目录中的脚本"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(current_dir, "scripts")
    
    if not os.path.exists(scripts_dir):
        print(f"[AARTFLOW] 脚本目录不存在: {scripts_dir}")
        return
    
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            script_name = os.path.splitext(filename)[0]
            script_path = os.path.join(scripts_dir, filename)
            _MODULE_PATHS[script_name] = script_path
            print(f"[AARTFLOW] 自动发现脚本: {script_name} -> {script_path}")

# 在模块加载时自动发现脚本
_discover_script_modules()

def set_module_paths(paths_dict):
    """设置模块路径的全局函数"""
    global _MODULE_PATHS
    if paths_dict:
        # 过滤掉 None 值
        _MODULE_PATHS = {k: v for k, v in paths_dict.items() if k is not None and v is not None}
    else:
        _MODULE_PATHS = {}

def get_module_paths():
    """获取当前模块路径的全局函数"""
    return dict(_MODULE_PATHS)

def add_module_path(key, path):
    """添加单个模块路径"""
    global _MODULE_PATHS
    if key is not None and path is not None:
        _MODULE_PATHS[key] = path

def remove_module_path(key):
    """移除单个模块路径"""
    global _MODULE_PATHS
    _MODULE_PATHS.pop(key, None)

def reset_to_default_paths():
    """清空所有模块路径，由用户在面板中重新配置"""
    global _MODULE_PATHS
    _MODULE_PATHS = {}
_loaded_modules = {}
 
# 记录被“重挂载”为子面板的原面板及其原始元数据，便于卸载时复原
_reparented_original_panels = []

# 记录被移除的原面板类（仅调试用途，不做恢复）
_removed_original_panels = []

# 记录当前要移除的模块的面板ID，避免在 _unregister_proxies 中恢复
_panels_to_remove_permanently = set()

# 键盘快捷键映射
_keymaps = []

# 当前聚焦显示的模块名；None 表示显示全部
_focused_module_key = None

def _load_ext_module(modname: str, filepath: str):
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("找不到模块文件: " + str(filepath))
    _ensure_ext_namespace_packages()
    pkgname = f"{_EXT_NAMESPACE_PREFIX}.{modname}"
    if pkgname in sys.modules:
        try:
            del sys.modules[pkgname]
        except Exception:
            pass
    loader = importlib.machinery.SourceFileLoader(pkgname, filepath)
    spec = importlib.util.spec_from_loader(pkgname, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    sys.modules[pkgname] = mod
    return mod

def _ensure_loaded():
    """按 `_MODULE_PATHS` 抽象加载所有外部模块，不出现具体业务名。"""
    global _loaded_modules
    # 允许无模块状态，不自动加载默认模块
    
    for mod_name, file_path in list(_MODULE_PATHS.items()):
        if mod_name not in _loaded_modules:
            try:
                _loaded_modules[mod_name] = _load_ext_module(mod_name, file_path)
            except Exception as e:
                # 某个模块加载失败时不阻断整体，但记录错误
                print(f"[AARTFLOW] 加载模块 {mod_name} 失败: {e}")
                pass

class VIEW3D_PT_aartflow_root(bpy.types.Panel):
    bl_label = "AartFlow"
    bl_idname = "VIEW3D_PT_aartflow_root"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_context = "objectmode"
    bl_order = -100

    @classmethod
    def poll(cls, context):
        # 始终显示 AartFlow 面板，即使没有模块
        return True

    def draw(self, context):
        layout = self.layout
        
        # 添加设置面板内容到根面板
        # 顶部添加按钮
        col = layout.column(align=True)
        col.operator("af.add_integration_module", icon='FILE_FOLDER', text="添加模块...")
        
        # 饼菜单呼出按钮
        col.operator("af.show_pie_menu", icon='MENU_PANEL', text="显示饼菜单")
        
        # 模块路径管理
        path_box = layout.box()
        path_row = path_box.row(align=True) 
        path_row.operator("af.configure_module_paths", icon='INFO', text="查看配置")
        path_row.operator("af.reset_module_paths", icon='FILE_REFRESH', text="重置默认")
        
        # 列表基于 _MODULE_PATHS 展示，确保与真实引用一致
        box = layout.box()
        try:
            import os
            
            if not _MODULE_PATHS:
                box.label(text="当前未引用任何模块")

            else:
                # 去重：按绝对路径聚合，保留第一个 key
                seen_paths = {}
                for key, path in _MODULE_PATHS.items():
                    try:
                        # 确保 key 和 path 都不为 None
                        if key is None:
                            continue
                        if path is None:
                            seen_paths[key] = key
                            continue
                            
                        ap = os.path.abspath(path or "")
                        if ap in seen_paths:
                            continue
                        seen_paths[ap] = key
                    except Exception:
                        # 如果路径无效，仍然显示 key
                        if key is not None:
                            seen_paths[key] = key
                
                for ap, key in seen_paths.items():
                    row = box.row(align=True)
                    # 仅显示模块标识（key）
                    row.label(text=str(key))
                    # 刷新按钮
                    op_r = row.operator("af.refresh_integration_module", text="", icon='FILE_REFRESH')
                    op_r.key = str(key)
                    # 仅保留一个移除按钮（图标按钮）
                    op = row.operator("af.remove_integration_module", text="", icon='X')
                    op.key = str(key)
                    # 打开所在文件夹
                    op_open = row.operator("af.open_module_folder", text="", icon='FILE_FOLDER')
                    op_open.key = str(key)
        except Exception as e:
            box.label(text=f"读取引用列表失败: {str(e)}", icon='ERROR')
            box.operator("af.reset_module_paths", text="重置为默认", icon='FILE_REFRESH')

        # 在根面板下方挂一个固定子面板承载所有集成模块内容
        # 业务面板的代理会将 bl_parent_id 指向该子面板

class VIEW3D_PT_aartflow_modules(bpy.types.Panel):
    bl_label = "集成模块"
    bl_idname = "VIEW3D_PT_aartflow_modules"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AartFlow"
    bl_order = -50

    @classmethod
    def poll(cls, context):
        # 仅当存在集成模块时显示
        try:
            return bool(_MODULE_PATHS)
        except Exception:
            return False

    def draw(self, context):
        # 本面板仅作为容器，实际内容由代理面板绘制
        layout = self.layout
        col = layout.column(align=True)
          
class AF_ModuleItem(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty(name="标识", description="模块标识（根据文件名生成）", default="")
    filepath: bpy.props.StringProperty(name="路径", description="模块文件绝对路径", default="", subtype='FILE_PATH', maxlen=1024)

class AartFlowIntegrationSettings(bpy.types.PropertyGroup):
    modules: bpy.props.CollectionProperty(type=AF_ModuleItem)
    active_index: bpy.props.IntProperty(name="当前", default=0, min=0)

class AF_OT_add_integration_module(bpy.types.Operator):
    bl_idname = "af.add_integration_module"
    bl_label = "添加引用模块"
    bl_description = "选择一个 .py 文件加入集成引用并立即刷新"

    # 支持单选与多选
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    filter_glob: bpy.props.StringProperty(default="*.py", options={'HIDDEN'})
    
    def execute(self, context):
        import os
        global _MODULE_PATHS, _loaded_modules
        # 收集待添加的路径（支持多选）
        selected_paths = []
        try:
            dir_path = os.path.abspath(self.directory or "").strip()
            if self.files and len(self.files) > 0 and dir_path:
                for f in self.files:
                    try:
                        p = os.path.abspath(os.path.join(dir_path, f.name))
                        if p:
                            selected_paths.append(p)
                    except Exception:
                        pass
            else:
                # 单选模式：可能选择的是文件，也可能是目录
                p = os.path.abspath(self.filepath or "").strip()
                if p:
                    selected_paths.append(p)
                elif dir_path and os.path.isdir(dir_path):
                    # 如果未选择具体文件但选择了目录，则将目录作为输入
                    selected_paths.append(dir_path)
        except Exception:
            pass

        if not selected_paths:
            return {'CANCELLED'}

        # 展开目录：仅将包含 Panel 定义的 .py 文件视为独立模块
        def _expand_dir_to_py_files(folder: str):
            results = []
            try:
                import re

                def _has_panel_definition(py_file: str) -> bool:
                    try:
                        with open(py_file, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read()
                        if 'bpy.types.Panel' in content:
                            return True
                        # 粗略匹配 class Xxx( ... Panel ... ):
                        return re.search(r"class\s+\w+\s*\(.*Panel.*\):", content) is not None
                    except Exception:
                        return False

                for name in os.listdir(folder):
                    if not name.lower().endswith('.py'):
                        continue
                    # 跳过一些不应作为模块集成的文件
                    if name in {'__init__.py'}:
                        continue
                    if name.lower() == 'aartflow_integration.py':
                        continue
                    full = os.path.join(folder, name)
                    if os.path.isfile(full) and _has_panel_definition(full):
                        results.append(os.path.abspath(full))
            except Exception:
                pass
            return results

        expanded_paths = []
        for path in selected_paths:
            try:
                if os.path.isdir(path):
                    expanded_paths.extend(_expand_dir_to_py_files(path))
                else:
                    # 单文件：若不包含 Panel 定义则跳过
                    ap = os.path.abspath(path)
                    try:
                        import re
                        with open(ap, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read()
                        has_panel = ('bpy.types.Panel' in content) or (re.search(r"class\s+\w+\s*\(.*Panel.*\):", content) is not None)
                    except Exception:
                        has_panel = False
                    if has_panel:
                        expanded_paths.append(ap)
            except Exception:
                pass

        if not expanded_paths:
            return {'CANCELLED'}

        added_keys = []
        skipped = 0
        for path in expanded_paths:
            if not path:
                continue
            # 去重：路径已存在则跳过
            exists = False
            try:
                for _k, _v in list(_MODULE_PATHS.items()):
                    if os.path.abspath(_v or "").strip() == path:
                        exists = True
                        break
            except Exception:
                pass
            if exists:
                skipped += 1
                continue
            # 生成 key（若重复则报错并跳过，不自动追加后缀）
            base_key = os.path.splitext(os.path.basename(path))[0] or "module"
            if base_key in _MODULE_PATHS:
                try:
                    self.report({'ERROR'}, f"键名已存在，跳过: {base_key}")
                except Exception:
                    pass
                skipped += 1
                continue
            _MODULE_PATHS[base_key] = path
            added_keys.append(base_key)

        # 重新加载
        try:
            _unregister_proxies()
        except Exception:
            pass
        try:
            # 清理旧缓存
            for _k in list(sys.modules.keys()):
                if _k.startswith(f"{_EXT_NAMESPACE_PREFIX}."):
                    try:
                        del sys.modules[_k]
                    except Exception:
                        pass
            _loaded_modules.clear()
            _ensure_loaded()
            # 确保外部模块完成自身注册（Operator/属性等），以便面板按钮正常
            try:
                for _name, _mod in list(_loaded_modules.items()):
                    try:
                        if hasattr(_mod, "register") and callable(_mod.register):
                            _mod.register()
                            _unregister_panels_from_module(_mod)
                    except Exception:
                        pass
            except Exception:
                pass
            _register_proxies()
        except Exception as e:
            self.report({'ERROR'}, f"添加失败: {e}")
            return {'CANCELLED'}
        if added_keys:
            self.report({'INFO'}, f"已添加: {', '.join(added_keys)}")
        if skipped:
            self.report({'INFO'}, f"已跳过重复: {skipped}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class AF_OT_remove_integration_module(bpy.types.Operator):
    bl_idname = "af.remove_integration_module"
    bl_label = "移除"
    bl_description = "从集成列表中移除该模块并刷新"
    key: bpy.props.StringProperty()

    def execute(self, context):
        key = (self.key or "").strip()
        
        if not key:
            self.report({'ERROR'}, "无效的模块标识")
            return {'CANCELLED'}
        
        print(f"[AARTFLOW] 开始移除模块: {key}")
        
        try:
            # 1. 彻底清理被移除模块的所有资源
            _cleanup_removed_module(key)
            
            # 2. 从设置集合中移除
            settings = getattr(context.scene, 'af_integration_settings', None)
            if settings is not None:
                try:
                    idx = next((i for i, it in enumerate(settings.modules) if it.key == key), -1)
                    if idx >= 0:
                        settings.modules.remove(idx)
                        print(f"[AARTFLOW] 从设置集合中移除: {key}")
                except Exception:
                    pass
            
            # 3. 刷新界面（_cleanup_removed_module 已经处理了重新注册）
            _refresh_ui()
            
            self.report({'INFO'}, f"已彻底移除模块: {key}，面板已同步")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"[AARTFLOW] 移除模块失败: {e}")
            self.report({'ERROR'}, f"移除模块失败: {e}")
            return {'CANCELLED'}

class AF_OT_refresh_integration_module(bpy.types.Operator):
    bl_idname = "af.refresh_integration_module"
    bl_label = "刷新"
    bl_description = "重新加载该引用模块（不改变其它模块）"
    key: bpy.props.StringProperty()

    def execute(self, context):
        k = (self.key or "").strip()
        try:
            _reload_one_module_and_remount(k)
        except Exception as e:
            self.report({'ERROR'}, f"刷新失败: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"已刷新: {k}")
        return {'FINISHED'}

class AF_OT_refresh_all_modules(bpy.types.Operator):
    bl_idname = "af.refresh_all_modules"
    bl_label = "刷新所有模块"
    bl_description = "重新加载所有引用模块并刷新界面"
    
    def execute(self, context):
        global _loaded_modules
        try:
            # 重新加载所有模块
            for key in list(_MODULE_PATHS.keys()):
                try:
                    _reload_one_module_and_remount(key)
                except Exception as e:
                    print(f"[AARTFLOW] 刷新模块 {key} 失败: {e}")
            
            # 刷新界面
            for area in bpy.context.screen.areas:
                area.tag_redraw()
            
            self.report({'INFO'}, f"已刷新 {len(_MODULE_PATHS)} 个模块")
        except Exception as e:
            self.report({'ERROR'}, f"刷新失败: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class AF_OT_configure_module_paths(bpy.types.Operator):
    bl_idname = "af.configure_module_paths"
    bl_label = "配置模块路径"
    bl_description = "配置外部模块的路径设置"
    
    def execute(self, context):
        # 显示当前配置（以 "key": r"path" 的可复制格式输出到 Blender 信息日志）
        current_paths = get_module_paths()
        if current_paths:
            try:
                # 逐行写入到 Blender 信息日志（顶部信息区/Info 编辑器可见）
                lines = []
                lines.append("{")
                for i, key in enumerate(sorted(current_paths.keys())):
                    path = current_paths.get(key) or ""
                    comma = "," if i < len(current_paths) - 1 else ""
                    lines.append(f"    \"{key}\": r\"{path}\"{comma}")
                lines.append("}")
                # 输出
                self.report({'INFO'}, "模块路径配置（可复制为字典）：")
                for line in lines:
                    self.report({'INFO'}, line)
            except Exception as e:
                self.report({'ERROR'}, f"打印模块路径配置失败: {e}")
            else:
                self.report({'INFO'}, f"已输出 {len(current_paths)} 个模块路径到信息日志")
        else:
            self.report({'INFO'}, "当前未配置任何模块路径")
        return {'FINISHED'}

class AF_OT_reset_module_paths(bpy.types.Operator):
    bl_idname = "af.reset_module_paths"
    bl_label = "清空配置"
    bl_description = "清空已配置的模块路径（不再加载默认模块）"
    
    def execute(self, context):
        # 彻底清空
        try:
            _clear_all_integrations()
        except Exception as e:
            self.report({'ERROR'}, f"清空失败: {e}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, "已彻底清空所有模块与面板")
        return {'FINISHED'}

class AF_OT_open_module_folder(bpy.types.Operator):
    bl_idname = "af.open_module_folder"
    bl_label = "打开模块所在文件夹"
    bl_description = "在文件资源管理器中打开该模块所在目录"
    key: bpy.props.StringProperty()

    def execute(self, context):
        import os, subprocess
        k = (self.key or "").strip()
        try:
            path = _MODULE_PATHS.get(k)
            if not path:
                self.report({'ERROR'}, "未找到该模块路径")
                return {'CANCELLED'}
            folder = os.path.dirname(os.path.abspath(path))
            if not os.path.isdir(folder):
                self.report({'ERROR'}, "目录不存在")
                return {'CANCELLED'}
            # Windows Explorer 打开
            subprocess.Popen(['explorer', folder])
            self.report({'INFO'}, f"已打开: {folder}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"打开失败: {e}")
            return {'CANCELLED'}

class AF_OT_show_pie_menu(bpy.types.Operator):
    bl_idname = "af.show_pie_menu"
    bl_label = "显示饼菜单"
    bl_description = "呼出AartFlow饼菜单，快速访问常用功能"
    
    def invoke(self, context, event):
        # 使用 invoke 触发饼菜单，兼容按键交互
        global _focused_module_key
        _focused_module_key = None
        # 确保相关类已注册，防止找不到 operator/menu
        def _ensure(cls):
            try:
                is_registered = False
                if hasattr(cls, 'is_registered'):
                    is_registered = cls.is_registered() if callable(cls.is_registered) else bool(cls.is_registered)
                if not is_registered:
                    bpy.utils.register_class(cls)
            except Exception:
                pass
        _ensure(AF_MT_pie_menu)
        _ensure(AF_OT_pie_module_action)
        _ensure(AF_OT_module_popup)
        bpy.ops.wm.call_menu_pie(name="AF_MT_pie_menu")
        return {'FINISHED'}

class AF_MT_pie_menu(bpy.types.Menu):
    # ASCII 避免中文乱码
    bl_label = "AartFlow Modules"
    bl_idname = "AF_MT_pie_menu"

    def draw(self, context):
        layout = self.layout
        
        # 饼菜单布局
        pie = layout.menu_pie()
        
        # 仅显示模块面板：优先使用 _MODULE_PATHS；为空时回退到已加载模块
        _ensure_loaded()
        base_list = list(_MODULE_PATHS.keys()) or list(_loaded_modules.keys())
        loaded_modules = sorted(list(set(base_list)))
        # 最多 8 个扇区：7 个模块 + 1 个 More...（当模块>8时）
        if len(loaded_modules) > 8:
            primary = loaded_modules[:7]
            rest = loaded_modules[7:]
        else:
            primary = loaded_modules
            rest = []
        
        if not primary:
            # 无模块时仅提示
            pie.label(text="No modules")
        else:
            # 仅放模块项
            for name in primary:
                op = pie.operator("af.pie_module_action", icon='SCRIPT', text=name)
                op.module_name = name
                op.action = "popup"
        
        # 当模块超出 8 个时，用 More... 承载剩余模块列表
        if rest:
            op_more = pie.operator("af.pie_module_action", icon='MENU_PANEL', text="More...")
            op_more.module_name = ";".join(rest)
            op_more.action = "more_popup"

class AF_OT_pie_module_action(bpy.types.Operator):
    bl_idname = "af.pie_module_action"
    # ASCII 避免中文乱码
    bl_label = "Module Action"
    bl_description = "Operate on selected module"
    
    module_name: bpy.props.StringProperty(name="模块名", description="要操作的模块名称")
    action: bpy.props.StringProperty(name="操作", description="要执行的操作", default="refresh")
    
    def execute(self, context):
        module_name = self.module_name.strip()
        action = self.action.strip()
        
        if not module_name:
            self.report({'ERROR'}, "无效的模块名称")
            return {'CANCELLED'}
        
        global _focused_module_key

        if action == "popup":
            try:
                # 使用临时对话框，不干扰 N 面板
                bpy.ops.af.module_dialog('INVOKE_DEFAULT', module_name=module_name)
            except Exception as e:
                self.report({'ERROR'}, f"Popup failed: {e}")
                return {'CANCELLED'}
        elif action == "more_popup":
            try:
                bpy.ops.af.module_dialog('INVOKE_DEFAULT', module_list=module_name)
            except Exception as e:
                self.report({'ERROR'}, f"More popup failed: {e}")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, f"未知操作: {action}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

def _is_panel_class(obj) -> bool:
    try:
        return isinstance(obj, type) and issubclass(obj, bpy.types.Panel)
    except Exception:
        return False

def _get_panels_for_module(module_key: str):
    """返回指定模块对象里声明的面板类，优先直接从 _loaded_modules 读取以确保可见。"""
    results = []
    try:
        key = (module_key or '').strip()
        mod = _loaded_modules.get(key)
        if not mod:
            return results
        module_dict = getattr(mod, '__dict__', {})
        for attr_name, obj in module_dict.items():
            try:
                if not (isinstance(obj, type) and issubclass(obj, bpy.types.Panel)):
                    continue
                # 排除基础 Panel、代理和容器
                if obj is bpy.types.Panel or getattr(obj, '__name__', '') == 'Panel':
                    continue
                bl_idname = getattr(obj, 'bl_idname', '')
                if not isinstance(bl_idname, str) or '_PT_' not in bl_idname:
                    continue
                results.append(obj)
            except Exception:
                pass
    except Exception:
        pass
    return results

def _collect_target_panels():
    """从所有已加载外部模块中抽象收集 3D 视图侧栏面板类。"""
    _ensure_loaded()
    candidates = []
    print(f"[AARTFLOW] 开始收集面板，已加载模块数量: {len(_loaded_modules)}")
    print(f"[AARTFLOW] 模块路径配置: {list(_MODULE_PATHS.keys())}")
    
    for mod_name, mod in list(_loaded_modules.items()):
        print(f"[AARTFLOW] 检查模块: {mod_name}")
        mod_dict = getattr(mod, "__dict__", {})
        print(f"[AARTFLOW] 模块 {mod_name} 包含 {len(mod_dict)} 个属性")
        
        for _name, obj in mod_dict.items():
            # 必须是自定义 Panel 子类，且具有有效的 bl_idname（包含 PT），排除基础 Panel 类型别名
            if not _is_panel_class(obj):
                continue
            print(f"[AARTFLOW] 检查对象 {_name}: {type(obj)}")
            try:
                if obj is bpy.types.Panel or getattr(obj, "__name__", "") == "Panel":
                    continue
            except Exception:
                pass
            bid = getattr(obj, "bl_idname", "") or ""
            if not isinstance(bid, str) or "_PT_" not in bid:
                print(f"[AARTFLOW] 跳过面板 {_name}: bl_idname='{bid}' (不包含_PT_)")
                continue
            # 收纳所有自定义 Panel（无论原本属于哪个 Space/Region），
            # 统一在挂载阶段改为 VIEW_3D/UI 并置于 AartFlow 根面板下
            print(f"[AARTFLOW] 找到面板: {bid} (来自模块 {mod_name})")
            candidates.append(obj)
    
    print(f"[AARTFLOW] 总共收集到 {len(candidates)} 个面板")
    
    # 去除父面板自身等非业务面板
    filtered = []
    for cls in candidates:
        bid = getattr(cls, "bl_idname", "")
        if bid == "VIEW3D_PT_aartflow_root":
            continue
        filtered.append(cls)
    
    print(f"[AARTFLOW] 过滤后剩余 {len(filtered)} 个面板")
    return filtered

def _reload_one_module_and_remount(module_key: str):
    """仅重载一个引用模块并重新挂载所有面板，其他已加载模块保持不变。"""
    global _loaded_modules
    key = (module_key or "").strip()
    if not key or key not in _MODULE_PATHS:
        return
    # 1) 从缓存与 sys.modules 中移除该模块
    try:
        _loaded_modules.pop(key, None)
    except Exception:
        pass
    try:
        mod_full = f"{_EXT_NAMESPACE_PREFIX}.{key}"
        if mod_full in sys.modules:
            del sys.modules[mod_full]
    except Exception:
        pass
    # 2) 重新导入该模块到 _loaded_modules
    try:
        _loaded_modules[key] = _load_ext_module(key, _MODULE_PATHS[key])
    except Exception:
        pass
    # 2.5) 先不调用模块的 register，让 _register_proxies 来处理面板注册
    # 3) 先注册模块（获取操作器/属性等），随后卸载其面板类，最后挂代理
    try:
        _mod = _loaded_modules.get(key)
        if _mod and hasattr(_mod, "register") and callable(_mod.register):
            # 先调用模块的 register 函数注册所有内容
            _mod.register()
            # 然后立即卸载面板类，只保留操作器、属性等
            _unregister_panels_from_module(_mod)
            print(f"[AARTFLOW] 模块 {key} 已注册非面板内容，面板通过代理机制显示")
    except Exception as e:
        print(f"[AARTFLOW] 注册模块 {key} 内容失败: {e}")
        pass
    # 4) 最后挂代理，确保原面板不会出现为独立页签
    try:
        _register_proxies()
    except Exception:
        pass

def _unregister_panels_from_module(module):
    """从模块中卸载面板类，只保留操作器、属性等非面板内容。
    更健壮：即便缺少 is_registered 属性也尝试卸载，失败静默。"""
    try:
        module_dict = getattr(module, "__dict__", {})
        for attr_name, obj in module_dict.items():
            if isinstance(obj, type) and issubclass(obj, bpy.types.Panel):
                # 过滤基础 Panel 与无效 id 的类，避免 RNAMeta 垃圾值
                try:
                    if obj is bpy.types.Panel or getattr(obj, "__name__", "") == "Panel":
                        continue
                    bl_idname = getattr(obj, 'bl_idname', '')
                    if not isinstance(bl_idname, str) or '_PT_' not in bl_idname:
                        continue
                    mod_name = getattr(module, '__name__', '')
                    obj_mod = getattr(obj, '__module__', '')
                    if mod_name and (obj_mod != mod_name and not str(obj_mod).startswith(mod_name)):
                        continue
                except Exception:
                    pass
                try:
                    # 优先判断已注册状态，判断失败则直接尝试卸载
                    can_try = True
                    try:
                        if hasattr(obj, 'is_registered'):
                            if callable(obj.is_registered):
                                can_try = obj.is_registered()
                            else:
                                can_try = bool(obj.is_registered)
                    except Exception:
                        can_try = True
                    if can_try:
                        bpy.utils.unregister_class(obj)
                        print(f"[AARTFLOW] 已卸载模块面板: {attr_name}")
                except Exception as e:
                    print(f"[AARTFLOW] 卸载模块面板 {attr_name} 失败: {e}")
    except Exception as e:
        print(f"[AARTFLOW] 处理模块面板卸载失败: {e}")

def _create_proxy_panel(original_panel_class):
    """为原始面板创建代理面板，保持原有功能完整"""
    original_bid = getattr(original_panel_class, "bl_idname", "Unknown")
    proxy_bid = f"AF_PROXY_{original_bid}"
    original_module = str(getattr(original_panel_class, "__module__", ""))
    
    class ProxyPanel(bpy.types.Panel):
        # 使用 ASCII 标签，避免中文在某些平台乱码
        bl_label = getattr(original_panel_class, "bl_label", "ProxyPanel")
        bl_idname = proxy_bid
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "AartFlow"
        bl_parent_id = "VIEW3D_PT_aartflow_modules"
        
        # 复制原始面板的所有属性，显式排除会破坏注册的内部/定位属性
        _exclude_attrs = {
            'bl_space_type', 'bl_region_type', 'bl_category', 'bl_parent_id',
            'bl_idname', 'bl_rna', 'bl_owner_id', 'id_data', 'rna_type'
        }
        for attr_name in dir(original_panel_class):
            if attr_name.startswith('_') or attr_name in _exclude_attrs:
                continue
            try:
                original_value = getattr(original_panel_class, attr_name)
                # 仅复制安全的非可调用属性，允许少数声明型属性透传
                if not callable(original_value) or attr_name in ['bl_label', 'bl_options', 'bl_context', 'bl_order']:
                    setattr(ProxyPanel, attr_name, original_value)
            except Exception:
                pass
        
        @classmethod
        def poll(cls, context):
            # 委托到原始面板的 poll 方法
            try:
                base_ok = original_panel_class.poll(context) if hasattr(original_panel_class, 'poll') else True
            except Exception:
                base_ok = True
            # 如果设置了聚焦模块，仅显示来自该模块的面板
            try:
                if _focused_module_key:
                    return base_ok and original_module.startswith(f"{_EXT_NAMESPACE_PREFIX}.{_focused_module_key}")
            except Exception:
                pass
            return base_ok
        
        def draw(self, context):
            # 委托到原始面板的 draw 方法
            if hasattr(original_panel_class, 'draw'):
                original_panel_class.draw(self, context)
    
    return ProxyPanel

def _register_proxies():
    global _removed_original_panels
    print(f"[AARTFLOW] 开始注册代理面板")
    
    # 确保主面板与子面板已注册
    try:
        # 更安全的注册检查
        is_registered = False
        try:
            if hasattr(VIEW3D_PT_aartflow_root, 'is_registered'):
                if callable(VIEW3D_PT_aartflow_root.is_registered):
                    is_registered = VIEW3D_PT_aartflow_root.is_registered()
                else:
                    is_registered = VIEW3D_PT_aartflow_root.is_registered
        except Exception:
            # 如果检查注册状态失败，假设未注册
            is_registered = False
        
        if not is_registered:
            try:
                bpy.utils.register_class(VIEW3D_PT_aartflow_root)
                print(f"[AARTFLOW] 主面板注册成功")
            except Exception as reg_error:
                print(f"[AARTFLOW] 主面板注册失败: {reg_error}")
                # 如果注册失败，尝试先卸载再注册
                try:
                    bpy.utils.unregister_class(VIEW3D_PT_aartflow_root)
                    bpy.utils.register_class(VIEW3D_PT_aartflow_root)
                    print(f"[AARTFLOW] 主面板重新注册成功")
                except Exception as retry_error:
                    print(f"[AARTFLOW] 主面板重新注册失败: {retry_error}")
                    return

        # 注册子面板容器
        try:
            is_sub_registered = False
            if hasattr(VIEW3D_PT_aartflow_modules, 'is_registered'):
                if callable(VIEW3D_PT_aartflow_modules.is_registered):
                    is_sub_registered = VIEW3D_PT_aartflow_modules.is_registered()
                else:
                    is_sub_registered = VIEW3D_PT_aartflow_modules.is_registered
        except Exception:
            is_sub_registered = False
        if not is_sub_registered:
            try:
                bpy.utils.register_class(VIEW3D_PT_aartflow_modules)
                print(f"[AARTFLOW] 集成模块容器面板注册成功")
            except Exception as e:
                print(f"[AARTFLOW] 集成模块容器面板注册失败: {e}")
                return
        else:
            print(f"[AARTFLOW] 主面板已注册，跳过")
    except Exception as e:
        print(f"[AARTFLOW] 主面板注册检查失败: {e}")
        return

    # 收集目标面板
    targets = _collect_target_panels()
    print(f"[AARTFLOW] 准备为 {len(targets)} 个面板创建代理")
    
    if not targets:
        print("[AARTFLOW] 没有找到任何目标面板，AartFlow 面板将以空状态显示")
        if _loaded_modules:
            print("[AARTFLOW] 调试信息：")
            print(f"  - 已加载模块数量: {len(_loaded_modules)}")
            for name, mod in _loaded_modules.items():
                print(f"  - 模块 {name}: {type(mod)}")
                if hasattr(mod, "__dict__"):
                    panel_count = 0
                    for attr_name, obj in mod.__dict__.items():
                        if isinstance(obj, type) and issubclass(obj, bpy.types.Panel):
                            panel_count += 1
                    print(f"    - 包含 {panel_count} 个面板类")
        return

    # 为每个原始面板创建代理面板
    print(f"[AARTFLOW] 开始处理 {len(targets)} 个目标面板")
    for i, original_cls in enumerate(targets):
        original_bid = getattr(original_cls, "bl_idname", "Unknown")
        print(f"[AARTFLOW] [{i+1}/{len(targets)}] 为面板 {original_bid} 创建代理")
        
        # 检查这个面板是否已经存在代理（避免重复注册）
        if any(meta.get("original_bid") == original_bid for meta in _reparented_original_panels):
            print(f"[AARTFLOW] 面板 {original_bid} 已存在代理，跳过")
            continue
        
        try:
            # 先卸载原始面板，避免重复显示
            try:
                if hasattr(original_cls, 'is_registered'):
                    if callable(original_cls.is_registered):
                        if original_cls.is_registered():
                            bpy.utils.unregister_class(original_cls)
                            print(f"[AARTFLOW] 原始面板 {original_bid} 已卸载")
                    else:
                        if original_cls.is_registered:
                            bpy.utils.unregister_class(original_cls)
                            print(f"[AARTFLOW] 原始面板 {original_bid} 已卸载")
            except Exception as e:
                print(f"[AARTFLOW] 卸载原始面板 {original_bid} 失败: {e}")
            
            # 创建代理面板类
            proxy_cls = _create_proxy_panel(original_cls)
            
            # 记录代理面板信息
            _reparented_original_panels.append({
                "original_cls": original_cls,
                "proxy_cls": proxy_cls,
                "original_bid": original_bid,
                "proxy_bid": proxy_cls.bl_idname
            })
            
            # 注册代理面板
            bpy.utils.register_class(proxy_cls)
            print(f"[AARTFLOW] 代理面板 {proxy_cls.bl_idname} 注册成功")
            
        except Exception as e:
            print(f"[AARTFLOW] 创建代理面板 {original_bid} 失败: {e}")

    # 验证所有被集成模块的面板是否都被隐藏
    _verify_panel_hiding()

    # 刷新界面
    try:
        for area in getattr(bpy.context, "screen", {}).areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    except Exception:
        pass

def _cleanup_removed_module(key):
    """彻底清理被移除模块的所有相关资源"""
    print(f"[AARTFLOW] 开始清理模块 {key} 的所有资源")
    
    # 声明全局变量
    global _reparented_original_panels, _loaded_modules, _MODULE_PATHS, _panels_to_remove_permanently
    
    # 1. 先标记要永久移除的面板ID
    print(f"[AARTFLOW] 标记要永久移除的面板")
    for meta in list(_reparented_original_panels):
        original_bid = meta.get("original_bid", "")
        proxy_bid = meta.get("proxy_bid", "")
        original_cls = meta.get("original_cls")
        
        # 检查面板ID是否包含要移除的模块名
        id_match = key in original_bid or key in proxy_bid
        
        # 检查面板的其他属性是否包含模块名
        attr_match = False
        if original_cls is not None:
            try:
                # 检查 bl_category 和 bl_label
                category = getattr(original_cls, 'bl_category', '')
                label = getattr(original_cls, 'bl_label', '')
                if key in str(category) or key in str(label):
                    attr_match = True
            except Exception:
                pass
        
        if id_match or attr_match:
            _panels_to_remove_permanently.add(original_bid)
            print(f"[AARTFLOW] 标记面板 {original_bid} 为永久移除 (ID匹配: {id_match}, 属性匹配: {attr_match})")
    
    # 2. 卸载所有代理面板并恢复原始面板（在清理记录之前）
    print(f"[AARTFLOW] 先卸载所有代理面板")
    _unregister_proxies()
    
    # 2. 清理代理面板记录（通过模块名匹配）
    panels_to_remove = []
    for meta in list(_reparented_original_panels):
        original_bid = meta.get("original_bid", "")
        proxy_bid = meta.get("proxy_bid", "")
        
        # 简单直接的匹配：检查面板ID是否包含模块名
        if key in original_bid or key in proxy_bid:
            panels_to_remove.append(meta)
            print(f"[AARTFLOW] 标记移除面板记录: {original_bid} -> {proxy_bid}")
    
    # 从记录中移除匹配的面板
    for meta in panels_to_remove:
        _reparented_original_panels.remove(meta)
    
    print(f"[AARTFLOW] 已清理 {len(panels_to_remove)} 个面板记录")
    
    # 3. 清理模块缓存
    if key in _loaded_modules:
        del _loaded_modules[key]
        print(f"[AARTFLOW] 已从已加载模块中移除: {key}")
    
    # 4. 清理 sys.modules
    mod_full = f"{_EXT_NAMESPACE_PREFIX}.{key}"
    if mod_full in sys.modules:
        del sys.modules[mod_full]
        print(f"[AARTFLOW] 已从 sys.modules 中移除: {mod_full}")
    
    # 5. 清理模块路径
    if key in _MODULE_PATHS:
        del _MODULE_PATHS[key]
        print(f"[AARTFLOW] 已从模块路径中移除: {key}")
    
    # 6. 强制清理：卸载所有属于该模块的残留面板（通过 __module__ 判断）
    try:
        _force_unload_module_panels(key)
    except Exception as e:
        print(f"[AARTFLOW] 强制清理模块 {key} 面板失败: {e}")

    # 7. 重新注册代理面板，确保面板与模块清单同步
    print(f"[AARTFLOW] 重新注册代理面板以保持同步")
    _register_proxies()
    
    # 7. 刷新界面
    _refresh_ui()
    
    # 8. 调试面板同步状态
    _debug_panel_sync()
    
    # 9. 清空永久移除面板标记
    _panels_to_remove_permanently.clear()
    
    print(f"[AARTFLOW] 模块 {key} 清理完成，面板已同步")

def _cleanup_proxy_panels_by_key(key):
    """直接通过面板ID清理代理面板"""
    print(f"[AARTFLOW] 直接清理包含 '{key}' 的代理面板")
    
    # 获取所有已注册的面板
    panels_to_cleanup = []
    for attr_name in dir(bpy.types):
        if attr_name.startswith('AF_PROXY_'):
            try:
                panel_class = getattr(bpy.types, attr_name)
                if hasattr(panel_class, 'is_registered') and callable(panel_class.is_registered):
                    if panel_class.is_registered():
                        # 检查面板ID是否包含模块名
                        if key in attr_name:
                            panels_to_cleanup.append((attr_name, panel_class))
                            print(f"[AARTFLOW] 找到需要清理的代理面板: {attr_name}")
            except Exception as e:
                print(f"[AARTFLOW] 检查面板 {attr_name} 时出错: {e}")
    
    # 清理找到的代理面板
    for panel_name, panel_class in panels_to_cleanup:
        try:
            bpy.utils.unregister_class(panel_class)
            print(f"[AARTFLOW] 代理面板 {panel_name} 已卸载")
        except Exception as e:
            print(f"[AARTFLOW] 卸载代理面板 {panel_name} 失败: {e}")
    
    print(f"[AARTFLOW] 直接清理完成，共清理 {len(panels_to_cleanup)} 个代理面板")
    
    # 额外检查：清理所有可能的残留代理面板
    _cleanup_orphaned_proxy_panels()

def _cleanup_orphaned_proxy_panels():
    """清理所有孤立的代理面板（没有对应模块的代理面板）"""
    print("[AARTFLOW] 检查并清理孤立的代理面板")
    
    # 获取当前有效的模块名列表
    valid_module_names = set(_MODULE_PATHS.keys())
    
    # 获取所有代理面板
    orphaned_panels = []
    for attr_name in dir(bpy.types):
        if attr_name.startswith('AF_PROXY_'):
            try:
                panel_class = getattr(bpy.types, attr_name)
                if hasattr(panel_class, 'is_registered') and callable(panel_class.is_registered):
                    if panel_class.is_registered():
                        # 检查这个代理面板是否还有对应的有效模块
                        is_orphaned = True
                        for module_name in valid_module_names:
                            if module_name in attr_name:
                                is_orphaned = False
                                break
                        
                        if is_orphaned:
                            orphaned_panels.append((attr_name, panel_class))
                            print(f"[AARTFLOW] 发现孤立代理面板: {attr_name}")
            except Exception as e:
                print(f"[AARTFLOW] 检查面板 {attr_name} 时出错: {e}")
    
    # 清理孤立的代理面板
    for panel_name, panel_class in orphaned_panels:
        try:
            bpy.utils.unregister_class(panel_class)
            print(f"[AARTFLOW] 孤立代理面板 {panel_name} 已清理")
        except Exception as e:
            print(f"[AARTFLOW] 清理孤立代理面板 {panel_name} 失败: {e}")
    
    print(f"[AARTFLOW] 孤立代理面板清理完成，共清理 {len(orphaned_panels)} 个")

def _clear_all_integrations():
    """彻底清空：卸载所有代理/原面板、调用各模块的 unregister、清理 sys.modules、清空路径与缓存，并刷新 UI。"""
    global _MODULE_PATHS, _loaded_modules, _reparented_original_panels, _panels_to_remove_permanently

    print("[AARTFLOW] 开始彻底清空所有集成模块")
    # 1) 卸载所有代理与容器，避免 UI 占用
    try:
        _unregister_proxies()
    except Exception as e:
        print(f"[AARTFLOW] 卸载代理失败: {e}")

    # 2) 调用各外部模块的 unregister（如果提供）
    for _name, _mod in list(_loaded_modules.items()):
        try:
            if hasattr(_mod, "unregister") and callable(_mod.unregister):
                _mod.unregister()
                print(f"[AARTFLOW] 外部模块 {_name} 已调用 unregister()")
        except Exception as e:
            print(f"[AARTFLOW] 调用模块 {_name} unregister 失败: {e}")

    # 3) 强制卸载所有残留面板（遍历当前路径键）
    for key in list(_MODULE_PATHS.keys()):
        try:
            _force_unload_module_panels(key)
        except Exception as e:
            print(f"[AARTFLOW] 强制卸载模块 {key} 残留面板失败: {e}")

    # 4) 清理 sys.modules 中的动态导入模块
    try:
        for _k in list(sys.modules.keys()):
            if _k.startswith(f"{_EXT_NAMESPACE_PREFIX}."):
                try:
                    del sys.modules[_k]
                except Exception:
                    pass
        print(f"[AARTFLOW] sys.modules 中的 {_EXT_NAMESPACE_PREFIX}.* 已清空")
    except Exception as e:
        print(f"[AARTFLOW] 清理 sys.modules 失败: {e}")

    # 5) 清空缓存与记录
    _loaded_modules.clear()
    _MODULE_PATHS.clear()
    _reparented_original_panels.clear()
    _panels_to_remove_permanently.clear()

    # 6) 清理所有孤立代理（双保险）
    try:
        _cleanup_orphaned_proxy_panels()
    except Exception:
        pass

    # 7) 清空面板设置集合（UI 列表）
    try:
        settings = getattr(bpy.context.scene, 'af_integration_settings', None)
        if settings is not None and hasattr(settings, 'modules'):
            # 逐个删除避免引用断裂
            for i in range(len(settings.modules) - 1, -1, -1):
                try:
                    settings.modules.remove(i)
                except Exception:
                    pass
            print("[AARTFLOW] 场景设置中的模块列表已清空")
    except Exception as e:
        print(f"[AARTFLOW] 清空场景设置失败: {e}")

    # 8) 重新注册容器面板（空状态）并刷新
    try:
        _register_proxies()
    except Exception:
        pass
    try:
        _refresh_ui()
        _debug_panel_sync()
    except Exception:
        pass
    print("[AARTFLOW] 清空完成")

def _force_unload_module_panels(module_key: str):
    """强制卸载属于指定模块的所有面板（非代理），通过 __module__ 前缀匹配。
    例如模块键 standardView → bl_ext.aartflow_blender.standardView.*
    """
    try:
        prefix = f"{_EXT_NAMESPACE_PREFIX}.{(module_key or '').strip()}"
        if not prefix or prefix == f"{_EXT_NAMESPACE_PREFIX}.":
            return
        removed = 0
        for attr_name in dir(bpy.types):
            try:
                panel_class = getattr(bpy.types, attr_name)
                is_panel_class = isinstance(panel_class, type) and issubclass(panel_class, bpy.types.Panel)
                if not is_panel_class:
                    continue
                # 跳过代理与集成容器类
                if attr_name.startswith("AF_PROXY_"):
                    continue
                if attr_name in {"VIEW3D_PT_aartflow_root", "VIEW3D_PT_aartflow_modules"}:
                    continue
                cls_mod = getattr(panel_class, "__module__", "")
                if not isinstance(cls_mod, str):
                    continue
                if not cls_mod.startswith(prefix):
                    continue
                try:
                    bpy.utils.unregister_class(panel_class)
                    removed += 1
                    print(f"[AARTFLOW] 强制卸载残留面板: {attr_name} ({cls_mod})")
                except Exception:
                    # 可能未注册或已被其他流程卸载
                    pass
            except Exception:
                # 某些属性访问可能抛错，直接忽略
                pass
        print(f"[AARTFLOW] 强制清理完成，共卸载 {removed} 个残留面板")
    except Exception as e:
        print(f"[AARTFLOW] 强制卸载面板时出错: {e}")

def _verify_panel_hiding():
    """验证所有被集成模块的面板是否都被正确隐藏"""
    print("[AARTFLOW] 验证面板隐藏状态...")
    
    # 获取所有已注册的面板
    registered_panels = []
    for attr_name in dir(bpy.types):
        if attr_name.startswith('VIEW3D_PT_'):
            try:
                panel_class = getattr(bpy.types, attr_name)
                if hasattr(panel_class, 'is_registered') and callable(panel_class.is_registered):
                    if panel_class.is_registered():
                        registered_panels.append(attr_name)
            except Exception:
                pass
    
    print(f"[AARTFLOW] 当前已注册的面板数量: {len(registered_panels)}")
    
    # 检查是否有被集成模块的面板仍然显示
    for panel_name in registered_panels:
        if not panel_name.startswith('AF_PROXY_') and panel_name != 'VIEW3D_PT_aartflow_root':
            # 检查这个面板是否来自被集成的模块
            is_from_integrated_module = False
            for mod_name, mod in _loaded_modules.items():
                if hasattr(mod, "__dict__"):
                    for attr_name, obj in mod.__dict__.items():
                        if isinstance(obj, type) and issubclass(obj, bpy.types.Panel):
                            if hasattr(obj, 'bl_idname') and obj.bl_idname == panel_name:
                                is_from_integrated_module = True
                                break
                if is_from_integrated_module:
                    break
            
            if is_from_integrated_module:
                print(f"[AARTFLOW] 警告: 面板 {panel_name} 来自被集成模块但未被隐藏")
            else:
                print(f"[AARTFLOW] 面板 {panel_name} 不是来自被集成模块，正常显示")
    
    print("[AARTFLOW] 面板隐藏验证完成")

def _refresh_ui():
    """刷新用户界面"""
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        print("[AARTFLOW] 界面已刷新")
    except Exception as e:
        print(f"[AARTFLOW] 刷新界面失败: {e}")

def _debug_panel_sync():
    """调试面板同步状态"""
    print("[AARTFLOW] 调试面板同步状态...")
    print(f"[AARTFLOW] 当前模块路径: {list(_MODULE_PATHS.keys())}")
    print(f"[AARTFLOW] 当前已加载模块: {list(_loaded_modules.keys())}")
    print(f"[AARTFLOW] 当前代理面板记录数: {len(_reparented_original_panels)}")
    
    # 显示所有代理面板记录
    for i, meta in enumerate(_reparented_original_panels):
        original_bid = meta.get("original_bid", "Unknown")
        proxy_bid = meta.get("proxy_bid", "Unknown")
        print(f"[AARTFLOW] 记录 {i+1}: {original_bid} -> {proxy_bid}")
    
    # 检查代理面板是否与模块清单一致
    expected_proxies = set()
    for mod_name in _MODULE_PATHS.keys():
        for meta in _reparented_original_panels:
            if mod_name in meta.get("original_bid", ""):
                expected_proxies.add(meta.get("proxy_bid", ""))
    
    actual_proxies = set()
    for attr_name in dir(bpy.types):
        if attr_name.startswith('AF_PROXY_'):
            try:
                obj = getattr(bpy.types, attr_name)
                if hasattr(obj, 'is_registered') and callable(obj.is_registered):
                    if obj.is_registered():
                        actual_proxies.add(attr_name)
            except Exception:
                pass
    
    print(f"[AARTFLOW] 期望的代理面板: {expected_proxies}")
    print(f"[AARTFLOW] 实际的代理面板: {actual_proxies}")
    
    if expected_proxies == actual_proxies:
        print("[AARTFLOW] ✅ 面板同步状态正常")
    else:
        print("[AARTFLOW] ❌ 面板同步状态异常")
        missing = expected_proxies - actual_proxies
        extra = actual_proxies - expected_proxies
        if missing:
            print(f"[AARTFLOW] 缺失的代理面板: {missing}")
        if extra:
            print(f"[AARTFLOW] 多余的代理面板: {extra}")
    
    print("[AARTFLOW] 面板同步状态调试完成")

def _add_keymap():
    """添加键盘快捷键映射"""
    global _keymaps
    
    # 获取3D视图的keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon or wm.keyconfigs.user
    if kc:
        km = kc.keymaps.get('3D View') or kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        # 添加F5键快捷键
        kmi = km.keymap_items.new("af.show_pie_menu", type='F5', value='PRESS')
        _keymaps.append((km, kmi))
        
        print("[AARTFLOW] 键盘快捷键已添加: F5键呼出饼菜单")

def _remove_keymap():
    """移除键盘快捷键映射"""
    global _keymaps
    
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    
    print("[AARTFLOW] 键盘快捷键已移除")

def _unregister_proxies():
    # 卸载代理面板并恢复原始面板
    global _reparented_original_panels, _panels_to_remove_permanently

    # 卸载所有代理面板并恢复原始面板
    for meta in list(_reparented_original_panels):
        proxy_cls = meta.get("proxy_cls")
        original_cls = meta.get("original_cls")
        original_bid = meta.get("original_bid", "Unknown")
        
        # 卸载代理面板
        if proxy_cls is not None:
            try:
                bpy.utils.unregister_class(proxy_cls)
                print(f"[AARTFLOW] 代理面板 {meta.get('proxy_bid', 'Unknown')} 卸载成功")
            except Exception as e:
                print(f"[AARTFLOW] 代理面板 {meta.get('proxy_bid', 'Unknown')} 卸载失败: {e}")
        
        # 只恢复未被标记为永久移除的原始面板
        if original_cls is not None and original_bid not in _panels_to_remove_permanently:
            try:
                bpy.utils.register_class(original_cls)
                print(f"[AARTFLOW] 原始面板 {original_bid} 已恢复")
            except Exception as e:
                print(f"[AARTFLOW] 恢复原始面板 {original_bid} 失败: {e}")
        elif original_bid in _panels_to_remove_permanently:
            print(f"[AARTFLOW] 跳过恢复被标记为永久移除的面板: {original_bid}")
    
    _reparented_original_panels.clear()

    # 卸载主面板与子面板
    try:
        # 检查主面板是否已注册再卸载
        is_registered = False
        try:
            if hasattr(VIEW3D_PT_aartflow_root, 'is_registered'):
                if callable(VIEW3D_PT_aartflow_root.is_registered):
                    is_registered = VIEW3D_PT_aartflow_root.is_registered()
                else:
                    is_registered = VIEW3D_PT_aartflow_root.is_registered
        except Exception:
            is_registered = False
        
        if is_registered:
            bpy.utils.unregister_class(VIEW3D_PT_aartflow_root)
            print(f"[AARTFLOW] 主面板已卸载")
        else:
            print(f"[AARTFLOW] 主面板未注册，跳过卸载")
    except Exception as e:
        print(f"[AARTFLOW] 主面板卸载失败: {e}")

    try:
        is_sub_registered = False
        if hasattr(VIEW3D_PT_aartflow_modules, 'is_registered'):
            if callable(VIEW3D_PT_aartflow_modules.is_registered):
                is_sub_registered = VIEW3D_PT_aartflow_modules.is_registered()
            else:
                is_sub_registered = VIEW3D_PT_aartflow_modules.is_registered
        if is_sub_registered:
            bpy.utils.unregister_class(VIEW3D_PT_aartflow_modules)
            print(f"[AARTFLOW] 集成模块容器面板已卸载")
    except Exception as e:
        print(f"[AARTFLOW] 集成模块容器面板卸载失败: {e}")

def register():
    # 自动发现并加载 scripts 目录中的脚本
    global _MODULE_PATHS
    _discover_script_modules()
    _ensure_loaded()
    # 不需要卸载外部模块，因为我们使用代理面板，原始模块保持完整

    # 优先注册饼菜单相关三类，确保按键触发时可用
    try:
        bpy.utils.register_class(AF_OT_pie_module_action)
    except Exception:
        pass
    try:
        bpy.utils.register_class(AF_MT_pie_menu)
    except Exception:
        pass
    try:
        bpy.utils.register_class(AF_OT_module_dialog)
    except Exception:
        pass

    # 注册集成设置与面板
    try:
        bpy.utils.register_class(AF_ModuleItem)
        bpy.utils.register_class(AartFlowIntegrationSettings)
        bpy.types.Scene.af_integration_settings = bpy.props.PointerProperty(type=AartFlowIntegrationSettings)
    except Exception:
        pass

    # 注册其他 Operator 与面板
    try:
        bpy.utils.register_class(AF_OT_add_integration_module)
        bpy.utils.register_class(AF_OT_refresh_integration_module)
        bpy.utils.register_class(AF_OT_remove_integration_module)
        bpy.utils.register_class(AF_OT_refresh_all_modules)
        bpy.utils.register_class(AF_OT_configure_module_paths)
        bpy.utils.register_class(AF_OT_reset_module_paths)
        bpy.utils.register_class(AF_OT_open_module_folder)
        bpy.utils.register_class(AF_OT_show_pie_menu)
        bpy.utils.register_class(AF_OT_close_module_popup)
        bpy.utils.register_class(VIEW3D_PT_aartflow_popup)
    except Exception as e:
        print(f"[AARTFLOW] 操作器注册失败: {e}")
        pass
    

    # 先注册主面板
    try:
        # 检查面板是否已注册
        is_registered = False
        if hasattr(VIEW3D_PT_aartflow_root, 'is_registered'):
            if callable(VIEW3D_PT_aartflow_root.is_registered):
                is_registered = VIEW3D_PT_aartflow_root.is_registered()
            else:
                is_registered = VIEW3D_PT_aartflow_root.is_registered
        
        if not is_registered:
            bpy.utils.register_class(VIEW3D_PT_aartflow_root)
            print(f"[AARTFLOW] 主面板注册成功")
        else:
            print(f"[AARTFLOW] 主面板已注册，跳过")
    except Exception as e:
        print(f"[AARTFLOW] 主面板注册失败: {e}")
    
    # 先注册外部模块，确保所有功能正常
    for _name, mod in list(_loaded_modules.items()):
        try:
            if hasattr(mod, "register") and callable(mod.register):
                # 先注册所有内容
                mod.register()
                # 然后卸载面板类，只保留操作器、属性等
                _unregister_panels_from_module(mod)
                print(f"[AARTFLOW] 外部模块 {_name} 已注册非面板内容")
        except Exception as e:
            print(f"[AARTFLOW] 外部模块 {_name} 注册失败: {e}")
    
    # 然后注册 AartFlow 根面板和代理面板（这会隐藏原始面板）
    _register_proxies()
    
    # 添加键盘快捷键
    _add_keymap()

def unregister():
    # 先移除键盘快捷键
    _remove_keymap()
    
    # 再卸载代理面板
    _unregister_proxies()

    # 再卸载所有外部模块（其自身清理属性/处理器）
    for _name, mod in list(_loaded_modules.items()):
        try:
            if hasattr(mod, "unregister") and callable(mod.unregister):
                mod.unregister()
                print(f"[AARTFLOW] 外部模块 {_name} 卸载成功")
        except Exception as e:
            print(f"[AARTFLOW] 外部模块 {_name} 卸载失败: {e}")

    # 注销操作器与面板（先注销提前注册的三类）
    try:
        # 与 register 顶部对应：先注销饼菜单相关三类
        bpy.utils.unregister_class(AF_OT_module_dialog)
        bpy.utils.unregister_class(AF_MT_pie_menu)
        bpy.utils.unregister_class(AF_OT_pie_module_action)
        # 再注销其余
        bpy.utils.unregister_class(VIEW3D_PT_aartflow_popup)
        bpy.utils.unregister_class(AF_OT_close_module_popup)
        bpy.utils.unregister_class(AF_OT_show_pie_menu)
        bpy.utils.unregister_class(AF_OT_reset_module_paths)
        bpy.utils.unregister_class(AF_OT_open_module_folder)
        bpy.utils.unregister_class(AF_OT_configure_module_paths)
        bpy.utils.unregister_class(AF_OT_refresh_all_modules)
        bpy.utils.unregister_class(AF_OT_refresh_integration_module)
        bpy.utils.unregister_class(AF_OT_remove_integration_module)
        bpy.utils.unregister_class(AF_OT_add_integration_module)
    except Exception as e:
        print(f"[AARTFLOW] 操作器注销失败: {e}")
        pass
    try:
        if hasattr(bpy.types.Scene, 'af_integration_settings'):
            del bpy.types.Scene.af_integration_settings
        bpy.utils.unregister_class(AartFlowIntegrationSettings)
        bpy.utils.unregister_class(AF_ModuleItem)
    except Exception:
        pass

if __name__ == "__main__":
    # 连续点击“Run Script”时：先卸载上一次，再重新加载并注册（热重载）
    try:
        unregister()
    except Exception:
        pass
    try:
        # 清空已加载模块，确保外部脚本改动被重新加载
        for _k in list(sys.modules.keys()):
            if _k.startswith("aartflow_ext."):
                try:
                    del sys.modules[_k]
                except Exception:
                    pass
    except Exception:
        pass
    try:
        register()
        print("[AARTFLOW] 已直接注册（文本编辑器运行模式）。N 面板 > AartFlow 查看。再次运行将热重载。")
    except Exception as e:
        print("[AARTFLOW] 直接注册失败：", e)