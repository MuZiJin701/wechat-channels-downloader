# WeChat Channels Downloader

[简体中文](README.md)

A portable TUI for Windows, Linux, and macOS. It checks the Yuanbao session, displays a WeChat login QR code when necessary, and downloads the video or image post addressed by a `https://weixin.qq.com/sph/...` share link. Image posts retain all images in order and their available text. No transcoding or OCR is performed.

## Portable packages

Extract the entire package and keep its contents together. No Python installation or additional browser is required. Bundled Chromium makes the package relatively large.

- Windows: double-click `wechat-channels-downloader.exe`.
- macOS: double-click `微信视频号下载.command`. Intel and Apple Silicon packages are built separately. Apple signing and notarization have not been performed.
- Ubuntu desktop: use `微信视频号下载.desktop`. The desktop environment may require allowing the launcher to run; Chromium's system libraries must be available. Actual desktop double-click behavior still needs manual acceptance.

On a Linux server, use an SSH session with a terminal allocated, enter the extracted directory, and run `./wechat-channels-downloader`. To launch directly from another machine, use `ssh -t host 'cd extracted-directory && ./wechat-channels-downloader'`. The program uses the current terminal; it does not bundle a terminal emulator.

On startup, valid sessions are reused. Otherwise, scan the QR code with WeChat and confirm on your phone. Enlarge the terminal as prompted if the complete QR code is not visible. If Yuanbao explicitly requires agreement before registration/login, the TUI presents a confirmation button. Additional security verification stops the flow with a message.

The program waits for the WeChat login dialog, using it when it opens automatically and trying the login entry otherwise. It avoids waiting indefinitely to click a homepage button covered by that dialog.

Paste one share link, then press Enter or select “下载”. The TUI shows the current stage and the completed output location. Correct an invalid link or use “重新检查 / 扫码登录” after failure. Ctrl+Q exits.

On Linux/macOS, the original terminal attributes are restored after Playwright subprocess cleanup. If an older package or forced termination leaves typed commands invisible, type `stty sane` blindly and press Enter; use `reset` if needed, or Ctrl+J if Enter does not work. Forced termination such as SIGKILL cannot guarantee cleanup.

Session data is stored beside the program in `data/session.json`; downloads are stored in `downloads/`. If placed in a macOS application bundle, data is located outside the bundle. Moving the program and its data together is possible, but sessions are revalidated and may not survive moving between machines or operating systems. An unwritable location produces an error without silently falling back elsewhere.

Session files and temporary `data/login-qr.png` are sensitive local data. The QR image is removed when login ends. Do not publish or share the data directory. Delete `data/session.json` to require a fresh scan on the next startup.

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

On Linux/macOS, the full suite also opens a real PTY, starts the offline TUI and Chromium, presses Ctrl+Q, and checks that echo, canonical input, and all other terminal attributes match their original values. Windows explicitly skips this POSIX check. To check the source entry separately:

```sh
uv run --locked python tools/check_terminal.py "$PWD/.venv/bin/python" "$PWD/main.py"
```

This command uses `--terminal-smoke-test` with an offline temporary session and exits automatically, without reading real accounts. Packaging runs the same check against the actual Linux/macOS executable.

The build script creates a platform-specific portable directory and archive under `dist/`, including Chromium, dependencies, and third-party notices. It executes the packaged offline smoke check from a different working directory before creating the archive. Windows cannot cross-build the macOS or Linux package.

On macOS, the build copies Chromium's complete application directory and symbolic links into the package, preserving the browser's existing signature instead of letting PyInstaller rewrite its frameworks.

The build refuses to overwrite an existing output directory containing `data/` or `downloads/`; move the existing program and its data together first. It also checks the completed archive for these private directories, cancelling archive creation while preserving local data if either is found.

The GitHub Actions workflow targets Ubuntu 24.04 x64, macOS 14 arm64, and macOS 15 Intel. It runs type checking, tests, packaging, bundled Chromium/TUI startup, and PTY exit restoration before uploading archives. Run links and their corresponding code versions appear in the [validation record](docs/validation.md). Intel macOS 15 success does not establish macOS 14 compatibility.

See the [validation record](docs/validation.md) for executed checks and remaining acceptance work. Real QR login, online downloads, and file-manager double-click behavior need separate acceptance.

## Documentation

- [Spec #1](https://github.com/MuZiJin701/wechat-channels-downloader/issues/1) / [local specification](docs/spec.md)
- [Requirements interview](docs/requirements.md), [glossary](GLOSSARY.md), and [architecture decisions](docs/adr/)
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues) / [agent conventions](AGENTS.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md): the reference resolver includes the Commons Clause and must not be described as unrestricted MIT.

Edit `docs/agents/*.md` directly to adjust engineering skill configuration. Run setup-matt-pocock-skills again only to switch trackers or restart setup.
