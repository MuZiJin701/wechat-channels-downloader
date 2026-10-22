# 微信视频号下载

[English](README.en.md)

适用于 Windows、Linux 和 macOS 的微信视频号下载工具：需要时用微信扫码，再粘贴单条 `https://weixin.qq.com/sph/...` 视频号分享链接即可归档动态。保存接口提供的全部视频版本、图文图片、封面、作者头像、认证图标与背景音乐，并生成离线 HTML 和两步解析的完整 JSON；媒体不转码，不做 OCR 或笔记生成。

## 使用便携包

解压后保持整个目录完整，不需要安装 Python 或额外浏览器。Chromium 随包提供，包体积较大。

Windows 解压路径请避开分号 `;`：当前打包运行时在这类路径下无法加载必要 DLL。中文、空格及其他常见路径字符另有离线产物检查。

- Windows：双击 `wechat-channels-downloader.exe`，优先打开独立 Windows Terminal 窗口，依次选择 PowerShell 7（`pwsh`）、Windows PowerShell、cmd；Terminal 不可用或启动失败时回退系统控制台。Windows 11 24H2（26100）及以上通过启动清单避免先自动创建控制台；更早 Windows 11 仍可运行，但可能短暂显示初始控制台。不要求管理员权限，不自动安装软件或改变系统默认设置。
- macOS：双击带图标的 `wechat-channels-downloader.app`，它会打开 Terminal 运行同一 TUI。保留整个解压目录，不能只移动启动器；首次可能需要允许打开或控制 Terminal。包按 Intel / Apple Silicon 分别构建；未进行 Apple 签名或公证。
- Ubuntu 桌面：使用 `wechat-channels-downloader.desktop`。桌面环境可能要求先允许启动；需要系统具备 Chromium 所需的动态库。图标采用绝对路径，首次启动或移动目录后的下一次启动会刷新自身入口的图标引用；文件管理器可能需要刷新。该入口的真实桌面双击行为仍需人工验收。

在已有终端运行 Windows 的 `./wechat-channels-downloader.exe`，或 Linux/macOS 的 `./wechat-channels-downloader`，会直接复用当前终端，shell 等待程序退出。Windows 双击和终端运行使用同一个应用 EXE；仍须保留整个解压目录，包括 `_internal/` 中的 Chromium 和依赖。

界面使用鼠尾草绿浅色、森林绿深色两套主题，品牌区展示播放与保存标志和静态渐变，成功、警告和错误另有语义颜色及文字。顶部“外观”选择器支持鼠标及键盘，提供“跟随系统 / 浅色 / 深色”；首次默认跟随系统，选择立即生效并保存，切换不影响扫码、下载、输入及结果。

自动模式约每两秒检查程序运行所在机器的系统明暗；Windows 读取应用主题偏好，macOS 读取系统外观，Ubuntu/GNOME 读取桌面颜色偏好。没有桌面、缺少查询工具或无法识别时使用浅色，可手动切换；SSH 不读取客户端电脑的系统主题。手动选择后保持指定主题，重新选“跟随系统”恢复自动变化。不修改全局终端配置。

窗口放大时内容区随之展开，缩小时减少留白、重排按钮与外观选择器，高度不足时滚动；二维码保持静态黑白，过小窗口会提示放大。字体大小保持终端原设置。真彩色终端可展示渐变，其他终端可能出现色阶；已有 `NO_COLOR` 设置仍会被尊重。

底部的 `GitHub · MuZiJin701/wechat-channels-downloader ↗` 为文本链接，可点击，或用 Tab / Shift+Tab 聚焦后按 Enter 打开；没有独立 GitHub 按钮或专用快捷键。

Linux 服务器通过 SSH 使用时，在已分配终端的会话中进入解压目录，执行 `./wechat-channels-downloader`；从另一台机器直接启动可使用 `ssh -t 主机 'cd 解压目录 && ./wechat-channels-downloader'`。程序使用当前终端，不自带终端模拟器。

启动显示“环境检测中”，有效登录态直接复用，输入框在就绪后出现；缺失或明确过期时居中显示微信二维码，扫码成功后再显示输入框。网络异常提示重试，不清除旧登录态。二维码显示不完整时请按提示增大终端窗口。若实际服务要求同意账号协议后注册/登录，界面会准确说明服务对象并等待明确确认。遇到额外安全验证时停止并提示，不自动绕过。

程序会等待页面的微信登录弹窗；弹窗自动出现时直接使用，未出现时尝试登录入口，避免点击被弹窗遮挡的首页按钮。

在输入框粘贴单条分享链接，按 Enter 或点击“下载”。只保留最近一次结果，显示阶段、结果及保存位置，失败详情可展开；全部完成后清空并聚焦输入框，失败或部分完成保留链接。下载中禁用重复提交。按钮标注快捷键，均不使用 F 区按键：

| 操作 | 快捷键 |
| --- | --- |
| 下载 | 输入框内 Enter |
| 重试当前失败操作 | Ctrl+R |
| 打开下载目录 | Ctrl+O |
| 全选输入内容 | 输入框内 Ctrl+A |
| 退出 | Ctrl+Q |
| 切换操作 / 确认按钮 | Tab、Shift+Tab / Enter、空格 |

输入区使用普通单行文本编辑，占位提示“粘贴视频号分享链接”不含示例网址。点击定位光标、拖动选择，支持 Home / End、方向键与 Shift 选区、退格、删除及复制剪切粘贴；程序不把输入区做成超链接。聚焦且输入位置可见时，使用终端原生细竖线闪烁光标，失焦或被遮挡时隐藏，正常退出时恢复终端配置的默认光标形状。具体显示与闪烁仍受终端支持影响。系统剪贴板粘贴及宿主对实际网址的链接识别仍需在目标 Windows Terminal 等终端中实际验收。

