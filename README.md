# 微信视频号下载

[English](README.en.md) · [下载最新版](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest)

**下载微信视频号的视频和图文。**

按提示扫码登录，粘贴视频号分享链接，点击下载。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/深色模式使用截图.png">
  <img src="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/浅色模式使用截图.png" alt="微信视频号下载：粘贴分享链接即可下载，支持浅色和深色外观" width="960">
</picture>

## 能做什么

- 下载视频、图文图片，以及可取得的封面、背景音乐等附件。
- 保留正文、作者和发布时间，并生成浏览页面。

## 1. 下载并打开

到 [Releases 下载页面](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest)，选择适合自己电脑的文件：

| 电脑 | 下载文件名的结尾 | 解压后打开 |
| --- | --- | --- |
| Windows 11，64 位 | `windows-x64.zip` | `wechat-channels-downloader.exe` |
| Mac，Apple 芯片 | `darwin-arm64.tar.gz` | `wechat-channels-downloader.app` |
| Mac，Intel 芯片 | `darwin-x64.tar.gz` | `wechat-channels-downloader.app` |
| Ubuntu 24.04，64 位 | `linux-x64.tar.gz` | `wechat-channels-downloader.desktop` |

Mac 需要 macOS 14 或更新版本；可在“关于本机”查看芯片类型。各平台的实际验证范围见[验证记录](docs/validation.md)。

**先完整解压，再打开程序。** 保留解压后的所有文件和文件夹，不能只拿走一个 EXE 或 `.app`。Windows 解压路径请避开分号 `;`。

程序打开的是可点击的终端界面。macOS 首次打开可能出现来源或终端控制权限提示；目前应用未签名、公证，请先确认下载来源。Ubuntu 桌面可能需要先允许启动；缺少系统运行库时请查看[开发与排查指南](docs/development.md)。

## 2. 扫码、粘贴、下载

1. 打开程序，等待“环境检测中”结束。
2. 如果出现二维码，用微信扫码并在手机上确认。扫码用于腾讯元宝登录，请按界面提示操作；已有有效登录信息时会跳过这一步。
3. 复制一条以 `https://weixin.qq.com/sph/` 开头的视频号分享链接，粘贴到输入框。
4. 点击“下载”，或在输入框按 **Enter**。等待界面显示下载结果。

二维码显示不全时，把窗口放大。右上角“外观”可以选择跟随系统、浅色或深色，下次打开会记住选择。

## 3. 查看下载结果

点击“下载目录”，打开程序旁边的 `downloads` 文件夹。每条内容单独放在一个文件夹中，重复下载会新建文件夹，不覆盖旧文件。

视频和图片可以直接打开。打开同一文件夹中的 **`index.html`**，可一起查看正文、作者、发布时间和下载的内容。

显示“部分完成”时，请展开失败详情：成功的文件已经保留，可以稍后重试。视频在浏览页面中无法播放时，试试用电脑上的视频播放器打开视频文件。

## 常见问题

**能一次下载整个账号吗？** 目前一次下载一条分享链接，具体可下载的内容以结果为准。

**扫码或下载失败怎么办？** 先检查网络，再点击“重试”。如果仍然失败，到 [Issues 反馈](https://github.com/MuZiJin701/wechat-channels-downloader/issues)，附上系统版本和不含隐私的错误说明。

**为什么有些终端没有 Logo 图片？** 图片显示取决于终端能力；不支持时会显示简洁文字版，下载功能照常使用。运行中修改终端字号或屏幕缩放后，请重启程序。

**通过 SSH 运行时，为什么浅色变成灰粉色、渐变出现色块？** 可能是 SSH 会话没有声明支持真彩色。若本地使用 Windows Terminal 等支持真彩色的终端，先按 **Ctrl+Q** 退出，再在服务器的解压目录运行：

```sh
COLORTERM=truecolor ./wechat-channels-downloader
```

这只对本次启动生效，更多排查见[SSH 颜色说明](docs/development.md#ssh-颜色失真)。

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
