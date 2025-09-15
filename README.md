# AartFlow Blender Add-on

AartFlow 是一个模块化的 Blender 插件（Blender 4.2+），通过 AARTFLOW_integration.py 动态发现并集成 AartFlow/ 下的独立脚本模块。

## 目录结构
`
AartFlow/
 __init__.py               # 插件入口（含 bl_info）
 AARTFLOW_integration.py   # 集成器：发现并加载 scripts 模块
 manifest.json             # 扩展清单（用于扩展分发场景）
 README.md                 # 插件说明
 scripts/                  # 独立脚本模块（保持原脚本独立性）
     artrender_front.py
     artrender_back.py
     objectmeasure.py
     dataplotting.py
     standardview.py
     skylightsmanage.py
     skp_drag.py
     open_cmd.py
`

## 安装（两种方式任选其一）
- Blender 内安装 ZIP：编辑 > 偏好设置 > 插件 > 安装，选择打包后的 ZIP
- 手动拷贝：将 AartFlow/ 目录放入 Blender 的 scripts/addons/ 目录

## 开发与调试
- 在 Blender 文本编辑器中直接运行 AartFlow/__init__.py 或 AartFlow/AARTFLOW_integration.py 可快速热重载
- 所有业务脚本保持独立，集成器仅负责发现 + 代理面板，不改动原面板逻辑

## 打包发布
在项目根目录执行：
`powershell
New-Item -ItemType Directory -Force dist | Out-Null
Compress-Archive -Path "AartFlow\*" -DestinationPath "dist\AartFlow-1.0.0.zip" -Force
`

## 许可证
本项目采用 GPL-3.0 许可。详见 LICENSE 文件。