Windows 运行期间还会临时匹配光标颜色，避免浅色终端中手动选择深色应用主题后光标难以辨认；正常退出恢复宿主默认光标颜色，不写入终端设置文件。

每次归档在 `downloads/` 新建 `作者_正文摘要` 目录，允许中文；缺作者时省略，缺正文时回退分享标识。非法字符清理，长名称截短，原正文完整保留。媒体沿用此前缀并附用途、顺序或编码；重名时加序号，不覆盖旧下载。目录中包含：

- 接口提供的媒体文件：所有不同视频版本、按序图片和其他附件；完全相同的地址只下载一次，扩展名根据实际媒体类型保存。
- `index.html`：双击查看原正文、作者、UTC 时间、查询时的互动展示数量、其他可取得的信息与本地媒体。不依赖远端媒体地址；浏览器不支持某个编码时可使用页面中的文件链接交给本地播放器。
- `parse.json`、`feed.json`：分别保存完整解析响应和动态响应，离线页显示“解析原始数据”和“动态原始数据”；仅在已取得对应响应时生成。未知字段原样保留，不额外生成 TXT。旧归档及其中的旧文件名不修改。

资源齐全时显示“完成”；某项失败后继续处理其他资源，保留成果并显示“部分完成”，HTML 列出缺失项。全部媒体失败时仍保留已取得的信息并显示“失败”；正常退出中断下载时，保留完整文件和可保存的信息，HTML 标记“已中断”，未完成文件不作为有效媒体保留。再次下载会生成新目录。存储不可写时明确报错；强制杀进程或断电无法保证完成最后的记录。

归档范围限于接口本次返回的内容；没有返回的可选资源自然省略，不承诺评论正文、上传前原片、独立字幕或完整账号历史。不同视频版本会额外占用磁盘空间。

Linux/macOS 退出时会在 Playwright 子进程清理完成后恢复启动前的终端属性。使用旧包或强制终止后若输入命令不显示，可盲输入 `stty sane` 并回车；必要时再执行 `reset`，回车无反应时尝试 Ctrl+J。强制杀进程（如 SIGKILL）无法保证执行清理。

登录态位于程序旁 `data/session.json`，主题模式单独保存在 `data/appearance.json`，内容位于 `downloads/`。macOS 的这些目录均位于 `.app` 启动器外侧。删除 `appearance.json` 可恢复默认跟随系统，不影响登录态；偏好损坏时也恢复自动模式，保存失败会提示且保留本次主题。移动程序时可连同数据目录一起移动，但登录态仍需重新校验，不能保证跨机器或跨系统继续有效。目录不可写时明确报错，不静默改用其他位置。

登录态及临时 `data/login-qr.png` 属于敏感本地数据；扫码结束后删除临时二维码。请勿上传、分享或提交数据目录。清除 `data/session.json` 可在下次启动重新扫码。

归档 JSON 可能包含带访问参数和有效期的媒体地址，也应只在本地保留，不进入公共日志、仓库或分发包。登录凭据不随媒体请求发送到其他域名。

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

构建脚本在当前平台生成 `dist/` 便携目录与压缩包，包含 Chromium、依赖及第三方声明。顶层仅保留双 README 使用文档，第三方声明和许可位于 `_internal/`，开发文档不随包分发；包内 README 的开发文档链接转向公开仓库。脚本会从其他工作目录执行打包产物的离线 smoke 检查，通过后才生成压缩包。不能从 Windows 交叉构建 macOS 或 Linux 包。

macOS 构建将 Chromium 的完整应用目录及符号链接复制到包内，保留浏览器原有签名，避免 PyInstaller 重新处理其框架。

Logo 原图和各平台图标位于 `downloader/assets/`。修改程序图标后运行 `uv run --locked python tools/draw_logo.py`，使用已有 Pillow 同步生成 PNG、Windows ICO 与 macOS ICNS。主界面使用专门按终端格子绘制的纯色、高对比播放与下载标志，避免缩小图片的条纹；按钮和外观选择框采用对称细线边框，保留焦点、悬停及禁用反馈。打包保留高清图标资源，macOS 构建另检查启动脚本语法并编译 AppleScript；实际 Finder/Terminal 交互需人工验收。

若已有输出目录包含 `data/` 或 `downloads/`，构建会拒绝覆盖；先将旧程序与数据整体移到其他位置。压缩包生成后还会检查不含这两个私有目录，发现时取消归档并保留本地数据。

GitHub Actions 工作流覆盖 Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel：检查类型、完整测试、构建、包内 Chromium / TUI 启动与 PTY 退出恢复后上传压缩包。运行链接与对应代码版本见[验证记录](docs/validation.md)；Intel macOS 15 的通过不能证明 macOS 14 已验收。

当前验证范围与尚未完成事项见[验证记录](docs/validation.md)。真实扫码、线上下载和文件管理器双击体验须单独验收，不能以模拟流程通过替代。

## 项目文档

- 完整归档与终端体验：[Spec #2](https://github.com/MuZiJin701/wechat-channels-downloader/issues/2) / [本地规格](docs/spec.md)；[初版 Spec #1](https://github.com/MuZiJin701/wechat-channels-downloader/issues/1)
- [需求澄清记录](docs/requirements.md)、[词汇表](GLOSSARY.md)、[架构决策](docs/adr/)
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues) / [代理工作约定](AGENTS.md)
- [第三方声明](THIRD_PARTY_NOTICES.md)：参考解析器包含 Commons Clause 条款，不应按无限制 MIT 对待。

工程技能配置可直接编辑 `docs/agents/*.md`；切换 tracker 或重新初始化时再运行 setup-matt-pocock-skills。
