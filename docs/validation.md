# 验证记录

验证对象：Spec #1 的便携式 TUI 实现。自动化只使用临时登录态与模拟外部服务；本文件不把模拟检查写成真实业务验收。

## 登录弹窗与终端恢复修正（2026-10-21）

Linux 服务器（Ubuntu 24.04.5 x64）实际复现：元宝首页约 1 秒加载后，约 3 秒自动出现微信登录弹窗，约 4 秒二维码可见；旧代码却一直点击被弹窗遮挡的首页按钮，10 秒后超时。延长到 20 秒仍被遮挡。包内 Chromium 离线检查通过，相关服务的首页 HTTP 请求也正常。

旧包在真实 PTY 中按 Ctrl+Q 正常退出后，`ECHO` 和 `ICANON` 均保持关闭。独立 Node 实验验证：Node 在 TUI 的原始输入模式下启动，若晚于 TUI 退出，会覆盖 TUI 已恢复的终端属性。修正入口在所有应用清理完成后恢复启动前的完整属性，不强制覆盖为一套默认值。

| 本轮检查 | 状态 | 范围 |
| --- | --- | --- |
| 类型检查 | 通过 | mypy strict，7 个源文件；另以 Linux/macOS 平台配置检查 POSIX 分支 |
| Windows 回归 | 通过 | 23 项中 22 项通过，1 项 POSIX PTY 检查明确跳过；新增延迟自动弹窗和主动登录入口流程 |
| Windows 修正版便携包 | 通过 | 构建完成；从其他工作目录运行包内 Chromium / TUI 离线检查；归档不含 data/downloads |
| Linux/macOS 修正版 CI | 待执行 | 完整 23 项、源码真实 PTY、打包产物真实 PTY 与浏览器离线检查 |
| Linux 服务器修正版实机 | 待执行 | 使用新构建产物检查真实二维码出现与 Ctrl+Q 退出后的终端恢复；不自动扫码登录 |

`tools/check_terminal.py` 创建独立 PTY，用 `--terminal-smoke-test` 运行源码或实际便携程序；使用临时会话及模拟外部服务，观察真实屏幕模式、Ctrl+Q 退出与完整 termios 属性一致性。构建中任何一项失败都会阻止归档和上传。旧包受影响的终端可用 `stty sane` 恢复；强制杀进程或 SSH 断开无法保证完成清理。

首轮新增 PTY 检查发现 macOS 的 lflag 差异恰为 `0x20000000`（PENDIN）；回显、按行输入、速度与全部控制字符已经恢复。此位是 [XNU 定义的待处理输入状态](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/termios.h)，[恢复 ICANON 时由内核自动设置](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/tty.c)。因此仅在 macOS 比较配置时排除此状态位，保留其余全部属性检查，不修改程序的实际恢复逻辑。

本轮 Standards 与 Spec 两个审查轴均无新增可行动问题。旧 Windows 程序及其本地数据整体保留在单独目录；新包不携带个人数据。

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
