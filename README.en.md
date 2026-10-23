# WeChat Channels Downloader

[简体中文](README.md) · [Download the latest version](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest)

**Download videos and image posts from WeChat Channels.**

Scan with WeChat when prompted, paste a Channels share link, and click Download. The app's interface is in Chinese.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/深色模式使用截图.png">
  <img src="https://raw.githubusercontent.com/MuZiJin701/wechat-channels-downloader/main/docs/images/浅色模式使用截图.png" alt="WeChat Channels Downloader: paste a share link to download, with light and dark appearances" width="960">
</picture>

## What you can download

- Download videos, post images, and available attachments such as covers and background music.
- Keep the text, author, and publication time, with a viewing page for each post.

## 1. Download and open

Visit the [Releases page](https://github.com/MuZiJin701/wechat-channels-downloader/releases/latest) and choose the file for your computer:

| Computer | Filename ending | Open after extraction |
| --- | --- | --- |
| Windows 11, 64-bit | `windows-x64.zip` | `wechat-channels-downloader.exe` |
| Mac, Apple Silicon | `darwin-arm64.tar.gz` | `wechat-channels-downloader.app` |
| Mac, Intel | `darwin-x64.tar.gz` | `wechat-channels-downloader.app` |
| Ubuntu 24.04, 64-bit | `linux-x64.tar.gz` | `wechat-channels-downloader.desktop` |

Mac requires macOS 14 or later. Check About This Mac to identify your chip. See the [validation record](docs/validation.md) for the systems actually tested.

**Extract everything before opening the app.** Keep all files and folders together; do not move just the EXE or `.app`. On Windows, avoid semicolons (`;`) in the extraction path.

The app opens a clickable terminal interface. On macOS, first launch may show an app-source or Terminal-control permission prompt. The app is currently unsigned and not notarized, so confirm the download source first. Ubuntu may require allowing the desktop launcher to run. For missing system libraries, see the [development and troubleshooting guide](docs/development.md).

## 2. Scan, paste, and download

1. Open the app and wait for the environment check (“环境检测中”) to finish.
2. If a QR code appears, scan it with WeChat and confirm on your phone. This signs you in to Tencent Yuanbao; follow the on-screen prompts. A valid saved session skips this step.
3. Copy one WeChat Channels share link beginning with `https://weixin.qq.com/sph/` and paste it into the input field.
4. Click **下载** (Download), or press **Enter** in the input field. Wait for the result.

Enlarge the window if the QR code is cut off. The top-right **外观** (Appearance) selector offers system, light, and dark modes and remembers your choice.

## 3. View your downloads

Click **下载目录** (Downloads folder) to open `downloads` beside the program. Each post has its own folder. Downloading again creates a new folder without replacing previous files.

Open the videos and images directly, or open **`index.html`** in the same folder to view them alongside the text, author, and publication time.

If the result is **部分完成** (Partially complete), expand the failure details. Successful files have been kept, and you can retry later. If a video will not play on the viewing page, try opening the file in a video player on your computer.

## Common questions

**Can I download an entire account?** The app downloads one share link at a time. The results show which content was available to download.

**What if sign-in or downloading fails?** Check your connection and click **重试** (Retry). If it still fails, [open an issue](https://github.com/MuZiJin701/wechat-channels-downloader/issues) with your system version and an error description that does not contain private information.

**Why is there no logo image in my terminal?** Image support varies between terminals. A compact text header appears when images are unavailable; downloading still works. Restart the app after changing the terminal font size or display scaling while it is running.

**Why does light mode look gray or pink over SSH, with a banded gradient?** The SSH session may not advertise truecolor support. If your local terminal supports truecolor, such as Windows Terminal, quit with **Ctrl+Q**, then run this in the extracted folder on the server:

```sh
COLORTERM=truecolor ./wechat-channels-downloader
```

This applies only to this launch. See [SSH color troubleshooting](docs/development.md#ssh-颜色失真) (Chinese) for details.

**Where is my sign-in information?** The `data` folder beside the program stores your session and appearance choice. On Mac, it is outside the `.app`. Do not publish `data`; original information in download folders can also contain temporary access links. To sign in again, close the app and delete `data/session.json`.

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| Download | Enter in the input field |
| Retry | Ctrl+R |
| Open downloads | Ctrl+O |
| Quit | Ctrl+Q |

## More information

[Documentation index](docs/README.md) · [Run from source and develop](docs/development.md) (Chinese) · [Third-party notices](THIRD_PARTY_NOTICES.md)
