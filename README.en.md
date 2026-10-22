# WeChat Channels Downloader

[简体中文](README.md)

A portable WeChat Channels downloader for Windows, Linux, and macOS. Scan with WeChat when needed, then paste a single `https://weixin.qq.com/sph/...` share link to archive its post. It saves all returned video versions, post images, covers, author avatars, certification icons, and background music, together with an offline HTML page and both complete JSON responses. No transcoding, OCR, or generated notes are performed.

## Portable packages

Extract the entire package and keep its contents together. No Python installation or additional browser is required. Bundled Chromium makes the package relatively large.

On Windows, avoid semicolons (`;`) in the extraction path: the current packaged runtime cannot load required DLLs there. Chinese characters, spaces, and other common path characters have separate offline artifact checks.

- Windows: double-click `wechat-channels-downloader.exe`. The windowless launcher requests a separate Windows Terminal window directly, preferring PowerShell 7 (`pwsh`), then Windows PowerShell, then cmd, without creating a traditional console first. If Windows Terminal is unavailable or cannot launch, it falls back to the system console. It does not install software or change system defaults.
- macOS: double-click the branded `wechat-channels-downloader.app` launcher to open Terminal with the same TUI. Keep the entire extracted directory together; do not move only the launcher. First launch may require permission to open the app or control Terminal. Intel and Apple Silicon packages are built separately. Apple signing and notarization have not been performed.
- Ubuntu desktop: use `wechat-channels-downloader.desktop`. The desktop environment may require allowing the launcher to run; Chromium's system libraries must be available. Desktop icons require absolute paths, so first launch and the next launch after moving the directory refresh this launcher's icon reference; refreshing the file manager may also be necessary. Actual desktop double-click behavior still needs manual acceptance.

In an existing terminal, run `./wechat-channels-downloader-cli.exe` on Windows or `./wechat-channels-downloader` on Linux/macOS to reuse that terminal. Both entry methods share the TUI, Chromium, and portable data. Keep both Windows EXEs beside `_internal/`; the CLI entry lets the invoking shell wait correctly for exit.

The interface offers sage-green light and forest-green dark themes, with a play-and-save logo and a static gradient in the brand area. Success, warnings, and errors keep distinct semantic colors and text. The top appearance selector supports mouse and keyboard with three modes: follow system, light, and dark. First launch follows the system; changes apply immediately and are saved without interrupting login or downloads, or clearing input and results.

Automatic mode checks the executing machine's OS appearance roughly every two seconds: the Windows application-theme preference, macOS appearance, or Ubuntu/GNOME desktop color preference. Missing desktop settings or query tools fall back to light, with manual selection available. SSH does not inspect the client computer's theme. Manual light/dark remains fixed until follow-system is selected again. Global terminal settings are not changed.

Content expands with larger windows; smaller windows reduce whitespace and rearrange actions and the appearance selector, with scrolling when needed. QR codes stay static black and white and request a larger window when necessary. The terminal's font size is retained. Truecolor terminals can display gradients; other terminals may show color banding. An existing `NO_COLOR` setting is respected.

The footer text link `GitHub · MuZiJin701/wechat-channels-downloader ↗` opens by clicking or focusing with Tab / Shift+Tab and pressing Enter. There is no dedicated GitHub button or shortcut.

On a Linux server, use an SSH session with a terminal allocated, enter the extracted directory, and run `./wechat-channels-downloader`. To launch directly from another machine, use `ssh -t host 'cd extracted-directory && ./wechat-channels-downloader'`. The program uses the current terminal; it does not bundle a terminal emulator.

Startup displays an environment check. Valid sessions go straight to the link input; missing or explicitly expired sessions show a centered WeChat QR code, followed by the input after login. Network errors offer retry without clearing the previous session. Enlarge the terminal as prompted if the QR code is incomplete. If the service requires account agreement before registration/login, the TUI identifies the actual service and waits for explicit confirmation. Additional security verification stops the flow with a message.

