# 贡献与支持

![Contributing](https://img.shields.io/badge/Contributing-Welcome-green?style=flat-square&logo=github)
![Support](https://img.shields.io/badge/Support-Active-brightgreen?style=flat-square&logo=help)
![Community](https://img.shields.io/badge/Community-Friendly-blue?style=flat-square&logo=users)

<p align="center">
<strong>加入 AartFlow 社区，一起构建更好的 Blender 插件生态</strong>
</p>

## 📋 目录

- [🤝 如何贡献](#-如何贡献)
- [🔧 开发流程](#-开发流程)
- [📋 Pull Request 指南](#-pull-request-指南)
- [🆘 获取帮助](#-获取帮助)
- [❓ 常见问题](#-常见问题)
- [🏷️ 标签说明](#️-标签说明)
- [📞 社区资源](#-社区资源)
- [🙏 致谢](#-致谢)

---

## 🤝 如何贡献

我们欢迎所有形式的贡献！无论是代码、文档、测试还是反馈，都对项目发展非常重要。

### 贡献方式

#### 1. 报告问题
- 在 [GitHub Issues](https://github.com/yizhww/AartFlow_blender/issues) 中报告 Bug
- 提供详细的问题描述和复现步骤
- 包含系统信息和错误日志

#### 2. 功能建议
- 在 Issues 中提出新功能建议
- 描述功能的使用场景和价值
- 讨论实现方案和技术细节

#### 3. 代码贡献
- Fork 本仓库
- 创建特性分支
- 提交 Pull Request

#### 4. 文档改进
- 完善使用说明
- 添加教程和示例
- 翻译文档内容

#### 5. 测试和反馈
- 测试新功能
- 报告使用体验
- 分享使用技巧

---

## 🔧 开发流程

### 1. 环境准备

```bash
# Fork 并克隆仓库
git clone https://github.com/your-username/AartFlow_blender.git
cd AartFlow_blender

# 创建开发分支
git checkout -b feature/your-feature-name
```

### 2. 开发规范

#### 代码风格
- 使用 Python PEP 8 代码风格
- 添加适当的注释和文档字符串
- 确保代码可读性和可维护性
- 遵循项目命名规范

#### 提交规范
```bash
# 提交格式
git commit -m "type: 简短描述"

# 类型说明
feat: 新功能
fix: Bug 修复
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

### 3. 测试要求
- 确保新功能不会破坏现有模块
- 测试新功能在 Blender 4.2+ 中的兼容性
- 添加适当的单元测试
- 验证用户界面功能正常

### 4. 文档更新
- 更新相关文档
- 添加使用示例
- 更新 API 文档
- 遵循文档规范

---

## 📋 Pull Request 指南

### 提交前检查
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 提交信息清晰明确
- [ ] 遵循命名规范

### PR 描述模板
```markdown
## 变更描述
简要描述本次变更的内容

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 其他

## 测试说明
描述如何测试这些变更

## 相关 Issue
关联的 Issue 编号（如果有）

## 截图/演示
如果有 UI 变更，请提供截图或演示
```

### 审查流程
1. 自动检查（CI/CD）
2. 代码审查
3. 功能测试
4. 文档检查
5. 合并到主分支

---

## 🆘 获取帮助

如果您在使用 AartFlow 过程中遇到问题，我们提供多种方式帮助您解决问题。

### 支持渠道

#### GitHub 讨论
- 在 [GitHub Discussions](https://github.com/yizhww/AartFlow_blender/discussions) 中提问
- 与其他用户交流使用经验
- 分享使用技巧和最佳实践

#### GitHub Issues
- 报告 Bug 和功能建议
- 查看已知问题和解决方案
- 跟踪问题修复进度

#### 邮件支持
对于重要问题，可以发送邮件到项目维护者：
- 邮箱：通过 GitHub 个人资料获取
- 主题：AartFlow 问题反馈

#### 社区资源
- [Blender 官方论坛](https://blenderartists.org/)
- [Blender Stack Exchange](https://blender.stackexchange.com/)
- [Python 官方文档](https://docs.python.org/3/)

---

## ❓ 常见问题

### 安装问题

**Q: 插件安装后没有显示面板？**
A: 
1. 确保插件已启用
2. 检查 Blender 版本是否兼容（需要 4.2+）
3. 查看控制台是否有错误信息
4. 尝试重新安装插件

**Q: 模块加载失败？**
A:
1. 检查 Python 版本（需要 3.10+）
2. 确认脚本文件权限
3. 查看模块文件是否有语法错误
4. 检查依赖项是否完整

**Q: 热重载不工作？**
A:
1. 确保在文本编辑器中运行脚本
2. 检查脚本文件路径
3. 确认模块注册函数正确
4. 查看控制台错误信息

### 使用问题

**Q: 面板功能不响应？**
A:
1. 检查 Blender 上下文是否正确
2. 确认操作对象已选择
3. 查看控制台错误信息
4. 尝试刷新模块

**Q: 渲染功能异常？**
A:
1. 检查渲染设置
2. 确认场景对象完整
3. 查看渲染日志
4. 尝试重置渲染参数

**Q: 模块集成不工作？**
A:
1. 检查模块文件路径
2. 确认模块包含必要的类定义
3. 查看模块注册函数
4. 检查模块依赖关系

### 开发问题

**Q: 如何添加新模块？**
A:
1. 创建符合规范的模块文件
2. 实现必要的类和函数
3. 添加注册和注销函数
4. 测试模块功能

**Q: 如何调试模块问题？**
A:
1. 使用 Blender 控制台查看错误
2. 添加调试输出语句
3. 检查模块导入路径
4. 验证类定义正确性

---

## 🏷️ 标签说明

### Issue 标签
- `bug` - Bug 报告
- `enhancement` - 功能增强
- `documentation` - 文档相关
- `question` - 问题咨询
- `help wanted` - 需要帮助
- `good first issue` - 适合新手的任务
- `priority: high` - 高优先级
- `priority: medium` - 中优先级
- `priority: low` - 低优先级

### PR 标签
- `ready for review` - 准备审查
- `needs testing` - 需要测试
- `breaking change` - 破坏性变更
- `documentation` - 文档更新
- `draft` - 草稿状态
- `WIP` - 进行中

---

## 📞 社区资源

### 官方资源
- **项目仓库**: [GitHub Repository](https://github.com/yizhww/AartFlow_blender)
- **问题跟踪**: [GitHub Issues](https://github.com/yizhww/AartFlow_blender/issues)
- **讨论区**: [GitHub Discussions](https://github.com/yizhww/AartFlow_blender/discussions)
- **文档中心**: [Project Documentation](./README.md)

### 技术资源
- [Blender Python API](https://docs.blender.org/api/current/)
- [Python 官方文档](https://docs.python.org/3/)
- [Git 使用指南](https://git-scm.com/docs)
- [Markdown 语法](https://www.markdownguide.org/)

### 学习资源
- [Blender 官方教程](https://www.blender.org/support/tutorials/)
- [Python 编程指南](https://docs.python.org/3/tutorial/)
- [Git 工作流指南](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

## 🙏 致谢

感谢所有为 AartFlow 项目做出贡献的开发者！

### 核心贡献者
- **yizhww** - 项目创建者和维护者
- 所有提交代码的贡献者
- 报告问题和建议的用户
- 文档翻译和维护者

### 社区贡献
- 测试和反馈用户
- 功能建议提供者
- 教程和示例创作者
- 社区问题解答者

### 特别感谢
- Blender 开发团队提供的优秀平台
- Python 社区的技术支持
- 所有开源项目的启发和帮助

---

## 相关链接

- [返回文档中心](./README.md)
- [开发指南](./development.md)
- [模块开发规范](./module-development.md)
- [许可证](./license.md)

---

<p align="center">
Made with ❤️ for the Blender Community
</p>
