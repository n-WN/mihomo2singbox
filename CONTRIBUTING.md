# 贡献指南

感谢您对 mihomo2singbox 项目的关注！我们欢迎各种形式的贡献。

## 📋 贡献方式

### 🐛 报告 Bug
- 使用 [Issues](https://github.com/n-WN/mihomo2singbox/issues) 报告 bug
- 提供详细的错误信息和复现步骤
- 附上相关的配置文件（请移除敏感信息）

### 💡 功能建议
- 在 Issues 中提出新功能建议
- 详细描述功能需求和使用场景
- 欢迎讨论实现方案

### 🔧 代码贡献
1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 🛠️ 开发环境设置

### 环境要求
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (推荐)

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/n-WN/mihomo2singbox.git
cd mihomo2singbox

# 2. 安装 uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 安装依赖
uv sync --dev

# 4. 运行测试
uv run mihomo2singbox --help
```

### 开发工具

```bash
# 代码格式化
uv run ruff check --fix .
uv run ruff format .

# 类型检查
uv run mypy mihomo2singbox/

# 运行测试
uv run pytest tests/
```

## 📝 代码规范

### Python 代码风格
- 遵循 PEP 8 规范
- 使用 `ruff` 进行代码检查和格式化
- 使用类型注解 (Python 3.11+ 语法)
- 函数和类需要添加 docstring

### 提交信息格式

```
type(scope): description

body (可选)

footer (可选)
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**范围 (scope):**
- `core`: 核心转换逻辑
- `tun`: TUN 功能
- `dns`: DNS 配置
- `rules`: 路由规则
- `cli`: 命令行界面
- `docs`: 文档

**示例:**
```
feat(tun): add advanced tun configuration support
fix(dns): resolve dns server format compatibility issue
docs(readme): update installation instructions
```

## 🧪 测试

### 测试覆盖
- 为新功能编写单元测试
- 确保现有测试通过
- 测试覆盖率应保持在合理水平

### 测试命令
```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_converter.py

# 查看测试覆盖率
uv run pytest --cov=mihomo2singbox
```

### 手动测试
```bash
# 基本转换测试
uv run mihomo2singbox input.yaml -o test_output.json

# TUN 模式测试
uv run mihomo2singbox input.yaml --tun -o test_tun.json
uv run mihomo2singbox input.yaml --tun-simple -o test_simple_tun.json

# 验证配置
sing-box check -c test_output.json
```

## 📚 文档

### 文档更新
- 更新 README.md 中的功能描述
- 添加新功能的使用示例
- 更新 API 文档

### 文档风格
- 使用清晰的标题结构
- 提供代码示例
- 包含必要的警告和注意事项
- 支持中英文文档

## 🎯 协议支持开发

### 当前状态
- ✅ **Shadowsocks**: 完整测试和支持
- ⚠️ **其他协议**: 代码已实现，需要测试

### 新协议支持
1. 在 `MihomoToSingboxConverter` 类中添加转换方法
2. 更新协议映射表
3. 编写测试用例
4. 更新文档

### 测试新协议
```python
# 示例：添加新协议支持
def _convert_new_protocol_proxy(self, proxy_config: Dict[str, Any]) -> Dict[str, Any]:
    """转换新协议配置"""
    return {
        "tag": proxy_config["name"],
        "type": "new_protocol",
        # ... 其他配置
    }
```

## 🔍 问题排查

### 常见问题
1. **类型检查错误**: 确保使用正确的类型注解
2. **测试失败**: 检查测试环境和依赖
3. **格式检查失败**: 运行 `ruff format .` 修复格式问题

### 调试技巧
```bash
# 启用详细日志
uv run mihomo2singbox input.yaml --log-level debug

# 查看生成的配置
jq '.' output.json

# 验证配置语法
sing-box check -c output.json
```

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/n-WN/mihomo2singbox/issues)
- **Discussions**: [GitHub Discussions](https://github.com/n-WN/mihomo2singbox/discussions)
- **Email**: 通过 GitHub Issues 联系维护者

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT 许可证](LICENSE) 下分发。

---

感谢您的贡献！🎉
