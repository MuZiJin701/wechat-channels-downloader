# Windows 单应用 EXE 启动方案核实

研究日期：2026-10-22。状态：用户已在 Q5 接受推荐方向，随后整体确认并授权实现、验证 Windows、提交且不推送。本文保留研究时的候选比较及当时未验证项；确认见[需求记录](requirements.md)，后续实际执行结果见[验证记录](validation.md)。

问题范围：同一个 `wechat-channels-downloader.exe` 能双击启动，也能在已有 cmd、Windows PowerShell、PowerShell 7、Windows Terminal 中运行同一 TUI 并等待退出；双击优先独立 Windows Terminal，缺失或移交失败时回退系统控制台；不提权、不安装软件、不修改系统默认设置。原支持目标为 Windows 11 x64，不预先收窄为 24H2。这里的“单 EXE”指只有一个应用 EXE，不再有独立 CLI EXE；仍保留 `_internal/`、Chromium 自身的可执行文件和便携数据目录。

## 结论与推荐

**最合适的候选是一个 Console 子系统 EXE，加 `consoleAllocationPolicy=detached` manifest 作为新系统增强；保留旧 Windows 的控制台启动路径。** 这不是“所有 Windows 11 上均零闪窗”的承诺。

- Windows 11 24H2（26100）及以上支持该策略：保持 Console 身份让 shell 等待，未继承控制台时不自动分配控制台。双击之后再由本程序请求 Windows Terminal。[微软已发布 API 文档](https://learn.microsoft.com/en-us/windows/console/console-allocation-policy)
- 微软设计文档明确说明，控制台继承照常进行；旧系统不理解该字段时按 PE 子系统处理。因此可以保留原支持范围，把不预先创建控制台作为新系统增强，而不是把 24H2 自动设为程序最低版本。这一兼容结论有官方设计依据，仍须验证最终 PyInstaller 产物在旧版本上的 manifest 装载和启动。[微软设计：继承、Downlevel](https://github.com/microsoft/terminal/blob/main/doc/specs/%237335%20-%20Console%20Allocation%20Policy.md)
- 在较早 Windows 11 上，Console EXE 双击仍可能先产生控制台，再转交 Windows Terminal；没有从所查主来源找到一个既沿用普通 PyInstaller 单 EXE、又保证所有这些旧系统不先闪窗、同时让所有已有 shell 自然等待的开关。若“全部支持版本零闪窗”是硬要求，应保留双入口方案，或另行讨论快捷方式等入口取舍，不能把此候选写成全条件已经满足。

此前“这个新机制要求 24H2”的说法适用于**机制生效**，不等于“带此 manifest 的整个应用必须只支持 24H2”。

## 已确认事实

### Console 身份决定 shell 的默认等待

微软说明，Console 子系统程序在 CMD、PowerShell 中执行时会阻塞 shell，直到程序结束；GUI 子系统通常不具有此行为。`AttachConsole` 改变的是控制台附着关系，不能倒转调用方已经作出的等待决定。因此不推荐把本项目合并为一个 GUI EXE，事后仅靠 `AttachConsole` 模拟 CLI。[Console Allocation Policy](https://learn.microsoft.com/en-us/windows/console/console-allocation-policy)、[AttachConsole](https://learn.microsoft.com/en-us/windows/console/attachconsole)

微软设计文档还说明，`detached` 只影响没有继承控制台时的分配，建议其优先于 `CREATE_NEW_CONSOLE`。因此加入 manifest 后，不能继续把“重启同一 EXE 并只传 `CREATE_NEW_CONSOLE`”当作已证明可靠的回退。[微软设计：Interaction with existing APIs](https://github.com/microsoft/terminal/blob/main/doc/specs/%237335%20-%20Console%20Allocation%20Policy.md)

### 回退可以用长期存在的 AllocConsole

`AllocConsole()` 为当前没有控制台的进程创建控制台，并初始化 Win32 标准输入、输出和错误句柄；已有控制台时失败。它从 Windows 2000 起存在。较新的 `AllocConsoleWithOptions` 才要求 Windows 11 24H2；本项目最小方案没有必要无条件调用该新 API。[AllocConsole](https://learn.microsoft.com/en-us/windows/console/allocconsole)、[AllocConsoleWithOptions](https://learn.microsoft.com/en-us/windows/console/allocconsolewithoptions)

系统控制台的实际显示宿主由用户系统配置决定；“回退系统控制台”不应承诺强制回到传统 conhost，也不应为了外观修改默认终端。[控制台创建](https://learn.microsoft.com/en-us/windows/console/creation-of-a-console)

### Win32 句柄、CRT 文件描述符、Python 标准流不是同一层

无标准句柄时 `GetStdHandle` 可返回 NULL；句柄也可能是父进程重定向的管道或文件。附着、创建控制台之后必须重新检查；有句柄不能直接证明它是交互终端。`CONIN$`、`CONOUT$` 可以打开当前控制台的输入及输出缓冲区，即便标准句柄已被重定向。[GetStdHandle](https://learn.microsoft.com/en-us/windows/console/getstdhandle)、[Console Handles](https://learn.microsoft.com/en-us/windows/console/console-handles)

CPython 3.11 的 `create_stdio` 遇到无效文件描述符时返回 `None`，初始化时分别设置 `sys.stdin/stdout/stderr` 及其双下划线版本；不会因为后来调用了 `AllocConsole` 就重新执行这段初始化。因此，新路径必须在导入 TUI、建立日志和启动外部进程前，恢复必要的 Python 流及其底层文件描述符，保留原本有效的流；不能只调用一个 Win32 函数就认为 Textual 可运行。[CPython 3.11 源码：create_stdio / init_sys_streams](https://github.com/python/cpython/blob/v3.11.14/Python/pylifecycle.c#L2067)

本项目锁定 PyInstaller 6.22.3。其 bootloader 在 Python 3.11 路径初始化隔离配置，调用 `Py_InitializeFromConfig`；入口区分 `wmain`（Console）和 `wWinMain`（GUI）。源码没有提供“此 manifest 加 Textual”的交付保证。结合 CPython 源码，可推断无控制台时可能正常启动解释器并得到 `None` 标准流，足以进入启动分流逻辑；此处是**源码推断**，不是本项目打包验证结果。[PyInstaller 6.22.3：解释器初始化](https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/bootloader/src/pyi_python.c#L96)、[bootloader 入口](https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/bootloader/src/main.c)

### hide-console 不是合适的补丁

PyInstaller 的 `hide-early/minimize-early` 在 bootloader 执行后处理已创建的控制台，官方承认仍可能短暂闪窗。Windows Terminal 是默认宿主时，隐藏退化为最小化；若进入已有窗口的新标签页，还可能最小化含其他标签页的整个窗口，且存在时序失效。为了一个 TUI 启动入口引入这些副作用不合适。推荐候选不启用这组参数，也不操作用户现有终端的窗口显示状态。[PyInstaller 官方 caveats](https://pyinstaller.org/en/stable/feature-notes.html#automatic-hiding-and-minimization-of-console-window-under-windows)

### Windows Terminal 显式请求独立窗口

`wt -w new`（或 `-w -1`）明确请求新窗口，可覆盖默认的新窗口/新标签页选择；`new-tab`、标题和尺寸参数有官方接口。保留当前项目已经实现的 PowerShell 7 → Windows PowerShell → cmd 优先级，以及处理路径中空格、中文、单引号和分号的引用方式，无需新依赖。[Windows Terminal 命令行参数](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments)

## 最小实现轮廓（未实施）

1. `tools/windows.spec` 只生成一个 `console=True` 的 `wechat-channels-downloader.exe`，合并上述 manifest，保留现有依赖、浏览器及图标。检查实际嵌入资源，不能只检查源 XML。[PyInstaller manifest 构建选项](https://pyinstaller.org/en/stable/usage.html#cmdoption-m)
2. 将 `main.py` 当前按 `sys.stdin is None` 判断“GUI 启动器”的逻辑改为显式 Windows 启动分流。已有可用控制台/终端时原地运行，不启动另一个窗口；无控制台时尝试附着父进程，成功后恢复流再运行。`AttachConsole` 在已经附着时返回 `ERROR_ACCESS_DENIED`，此失败不能解释成“双击”。[AttachConsole](https://learn.microsoft.com/en-us/windows/console/attachconsole)
3. 双击路径继续复用 `downloader/launcher.py` 中对 Windows Terminal 和 shell 的调用，只把目标换成自身；通过内部启动标记防止迁移后再次迁移。旧系统自动分配的控制台必须与继承的控制台区分。`GetConsoleProcessList` 可查询附着进程，但微软提醒其不是跨远程终端的通用接口；不能只检查 `WT_SESSION` 是否存在，也不能仅以 `GetConsoleWindow` 的窗口可见性判断，因为 ConPTY 的窗口句柄并不对应用户看到的窗口。[GetConsoleProcessList](https://learn.microsoft.com/en-us/windows/console/getconsoleprocesslist)、[GetConsoleWindow](https://learn.microsoft.com/en-us/windows/console/getconsolewindow)
4. Windows Terminal 不可用或明确移交失败时，已有本进程控制台则直接使用；完全没有控制台则调用 `AllocConsole` 并恢复流，在当前进程进入 TUI。创建失败以现有错误对话框明确报错，不静默退出，不无限重启。[AllocConsole](https://learn.microsoft.com/en-us/windows/console/allocconsole)
5. “`wt.exe` 命令调用成功”与“目标 TUI 已进入可交互状态”分别验证；现有 `subprocess.run(..., timeout=10)` 只检查命令层，不能凭它宣称任意延迟失败均能可靠回退。若实施中发现需要就绪信号，使用最小本地握手，避免既启动成功又触发回退产生重复实例；此握手是否必需由实际故障验证决定，不预建通用启动框架。

旧系统双击识别及迁移是这套方案最需验证的部分；检测不确定时优先保留当前可用终端，不隐藏、关闭或误迁移用户 shell。单纯的“只有自己一个控制台进程”不能作为覆盖所有调用环境的普遍定理。

## 方案比较

| 候选 | 已有 shell 等待 | 双击初始控制台 | 本项目判断 |
| --- | --- | --- | --- |
| 当前 GUI + Console 两个入口 | CLI 自然等待 | GUI 不预先分配 | 当前基线，不满足一个顶层 EXE |
| 单 GUI + AttachConsole | 不能保证调用 shell 等待 | 不预先分配 | 不推荐 |
| 单 Console，按需迁移 | 自然等待 | 旧系统可能出现 | 可行基础，但需接受旧系统外观限制 |
| 单 Console + detached manifest | 自然等待；继承照常 | 24H2+ 可避免自动分配；旧系统仍可能出现 | 推荐验证的渐进增强候选 |
| 单 Console + hide/minimize early | 自然等待 | 仍可能闪窗，并可能影响其他 WT 标签页 | 不推荐 |

表格是上述微软、PyInstaller 文档的归纳及针对本项目的判断，不代表这些候选已在此仓库实际运行。

## 必须补做的验证

- Windows 11 24H2+ 与至少一个仍在目标范围内的更早 Windows 11：真实最终 EXE 的 PE Console 子系统、嵌入 manifest、双击启动、退出及初始闪窗表现分别记录。
- cmd、Windows PowerShell、PowerShell 7，以及 Windows Terminal 内这些 shell：直接执行、shell 等待、退出码、Ctrl+C / Ctrl+Q、输入和退出后光标恢复；检查不出现第二个窗口。
- 默认终端分别为 Windows Terminal / Windows Console Host；双击时 Windows Terminal 开启/关闭、偏好新标签页时仍创建独立窗口；无 Windows Terminal、命令调用失败、目标程序无法进入 TUI及回退失败分别覆盖。
- 标准流最初缺失、有效、重定向时分别验证；恢复后的 `fileno()`、`isatty()`、中文输出和真实 Textual 交互都要成立；不得把重定向输入误判为 Explorer 双击。
- 路径含中文、空格、`% ! ' & ;`；随包 Chromium、便携数据位置与异常日志脱敏保持既有要求；所有自动会话仍使用离线临时数据。
- 同步检查调用方：`main.py`、`downloader/launcher.py`、`tools/windows.spec`、`tools/build.py`、`tests/test_startup.py`、构建相关测试、双 README、规格及验证记录中的 `-cli.exe` 与双入口描述。

本次只读核实本地源码、锁文件、领域约定并查询主来源，新增本研究文件；未安装依赖、运行应用、读取真实登录态、构建或完成上述验收。未改正式规格，也未把候选记为已接受决定。
