# 微信视频号下载

[English](README.en.md)

适用于 Windows、Linux 和 macOS 的便携式 TUI：检查元宝登录态，需要时展示微信二维码，输入 `https://weixin.qq.com/sph/...` 视频号分享链接后下载视频或图文。图文保存全部图片、顺序编号和正文；视频与图片均保留下载内容，不做转码或 OCR。

## 使用便携包

解压后保持整个目录完整，不需要安装 Python 或额外浏览器。Chromium 随包提供，包体积较大。

- Windows：双击 `wechat-channels-downloader.exe`。
- macOS：双击 `微信视频号下载.command`。包按 Intel / Apple Silicon 分别构建；未进行 Apple 签名或公证。
- Ubuntu 桌面：使用 `微信视频号下载.desktop`。桌面环境可能要求先允许启动；需要系统具备 Chromium 所需的动态库。该入口的真实桌面双击行为仍需人工验收。

Linux 服务器通过 SSH 使用时，在已分配终端的会话中进入解压目录，执行 `./wechat-channels-downloader`；从另一台机器直接启动可使用 `ssh -t 主机 'cd 解压目录 && ./wechat-channels-downloader'`。程序使用当前终端，不自带终端模拟器。

启动后自动检查登录态，缺失或明确过期时显示二维码。使用微信扫码并在手机确认；二维码显示不完整时请按提示增大终端窗口。若元宝实际要求同意协议后注册/登录，TUI 会显示确认按钮。遇到额外安全验证时会停止并提示，不自动绕过。

程序会等待页面的微信登录弹窗；弹窗自动出现时直接使用，未出现时尝试登录入口，避免点击被弹窗遮挡的首页按钮。

在输入框粘贴单条分享链接，按 Enter 或点击“下载”。界面显示当前阶段及完成后的保存位置；失败后可修正链接，或使用“重新检查 / 扫码登录”。Ctrl+Q 退出。

Linux/macOS 退出时会在 Playwright 子进程清理完成后恢复启动前的终端属性。使用旧包或强制终止后若输入命令不显示，可盲输入 `stty sane` 并回车；必要时再执行 `reset`，回车无反应时尝试 Ctrl+J。强制杀进程（如 SIGKILL）无法保证执行清理。

登录态位于程序旁 `data/session.json`，内容位于 `downloads/`。macOS 若放入应用包，数据仍定位到包外侧。移动程序时可连同数据目录一起移动，但登录态仍需重新校验，不能保证跨机器或跨系统继续有效。目录不可写时明确报错，不静默改用其他位置。

登录态及临时 `data/login-qr.png` 属于敏感本地数据；扫码结束后删除临时二维码。请勿上传、分享或提交数据目录。清除 `data/session.json` 可在下次启动重新扫码。

## 源码运行

使用 uv 管理 Python 3.11 和项目独立环境：

```powershell
uv sync --locked
uv run --locked playwright install chromium
uv run --locked python main.py
```

不使用系统 Chrome 或 ChromeDriver。首次开发安装会下载 Playwright 管理的 Chromium；便携包运行时使用包内浏览器，不自动安装系统软件。

## 检查与打包

```powershell
uv run --locked mypy
uv run --locked python -m unittest discover -s tests -v
uv run --locked python main.py --smoke-test
uv run --locked python tools/build.py
```

自动化通过 TUI 用户流程运行真实无头 Chromium，只模拟元宝、微信和媒体等外部服务，并使用临时目录。离线 smoke 检查也不加载真实账户或访问外网。

Linux/macOS 的完整测试额外创建真实 PTY：启动离线 TUI、启动 Chromium、按 Ctrl+Q 退出，并检查回显、按行输入及其他终端配置与启动前一致；macOS 仅排除内核自动设置的 PENDIN 待处理输入状态位。Windows 明确跳过该 POSIX 检查。单独运行源码检查：

```sh
uv run --locked python tools/check_terminal.py "$PWD/.venv/bin/python" "$PWD/main.py"
```

该命令通过 `--terminal-smoke-test` 启动离线临时会话并自动退出，不读取真实账户。打包脚本也会对 Linux/macOS 的实际可执行文件运行同一检查。

构建脚本在当前平台生成 `dist/` 便携目录与压缩包，包含 Chromium、依赖及第三方声明。脚本会从其他工作目录执行打包产物的离线 smoke 检查，通过后才生成压缩包。不能从 Windows 交叉构建 macOS 或 Linux 包。

macOS 构建将 Chromium 的完整应用目录及符号链接复制到包内，保留浏览器原有签名，避免 PyInstaller 重新处理其框架。

若已有输出目录包含 `data/` 或 `downloads/`，构建会拒绝覆盖；先将旧程序与数据整体移到其他位置。压缩包生成后还会检查不含这两个私有目录，发现时取消归档并保留本地数据。

GitHub Actions 工作流覆盖 Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel：检查类型、完整测试、构建、包内 Chromium / TUI 启动与 PTY 退出恢复后上传压缩包。运行链接与对应代码版本见[验证记录](docs/validation.md)；Intel macOS 15 的通过不能证明 macOS 14 已验收。

当前验证范围与尚未完成事项见[验证记录](docs/validation.md)。真实扫码、线上下载和文件管理器双击体验须单独验收，不能以模拟流程通过替代。

## 项目文档

- [Spec #1](https://github.com/MuZiJin701/wechat-channels-downloader/issues/1) / [本地规格](docs/spec.md)
- [需求澄清记录](docs/requirements.md)、[词汇表](GLOSSARY.md)、[架构决策](docs/adr/)
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues) / [代理工作约定](AGENTS.md)
- [第三方声明](THIRD_PARTY_NOTICES.md)：参考解析器包含 Commons Clause 条款，不应按无限制 MIT 对待。

工程技能配置可直接编辑 `docs/agents/*.md`；切换 tracker 或重新初始化时再运行 setup-matt-pocock-skills。
