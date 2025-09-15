# 打包发布

## 📦 插件打包

### 自动打包

在项目根目录执行以下 PowerShell 命令：

```powershell
# 创建 dist 目录
New-Item -ItemType Directory -Force dist | Out-Null

# 打包插件
Compress-Archive -Path "AartFlow\*" -DestinationPath "dist\AartFlow-1.0.0.zip" -Force

# 验证打包结果
Get-ChildItem dist
```

### 手动打包

1. 选择 `AartFlow/` 目录下的所有文件
2. 创建 ZIP 压缩包
3. 重命名为 `AartFlow-版本号.zip`

### 发布流程

1. 更新版本号
2. 创建 Git 标签
3. 上传到 GitHub Releases
4. 更新文档

---

[← 返回文档中心](README.md) | [版本管理 →](versioning.md)
