# AartFlow 插件打包脚本
# PowerShell 脚本用于自动打包 Blender 插件

param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "dist"
)

Write-Host "🚀 开始打包 AartFlow 插件 v$Version" -ForegroundColor Green

# 检查必要目录
if (-not (Test-Path "AartFlow")) {
    Write-Host "❌ 错误: 找不到 AartFlow 目录" -ForegroundColor Red
    exit 1
}

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "📁 创建输出目录: $OutputDir" -ForegroundColor Yellow
}

# 设置插件名称
$PluginName = "AartFlow-$Version"

# 清理旧的打包文件
$OldZip = "$OutputDir\$PluginName.zip"
if (Test-Path $OldZip) {
    Remove-Item $OldZip -Force
    Write-Host "🗑️  删除旧的打包文件: $OldZip" -ForegroundColor Yellow
}

# 创建临时目录
$TempDir = "temp_$PluginName"
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    # 复制插件文件到临时目录
    Write-Host "📋 复制插件文件..." -ForegroundColor Cyan
    Copy-Item -Path "AartFlow\*" -Destination "$TempDir\" -Recurse -Force
    
    # 验证必要文件
    $RequiredFiles = @(
        "__init__.py",
        "AARTFLOW_integration.py",
        "manifest.json"
    )
    
    foreach ($File in $RequiredFiles) {
        if (-not (Test-Path "$TempDir\$File")) {
            Write-Host "❌ 错误: 缺少必要文件 $File" -ForegroundColor Red
            exit 1
        }
    }
    
    # 验证脚本目录
    if (-not (Test-Path "$TempDir\scripts")) {
        Write-Host "❌ 错误: 缺少 scripts 目录" -ForegroundColor Red
        exit 1
    }
    
    # 统计文件数量
    $FileCount = (Get-ChildItem -Path $TempDir -Recurse -File).Count
    Write-Host "📊 打包文件数量: $FileCount" -ForegroundColor Cyan
    
    # 创建 ZIP 文件
    Write-Host "📦 创建 ZIP 文件..." -ForegroundColor Cyan
    Compress-Archive -Path "$TempDir\*" -DestinationPath $OldZip -Force
    
    # 验证打包结果
    if (Test-Path $OldZip) {
        $ZipSize = (Get-Item $OldZip).Length
        $ZipSizeMB = [math]::Round($ZipSize / 1MB, 2)
        Write-Host "✅ 打包成功!" -ForegroundColor Green
        Write-Host "📦 文件: $OldZip" -ForegroundColor White
        Write-Host "📏 大小: $ZipSizeMB MB" -ForegroundColor White
    } else {
        Write-Host "❌ 打包失败!" -ForegroundColor Red
        exit 1
    }
    
} finally {
    # 清理临时目录
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
        Write-Host "🧹 清理临时文件" -ForegroundColor Yellow
    }
}

Write-Host "🎉 打包完成!" -ForegroundColor Green
