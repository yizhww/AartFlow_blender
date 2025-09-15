# 开发指南

## 🔧 环境要求

- **Blender**: 4.2.0 或更高版本
- **Python**: 3.10 或更高版本
- **开发工具**: 任意文本编辑器或 IDE

## 🚀 本地开发

### 1. 克隆仓库
```bash
git clone https://github.com/yizhww/AartFlow_blender.git
cd AartFlow_blender
```

### 2. 开发环境设置
1. 在 Blender 文本编辑器中打开 `AartFlow/__init__.py`
2. 点击 "运行脚本" 进行热重载开发
3. 修改代码后重新运行即可看到效果

### 3. 调试技巧
- 使用 `print()` 语句输出调试信息
- 在控制台中查看错误和警告
- 使用 Blender 的内置调试工具

## 📝 添加新模块

### 1. 创建模块文件
在 `AartFlow/scripts/` 目录下创建新的 Python 文件

### 2. 模块开发规范
```python
import bpy

class YOUR_PANEL_NAME(bpy.types.Panel):
    bl_label = "面板名称"
    bl_idname = "VIEW3D_PT_your_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YourCategory"  # 原始分类，集成后会被代理
    
    def draw(self, context):
        layout = self.layout
        # 你的面板内容
        pass

def register():
    bpy.utils.register_class(YOUR_PANEL_NAME)

def unregister():
    bpy.utils.unregister_class(YOUR_PANEL_NAME)

if __name__ == "__main__":
    register()
```

### 3. 模块要求
- 必须包含 `bpy.types.Panel` 子类
- 必须实现 `register()` 和 `unregister()` 函数
- 建议添加适当的错误处理

## 🏗️ 项目结构

```
AartFlow_blender/
├── README.md                           # 项目说明文档
├── LICENSE                             # GPL-3.0 许可证
├── .gitignore                          # Git 忽略规则
├── texture/                            # 资源文件
│   └── 1.png                          # AartFlow Logo
├── docs/                              # 文档中心
│   ├── README.md                      # 文档索引
│   ├── installation.md                # 安装指南
│   ├── features.md                    # 功能特性
│   ├── quick-start.md                 # 快速开始
│   ├── development.md                 # 开发指南
│   ├── tutorials.md                   # 使用教程
│   ├── use-cases.md                   # 适用场景
│   ├── module-development.md          # 模块开发
│   ├── api-reference.md               # API 参考
│   ├── packaging.md                   # 打包发布
│   ├── versioning.md                  # 版本管理
│   ├── contributing.md                # 贡献指南
│   ├── support.md                     # 问题反馈
│   └── license.md                     # 许可证信息
└── AartFlow/                          # 插件主目录
    ├── __init__.py                    # 插件入口点
    ├── AARTFLOW_integration.py        # 核心集成器
    ├── manifest.json                  # 插件清单文件
    ├── README.md                      # 插件详细说明
    └── scripts/                       # 业务脚本模块目录
        ├── artrender_front.py         # 渲染前端模块
        ├── artrender_back.py          # 渲染后端模块
        ├── objectmeasure.py           # 对象测量工具
        ├── dataplotting.py            # 数据可视化
        ├── standardview.py            # 标准视图管理
        ├── skylightsmanage.py         # 天窗管理
        ├── skp_drag.py                # SKP 拖拽功能
        └── open_cmd.py                # 命令行工具
```

## 🧪 测试

### 单元测试
```python
import unittest
import bpy

class TestYourModule(unittest.TestCase):
    def setUp(self):
        # 测试前准备
        pass
    
    def test_panel_creation(self):
        # 测试面板创建
        pass
    
    def tearDown(self):
        # 测试后清理
        pass

if __name__ == '__main__':
    unittest.main()
```

### 集成测试
1. 在 Blender 中加载插件
2. 测试各个模块的功能
3. 验证模块间的交互

## 📦 打包发布

### 自动打包
```powershell
# 创建 dist 目录
New-Item -ItemType Directory -Force dist | Out-Null

# 打包插件
Compress-Archive -Path "AartFlow\*" -DestinationPath "dist\AartFlow-1.0.0.zip" -Force

# 验证打包结果
Get-ChildItem dist
```

### 版本管理
1. 更新 `__init__.py` 中的版本号
2. 更新 `manifest.json` 中的版本信息
3. 创建 Git 标签
4. 发布到 GitHub Releases

---

[← 返回文档中心](README.md) | [模块开发 →](module-development.md)
