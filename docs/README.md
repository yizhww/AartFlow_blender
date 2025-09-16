# AartFlow 文档中心

![Documentation Center](https://img.shields.io/badge/Documentation-Center-blue?style=flat-square&logo=book)
![Version-1.0.0](https://img.shields.io/badge/Version-1.0.0-green?style=flat-square)
![Status-Complete](https://img.shields.io/badge/Status-Complete-brightgreen?style=flat-square)

<p align="center">
<strong>欢迎来到 AartFlow Blender 插件文档中心！</strong>
</p>

## 📚 文档索引

### 👥 用户文档
- [📖 用户指南](user-guide.md) - 从安装到高级使用的完整指南

### 👨‍💻 开发文档
- [🚀 开发指南](development-guide.md) - 从环境配置到模块开发的完整指南

### 🤝 社区与支持
- [🤝 贡献与支持](contributing-and-support.md) - 参与贡献和获取帮助
- [📄 许可证](license.md) - 项目许可证信息

---

## 🏗️ 项目结构

### 完整项目结构

```
AartFlow_blender/
├── README.md                           # 项目说明文档
├── LICENSE                             # GPL-3.0 许可证
├── .gitignore                          # Git 忽略规则
├── index.json                          # 扩展库索引文件
├── texture/                            # 资源文件
│   └── 1.png                          # AartFlow Logo
├── docs/                              # 文档中心
│   ├── README.md                      # 文档索引（本文件）
│   ├── user-guide.md                  # 用户指南
│   ├── development-guide.md           # 开发指南
│   ├── contributing-and-support.md    # 贡献与支持
│   └── license.md                     # 许可证信息
├── dist/                              # 发布包目录
│   └── AartFlow-1.0.1.zip            # 发布包
└── AartFlow/                          # 插件主目录
    ├── __init__.py                    # 插件入口点
    ├── AARTFLOW_integration.py        # 核心集成器
    ├── manifest.json                  # 插件清单文件
    ├── blender_manifest.toml          # Blender 扩展清单
    ├── README.md                      # 插件详细说明
    └── scripts/                       # 业务脚本模块目录
        ├── artRenderFront.py         # 渲染前端模块
        ├── artRenderBack.py          # 渲染后端模块
        ├── objectMeasure.py           # 对象测量工具
        ├── dataPlotting.py            # 数据可视化
        ├── standardView.py            # 标准视图管理
        ├── skylightsManage.py         # 天窗管理
        ├── skpDrag.py                # SKP 拖拽功能
        └── openCmd.py                # 命令行工具
```

### 目录说明

#### 根目录文件
- **`README.md`**: 项目主要说明文档
- **`LICENSE`**: GPL-3.0 开源许可证
- **`.gitignore`**: Git 版本控制忽略规则
- **`index.json`**: Blender 扩展库索引文件

#### 文档目录 (`docs/`)
- **`README.md`**: 文档中心索引（本文件）
- **`user-guide.md`**: 完整用户指南
- **`development-guide.md`**: 开发指南
- **`contributing-and-support.md`**: 贡献与支持

#### 插件目录 (`AartFlow/`)
- **`__init__.py`**: 插件入口点，包含 `bl_info`
- **`AARTFLOW_integration.py`**: 核心集成器
- **`manifest.json`**: 插件元数据
- **`blender_manifest.toml`**: Blender 扩展系统清单
- **`scripts/`**: 业务模块脚本目录

#### 发布目录 (`dist/`)
- 存放打包后的发布文件
- 包含版本化的 ZIP 文件
- 用于扩展库分发

---

## 📦 打包发布

### 自动打包脚本

#### PowerShell 打包脚本
```powershell
# package.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# 创建 dist 目录
if (!(Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# 清理旧文件
$zipFile = "dist\AartFlow-$Version.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

# 打包插件
Compress-Archive -Path "AartFlow\*" -DestinationPath $zipFile -CompressionLevel Optimal -Force

# 计算文件信息
$fileInfo = Get-Item $zipFile
$fileSize = $fileInfo.Length
$fileHash = (Get-FileHash $zipFile -Algorithm SHA256).Hash.ToLower()

Write-Host "打包完成: $zipFile"
Write-Host "文件大小: $fileSize 字节"
Write-Host "SHA256: $fileHash"

# 更新 index.json
$indexPath = "index.json"
$indexContent = Get-Content $indexPath | ConvertFrom-Json
$indexContent.data[0].version = $Version
$indexContent.data[0].archive_size = $fileSize
$indexContent.data[0].archive_hash = "sha256:$fileHash"
$indexContent | ConvertTo-Json -Depth 10 | Set-Content $indexPath

Write-Host "已更新 index.json"
```

#### 使用方法
```powershell
.\package.ps1 -Version "1.0.1"
```

### 发布流程

#### 1. 预发布检查
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] 代码质量检查通过

#### 2. 创建发布
```bash
# 创建 Git 标签
git tag -a v1.0.1 -m "Release version 1.0.1"

# 推送到远程
git push origin main --tags
```

#### 3. 发布验证
- [ ] 扩展库索引可访问
- [ ] 下载链接有效
- [ ] 安装测试通过
- [ ] 功能验证正常

---

## 🏷️ 版本管理

### 语义化版本控制

使用 [Semantic Versioning](https://semver.org/) 标准：

- **主版本号 (MAJOR)**: 不兼容的 API 修改
- **次版本号 (MINOR)**: 向下兼容的功能性新增
- **修订号 (PATCH)**: 向下兼容的问题修正

### 版本号格式

```
主版本号.次版本号.修订号
例如：1.0.0, 1.1.0, 1.1.1
```

### 版本更新流程

#### 1. 确定版本类型
- **PATCH**: Bug 修复，向后兼容
- **MINOR**: 新功能，向后兼容
- **MAJOR**: 重大变更，可能不兼容

#### 2. 更新版本信息
```python
# AartFlow/__init__.py
bl_info = {
    "version": (1, 0, 1),  # 更新版本号
    "blender": (4, 2, 0),
    # 其他信息...
}
```

```json
// AartFlow/manifest.json
{
    "version": "1.0.1",  // 更新版本号
    "blender": "4.2.0",
    // 其他信息...
}
```

```toml
# AartFlow/blender_manifest.toml
version = "1.0.1"  # 更新版本号
blender_version_min = "4.2.0"
blender_version_max = "4.7.0"
```

#### 3. 创建版本标签
```bash
# 创建带注释的标签
git tag -a v1.0.1 -m "Release version 1.0.1

- 修复模块加载问题
- 优化性能
- 更新文档"

# 推送标签
git push origin v1.0.1
```

### 版本历史

| 版本 | 日期 | 类型 | 主要变更 |
|------|------|------|----------|
| 1.0.0 | 2025-01-15 | MAJOR | 初始版本发布 |
| 1.0.1 | 2025-01-16 | PATCH | 修复版本不匹配问题 |

---

<p align="center">
<strong>选择您需要的文档开始探索 AartFlow！</strong>
</p>
