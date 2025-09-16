# GitHub Pages 设置指南

## 📋 概述

本指南将帮助您设置GitHub Pages来托管AartFlow Blender扩展库，使Blender能够正确访问index.json文件。

## 🔧 设置步骤

### 1. 启用GitHub Pages

1. 访问您的GitHub仓库：`https://github.com/yizhww/AartFlow_blender`
2. 点击 **Settings** 标签页
3. 在左侧菜单中找到 **Pages** 选项
4. 在 **Source** 部分选择 **GitHub Actions**
5. 保存设置

### 2. 验证部署状态

1. 返回仓库主页面
2. 点击 **Actions** 标签页
3. 查看 **Deploy to GitHub Pages** 工作流
4. 等待部署完成（通常需要几分钟）

### 3. 访问扩展库

部署完成后，您的扩展库将在以下URL可用：
- **主页**: `https://yizhww.github.io/AartFlow_blender/`
- **索引文件**: `https://yizhww.github.io/AartFlow_blender/index.json`

## 🚀 自动部署

每次推送到 `main` 分支时，GitHub Actions会自动：
1. 检出最新代码
2. 部署 `docs_public` 目录到GitHub Pages
3. 使扩展库文件立即可用

## 📁 目录结构

```
docs_public/
├── index.html          # 扩展库主页
└── index.json          # Blender扩展库索引文件
```

## 🔍 故障排除

### 问题：404 Not Found
**解决方案**：
1. 确保GitHub Pages已启用
2. 检查GitHub Actions部署状态
3. 等待几分钟让DNS传播完成

### 问题：工作流失败
**解决方案**：
1. 检查 `.github/workflows/deploy-pages.yml` 文件
2. 确保仓库权限正确设置
3. 重新运行失败的Actions

### 问题：Blender无法访问
**解决方案**：
1. 验证URL是否正确：`https://yizhww.github.io/AartFlow_blender/index.json`
2. 检查index.json文件格式是否正确
3. 确保文件大小和哈希值匹配

## 📝 手动测试

您可以在浏览器中访问以下URL来测试：

```bash
# 测试主页
curl https://yizhww.github.io/AartFlow_blender/

# 测试索引文件
curl https://yizhww.github.io/AartFlow_blender/index.json
```

## 🔄 更新流程

当您需要更新扩展库时：

1. 修改 `index.json` 文件（在根目录）
2. 运行打包脚本：`.\package.ps1 -Version "1.0.2"`
3. 复制新的 `index.json` 到 `docs_public/` 目录
4. 提交并推送更改：
   ```bash
   git add .
   git commit -m "update: 更新扩展库到版本 1.0.2"
   git push origin main
   ```
5. GitHub Actions会自动部署更新

## 📚 相关文档

- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Blender 扩展库规范](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)

---

[← 返回文档中心](README.md) | [开发规范 →](development-standards.md)
