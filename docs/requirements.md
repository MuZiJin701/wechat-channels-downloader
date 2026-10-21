# 微信视频号下载：需求澄清记录

项目名称：微信视频号下载（`wechat-channels-downloader`）。

状态：历史记录。验收边界已在 [Spec #1](https://github.com/MuZiJin701/wechat-channels-downloader/issues/1) 中确认；当前实现与验证情况见 [README](../README.md)。

实现后的 Linux 服务器排查发现登录弹窗时序与退出后终端回显问题；后续修正及真实 PTY 验证见[本地规格补充](spec.md)和[验证记录](validation.md)。以下保留原始需求澄清历史。

## 需求澄清阶段的交付范围（已结束）

本次只按 `grill-with-docs` 完成需求澄清、词汇表和必要决策文档。下述程序行为与验证方式是未来项目的需求，不是本次执行事项。本次不编写应用、不安装依赖、不进行真实扫码或下载、不创建 GitHub 仓库、不提交或推送代码、不运行 GitHub Actions。

## 用户提出的目标与已确认事项

- 在 Windows、Linux、macOS 上提供 TUI 工具，各平台分别打包并提供双击启动入口；用户无需安装 Python 或输入命令。
- 启动时使用 Playwright 驱动无头 Chromium，检查元宝登录态。
- 登录态有效时自动复用；未登录时展示微信二维码，让用户扫码完成元宝登录。
- 提供链接输入框，接受 `https://weixin.qq.com/sph/...` 视频号分享链接；视频型动态下载视频，图文动态支持下载图片及文字内容，不将第一版限制为视频。
- 提供便携版，随包携带 Chromium；在启动程序旁用 `data/` 保存登录态、`downloads/` 保存下载内容。macOS 使用 `.app` 外侧目录，不修改应用包内部；目录不可写时明确报错。
- 新项目放在 `D:/data/projects`，参考已有项目实现。
- 平台目标：Windows 11 x64、Ubuntu 24.04 x64、macOS 14+ 的 Intel 与 Apple Silicon。Windows 本机验证，Linux 和 macOS 使用 GitHub Actions 验证；具体自动验证边界见下文。
- 按既有“元宝登录态 → 视频号解析 → 媒体下载”原理设计，不要求重新发明解析方案。

## 已查明的事实

- 当前工作仓库 `seu_lecture_reserve` 用于讲座预约，具有 Playwright 浏览器与学校登录代码，没有元宝登录或视频解析实现。
- 本机安装的 `wx-video-account-notes` 支持视频号 `https://weixin.qq.com/sph/...` 分享链接；其客户端调用远端解析服务，再下载返回的媒体地址。客户端中没有本地元宝登录实现。
- 上述 skill 指向上游仓库 [wx-video-account-notes](https://github.com/MuZiJin701/wx-video-account-notes)。其 [server/yuanbao_login.py](https://github.com/MuZiJin701/wx-video-account-notes/blob/main/server/yuanbao_login.py) 已实现无头 Chromium、微信二维码获取、元宝身份检查及 Cookie 提取；维护入口先校验现有 Cookie，有明确过期结果才重新登录。
- 上游解析链依次调用元宝 `/api/weixin/get_parse_result`、视频号 `/finder-preview/api/feed/get_feed_info`，取得媒体地址后流式下载。参考固定版本 [yuanbao.go](https://github.com/ltaoo/wx_channels_download/blob/124f044235bc706fe796c043a14ff442a150ae5d/pkg/scraper/wxchannels/yuanbao.go)。
- 上游入口含 Linux 文件锁、Linux 二进制路径和不适用于 Windows 普通 stdin 的 select 调用，不能直接视为跨平台实现。
- 笔记项目采用 [MIT](https://github.com/MuZiJin701/wx-video-account-notes/blob/main/LICENSE)；解析器固定依赖的 [LICENSE](https://github.com/ltaoo/wx_channels_download/blob/124f044235bc706fe796c043a14ff442a150ae5d/LICENSE) 还包含 Commons Clause 收费限制。用户要求沿用技术原理，并未提出收费分发需求；收费计划不是本次需求澄清的阻塞项。将来实际复用时保留适用许可声明，收费分发如成为需求再审查。
- Playwright 可保存 Cookie、localStorage 等认证状态；元宝所需的实际状态必须验证，不能预设仅 Cookie 足够。参考：<https://playwright.dev/python/docs/auth>。
- 各操作系统需要分别构建打包产物。参考：<https://pyinstaller.org/en/stable/usage.html#supporting-multiple-operating-systems>。

## 已收到的回答

1. 输入示例为 `https://weixin.qq.com/sph/AxzsxtATJv`，目标为下载视频号内容。
2. 接受各平台单独打包并提供双击入口。
3. 要求便携版，数据放在应用目录内。
4. 视频号内容包含视频和图文，图文必须支持。
5. 接受随包携带 Chromium、程序旁 data/ 与 downloads/、macOS 应用包外侧存储、不可写时报错的建议。
6. 接受上述平台目标；Windows 本机验证，Linux 和 macOS 通过 GitHub Actions 验证。
7. 沿用现有元宝解析原理；没有提出商业化需求。
8. 本次仅完成 skill 的澄清与文档，不能扩展为项目实现或外部操作。
9. 项目主题与名称为微信视频号下载，项目名称和目录名不包含 yuanbao；技术说明仍如实记录元宝解析依赖。

## 待最终确认的验收边界

建议将以下自动检查与真实业务验收分别记录，等待用户确认：

- Windows 本机：未来验证实际启动、微信扫码、登录态复用，以及视频和图文的完整下载。
- Linux/macOS GitHub Actions：未来验证各平台构建、打包产物启动、真实 Chromium 无头启动、隔离页面的登录态保存与复用，以及模拟响应下的视频和图文下载；不上传个人登录态。
- 没有人工扫码和目标桌面会话的 CI，不能据此宣称真实元宝扫码、线上完整下载或文件管理器双击体验已通过。
- 当前标准 runner 可覆盖 Ubuntu 24.04 x64、macOS 14 arm64 和 macOS 15 Intel。Intel macOS 14 仍是支持目标，不因 macOS 15 的 CI 通过就声称 14 已验证。参考 [GitHub runner 规格](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)。

其他交互与目录命名细节尚未形成需求，不在本次扩展设计。

## 后续验证

- 无头 Chromium 能否取得可扫码的元宝登录二维码，并可靠识别登录成功、过期与失败。上游有 Linux 扫码与解析通过的记录，本项目尚未验证。
- 使用该登录态解析实际目标链接并下载完整视频的可行性。
- 确定平台、系统版本与架构后，验证各平台双击入口、二维码可读性和打包运行。

上述记录形成时仅检查了参考实现与文档，当时尚未创建应用代码、安装依赖、执行真实登录或下载，也未运行平台测试或 Actions。原讲座项目未修改。
