# 微信视频号下载

[English](README.en.md) · [下载最新版](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest)

**把视频号的视频和图文保存到电脑，随时离线查看。**

需要时用微信扫码，粘贴一条分享链接，点击下载。无需安装 Python，也无需另外配置浏览器。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/深色模式使用截图.png">
  <img src="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/浅色模式使用截图.png" alt="微信视频号下载：粘贴分享链接即可下载，支持浅色和深色外观" width="960">
</picture>

## 能做什么

- **视频、图文都能保存**：下载可取得的视频版本、按顺序排列的图片，以及封面、背景音乐等附件。
- **正文和来源一起保留**：每条内容生成一个本地浏览页面，方便回看。
- **下载结果看得清楚**：部分文件失败时保留已下载的内容，并列出缺失项；重复下载会新建文件夹，不覆盖旧文件。

## 1. 下载并打开

到 [Releases 下载页面](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest)，选择适合自己电脑的文件：

| 电脑 | 下载文件名的结尾 | 解压后打开 |
| --- | --- | --- |
| Windows 11，64 位 | `windows-x64.zip` | `wechat-channels-downloader.exe` |
| Mac，Apple 芯片 | `darwin-arm64.tar.gz` | `wechat-channels-downloader.app` |
| Mac，Intel 芯片 | `darwin-x64.tar.gz` | `wechat-channels-downloader.app` |
| Ubuntu 24.04，64 位 | `linux-x64.tar.gz` | `wechat-channels-downloader.desktop` |

Mac 需要 macOS 14 或更新版本；可在“关于本机”查看芯片类型。各平台的实际验证范围见[验证记录](docs/validation.md)。

**先完整解压，再打开程序。** 保留解压后的所有文件和文件夹，不能只拿走一个 EXE 或 `.app`。Windows 路径请避开分号 `;`，例如可以放在 `D:\Videos\Channels`。包内已带浏览器，因此文件较大。

程序打开的是可点击的终端界面。macOS 首次打开可能出现来源或终端控制权限提示；目前应用未签名、公证，请先确认下载来源。Ubuntu 桌面可能需要先允许启动；缺少系统运行库时请查看[开发与排查指南](docs/development.md)。

## 2. 扫码、粘贴、下载

1. 打开程序，等待“环境检测中”结束。
2. 如果出现二维码，用微信扫码并在手机上确认。已有有效登录信息时会跳过这一步。扫码用于腾讯元宝登录；需要确认账号条款时，程序会先说明并等待你的选择。
3. 复制一条以 `https://weixin.qq.com/sph/` 开头的视频号分享链接，粘贴到输入框。
4. 点击“下载”，或在输入框按 **Enter**。等待界面显示下载结果。

二维码显示不全时，把窗口放大。右上角“外观”可以选择跟随系统、浅色或深色，下次打开会记住选择。

## 3. 查看保存的内容

点击“下载目录”，就能找到程序旁边的 `downloads` 文件夹。每条内容放在单独的文件夹中，名称通常由作者和正文开头组成。

打开其中的 **`index.html`**，即可查看正文、作者、发布时间和已保存的媒体。视频或图片文件也可以直接打开；`parse.json`、`feed.json` 是保留的原始信息，一般不需要打开。

显示“部分完成”时，请展开失败详情：成功的文件已经保留，可以稍后重试。视频在浏览页面中无法播放时，试试用电脑上的视频播放器打开视频文件。

## 常见问题

**能一次下载整个账号吗？** 目前一次处理一条分享链接，不支持账号全部历史、批量队列或直播录制。保存范围取决于服务实际提供的内容，不保证原片、评论正文或字幕。

**扫码或下载失败怎么办？** 先检查网络，再点击“重试”。如果仍然失败，到 [Issues 反馈](https://github.com/MuZiJin701/wechat-channels-downloader/issues)，附上系统版本和不含隐私的错误说明。

**为什么有些终端没有 Logo 图片？** 图片显示取决于终端能力；不支持时会显示简洁文字版，下载功能照常使用。运行中修改终端字号或屏幕缩放后，请重启程序。

**登录信息放在哪里？** 程序旁的 `data` 文件夹保存登录信息和外观选择；Mac 上它在 `.app` 外面。请勿公开分享 `data`，下载目录中的原始信息也可能含临时访问链接。需要重新扫码时，先关闭程序，再删除 `data/session.json`。

## 常用快捷键

| 操作 | 快捷键 |
| --- | --- |
| 开始下载 | 输入框内 Enter |
| 重试 | Ctrl+R |
| 打开下载目录 | Ctrl+O |
| 退出 | Ctrl+Q |

## 更多信息

[文档导航](docs/README.md) · [源码运行与开发](docs/development.md) · [第三方声明](THIRD_PARTY_NOTICES.md)
