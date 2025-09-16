# AartFlow 开发规范

## 📋 目录
- [代码规范](#代码规范)
- [文件命名规范](#文件命名规范)
- [Git工作流规范](#git工作流规范)
- [版本管理规范](#版本管理规范)
- [打包发布规范](#打包发布规范)
- [文档规范](#文档规范)
- [测试规范](#测试规范)

---

## 代码规范

### 1. Python代码风格
- 遵循PEP 8编码规范
- 使用4个空格缩进，不使用Tab
- 行长度限制为88字符（Black格式化器标准）
- 使用有意义的变量名和函数名

### 2. Blender API使用规范
```python
# 正确的导入顺序
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy.utils import register_class, unregister_class

# 类命名规范
class AF_OT_module_action(bpy.types.Operator):
    bl_idname = "af.module_action"  # 使用 af. 前缀
    bl_label = "操作名称"
    bl_options = {'REGISTER', 'UNDO'}
```

### 3. 错误处理规范
```python
def execute(self, context):
    """执行操作"""
    try:
        # 主要逻辑
        result = self._perform_action(context)
        
        if result:
            self.report({'INFO'}, "操作成功完成")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "操作未完成")
            return {'CANCELLED'}
            
    except Exception as e:
        self.report({'ERROR'}, f"操作失败: {e}")
        return {'CANCELLED'}
```

---

## 文件命名规范

### 1. 脚本模块文件
- **命名方式**: 帕斯卡命名法（PascalCase）
- **格式**: `模块功能名称.py`
- **示例**: 
  - `artRenderBack.py` - 艺术渲染后端模块
  - `objectMeasure.py` - 对象测量模块
  - `standardView.py` - 标准视图模块

### 2. 类命名规范
```python
# Operator 类
class AF_OT_module_action(bpy.types.Operator):
    bl_idname = "af.module_action"

# Panel 类
class AF_PT_module_panel(bpy.types.Panel):
    bl_idname = "AF_PT_module_panel"
    bl_category = "AartFlow"  # 统一使用 AartFlow 分类

# PropertyGroup 类
class ModuleSettings(bpy.types.PropertyGroup):
    pass
```

### 3. 函数命名规范
```python
# 公共函数：使用动词开头，描述性命名
def calculate_mesh_dimensions(obj):
    """计算网格尺寸"""
    pass

# 私有函数：使用下划线前缀
def _get_object_bounds(obj):
    """获取对象边界"""
    pass
```

---

## Git工作流规范

### 1. 分支管理
- **main**: 主分支，用于发布稳定版本
- **develop**: 开发分支，用于集成功能
- **feature/***: 功能分支，用于开发新功能
- **hotfix/***: 热修复分支，用于紧急修复

### 2. 提交信息规范
```bash
# 格式：类型(范围): 简短描述
# 类型：
# - feat: 新功能
# - fix: 修复bug
# - docs: 文档更新
# - style: 代码格式调整
# - refactor: 重构
# - test: 测试相关
# - chore: 构建过程或辅助工具的变动

# 示例：
git commit -m "feat(scripts): 添加新的测量工具模块"
git commit -m "fix(render): 修复渲染引擎内存泄漏问题"
git commit -m "docs(api): 更新API文档"
```

### 3. 提交前检查
- [ ] 代码通过语法检查
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 遵循命名规范

---

## 版本管理规范

### 1. 语义化版本控制
使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

### 2. 版本更新流程
```bash
# 1. 更新版本号
# 在 manifest.json 中更新版本号

# 打包 ZIP（必须先打包，再更新 index.json）
./package.ps1 -Version "1.0.1"

# 2. 更新 index.json
# 更新版本号、文件大小、哈希值

# 3. 创建Git标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 4. 推送到远程仓库
git push origin main --tags
```

### 3. 版本一致性校验与常见错误

#### Package version mismatch（remote: "X", archive: "Y"）

- **错误现象**: 安装时报错 `Package version mismatch (remote: "X", archive: "Y")`。
- **根因**: 远端索引文件 `index.json` 中的 `data[0].version` 与压缩包内部 `manifest.json.version` 不一致，或 `archive_url` 指向了旧包。
- **自检清单**:
  - 确认 `index.json` 中：
    - `version` 与目标版本一致
    - `archive_url` 指向最新包（建议使用 `raw.githubusercontent` 指向仓库 `dist`）
    - `archive_size` 与 `archive_hash` 与实际压缩包一致
  - 解压或读取压缩包内的 `manifest.json`，确认其中 `version` 与 `index.json` 一致
  - 资源发布/缓存：若通过 GitHub Pages 提供索引，变更后可能有缓存延时，等待数分钟或强制刷新

**校验示例（PowerShell）**

```powershell
# 1) 读取压缩包内部 manifest.json 的版本
$zip = "dist/AartFlow-1.0.1.zip"
$dst = "tmp_check"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $dst -Force
# 兼容两种布局：根目录或 AartFlow/ 目录
$manifestPath = @("$dst/manifest.json", "$dst/AartFlow/manifest.json") | Where-Object { Test-Path $_ } | Select-Object -First 1
$manifest = Get-Content $manifestPath | ConvertFrom-Json
Write-Host "archive manifest version = $($manifest.version)"

# 2) 计算压缩包大小与 SHA256（用于写入 index.json）
$size = (Get-Item $zip).Length
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
Write-Host "archive_size = $size"
Write-Host "archive_hash = sha256:$hash"

# 3) 快速验证下载链接可用（返回 200 即正常）
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/dist/AartFlow-1.0.1.zip" -Method Head -UseBasicParsing | Select-Object -ExpandProperty StatusCode
```

**参考**
- 在线扩展库索引：[`https://yizhww.github.io/AartFlow_blender/index.json`](https://yizhww.github.io/AartFlow_blender/index.json)

#### 在线索引 404（HTTP 404 Not Found）

- **错误现象**: 安装时报错 `install: HTTP error (HTTP Error 404: Not Found) reading '.../index.json'`。
- **根因**:
  - URL 拼写或路径大小写错误（`AartFlow_blender` 与 `aartflow_blender` 等）。
  - GitHub Pages 未部署或部署工件未包含 `index.json`。
  - 部署工作流产物路径不匹配（例如上传 `public/` 但未将 `index.json` 复制进去）。
  - 默认分支/目录变动导致路径失效。
  - Pages/CDN 缓存延迟。
- **快速排查**:
  - 直接访问索引 URL，或使用 PowerShell 检查：
    ```powershell
    Invoke-WebRequest -Uri "https://yizhww.github.io/AartFlow_blender/index.json" -Method Head -UseBasicParsing | Select-Object -ExpandProperty StatusCode
    ```
  - 查看仓库 Pages 设置与最近一次部署日志，确认成功并包含 `index.json`。
  - 核对工作流是否将根目录 `index.json` 复制到发布目录（例如 `public/index.json`）并作为 Pages 工件上传。
  - 验证原始链接可用性（用于快速定位是部署问题还是文件缺失）：
    ```powershell
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/index.json" -Method Head -UseBasicParsing | Select-Object -ExpandProperty StatusCode
    ```
- **修复建议**:
  - 更正 URL 与路径大小写；若迁移过目录/分支，更新链接。
  - 修正并触发 Pages 工作流，确保上传工件包含 `index.json`（例如将根 `index.json` 复制到 `public/` 后上传）。
  - 等待数分钟或添加查询参数（例如 `?t=timestamp`）绕过缓存。
  - 紧急安装可临时改用原始链接作为索引（仅测试用）：`https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/index.json`。

#### Archive checksum mismatch（sha256 不一致）

- **错误现象**: `Archive checksum mismatch "<id>", expected sha256:<expected>, was sha256:<actual>`。
- **根因**:
  - `index.json` 中的 `archive_hash` 与真实 ZIP 的哈希不一致（重新打包后未同步元数据）。
  - CDN/Pages 缓存返回了旧 ZIP（hash 与本地不同）。
  - 下载链路被代理替换（极少数环境）。
- **自检清单**:
  - 本地计算 ZIP 哈希：
    ```powershell
    (Get-FileHash dist/AartFlow-1.0.1.zip -Algorithm SHA256).Hash.ToLower()
    ```
  - 远端校验 ZIP 哈希：
    ```powershell
    iwr https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/dist/AartFlow-1.0.1.zip -OutFile _tmp.zip
    (Get-FileHash _tmp.zip -Algorithm SHA256).Hash.ToLower()
    Remove-Item _tmp.zip -Force
    ```
  - 若本地与远端一致，但与 `index.json` 不同 → 更新 `archive_hash`。
  - 若本地与 `index.json` 一致，但远端不同 → 等待缓存或变更下载 URL（添加查询参数）。
- **修复建议**:
  - 同步 `index.json` 的 `archive_hash` 与 `archive_size`（以本地为准）。
  - 避免频繁重打包；如需强制刷新，可将 `archive_url` 临时改为 `...?t=<timestamp>` 以穿透缓存。
  - 验证 Pages 返回 200 且内容更新：
    ```powershell
    Invoke-WebRequest -Uri "https://yizhww.github.io/AartFlow_blender/index.json?t=$(Get-Date -UFormat %s)" -Method Get -UseBasicParsing | % Content
    ```

#### Archive size mismatch（大小不一致）

- **错误现象**: `Archive size mismatch "<id>", expected <expected>, was <actual>`。
- **根因**:
  - `index.json` 中的 `archive_size` 与真实 ZIP 大小（字节）不一致（常见于打包后未同步更新索引）。
  - 远端缓存返回旧 ZIP，导致大小与本地不同。
- **自检清单**:
  - 本地计算 ZIP 大小：
    ```powershell
    (Get-Item dist/AartFlow-1.0.1.zip).Length
    ```
  - 对比 `index.json` 的 `archive_size` 数值是否一致（单位均为字节）。
  - 如使用 Pages/CDN，等待缓存或改用原始链接二次确认：
    ```powershell
    iwr https://raw.githubusercontent.com/yizhww/AartFlow_blender/main/dist/AartFlow-1.0.1.zip -OutFile _tmp.zip
    (Get-Item _tmp.zip).Length
    Remove-Item _tmp.zip -Force
    ```
- **修复建议**:
  - 以本地实际 ZIP 为准，更新 `index.json.archive_size`（与 `archive_hash` 一并更新）。
  - 严格遵循发布顺序：先打包 → 再更新 `index.json` → 再提交推送。
  - 必要时在 `archive_url` 添加查询参数（如 `?t=<timestamp>`）以绕过缓存。

### 4. 变更日志
在每次发布时更新CHANGELOG.md：
```markdown
## [1.0.1] - 2025-09-16

### Changed
- 重构所有模块文件名为帕斯卡命名法
- 更新模块开发规范文档

### Fixed
- 修复Blender扩展库索引文件
```

---

## 打包发布规范

### 1. 打包前检查清单
- [ ] 所有模块文件已重命名为帕斯卡命名法
- [ ] 代码通过语法检查
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] 所有引用已更新

### 2. 打包脚本使用
```powershell
# 使用打包脚本
.\package.ps1 -Version "1.0.1"

# 脚本会自动：
# - 验证必要文件
# - 创建ZIP文件
# - 计算文件大小
# - 清理临时文件
```

### 3. 发布流程
注意：发布顺序必须为“先打包 → 再更新 index.json → 再提交推送”，否则容易出现 Archive size/hash mismatch。
```bash
# 1. 重新打包
.\package.ps1 -Version "1.0.1"

# 2. 更新index.json
# 更新版本号、文件大小、哈希值

# 3. 提交更改
git add .
git commit -m "release: 发布版本 1.0.1"

# 4. 创建发布标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 5. 推送到远程仓库
git push origin main --tags
```

---

## 文档规范

### 1. 文档结构
```
docs/
├── README.md                 # 项目总览
├── installation.md          # 安装指南
├── quick-start.md           # 快速开始
├── features.md              # 功能特性
├── api-reference.md         # API参考
├── development.md           # 开发指南
├── module-development.md    # 模块开发规范
├── development-standards.md # 开发标准（本文件）
└── contributing.md          # 贡献指南
```

### 2. 文档编写规范
- 使用Markdown格式
- 包含目录结构
- 使用emoji增强可读性
- 代码示例使用语法高亮
- 保持文档与代码同步更新

### 3. 注释规范
```python
def calculate_dimensions(obj, precision=2):
    """
    计算对象的尺寸信息
    
    Args:
        obj (bpy.types.Object): 要计算尺寸的对象
        precision (int): 小数位数精度，默认为2
        
    Returns:
        dict: 包含长宽高信息的字典
        
    Raises:
        ValueError: 当对象类型不支持时抛出
    """
    pass
```

---

## 测试规范

### 1. 单元测试
- 为每个模块编写单元测试
- 测试覆盖率应达到80%以上
- 使用pytest框架

### 2. 集成测试
- 测试模块间的集成
- 测试与Blender API的交互
- 验证用户界面功能

### 3. 测试文件命名
```
tests/
├── test_artRender.py
├── test_objectMeasure.py
├── test_standardView.py
└── test_integration.py
```

---

## 质量保证

### 1. 代码审查
- 所有代码变更必须经过审查
- 审查重点：功能正确性、代码质量、安全性
- 使用Pull Request流程

### 2. 持续集成
- 自动化测试
- 代码质量检查
- 自动打包部署

### 3. 性能监控
- 监控内存使用
- 检查渲染性能
- 优化用户体验

---

## 工具和资源

### 1. 开发工具
- **IDE**: Visual Studio Code / PyCharm
- **版本控制**: Git
- **代码格式化**: Black
- **代码检查**: Flake8, Pylint

### 2. 参考资源
- [Blender Python API文档](https://docs.blender.org/api/current/)
- [PEP 8 Python编码规范](https://www.python.org/dev/peps/pep-0008/)
- [语义化版本控制](https://semver.org/)

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2025-09-15 | 初始版本，建立基础开发规范 |
| 1.0.1 | 2025-09-16 | 补充完整开发标准，更新文件命名规范 |

---

[← 返回文档中心](README.md) | [模块开发规范 →](module-development.md)
