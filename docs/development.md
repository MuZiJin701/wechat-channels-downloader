# 开发与排查指南

[文档导航](README.md) · [普通用户使用指南](../README.md) · [English user guide](../README.en.md)

本文面向源码使用者和维护者。产品行为以[当前规格](spec.md)为准，执行结果与平台边界见[验证记录](validation.md)。

## 源码运行

使用 uv 和 Python 3.11，按锁文件恢复项目依赖：

```sh
uv sync --locked
uv run --locked playwright install chromium
uv run --locked python main.py
```

项目使用 Playwright 管理的 Chromium，不使用系统 Chrome 或 ChromeDriver。Linux 缺少浏览器运行库时，可按 Playwright 的提示安装系统依赖；CI 使用 `uv run --locked playwright install --with-deps --no-shell chromium`。这一步可能需要系统权限，普通便携包运行不会自动安装系统软件。

已有终端中运行便携程序：Windows 为 `./wechat-channels-downloader.exe`，Linux/macOS 为 `./wechat-channels-downloader`。Linux 服务器需要带终端的 SSH 会话，例如 `ssh -t 主机 'cd 解压目录 && ./wechat-channels-downloader'`。

## 检查

```sh
uv run --locked mypy
uv run --locked python -m unittest discover -s tests -v
uv run --locked python main.py --smoke-test
```

测试从 TUI 用户流程运行真实 Chromium，只模拟元宝、微信及媒体等外部服务，并使用临时目录。`--smoke-test` 也只使用离线临时会话，不读取真实登录态。

Linux/macOS 的完整测试还检查真实 PTY 的退出恢复。单独检查源码入口：

```sh
uv run --locked python tools/check_terminal.py "$PWD/.venv/bin/python" "$PWD/main.py"
```

该检查通过 `--terminal-smoke-test` 运行真实终端驱动、主题切换、输入和正常退出；macOS 只排除内核管理的 PENDIN 状态位。Windows 明确跳过 POSIX PTY 检查，需分别记录实际 Windows 控制台/Terminal 验证。

扫码、真实线上下载、视频解码、系统剪贴板和文件管理器双击需要目标环境单独验收。模拟流程、截图或较新系统的检查不能代替这些结果。

## 打包

```sh
uv run --locked python tools/build.py
```

构建必须在目标系统上运行，不能从 Windows 交叉生成 Linux/macOS 包。脚本生成 `dist/wechat-channels-downloader/` 和对应压缩包，携带 Chromium、应用依赖及内部许可。

输出目录包含 `data/` 或 `downloads/` 时会拒绝覆盖。先把旧程序与数据整体备份到其他位置；明确不再需要这些数据时再清理旧输出。构建后会从其他工作目录执行实际产物的离线检查，Windows 另检查单 EXE 的子系统、嵌入清单与特殊路径；Linux/macOS 另检查实际产物的 PTY 恢复。

包顶层只分发 `README.md` 和 `README.en.md` 两份使用文档，其他文档链接转向公开仓库。README 宣传图直接引用仓库的 `docs/images/` 原图，避免向便携包复制整套开发文档；离线查看 README 时宣传图可能无法加载，不影响程序使用。

macOS 构建保留 Chromium 应用目录、符号链接与原有签名；`.app` 只是终端启动器，登录态和下载位于包外侧。Linux `.desktop` 使用绝对图标路径，首次运行及移动后会刷新自身引用。入口实现与 Windows 单 EXE 的兼容取舍见[规格](spec.md)和[研究记录](windows-single-exe-research.md)。

## 界面与图标

主题默认跟随运行机器的系统明暗，也可手动选择浅色或深色；仅改变应用界面，不修改全局终端配置。`data/appearance.json` 单独保存模式，无法识别系统偏好时回退浅色；SSH 不读取客户端电脑的系统主题。

图标源文件在 `downloader/assets/`。修改图标后，用已有 Pillow 同步生成各平台资源：

```sh
uv run --locked python tools/draw_logo.py
```

TUI 探测到 Sixel 或 kitty 图片能力及像素格尺寸后才绘制原图，按可见单元格处理裁剪与遮挡；无法确认能力、`NO_COLOR`、复用器或矮窗口采用文字版。像素格尺寸在启动时测量，更改字号或 DPI 后应重启。Textual 字符截图不包含真实像素图片，视觉检查应使用实际宿主窗口。

输入框使用终端原生细竖线光标；Windows 临时匹配光标颜色，正常退出恢复默认形状与颜色。字体由终端设置控制，正常文本编辑行为与快捷键见[规格](spec.md)。

## 运行问题排查

| 现象 | 排查方式 |
| --- | --- |
| Windows 报 DLL 加载失败 | 先确认已完整解压，路径不含分号 `;`，且 `_internal/` 未缺失 |
| 二维码不完整 | 放大终端窗口，按状态区提示操作 |
| 网络失败但此前已登录 | 优先重试，不删除旧登录态；明确过期时程序会重新扫码 |
| 想重新扫码或恢复默认外观 | 关闭程序后，仅删除 `data/session.json` 或 `data/appearance.json` 中对应的文件 |
| Linux/macOS 强制结束后输入不显示 | 在同一终端输入 `stty sane` 并回车；必要时用 `reset`，回车无效时尝试 Ctrl+J |
| 文件保存失败 | 检查程序所在目录是否可写、磁盘空间是否足够；程序不会静默改存其他位置 |
| HTML 不能播放某种视频 | 使用页面文件链接或本地播放器；不将文件存在等同于浏览器可解码 |

只保留最近一次结果；失败详情可展开。重复下载新建目录，部分失败或正常中断保留成功文件，强制杀进程或断电不保证最后记录完整。

## 数据与隐私

`data/session.json` 保存元宝登录态，`data/appearance.json` 保存主题模式，下载保存在 `downloads/`；位置不随当前工作目录改变。扫码结束后清除临时 `data/login-qr.png`。

登录态、二维码及归档原始 JSON 可能包含敏感信息或时效访问参数，不进入公共日志、Git 或发布包。报告问题时只提供脱敏错误及复现条件。解析能力的证据与限制见[能力核对](parse-capabilities.md)。

## CI 与发布

[Verify and package](https://github.com/MuZiJin701/wechat-channels-downloader/actions/workflows/verify.yml) 在 Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel 上执行类型检查、完整测试、构建及离线产物检查，并上传压缩包。Windows 便携包在 Windows 本机生成；Intel macOS 15 的通过不能证明最低目标 macOS 14 已实机验收。

测试包在 workflow 运行的 Artifacts 区域下载，需要登录 GitHub；正式用户包统一放在 [Releases](https://github.com/MuZiJin701/wechat-channels-downloader/releases)。发布时版本应与 `pyproject.toml` 一致，标签指向实际交付源码；核对各系统的包名、双 README、内部许可、无私有 data/downloads 以及实际验证范围后上传。未通过的系统不发布为已验证资产。

更新用户流程时同步两份 README；开发细节维护在本文件，产品约定维护在规格，历史访谈和检查结果分别保留在需求与验证记录中。稳定代理规则见 [AGENTS.md](../AGENTS.md)。
