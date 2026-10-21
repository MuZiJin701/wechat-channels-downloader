# 项目约定

运行与配置见 [中文 README](README.md) / [English README](README.en.md)。

- 使用 uv 和 Python 3.11，提交 uv.lock；同步依赖使用 `uv sync --locked`。
- 启动：`uv run --locked python main.py`；打包：`uv run --locked python tools/build.py`。
- 检查：`uv run --locked mypy`；完整测试：`uv run --locked python -m unittest discover -s tests -v`。先安装 Playwright 管理的 Chromium。
- 测试通过 TUI 完整流程进行，只模拟外部服务，使用真实 Chromium 和临时目录，不读取真实登录态。
- 登录态、扫码图片和下载内容只保存在本地，不提交或上传；失败信息不得包含 Cookie、页面或带令牌的 URL。
- 平台通过结论必须附实际验证范围；CI 自动化不替代人工扫码及桌面双击验收。

## Agent skills

### Issue tracker

读取或发布任务前，读 [Issue tracker](docs/agents/issue-tracker.md)，使用本仓库 GitHub Issues。

### Triage labels

分诊或修改标签前，读[标签映射](docs/agents/triage-labels.md)，使用五个默认角色。

### Domain docs

探索领域概念或设计变更前，读[领域文档](docs/agents/domain.md)，采用 single-context 布局。