The program waits for the WeChat login dialog, using it when it opens automatically and trying the login entry otherwise. It avoids waiting indefinitely to click a homepage button covered by that dialog.

Paste one share link, then press Enter or click “下载”. The interface keeps only the latest result, stage, and save location, with expandable failure details. Complete success clears and focuses the input; failures and partial results retain the link. Duplicate submissions are disabled during downloads. Buttons display shortcuts without using function keys:

| Action | Shortcut |
| --- | --- |
| Download | Enter in the input |
| Retry the failed operation | Ctrl+R |
| Open downloads | Ctrl+O |
| Select all input text | Ctrl+A in the input |
| Quit | Ctrl+Q |
| Move focus / activate a button | Tab, Shift+Tab / Enter, Space |

The single-line text field shows “粘贴视频号分享链接” when empty, without an example URL. Click to position the cursor or drag to select; Home / End, arrows, Shift selection, Backspace, Delete, copy, cut, and paste are supported. The application does not turn the input into a hyperlink. A native blinking bar caret appears when the input is focused and its insertion point is visible, hides when unfocused or covered, and resets to the terminal's configured default shape on normal exit. Rendering and blinking remain terminal-dependent. System clipboard paste and host link detection for actual URLs still need acceptance in Windows Terminal or the target terminal.

On Windows, the caret color also temporarily matches the app theme so manually selecting dark inside a light terminal keeps the caret legible. Normal exit resets the host's default cursor color without writing terminal settings.

Every run creates a new `author_excerpt` directory under `downloads/`. Chinese names are retained; absent authors are omitted and missing text falls back to the share identifier. Invalid characters are cleaned and long names shortened while preserving the full original text. Media names reuse the prefix and identify purpose, order, or codec. Collisions add a numeric suffix without overwriting previous downloads. Each directory contains:

- Returned media: every distinct video version, ordered images, and attachments. Identical URLs are downloaded once. Extensions follow the actual media type.
- `index.html`: double-click to read the original text, author, UTC time, interaction display values as queried, other available information, and local media. Remote media URLs are not needed. If a browser cannot play a codec, use the file link with a local player.
- `parse.json` and `feed.json`: complete parsing and post responses, linked as “解析原始数据” and “动态原始数据” on the offline page, created only when the corresponding response was obtained. Unknown fields remain unchanged; no TXT is generated. Existing archives and their older filenames are left intact.

The TUI reports “完成” when complete. Individual failures do not stop other transfers; saved files are retained, the result is “部分完成”, and HTML lists missing items. If all media fail, obtained information remains with a “失败” result. Normal quitting during transfer retains complete files and available information, marks HTML “已中断”, and removes incomplete files. Retrying creates a new directory. Unwritable storage is reported explicitly; forced termination or power loss cannot guarantee the final record is written.

Only content returned by the current interfaces is archived. Missing optional resources are omitted; comment bodies, original upload masters, separate subtitles, or account history are not promised. Multiple video versions use additional disk space.

On Linux/macOS, the original terminal attributes are restored after Playwright subprocess cleanup. If an older package or forced termination leaves typed commands invisible, type `stty sane` blindly and press Enter; use `reset` if needed, or Ctrl+J if Enter does not work. Forced termination such as SIGKILL cannot guarantee cleanup.

Session data is stored beside the program in `data/session.json`, the theme mode separately in `data/appearance.json`, and downloads in `downloads/`. These directories are outside the macOS `.app` launcher. Deleting `appearance.json` restores follow-system without affecting login; invalid preferences also fall back to automatic mode. Save failures report a warning while keeping the current appearance. Moving the program and its data together is possible, but sessions are revalidated and may not survive moving between machines or operating systems. An unwritable location produces an error without silently falling back elsewhere.

Session files and temporary `data/login-qr.png` are sensitive local data. The QR image is removed when login ends. Do not publish or share the data directory. Delete `data/session.json` to require a fresh scan on the next startup.

