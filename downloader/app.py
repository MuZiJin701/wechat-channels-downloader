from __future__ import annotations

import sys
import asyncio
from pathlib import Path

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Static
from rich.text import Text

from .service import BrowserSetup, PRIVACY, TERMS, Session, UserError


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
    BINDINGS = [("ctrl+q", "quit", "退出")]
    CSS = """
    Screen { align: center top; }
    #content { width: 100%; max-width: 110; padding: 1 2; }
    #status { height: auto; margin: 1 0; }
    #qr { height: auto; width: auto; color: black; background: white; }
    Input { margin: 1 0; }
    Button { margin: 0 1 1 0; }
    """

    def __init__(self, *, root: Path | None = None, transport: httpx.AsyncBaseTransport | None = None,
                 browser_setup: BrowserSetup | None = None) -> None:
        super().__init__()
        self.theme = "ansi-dark"
        self.session = Session(root or application_root(), transport, browser_setup)
        self.approval = asyncio.Event()

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="content"):
            yield Static("正在启动 Chromium 并检查元宝登录态…", id="status", markup=False)
            yield Static("", id="qr", markup=False)
            yield Static(f"扫码用于元宝登录，可能涉及账号注册。\n服务协议：{TERMS}\n隐私协议：{PRIVACY}", id="terms", markup=False)
            yield Button("同意元宝协议并继续登录/注册", id="approve")
            yield Button("重新检查 / 扫码登录", id="retry")
            yield Input(placeholder="粘贴 https://weixin.qq.com/sph/...", disabled=True)
            yield Button("下载", id="download", variant="primary", disabled=True)
        yield Footer()

    def show_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def on_mount(self) -> None:
        self.query_one("#terms").display = False
        self.query_one("#approve").display = False
        self.query_one("#retry").display = False
        self.connect()

    def show_qr(self, image: Text) -> None:
        if max(line.cell_len for line in image.split("\n")) > self.size.width - 6:
            raise UserError("登录失败：终端过窄，请放大窗口后重新登录。")
        self.query_one("#qr", Static).update(image)
        self.query_one("#terms").display = True
        rows = len(image.split("\n")) + 8
        if self.size.height < rows:
            self.show_status(f"请增大终端至至少 {rows} 行，完整显示下方二维码后用微信扫码。")

    def confirm_registration(self) -> None:
        button = self.query_one("#approve", Button)
        button.display = True
        self.query_one("#terms").display = True
        self.call_after_refresh(button.focus)

    @work(exclusive=True, group="login")
    async def connect(self) -> None:
        try:
            self.query_one("#retry").display = False
            self.query_one(Input).disabled = True
            self.query_one("#download", Button).disabled = True
            self.approval.clear()
            self.query_one("#qr", Static).update("")
            self.query_one("#terms").display = False
            if self.session.playwright:
                await self.session.close()
                self.session = Session(self.session.root, self.session.transport, self.session.browser_setup)
            await self.session.open()
            if not await self.session.authenticated():
                await self.session.login(self.show_status, self.show_qr, self.confirm_registration, self.approval)
            self.query_one("#qr", Static).update("")
            self.query_one("#terms").display = False
            self.query_one("#approve").display = False
            self.show_status("登录态有效，请输入视频号分享链接。")
            self.query_one(Input).disabled = False
            self.query_one("#download", Button).disabled = False
            self.query_one(Input).focus()
        except Exception as error:
            self.show_status(str(error) if isinstance(error, UserError) else f"启动或登录检查失败（{type(error).__name__}），请检查网络和 Chromium。")
            self.query_one("#approve").display = False
            self.query_one("#retry").display = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not event.input.disabled:
            self.download(event.value.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "download":
            self.download(self.query_one(Input).value.strip())
        elif event.button.id == "retry":
            self.connect()
        elif event.button.id == "approve":
            self.approval.set()
            event.button.display = False

    @work(exclusive=True, group="download")
    async def download(self, link: str) -> None:
        self.query_one("#retry").display = False
        self.query_one(Input).disabled = True
        self.query_one("#download", Button).disabled = True
        try:
            archive = await self.session.download(link, self.show_status)
            errors = archive.errors + [f"{item.label}：{item.error}" for item in archive.media if item.error]
            self.show_status(f"下载{archive.state}：{archive.path}" + ("；" + "；".join(errors) if errors else ""))
        except Exception as error:
            message = ("保存失败：请检查程序旁下载目录的写入权限和可用空间；已有文件保留。" if isinstance(error, OSError)
                       else str(error) if isinstance(error, UserError) else "解析或下载失败，请检查网络后重试。")
            self.show_status(message)
            self.query_one("#retry").display = True
        finally:
            self.query_one(Input).disabled = False
            self.query_one("#download", Button).disabled = False
            self.query_one(Input).focus()

    async def on_unmount(self) -> None:
        await self.session.close()


def main() -> None:
    DownloaderApp().run()
