from __future__ import annotations

import sys
import asyncio
import os
import subprocess
import webbrowser
from pathlib import Path

import httpx
from textual import events, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.theme import Theme
from textual.widgets import Button, Collapsible, Input, LoadingIndicator, Static
from rich.text import Text

from .service import BrowserSetup, LoginRequired, PRIVACY, TERMS, Session, UserError


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for parent in executable.parents:
            if parent.suffix == ".app":
                return parent.parent
        return executable.parent
    return Path(__file__).resolve().parents[1]


class DownloaderApp(App[None]):
    TITLE = "微信视频号下载"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [("ctrl+q", "quit", "退出"), ("ctrl+r", "retry", "重试"),
                ("ctrl+o", "open_downloads", "下载目录"), ("ctrl+g", "github", "GitHub")]
    CSS = """
    Screen { background: #080f13; color: #e7f5ee; }
    #brand { height: auto; padding: 1 3; background: #101f24; border-left: thick #19f58b; }
    #brand-title { color: #19f58b; text-style: bold; height: 1; }
    #brand-note { color: #8ca7a5; height: 1; }
    #body { height: 1fr; }
    #content { width: 100%; max-width: 100; height: auto; margin: 1 2; padding: 1 2;
               background: #101f24; border-top: solid #19f58b; }
    #body { align: center middle; }
    #stage { height: 1; color: #32dbe8; text-style: bold; margin-bottom: 1; }
    #status { height: auto; margin-bottom: 1; }
    #loading { height: 3; color: #19f58b; }
    #qr-wrap { height: auto; align-horizontal: center; }
    #qr { height: auto; width: auto; color: black; background: white; }
    #terms { height: auto; margin-top: 1; color: #b4c9c7; }
    #entry { height: auto; }
    #input-label { height: 1; color: #8ca7a5; }
    Input { height: 3; margin: 1 0; border: tall #32dbe8; background: #080f13; }
    Input:focus { border: tall #19f58b; }
    #actions { height: auto; }
    Button { margin-right: 1; min-width: 16; }
    #download { background: #19f58b; color: #052416; text-style: bold; }
    #approve { width: 100%; margin-top: 1; }
    #result { height: auto; margin-bottom: 1; color: #b4c9c7; }
    #details { height: auto; margin-top: 1; }
    #error-details { height: auto; }
    #bottom { height: auto; padding: 0 3 1 3; }
    #utility { height: auto; }
    #repository { height: auto; width: 1fr; color: #8ca7a5; }
    #repository-name { color: #32dbe8; height: auto; }
    #repository-note { height: auto; }
    .compact #content { margin: 0; padding: 1; }
    .compact #brand { padding: 0 1; }
    .compact #bottom { padding: 0 1; }
    .compact #utility { layout: vertical; }
    .compact #actions { layout: vertical; }
    .compact Button { margin-bottom: 1; }
    """

    def __init__(self, *, root: Path | None = None, transport: httpx.AsyncBaseTransport | None = None,
                 browser_setup: BrowserSetup | None = None) -> None:
        super().__init__()
        self.register_theme(Theme(name="channels", primary="#19f58b", secondary="#32dbe8",
                                  accent="#32dbe8", foreground="#e7f5ee", background="#080f13",
                                  surface="#101f24", panel="#142a2d", success="#19f58b",
                                  warning="#ffd166", error="#ff6b7a"))
        self.theme = "channels"
        self.session = Session(root or application_root(), transport, browser_setup)
        self.approval = asyncio.Event()
        self.busy = False
        self.retry_download = False

    def compose(self) -> ComposeResult:
        with Vertical(id="brand"):
            yield Static("微信视频号下载  /  CHANNELS", id="brand-title")
            yield Static("保存每一份值得留下的内容", id="brand-note")
        with VerticalScroll(id="body"):
            with Vertical(id="content"):
                yield Static("环境检测", id="stage")
                yield LoadingIndicator(id="loading")
                yield Static("环境检测中…", id="status", markup=False)
                with Horizontal(id="qr-wrap"):
                    yield Static("", id="qr", markup=False)
                yield Static(f"本次操作用于元宝账号登录或注册，请阅读后决定是否同意。\n服务协议：{TERMS}\n隐私协议：{PRIVACY}", id="terms", markup=False)
                yield Button("同意元宝协议并继续登录/注册", id="approve")
                with Vertical(id="entry"):
                    yield Static("视频号分享链接", id="input-label")
                    yield Input(placeholder="粘贴 https://weixin.qq.com/sph/...", disabled=True)
                yield Static("", id="result", markup=False)
                with Collapsible(title="查看失败详情", collapsed=True, id="details"):
                    yield Static("", id="error-details", markup=False)
                with Horizontal(id="actions"):
                    yield Button("下载 · Enter", id="download", disabled=True)
                    yield Button("重试 · Ctrl+R", id="retry")
                    yield Button("下载目录 · Ctrl+O", id="folder", disabled=True)
        with Vertical(id="bottom"):
            with Horizontal(id="utility"):
                with Vertical(id="repository"):
                    yield Static("MuZiJin701/wechat-channels-downloader", id="repository-name")
                    yield Static("喜欢这个工具？来 GitHub 点个 Star  ·  Tab 切换操作", id="repository-note")
                yield Button("GitHub · Ctrl+G", id="github")
                yield Button("退出 · Ctrl+Q", id="quit")

    def show_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def on_mount(self) -> None:
        self.screen.set_class(self.size.width < 72, "compact")
        self.connect()

    def on_resize(self, event: events.Resize) -> None:
        self.screen.set_class(event.size.width < 72, "compact")

    def action_github(self) -> None:
        try:
            if not webbrowser.open("https://github.com/MuZiJin701/wechat-channels-downloader", new=2):
                self.notify("请访问 github.com/MuZiJin701/wechat-channels-downloader", title="无法打开浏览器")
        except OSError:
            self.notify("请访问 github.com/MuZiJin701/wechat-channels-downloader", title="无法打开浏览器")

    def action_open_downloads(self) -> None:
        folder = self.session.root / "downloads"
        try:
            if not folder.is_dir():
                raise OSError
            if sys.platform == "win32":
                os.startfile(folder)
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(folder)])
        except OSError:
            self.notify("请手动打开程序旁的 downloads 目录。", title="无法打开下载目录", severity="warning")

    def action_retry(self) -> None:
        if not self.busy and self.query_one("#retry").display:
            if self.retry_download:
                self.download(self.query_one(Input).value.strip())
            else:
                self.connect()

    def show_qr(self, image: Text) -> None:
        self.query_one("#loading").display = False
        self.query_one("#stage", Static).update("微信扫码")
        self.query_one("#qr-wrap").display = True
        if max(line.cell_len for line in image.split("\n")) > min(100, self.size.width - 4) - 6:
            raise UserError("登录失败：终端过窄，请放大窗口后重新登录。")
        self.query_one("#qr", Static).update(image)
        rows = len(image.split("\n")) + 18
        if self.size.height < rows:
            self.show_status(f"请增大终端至至少 {rows} 行，完整显示下方二维码后用微信扫码。")

    def confirm_registration(self) -> None:
        button = self.query_one("#approve", Button)
        button.display = True
        self.query_one("#terms").display = True
        self.call_after_refresh(button.focus)

    @work(exclusive=True, group="login")
    async def connect(self) -> None:
        self.busy = True
        self.retry_download = False
        try:
            for selector in ("#retry", "#entry", "#download", "#qr-wrap", "#terms", "#approve", "#result", "#details"):
                self.query_one(selector).display = False
            self.query_one("#loading").display = True
            self.query_one("#stage", Static).update("环境检测")
            self.show_status("环境检测中…")
            self.query_one(Input).disabled = True
            self.query_one("#download", Button).disabled = True
            self.approval.clear()
            self.query_one("#qr", Static).update("")
            if self.session.playwright:
                await self.session.close()
                self.session = Session(self.session.root, self.session.transport, self.session.browser_setup)
            await self.session.open()
            self.query_one("#folder", Button).disabled = False
            if not await self.session.authenticated():
                await self.session.login(self.show_status, self.show_qr, self.confirm_registration, self.approval)
            self.query_one("#qr", Static).update("")
            self.query_one("#qr-wrap").display = False
            self.query_one("#terms").display = False
            self.query_one("#approve").display = False
            self.show_status("登录态有效，请输入视频号分享链接。")
            self.query_one("#stage", Static).update("准备就绪")
            self.query_one("#entry").display = True
            self.query_one("#download").display = True
            self.query_one(Input).disabled = False
            self.query_one("#download", Button).disabled = False
            self.query_one(Input).focus()
        except Exception as error:
            self.show_status(str(error) if isinstance(error, UserError) else "环境检测或登录失败，请检查网络和程序文件后重试。")
            self.query_one("#stage", Static).update("暂时无法继续")
            self.query_one("#qr-wrap").display = False
            self.query_one("#approve").display = False
            self.query_one("#retry").display = True
        finally:
            self.busy = False
            if self.is_running:
                self.query_one("#loading").display = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not event.input.disabled:
            self.download(event.value.strip())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "download":
            self.download(self.query_one(Input).value.strip())
        elif event.button.id == "retry":
            self.action_retry()
        elif event.button.id == "approve":
            self.approval.set()
            event.button.display = False
        elif event.button.id == "folder":
            self.action_open_downloads()
        elif event.button.id == "github":
            self.action_github()
        elif event.button.id == "quit":
            await self.action_quit()

    @work(exclusive=True, group="download")
    async def download(self, link: str) -> None:
        if self.busy:
            return
        self.busy = True
        self.retry_download = True
        self.query_one("#retry").display = False
        self.query_one("#result").display = False
        self.query_one("#details").display = False
        self.query_one("#details", Collapsible).collapsed = True
        self.query_one("#loading").display = True
        self.query_one("#stage", Static).update("正在下载")
        self.query_one(Input).disabled = True
        self.query_one("#download", Button).disabled = True
        try:
            archive = await self.session.download(link, self.show_status)
            errors = archive.errors + [f"{item.label}：{item.error}" for item in archive.media if item.error]
            self.query_one("#stage", Static).update("下载" + archive.state)
            self.show_status("下载" + archive.state + ("：" + errors[0] if errors else "，继续粘贴链接即可。"))
            self.query_one("#result", Static).update("保存位置：" + str(archive.path))
            self.query_one("#result").display = True
            if errors:
                self.query_one("#error-details", Static).update("\n".join(errors))
                self.query_one("#details").display = True
            if archive.state == "完成":
                self.query_one(Input).value = ""
            else:
                self.query_one("#retry").display = True
        except Exception as error:
            message = ("保存失败：请检查程序旁下载目录的写入权限和可用空间；已有文件保留。" if isinstance(error, OSError)
                       else str(error) if isinstance(error, UserError) else "解析或下载失败，请检查网络后重试。")
            if isinstance(error, LoginRequired):
                self.retry_download = False
            self.show_status(message)
            self.query_one("#stage", Static).update("下载未完成")
            self.query_one("#retry").display = True
        finally:
            self.busy = False
            if self.is_running:
                self.query_one("#loading").display = False
                self.query_one(Input).disabled = not self.retry_download
                self.query_one("#entry").display = self.retry_download
                self.query_one("#download").display = self.retry_download
                self.query_one("#download", Button).disabled = not self.retry_download
                if self.retry_download:
                    self.query_one(Input).focus()

    async def on_unmount(self) -> None:
        await self.session.close()


def main() -> None:
    DownloaderApp().run()