Archive JSON may contain expiring media addresses and access parameters. Keep it local and out of public logs, repositories, and distribution packages. Login credentials are not sent with media requests to other domains.

## Run from source

Use uv with Python 3.11 and a project-local environment:

```sh
uv sync --locked
uv run --locked playwright install chromium
uv run --locked python main.py
```

The application uses Playwright-managed Chromium rather than system Chrome or ChromeDriver. Development setup downloads Chromium; portable packages use their bundled browser without installing system software.

## Checks and packaging

```sh
uv run --locked mypy
uv run --locked python -m unittest discover -s tests -v
uv run --locked python main.py --smoke-test
uv run --locked python tools/build.py
```

Tests exercise the TUI workflow with real headless Chromium, temporary directories, and simulated external Yuanbao, WeChat, and media services. Offline smoke checks neither use real accounts nor access the internet.

On Linux/macOS, the full suite also opens a real PTY, starts the offline TUI and Chromium, presses Ctrl+Q, and checks that echo, canonical input, and all other terminal settings match their original values. On macOS only, it excludes the kernel-managed PENDIN pending-input state bit. Windows explicitly skips this POSIX check. To check the source entry separately:

```sh
uv run --locked python tools/check_terminal.py "$PWD/.venv/bin/python" "$PWD/main.py"
```

This command uses `--terminal-smoke-test` with an offline temporary session and exits automatically, without reading real accounts. Packaging runs the same check against the actual Linux/macOS executable.

The build script creates a platform-specific portable directory and archive under `dist/`, including Chromium, dependencies, and third-party notices. Only the two README documents remain at the top level; notices and licenses are under `_internal/`, and development documents are excluded. Development-document links in the packaged READMEs point to the public repository. It executes the packaged offline smoke check from a different working directory before creating the archive. Windows cannot cross-build the macOS or Linux package.

On macOS, the build copies Chromium's complete application directory and symbolic links into the package, preserving the browser's existing signature instead of letting PyInstaller rewrite its frameworks.

Logo assets are in `downloader/assets/`. After changing the drawing, run `uv run --locked python tools/draw_logo.py` to regenerate PNG, Windows ICO, and macOS ICNS with the existing Pillow dependency. The TUI renders the same shape with colored character blocks; individual controls do not use the logo. Packaging includes the assets, and macOS builds additionally check the launcher shell syntax and compile its AppleScript. Actual Finder/Terminal interaction requires manual acceptance.

The build refuses to overwrite an existing output directory containing `data/` or `downloads/`; move the existing program and its data together first. It also checks the completed archive for these private directories, cancelling archive creation while preserving local data if either is found.

The GitHub Actions workflow targets Ubuntu 24.04 x64, macOS 14 arm64, and macOS 15 Intel. It runs type checking, tests, packaging, bundled Chromium/TUI startup, and PTY exit restoration before uploading archives. Run links and their corresponding code versions appear in the [validation record](docs/validation.md). Intel macOS 15 success does not establish macOS 14 compatibility.

See the [validation record](docs/validation.md) for executed checks and remaining acceptance work. Real QR login, online downloads, and file-manager double-click behavior need separate acceptance.

## Documentation

- Complete archiving and terminal experience: [Spec #2](https://github.com/MuZiJin701/wechat-channels-downloader/issues/2) / [local specification](docs/spec.md); [initial Spec #1](https://github.com/MuZiJin701/wechat-channels-downloader/issues/1)
- [Requirements interview](docs/requirements.md), [glossary](GLOSSARY.md), and [architecture decisions](docs/adr/)
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues) / [agent conventions](AGENTS.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md): the reference resolver includes the Commons Clause and must not be described as unrestricted MIT.

Edit `docs/agents/*.md` directly to adjust engineering skill configuration. Run setup-matt-pocock-skills again only to switch trackers or restart setup.
