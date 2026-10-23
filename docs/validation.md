# 验证记录

验证对象：2026-10-23 宣传海报、图片 Logo 与文字回退、此前启动与界面改版、Spec #2 的动态完整归档与终端体验，以及下方保留的历史记录。自动化只使用临时登录态与模拟外部服务；本文件不把模拟检查写成真实业务验收。

## 宣传海报（2026-10-23，仅 Windows 本机）

制作[皇家紫宣传海报](images/宣传海报.png)，交付 [Python 绘制脚本](../tools/draw_poster.py)和[生成说明](development.md#宣传海报)。使用已有 Pillow 13.0.0、微软雅黑、本地图标和两张原始截图，不新增项目依赖；生成过程离线，不读取登录态或下载内容。

上一版曾按用户要求强化低门槛卖点，使用「微信扫码登录，粘贴链接，一键下载。」及技术步骤说明；历史依据与边界见[需求记录](requirements.md#低门槛下载卖点强化)。

用户随后重新澄清并确认面向普通用户的文案，当前海报改为「独立运行，无需打开电脑微信。」「扫码登录、粘贴下载，一处完成。」，保留视频图文与正文、作者、发布时间的功能说明，移除技术术语及「离线翻看」候选，不写竞品名称或未证实的首创判断。重新生成后检查文字边界与视觉布局，确认成图仅辅助文案区域变化，截图、背景和二维码像素与改动前一致；生成自检、13 个源文件的类型检查及 Git 差异检查通过。原二维码载荷记录继续适用，未重复访问在线识别服务；本轮未改应用，未重跑完整应用测试。确认及对比边界见[需求记录](requirements.md#与-wx_channels_download-对比后的宣传需求重新澄清2026-10-23已确认并授权实现)。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| 生成与自检 | 通过 | Windows、Python 3.11、锁定依赖；1800×2400 RGB PNG，检查主要文字边界、素材裁剪范围、二维码四模块留白及最终像素保真 |
| 视觉检查 | 通过 | 查看最终 PNG，核对皇家紫光弧、中文文案、深浅截图叠放、GitHub 地址和二维码；截图保持原色与比例，原始两张截图与 Git HEAD 一致 |
| 可重复生成 | 通过 | 从其他工作目录调用绝对脚本路径，默认字体重绘后 SHA-256 一致；无随机星空漂移 |
| 字体参数 | 通过 | 显式传入现有中文字体可生成；缺失字体时返回退出码 2 和明确提示；Linux/macOS 自定义字体未实测 |
| 静态类型 | 通过 | `uv run --locked mypy`，13 个源文件 |
| 二维码载荷 | 通过（限定范围） | 从 1800 像素宽成图及重采样到 900 像素宽的图片中读取模块，核对格式位、解掩码、反交织并读回字节载荷，均为 `https://github.com/MuZiJin701/wechat-channels-downloader`；复用本机编码器的格式表，不等同于通用扫码器的自动定位与纠错验收 |
| 在线二维码识别 | 失败 | 尝试 [QR Server 识别 API](https://goqr.me/api/doc/read-qr-code/) 返回 HTTP 403，随后采用上述本地载荷核验；仅发送包含公开仓库地址的二维码裁片，未发送截图或个人数据；生成脚本不依赖该服务 |
| 手机扫码及社交媒体压缩 | 未执行 | 尚未使用手机扫描或在实际社交平台上传；自动核验不能替代实际分享后的扫码效果 |

本轮仅新增海报及绘制工具、更新相关文档，未修改应用与原图，未重跑完整 TUI／Chromium 回归、打包或其他平台验收；未提交、推送或发布海报。用户明确确认的制作方案见[需求记录](requirements.md#项目宣传海报需求澄清2026-10-23已确认并授权制作)。

## SSH 颜色降级排查（2026-10-23）

用户报告 Windows Terminal 经 SSH 运行 Linux 发布包时，浅色背景偏灰粉、渐变分块，深色观感正常。只读检查服务器上正在运行的应用进程，确认 `TERM=xterm-256color`，未设置 `COLORTERM`、`TEXTUAL_COLOR_SYSTEM` 或 `NO_COLOR`；未读取登录态或下载内容，也未中断现有程序。

使用锁定依赖 Textual 8.2.8、Rich 15.0.0 核对实际自动检测代码，并在本地模拟 Rich 的 Linux 检测分支：上述环境检测为 `256`，浅色 `#88a28c` 输出 `48;5;246`，深色 `#283e2c` 输出 `48;5;22`。仅加入 `COLORTERM=truecolor` 后检测为 `truecolor`，分别输出精确 RGB `48;2;136;162;140` 和 `48;2;40;62;44`。这解释了浅色失真而深色仍偏绿的现象。

中英文 README 与开发指南补充本次启动的真彩色声明方法，限定于实际支持真彩色的终端链路。尚未重启用户的真实应用进行修正后的实屏验收；编码核对不等同于该项通过。此轮只更新文档，不改变应用、服务器配置或既有 v0.1.0 分发包。

## 用户文档与 v0.1.0 发布（2026-10-23）

双 README 改为面向普通用户的下载、扫码、保存和常见问题指南，使用用户提供的两张 `docs/images/` 原始截图，按阅读环境明暗显示。源码运行与维护内容集中到[开发指南](development.md)，其余入口见[文档导航](README.md)。同步修正规格、能力核对及研究文档中容易被误认为现状的历史描述；词汇表、既有 ADR、第三方许可与分诊／Issue 规则经核对无需变更。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| 文档链接与便携包链接 | 通过 | 检查 16 份 Markdown 的本地引用，执行现有构建脚本的 README 链接转换；包内文档跳转及原图地址可解析，开发文档不混入便携包 |
| 中英文 README 预览 | 通过 | 真实 Chromium 渲染中英文、浅深主题与 1100／390 像素宽度共 8 组预览；检查图片加载、明暗对应和页面不发生水平溢出 |
| 用户截图 | 通过 | 两张 PNG 完整可读，无可见二维码或登录凭据；文件 SHA-256 与整理前一致，原图未编辑 |
| Windows Release 候选 | 通过 | 基于此前已验证的干净 ZIP 更新双 README；逐个核对嵌入的项目模块及入口与当前源码执行内容一致，归档不含 data/downloads；解压到临时目录后，从其他工作目录执行实际 EXE 离线 smoke，返回 SMOKE_OK |

本轮未修改应用或构建代码，没有重复运行 Windows 完整业务回归；此前 Windows 的 52 项结果见下节。用户明确授权本轮提交、推送及创建 Release，公开发布仅包含项目源码、已检查的宣传图和干净分发包，不含现有运行目录中的个人数据。

发布源码为 `36a0de35f571d31b12bfa24dbc9c2709af9a67e0`。[Actions 39890082663](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39890082663) 的三个平台全部成功：

| 平台 | 完整回归 | 构建与产物检查 |
| --- | --- | --- |
| Ubuntu 24.04 x64 | 52 项，109.521 秒；44 项通过、8 项 Windows 专属检查跳过 | 12 个源文件类型检查、源码与实际产物的真实 PTY 退出恢复、包内 Chromium/TUI 离线 smoke、Desktop Entry 校验、打包与上传通过 |
| macOS 14 arm64 | 52 项，106.658 秒；43 项通过、9 项 Windows/Linux 专属检查跳过 | 12 个源文件类型检查、源码与实际产物的真实 PTY 退出恢复、包内 Chromium/TUI 离线 smoke、`.app` 构建与启动脚本检查、打包与上传通过 |
| macOS 15 Intel | 52 项，289.396 秒；43 项通过、9 项 Windows/Linux 专属检查跳过 | 同上，Intel 产物检查通过；不能据此宣称最低目标 macOS 14 已实机验证 |

正式 [v0.1.0 Release](https://github.com/MuZiJin701/wechat-channels-downloader/releases/tag/v0.1.0) 已发布并设为 latest，标签指向上述源码提交。附件包含 Windows x64、Linux x64、macOS arm64/x64 四个压缩包及 `SHA256SUMS.txt`；逐包检查当前双 README、启动入口、内部许可和无个人数据，五个远端附件的大小及 GitHub SHA-256 全部与本地一致。README 的最新版本下载入口已可用。此处仅补充结果记录，提交使用 `[skip ci]`，不重复构建已验证的相同程序。

这些检查使用真实 Chromium、临时目录和模拟外部服务；不能替代真实微信扫码、线上下载、Finder／Linux 文件管理器双击及实际宿主图片显示验收。Windows 图片显示的实际验证范围见下节，kitty 图片路径仍只有模拟协议与 TUI 检查。

## 图片 Logo 与文字回退（2026-10-23，仅 Windows 本机）

用户整体确认后授权实现、提交并先验证 Windows 效果。移除字符 Logo，复用已有 PNG，通过 Sixel 或 kitty 协议显示平滑图片，按标题高度缩小并居中。无法确认图片能力、图标不可用、`NO_COLOR`、终端复用器或过矮窗口采用紧凑文字版并收起占位；未新增依赖或改变应用图标资源。启动探测在 Textual 输入线程之前进行，终端模式在 finally 中恢复，协议响应不进入链接框；图片只绘制未被遮挡的可见单元格，kitty 图片在重绘与退出时清理。

本机 Windows x64 Build 26300，Python 3.11.17，Textual 8.2.8、PyInstaller 6.22.3；实际 Windows Terminal 返回 Sixel 能力与 10×20 像素单元格。以下通过结论只覆盖本轮 Windows 范围。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| strict 类型检查 | 通过 | `uv run --locked mypy`，12 个源文件，Windows 配置 |
| 完整回归 | 通过 | `uv run --locked python -m unittest discover -s tests -v`，52 项，185.931 秒；50 项通过，POSIX PTY 与 Linux 图标刷新两项明确跳过；真实 Chromium、临时会话，仅模拟外部服务 |
| 图像与回退 TUI 流程 | 通过 | 模拟 Sixel/kitty 终端能力，检查尺寸、主题切换、遮挡、小窗口隐藏后恢复与完整下载；验证无图时标题自然左对齐及原有对称控件。探测覆盖正向回复、无图片能力、缺失回复、零尺寸与超长数值，回复不进入链接输入 |
| 真实 Windows Terminal 源码界面 | 通过（离线限定范围） | 启动真实终端并接收实际协议响应，截图检查浅色、深色、外观下拉列表；实际改变窗口尺寸后图片收起、恢复大窗口后重现，并完成模拟下载、Ctrl+Q 退出。以 `TERM=dumb` 在独立进程模拟无图声明，真实窗口检查紧凑文字版及相同操作。未将内部 SVG 导出作为图片显示证据 |
| Windows 便携包 | 通过 | 使用只有仓库源码的隔离目录构建，包内单 EXE、Console 子系统、detached 清单、高清图标及原有许可检查通过；不同工作目录和特殊路径下的实际 Chromium/TUI 离线 smoke 均通过；压缩包不含 data/downloads，顶层仅双 README |
| 实际 EXE 的图片显示与终端退出 | 通过（离线限定范围） | 实际便携 EXE 在真实 Windows Terminal 运行 `--terminal-child --terminal-smoke-test`，窗口截图确认真实图片，离线会话执行主题选择、普通文本编辑、Home 与 Ctrl+Q；退出码 0，包目录未产生个人登录态或下载内容 |
| 标准构建目录替换 | 通过 | 用户说明旧构建无重要数据并授权覆盖后，将新包放回 `dist/wechat-channels-downloader/`，更新 `dist/wechat-channels-downloader-windows-x64.zip`；替换后再次从其他工作目录运行实际 EXE 的离线 smoke，通过。未读取旧登录态或下载内容 |

临时检查脚本、日志与真实窗口截图位于忽略的 `build/` 中；截图只用于本地检查，不提交或上传。图标编码复用现有 Pillow，来源依据为 [xterm 控制序列](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)、[kitty 图形协议](https://sw.kovidgoyal.net/kitty/graphics-protocol/)和 [Windows Terminal Sixel 说明](https://devblogs.microsoft.com/commandline/windows-terminal-preview-1-22-release/)。测试子进程单独清除工具环境的 `NO_COLOR` 与 `TERM=dumb` 来检查图片，不修改用户或系统环境。

未构建或运行 Linux/macOS，kitty 路径只有模拟终端/TUI 编码检查，不能宣称对应宿主实机通过；未触发 CI、读取真实账户、人工扫码或真实线上下载，也未进行用户本人视觉验收。像素格尺寸在启动时测量，运行中修改终端字号或 DPI 后需重启以重新测量；本轮未增加实时字体/DPI 重测或复用器透传。此前其他平台及旧 Logo 的通过记录不覆盖本轮新增图像路径。

## Windows 单 EXE、简化 Logo 与对称控件（2026-10-22）

用户整体确认方案并授权“实现代码，提交不推送，先验证windows系统即可”。Windows 使用单个 Console EXE 和 `detached` 清单；已有终端原地运行，双击移交独立 Windows Terminal，沿用 shell 优先级，失败时直接使用或分配控制台并恢复缺失的 Python/Textual 标准流。品牌区改为专门绘制的纯色字符标志，程序高清图标保留；按钮、外观选择框及其下拉列表均采用对称细边框。未新增依赖、修改系统设置或读取真实账户。

本机 Windows x64 Build 26300，Python 3.11.17，锁定 PyInstaller 6.22.3。以下仅记录本轮 Windows 范围；旧版跨平台 CI 结果不覆盖此次变更。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| strict 类型检查 | 通过 | `uv run --locked mypy`，11 个源文件，仅 Windows 配置 |
| 完整回归 | 通过 | 50 项，162.599 秒，48 项通过；POSIX PTY、Linux 图标刷新两项按平台明确跳过。真实 Chromium、临时会话和模拟外部服务；最终仅细化大尺寸字符标志后，重新运行相关控件/Logo 流程通过 |
| Windows 启动边界 | 通过（模拟系统服务） | 8 项启动检查覆盖继承/附着父控制台、旧系统初始控制台、自身重启防循环、shell 优先及安全参数、Terminal 缺失/失败回退、缺失标准流恢复且保留有效流、启动失败非零退出与错误脱敏 |
| 控件与 Logo 流程 | 通过 | 浅/深主题、110×40 与 60×20，按钮、选择器及下拉列表四边均为 solid；保留主题选择和键盘交互，字符标志不再含半格前背景色图像，宽高符合两个布局。原有连续 resize、输入和下载保护回归继续通过 |
| 源码及实际 EXE 真实终端驱动 | 通过（限定范围） | `--terminal-smoke-test` 使用离线临时 Chromium 会话，在 Windows 控制台/伪终端实际操作主题选择、文本输入、Home、Ctrl+Q；返回 SMOKE_OK，实际 EXE 输出包含闪烁细竖线启用和默认光标恢复序列 |
| 无控制台的原生启动与回退 | 通过（限定范围） | 本地检查器先仅脱离自身控制台，再用 Windows CreateProcess、空标准句柄和 CREATE_NEW_CONSOLE 启动实际 EXE。真实 Windows Terminal 启动一个应用子进程并完成离线 TUI；原进程及 TUI 子进程均以 0 退出。仅对子进程清空 PATH 后，Terminal 不可发现，实际控制台分配、流恢复和完整离线 TUI 正常退出；没有修改用户或系统 PATH |
| 实际 shell 与特殊路径 | 通过 | 将最终包硬链接复制到含中文、空格、`% ! ' &` 的临时路径，实际执行启动器生成的 PowerShell 7、Windows PowerShell、cmd 命令，均以 0 退出并返回 SMOKE_OK；引用及重启参数正常，无新增 data/downloads |
| Windows 便携包 | 通过 | 实际构建、检查唯一顶层应用 EXE、PE Console 子系统以及嵌入资源中的 detached 清单；不同工作目录及特殊路径下的 Chromium/TUI 离线 smoke；归档不含 data/downloads，顶层仅双 README 使用文档，内部许可和高清图标保留。最终包内 launcher、appearance、app 代码对象与当前源码编译结果相等，ZIP 内 EXE 与解压目录中的 EXE 字节相同 |
| 离线视觉预览 | 已检查（限定范围） | 实际 TUI 导出浅色、深色及小窗口图像，检查纯色标志与对称边框。预览进程单独移除 NO_COLOR、使用真彩色并校正 SVG 中文宽度；不修改用户环境，不能替代实际桌面字体和人工视觉验收 |

旧 `dist/wechat-channels-downloader/` 含便携数据，构建前已将整个目录保留为 `dist/wechat-channels-downloader-before-single-exe-20261022/`，其中 data/downloads 保留；未读取、迁移或打包其内容。新包为 `dist/wechat-channels-downloader-windows-x64.zip`，解压目录仍为 `dist/wechat-channels-downloader/`。

未验证：更早 Windows 11 实机及其闪窗表现、文件管理器鼠标双击与人眼无闪窗验收、真实微信扫码/线上下载、系统剪贴板；Linux/macOS 本轮按用户要求未运行、构建或触发 CI。原生 Windows API 启动与自动终端操作不等于人工桌面验收。旧系统单进程控制台按双击路径处理，shell-less 自定义 Windows 宿主未验收；现有 Windows 分号路径限制继续适用。本轮不推送。

## 绿系双主题、自适应、原生光标与 Logo（2026-10-22）

本轮按用户整体确认及“实现代码，更新相关文档，提交推送”的授权实施。增加绿色浅/深主题、默认跟随系统及本地偏好、品牌 Logo 与静态渐变、按宽度和高度调整布局、原生细竖线输入光标、三平台图标及 macOS `.app` 终端启动器。主题偏好使用独立的 `data/appearance.json` 原子保存；没有新增依赖、迁移真实登录态或修改全局终端设置。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| strict 类型检查 | 通过 | Windows、Linux、macOS 配置分别检查，11 个源文件；后两者仅为静态检查 |
| Windows 完整回归 | 通过 | 最终源码和夹具运行 45 项，167 秒，43 项通过，POSIX PTY 与 Linux 图标刷新两项明确跳过；真实 Chromium、临时目录和模拟外部服务，系统偏好查询在新增流程中模拟 |
| 新主题和输入流程 | 通过 | 三模式、立即切换及重启恢复、自动模式保存、系统变化、不可识别和无效配置回退、保存失败可见提示、下载期间切换保留传输与输入、结果保留；160×50、80×24、60×20、44×20、110×40 resize，中文和长链接、横向滚动及原生插入位置；扫码时切换仍保持黑白二维码，110×60 下恢复完整显示并清除尺寸提示 |
| Windows 真实终端驱动离线检查 | 通过（限定范围） | 源码及最终打包 CLI 在真实 Windows 控制台/伪终端使用 Textual Windows driver，临时离线 Chromium 会话，自动操作主题选择、文本输入、Home 和 Ctrl+Q，均返回 SMOKE_OK；输出包含原生闪烁竖线启用、随主题设置光标颜色及默认光标形状恢复序列，不等同于人工观察 Windows Terminal 闪烁形态 |
| Logo 与入口资源 | 通过（限定范围） | Pillow 生成器断言检查 PNG 透明度、ICO 16–256 尺寸与 1024 ICNS；跨平台入口生成检查 `.app` 元数据、图标可解码和安全路径传递、Linux 图标字段；Windows 不执行 macOS shell/AppleScript 或 Finder |
| 离线视觉预览 | 已检查（限定范围） | 实际 TUI 导出浅色、深色、60×20 小窗口、结果及黑白扫码状态，检查配色、图标、渐变、对齐和操作区。仅预览进程移除工具环境自带的 NO_COLOR，未改用户/系统环境；SVG 中文字符宽度在预览转换时校正，不能替代目标终端字体或实际光标验收 |
| Windows 最终便携包 | 通过 | 最终文档及布局调整后重建；包内 Chromium/TUI 离线检查、不同工作目录及含中文/空格/百分号/感叹号/单引号/`&` 的路径检查通过。实际解析两个 EXE 的 PE 图标资源，七种尺寸图像的 SHA-256 与源 ICO 全部一致；压缩包包含 PNG/ICO/ICNS、无 data/downloads；另运行最终 CLI 的真实驱动离线操作通过 |
| Ubuntu 24.04 x64 CI | 通过 | 45 项中 41 项通过、4 项 Windows 专属检查跳过；含 Linux 便携图标刷新、源码真实 PTY、实际包内 Chromium/TUI 与真实 PTY、Desktop Entry 校验、构建及上传 |
| macOS 14 arm64 CI | 通过 | 45 项中 40 项通过、4 项 Windows 专属和1项 Linux 专属检查跳过；类型检查、源码/实际产物真实 PTY、包内 Chromium/TUI、`.app` 生成、shell/AppleScript 语法检查、构建及上传 |
| macOS 15 Intel CI | 通过 | 同上，45 项中 40 项通过、5 项平台专属检查跳过；源码/实际产物真实 PTY、包内 Chromium/TUI 与 `.app` 启动器构建检查全部通过，压缩包已上传 |

本轮初次缩放回归发现旧尺寸参与 compact/short 判断，以及首次粘贴长链接可能未滚至插入点；已使用 Resize 的实际尺寸并在布局稳定后揭示输入位置，新增流程覆盖这些情况。窄窗口的主题选择器仅在空间不足时另起一行，为输入和下载保留更多可用高度。

二维码提示在每次实际绘制后检查可见区域，仅在裁剪状态变化时更新，并保留扫码服务的正常提示；覆盖小窗口提示、扫码中切换主题、放大后提示消失且二维码完整可见，避免布局更新顺序或服务状态文字覆盖尺寸提示。Windows 通过会话内 OSC 12 临时匹配输入光标颜色，并在正常退出时请求 OSC 112 恢复宿主默认色；相关能力核对参考微软[终端解析实现](https://github.com/microsoft/terminal/blob/main/src/terminal/parser/OutputStateMachineEngine.cpp)。

中途完整检查的“额外安全验证”分支失败，定位到模拟页面在服务端拒绝时仍直接写成功 Cookie，且定时轮询允许请求重叠。修正夹具仅由模拟服务端在允许登录时设置 Cookie，并串行轮询；没有改应用的安全判断或放宽断言。修正后的安全拦截、正常扫码、访客扫码和二维码缩放四项回归通过，再运行完整回归确认最终结果。打包 CLI 内的 UI、主题与 smoke 字节码已逐一与当前源码编译结果比较一致。

本轮远程验证：[Actions 39739234787](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39739234787)，代码提交 `105be66`。三个平台均成功，源码及实际产物日志均含 `TERMINAL_OK`，包内浏览器检查含 `SMOKE_OK`；Artifacts 提供 Linux x64、macOS arm64/x64 压缩包，Windows 压缩包位于本地 `dist/wechat-channels-downloader-windows-x64.zip`。此结果以仅文档提交补充，使用 `[skip ci]`，不重复构建已验证的相同程序。

Linux Desktop Entry 的图标字段要求绝对路径；便携包第一次运行或移动目录后运行会原子刷新自身入口的路径，保留权限和其他分组，不安装系统图标。首次打开包目录或移动后尚未运行时，文件管理器可能暂不显示 Logo，且可能需要刷新缓存。macOS `.app` 是与控制台程序共处同一便携目录的启动器，仍由 Terminal 运行 TUI；不能只移动 `.app`，数据继续在包外。未签名或公证，首次打开或控制 Terminal 可能需要系统授权。

尚未人工验收三平台文件管理器双击、新 macOS Finder/Terminal 交互、真实微信扫码/线上下载、系统剪贴板、实际终端颜色与闪烁形态；真实桌面系统明暗切换也未操作，新增流程模拟偏好变化。Windows 的真实驱动检查和下方旧版 CI 不能替代这些验收。最低 Intel macOS 14 仍未实机验证。

## 浅紫主题、仓库链接与输入编辑（2026-10-22）

最终背景按用户追加反馈加深为 `#ded0ee`，配合深紫主操作、紫灰辅助控件和深色文字。移除任务卡片外框，统一内容对齐；阶段文字使用紫色及成功、警告、错误语义颜色。底部改为可点击、可键盘聚焦的仓库文本链接，移除 GitHub 按钮、Ctrl+G 和 Star 提示。标准输入控件去掉占位示例网址，并将 Ctrl+A 改为全选；没有新增依赖、系统设置变更或数据迁移。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| 类型检查 | 通过 | strict mypy，9 个源文件；Windows、Linux、macOS 平台配置均通过，后两者为静态检查 |
| Windows 完整测试 | 通过 | 38 项中 37 项通过、1 项 POSIX PTY 明确跳过；真实 Chromium、临时目录与模拟外部服务 |
| 新交互回归 | 通过 | 仓库链接点击及 Tab / Shift+Tab、Enter 打开，浏览器打开失败反馈，Ctrl+G 不再打开；占位文案、Ctrl+A 替换、首尾定位、选区、删除、应用内部复制剪切粘贴、粘贴事件与鼠标拖选；点击编辑区不主动打开浏览器；保留下载及失败保护回归 |
| 离线视觉预览 | 已检查（限定范围） | 就绪、扫码、结果及 68×28 小窗口；浅紫连续画布、控件和焦点、状态语义颜色及静态黑白二维码；导出预览不等同于目标终端视觉和手机实扫 |
| Windows 便携包 | 通过 | 实际重建 GUI / Console 双入口，共用 Chromium；其他工作目录和含中文、空格、百分号、感叹号、单引号、`&` 路径的包内离线 Chromium / TUI 检查；归档不含 data/downloads，仅顶层双 README，内部许可保留 |
| Standards / Spec 独立审查 | 通过 | 固定差异 `0f8d16b...d32f2de` 及测试增量 `d32f2de...272742f`，两个审查轴均为 0 项可行动发现；未重复运行检查 |
| 本轮 Linux/macOS CI | 通过 | Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel 各运行 38 项：34 项通过、4 项 Windows 专属检查跳过；类型检查、源码及实际产物的真实 PTY 退出恢复、包内 Chromium/TUI 离线启动、打包与上传全部通过，Linux 桌面入口格式检查通过 |

浏览器失败提示回归进一步改为检查实际可见 Toast，未模拟应用内部通知；启用 Textual 测试通知后，修订后的单项回归通过，应用代码不变。

本轮远程验证：[Actions 39728596057](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39728596057)，提交 `272742f`，三个平台全部通过；应用实现为 `d32f2de`，后续增量只改测试。Linux/macOS 压缩包位于该运行的 Artifacts，Windows 压缩包位于本地 `dist/`。此结果记录以仅文档提交补充并使用 `[skip ci]`，不重复运行相同应用和测试代码。

本轮未人工验收 Windows Terminal 的系统剪贴板粘贴、宿主对真实 URL 的自动识别、文件管理器双击或实际扫码下载；应用内部剪贴板检查不能替代系统剪贴板验收。既有 Windows 分号路径限制继续适用，未修改全局终端配置。Intel macOS 14 仍未实机验收；下方历史结论不覆盖本轮变更。

## 启动与界面改版（2026-10-22）

按本轮已确认需求实现窗口启动器、统一主题、分阶段界面、按钮快捷键、最近一次结果、仓库入口和新归档通用命名。Windows 主 EXE 使用 GUI 子系统，控制台入口使用 `-cli.exe`；两者共用一份依赖与 Chromium。既有归档及真实登录态未读取或迁移。

| 检查 | 状态 | 实际范围 |
| --- | --- | --- |
| 类型检查 | 通过 | strict mypy，9 个源文件；Windows、Linux、macOS 三个平台配置分别检查，后两者属于静态检查 |
| Windows 完整测试 | 通过 | 37 项中 36 项通过，1 项 POSIX PTY 明确跳过；真实 Chromium、临时目录、模拟外部服务 |
| TUI 完整流程 | 通过 | 登录前隐藏输入、微信扫码及必要协议确认、失效后重新扫码并保留链接、网络重试保护旧状态、全部完成后清空输入、部分完成保留链接和可展开详情、Ctrl+R 重试下载、Ctrl+O 目录入口、Ctrl+G 仓库入口、Ctrl+Q 正常中断；保留既有资源归档与安全回归 |
| 新旧归档 | 通过 | 新归档生成 `parse.json`，HTML 通用数据名称和本地引用，响应原值保留；旧 `yuanbao.json` 不改动 |
| 界面预览 | 已检查（限定范围） | 离线模拟会话生成就绪、扫码、结果和小窗口画面，检查独立配色、留白、控件层次与二维码黑白；不等同于真实 Windows Terminal 字体或手机扫码验收 |
| Windows 启动边界 | 通过（模拟） | 优先 pwsh、旧 PowerShell 和 cmd 回退、独立新窗口参数、附着已有控制台、缺少或无法启动 Terminal 后回退，以及错误信息脱敏；外部终端和系统启动服务被模拟 |
| 修正后 Linux/macOS CI | 通过 | Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel 各运行 37 项，33 项通过、4 项 Windows 专属检查跳过；mypy、源码及实际产物的真实 PTY 退出恢复、打包 Chromium/TUI 离线检查均通过，压缩包已上传，Linux 桌面入口格式检查通过 |

Windows 最终便携包构建通过：两个 EXE 的 PE 子系统分别为 GUI / Console，共用依赖和 Chromium；不同工作目录及含中文、空格、百分号、感叹号、单引号与 `&` 的路径均实际执行离线 smoke 成功。另在这类目录中实际执行启动器生成的 PowerShell 7、Windows PowerShell、cmd 三种命令，均返回 SMOKE_OK；此检查模拟 wt 移交，不是实际 Terminal 窗口验收。压缩包检查通过，不含 data/downloads，顶层仅双 README，内部许可存在。

Standards / Spec 双轴独立审查已完成：固定基线 `7939299` 至实现 `126dfaa`，以及后续测试修正增量 `3eee249...1c39b83`，两个审查轴均无可行动发现。审查只读源码、规格及关联测试，未重复运行自动检查。

首轮[跨平台 CI 39723330632](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39723330632) 的 macOS 14 arm64 暴露了既有离线页检查的时序问题：页面使用懒加载图片，测试却在滚动及解码前立即要求所有图片完成。修正检查按用户浏览顺序滚动到每张图并等待 `decode()`，仍验证全部图片真实加载及原尺寸，不改变应用的懒加载行为、不增加固定等待。

最终远程验证：[Actions 39723699275](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39723699275)，提交 `1c39b83`，三个平台全部通过；应用实现与 `126dfaa` 一致，增量只涉及测试及验证文档。各平台压缩包位于该运行的 Artifacts，Windows 压缩包在本地 `dist/`。本条结果记录为后续仅文档提交，使用 `[skip ci]`，不重复运行相同应用和测试代码。

额外路径调查发现：包含分号的目录中直接运行控制台产物即发生 `_ctypes` DLL 加载失败，不依赖 shell 移交。尝试额外 DLL 目录和提前导入均无效，未保留这些补丁；双 README 明确要求 Windows 解压路径不含分号。本轮不把模拟编码命令的分号转义检查当作这类目录下的真实启动通过。

未执行真实账号扫码、线上内容下载、文件管理器双击、实际 Windows Terminal 零闪窗与等待耗时验收；新 Linux/macOS 桌面入口、最低 Intel macOS 14 也未实测。源码和打包自动检查不能代替这些人工验收，旧版 CI 结论不覆盖本轮。

## Spec #2：动态完整归档与终端体验

实现增加两步完整 JSON、离线 HTML、全部已知媒体与视频版本、信息命名、重复下载隔离和部分失败/中断保留；终端使用原生 ANSI 配色，Windows 独立控制台启动优先转入 Windows Terminal，打包使用英文入口且只在顶层保留双 README。

| 本轮检查 | 状态 | 实际范围 |
| --- | --- | --- |
| 类型检查 | 通过 | strict mypy，8 个源文件；另用 Linux/macOS 平台配置检查平台分支，属于静态检查 |
| Windows 完整测试 | 通过 | 35 项：34 项通过，1 项 POSIX PTY 按平台规则跳过；真实 Chromium 与临时目录，模拟外部服务 |
| 动态归档流程 | 通过 | 从 TUI 输入到文件落盘，覆盖两步独有字段、H264/H265、多图、独立封面、头像、认证图标、HTTPS 配乐、相同地址复用、无正文、非法/长名称、重复下载、部分/全部失败、解析失败保留、正常 Ctrl+Q 中断和不可写目录 |
| 离线 HTML | 通过 | 真实 Chromium 读取生成页面：原文不改写、HTML 安全转义、真实 PNG 本地加载、本地媒体引用和查询时信息；音视频使用模拟字节比对，不等同于真实播放验收 |
| Windows 启动 | 通过（限定范围） | 真实入口测试中模拟外部控制台/终端服务，覆盖优先、回退、已有终端及防循环；生成的 PowerShell 编码命令另实际启动便携 EXE 的离线临时会话并返回 SMOKE_OK，未操作文件管理器或真实 Windows Terminal 窗口 |
| 终端原生配色 | 通过（自动检查） | TUI 实际前景/背景为终端默认色，二维码仍黑白；浅色/自定义终端的视觉可读性仍需桌面验收 |
| Windows 便携包 | 通过 | 实际构建及不同工作目录下包内 Chromium/TUI 离线检查；包内仅双 README，内部许可存在、相对链接有效、无开发文档或个人 data/downloads |
| Standards / Spec 双轴审查 | 通过 | 两个独立审查轴检查 `184d23f...9f35c1d` 的完整变更及相关调用方；均无可行动发现。审查未重复运行测试，未访问真实登录态 |
| 本轮 Linux/macOS CI | 通过 | Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel 各运行 35 项：32 项通过，3 项 Windows 专属入口检查跳过；mypy、源码与实际便携产物 PTY 退出恢复、包内 Chromium/TUI 离线启动全部通过，压缩包已上传；Linux 桌面入口格式检查通过 |

本轮未读取真实登录态、未要求扫码、未对真实动态进行完整下载或音视频离线播放，也未人工验收各平台文件管理器双击、终端主题和二维码实扫。Windows 本机为 Build 26300 x64，Python 3.11.17；尚未执行最低目标 Intel macOS 14 验收。测试仅在临时目录写入模拟内容，不将原始样本或带访问参数的资源地址放入仓库。

代码与检查发生变更后，需按变更影响重新验证；后续审查修正和远程结果追加于本节，不改写以下历史结论。

远程验证：[Actions 39635002893](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39635002893)，提交 `27ada56`（应用实现为 `9f35c1d`），三个平台均通过。Linux/macOS 各架构压缩包位于该运行的 Artifacts；Windows 压缩包已在本机构建并检查。此后的结果记录仅修改文档，使用 `[skip ci]` 提交，应用及检查代码不变。

## 登录弹窗与终端恢复修正（2026-10-21）

Linux 服务器（Ubuntu 24.04.5 x64）实际复现：元宝首页约 1 秒加载后，约 3 秒自动出现微信登录弹窗，约 4 秒二维码可见；旧代码却一直点击被弹窗遮挡的首页按钮，10 秒后超时。延长到 20 秒仍被遮挡。包内 Chromium 离线检查通过，相关服务的首页 HTTP 请求也正常。

旧包在真实 PTY 中按 Ctrl+Q 正常退出后，`ECHO` 和 `ICANON` 均保持关闭。独立 Node 实验验证：Node 在 TUI 的原始输入模式下启动，若晚于 TUI 退出，会覆盖 TUI 已恢复的终端属性。修正入口在所有应用清理完成后恢复启动前的完整属性，不强制覆盖为一套默认值。

| 本轮检查 | 状态 | 范围 |
| --- | --- | --- |
| 类型检查 | 通过 | mypy strict，7 个源文件；另以 Linux/macOS 平台配置检查 POSIX 分支 |
| Windows 回归 | 通过 | 23 项中 22 项通过，1 项 POSIX PTY 检查明确跳过；新增延迟自动弹窗和主动登录入口流程 |
| Windows 修正版便携包 | 通过 | 构建完成；从其他工作目录运行包内 Chromium / TUI 离线检查；归档不含 data/downloads |
| Linux/macOS 修正版 CI | 通过 | Ubuntu 24.04 x64、macOS 14 arm64、macOS 15 Intel 各完整 23 项全部通过，无跳过；源码真实 PTY、打包产物真实 PTY 与浏览器离线检查全部通过，压缩包已上传 |
| Linux 服务器修正版实机 | 通过 | 新包约 6.16 秒出现真实微信二维码；Ctrl+Q 正常退出，无 TimeoutError；全部 termios 配置与启动前一致，ECHO/ICANON 均启用，退出后写入文字确认正常回显；二维码已删除，没有扫码或保存账户 |

`tools/check_terminal.py` 创建独立 PTY，用 `--terminal-smoke-test` 运行源码或实际便携程序；使用临时会话及模拟外部服务，观察真实屏幕模式、Ctrl+Q 退出与完整 termios 属性一致性。构建中任何一项失败都会阻止归档和上传。旧包受影响的终端可用 `stty sane` 恢复；强制杀进程或 SSH 断开无法保证完成清理。

首轮新增 PTY 检查发现 macOS 的 lflag 差异恰为 `0x20000000`（PENDIN）；回显、按行输入、速度与全部控制字符已经恢复。此位是 [XNU 定义的待处理输入状态](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/termios.h)，[恢复 ICANON 时由内核自动设置](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/tty.c)。因此仅在 macOS 比较配置时排除此状态位，保留其余全部属性检查，不修改程序的实际恢复逻辑。

本轮 Standards 与 Spec 两个审查轴均无新增可行动问题。旧 Windows 程序及其本地数据整体保留在单独目录；新包不携带个人数据。

服务器实机验证使用 `23e900b` 的 Linux 产物；后续 `7bb132a`、`96244f4` 只调整检查诊断、macOS PENDIN 状态比较及文档，应用实现相同。新包解压到独立目录，原安装目录未覆盖。

最终远程验证：[Actions 39600651065](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39600651065)，提交 `96244f4`，三个平台均通过。Linux/macOS 各架构压缩包位于该运行的 Artifacts；首轮失败已通过终端状态诊断查明为上述 PENDIN 比较问题。此后的结果记录仅修改文档，使用 `[skip ci]` 提交，应用及检查代码不变。

## 初版验证（历史）

| 检查 | 状态 | 范围 |
| --- | --- | --- |
| 项目类型检查 | 通过 | mypy strict；Python 应用、离线 smoke 与构建脚本，共 6 个源文件 |
| TUI 工作流回归 | 完整 20 项通过 | 真实 Chromium；视频、图文、模拟扫码与登录态保存、失败处理；另含构建数据保护 |
| Windows 便携包 | 构建、离线启动检查与真实登录/视频流程通过 | 包内 Chromium 与离线 TUI；从其他工作目录启动；生成的压缩包不含登录态与下载内容 |
| Ubuntu 24.04 x64 Actions | 通过 | mypy、完整 20 项测试、便携包构建、从其他工作目录启动包内 Chromium / TUI、Linux 桌面入口格式检查、上传压缩包 |
| macOS 14 arm64 Actions | 通过 | mypy、完整 20 项测试、便携包构建、从其他工作目录启动包内 Chromium / TUI、上传压缩包 |
| macOS 15 Intel Actions | 通过 | mypy、完整 20 项测试、便携包构建、从其他工作目录启动包内 Chromium / TUI、上传压缩包 |
| Windows 真实微信扫码与线上下载 | 通过 | 用户扫描程序取得的二维码并在手机确认；真实身份确认、状态保存与重启复用通过；视频 15,630,609 字节且具有 MP4 文件头；两条图文链接各下载 6 张图片与 101 字正文，图片均通过 Pillow 解码校验 |
| 文件管理器双击与终端字符二维码手机实扫 | 未执行 | 实际 exe 在终端启动；用户扫描的是同一二维码的临时图片，不能等同于终端字符码实扫或文件管理器双击验收 |
| Intel macOS 14 | 未执行 | 当前 CI 选用 macOS 15 Intel，不能据此证明 14 通过 |

真实登录由用户参与确认，登录态与下载内容仅留在本地忽略目录。自动化使用临时测试会话，不加载真实账户，也不把它们上传到 CI。暂未进行 Apple 签名、公证或 Windows 代码签名。

本机：Windows 11 x64，Build 26300；Python 3.11.17。构建及测试依赖由 uv.lock 锁定。

远程验证：[Actions 39591619812](https://github.com/MuZiJin701/wechat-channels-downloader/actions/runs/39591619812)，代码提交 `2a9310c`。各平台压缩包位于该运行的 Artifacts。此前首轮 CI 暴露了 macOS Chromium 应用包被 PyInstaller 重新处理后签名失败的问题；现已改为完整复制浏览器并保留符号链接，本轮使用实际打包产物执行离线启动检查。

验证结果记录在后续仅文档提交中；该提交使用 `[skip ci]`，不重复运行已通过的相同应用与构建代码。

审查：Standards 发现的重建覆盖用户数据问题已修复，并有构建命令回归；Spec 发现的身份确认与访客扫码分支问题已修复，并有 TUI 回归。实际服务响应中的空错误包装与 image/jpg 兼容问题也已补回归。两个审查轴均无未解决发现。
