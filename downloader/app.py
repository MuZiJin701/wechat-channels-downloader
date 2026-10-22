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
from textual.geometry import Offset, Region, Size
from textual.errors import NoWidget
from textual.renderables.gradient import LinearGradient
from textual.widgets import Button, Collapsible, Input, Link, LoadingIndicator, Select, Static
from rich.text import Text

from .appearance import MODES, THEMES, load_mode, refresh_desktop_icon, save_mode, system_dark, terminal_logo
from .service import BrowserSetup, LoginRequired, PRIVACY, TERMS, Session, UserError


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for parent in executable.parents:
            if parent.suffix == ".app":
                return parent.parent
        return executable.parent
    return Path(__file__).resolve().parents[1]


class ShareLinkInput(Input):
    BINDINGS = [("ctrl+a", "select_all", "全选")]

    @property
    def _cursor_offset(self) -> int:
        # Textual reserves an extra cell at the end for its painted block cursor.
        return super()._cursor_offset - int(self.cursor_at_end)

    def reveal_cursor(self) -> None:
        if self.has_focus:
            self.scroll_to_region(Region(self._cursor_offset, 0, 1, 1), force=True, animate=False)
            self.scroll_visible(animate=False)

    def on_input_changed(self, event: Input.Changed) -> None:
        self.set_class(not event.value, "empty")
        # Initial paste and resizing can change the scroll range after selection is updated.
        self.call_after_refresh(self.reveal_cursor)

    def on_resize(self) -> None:
        self.call_after_refresh(self.reveal_cursor)


class DownloaderApp(App[None]):
    TITLE = "微信视频号下载"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [("ctrl+q", "quit", "退出"), ("ctrl+r", "retry", "重试"),
                ("ctrl+o", "open_downloads", "下载目录")]
    CSS = """
    Screen { background: $background; color: $foreground; }
    #brand { width: 100%; height: auto; padding: 1 4; align-vertical: middle; }
    #identity { width: 1fr; height: auto; align-vertical: middle; }
    #logo { width: 14; height: 7; }
    #brand-copy { width: 1fr; height: auto; margin: 0 3; }
    #brand-kicker { color: $muted; height: 1; }
    #brand-title { color: $foreground; text-style: bold; height: auto; margin: 1 0; }
    #brand-note { color: $muted; height: auto; }
    #theme-control { width: 20; height: auto; }
    #theme-label { color: $muted; height: 1; }
    Select { width: 100%; }
    #ribbon { height: 1; margin: 0 4; }
    #body { height: 1fr; min-height: 1; align: center middle; }
    #content { width: 100%; height: auto; margin: 1 4; padding: 1 2; }
    #stage { height: auto; color: $accent; text-style: bold; margin-bottom: 1; }
    #stage.success { color: $success; }
    #stage.warning { color: $warning; }
    #stage.error { color: $error; }
    #status { height: auto; margin-bottom: 1; }
    #loading { height: 3; color: $accent; }
    #qr-wrap { height: auto; align-horizontal: center; }
    #qr { height: auto; width: auto; color: black; background: white; }
    #terms { height: auto; margin-top: 1; color: $muted; }
    #entry { height: auto; }
    #input-label { height: 1; color: $muted; }
    Input { height: 3; margin: 1 0; border: solid $line; background: $entry-bg; color: $foreground; }
    Input:focus { border: solid $accent; background: $entry-bg; }
    Input>.input--placeholder { color: $muted; }
    Input>.input--selection { background: $primary; color: $button-fg; }
    Input>.input--cursor { background: transparent; color: $foreground; text-style: none; }
    Input.empty>.input--cursor { color: $muted; }
    #actions { height: auto; }
    Button { margin-right: 1; min-width: 16; background: $panel; color: $foreground; border: tall $panel; }
    Button:hover { background: $surface; border: tall $surface; }
    Button:focus { border: tall $accent; text-style: bold; }
    #download { background: $primary; color: $button-fg; border: tall $primary; text-style: bold; }
    #download:hover { background: $accent; border: tall $accent; }
    #download:focus { border: tall $foreground; }
    #approve { width: 100%; margin-top: 1; }
    #result { height: auto; margin-bottom: 1; color: $muted; }
    #details { height: auto; margin-top: 1; }
    #error-details { height: auto; }
    #bottom { width: 100%; height: auto; padding: 0 4 1 4; }
    #utility { height: auto; }
    #repository { height: auto; width: 1fr; color: $muted; margin: 1 1 0 0; }
    #repository:hover { color: $accent; }
    #repository:focus { color: $button-fg; background: $primary; text-style: bold; }
    .compact #content { margin: 0; padding: 1; }
    .compact #brand { margin: 0; padding: 0 1; }
    .narrow #brand { layout: vertical; }
    .compact #brand-copy { margin: 0 2; }
    .narrow #theme-control { width: 100%; }
    .compact #theme-label { display: none; }
    .compact #bottom { margin: 0; padding: 0 1; }
    .compact #utility { layout: vertical; }
    .compact #actions { layout: vertical; }
    .compact Button { margin-bottom: 1; }
    .compact #ribbon { margin: 0 1; }
    .compact #body, .short #body { align-vertical: top; }
    .short #brand { padding-top: 0; padding-bottom: 0; }
    .short #brand-note, .short #brand-kicker, .compact #brand-note { display: none; }
    .short #brand-title { margin: 0; }
    .short #content { margin-top: 0; margin-bottom: 0; padding-top: 0; padding-bottom: 0; }
    .short #bottom { padding-bottom: 0; }
    """

    def __init__(self, *, root: Path | None = None, transport: httpx.AsyncBaseTransport | None = None,
                 browser_setup: BrowserSetup | None = None) -> None:
        super().__init__()
        for theme in THEMES:
            self.register_theme(theme)
        self.session = Session(root or application_root(), transport, browser_setup)
        self.theme_mode = load_mode(self.session.root)
        self.theme = "channels-dark" if self.theme_mode == "dark" else "channels-light"
        self.native_cursor_visible = False
        self.native_cursor_color: str | None = None
        self.qr_image: Text | None = None
        self.qr_warning: bool | None = None
        self.qr_status = "请用微信扫描二维码，并在手机上确认登录。"
        self.approval = asyncio.Event()
        self.busy = False
        self.retry_download = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="brand"):
            with Horizontal(id="identity"):
                yield Static("", id="logo")
                with Vertical(id="brand-copy"):
                    yield Static("CHANNELS  /  本地归档", id="brand-kicker")
                    yield Static("微信视频号下载", id="brand-title")
                    yield Static("保存每一份值得留下的内容", id="brand-note")
            with Vertical(id="theme-control"):
                yield Static("外观", id="theme-label")
                yield Select([(label, mode) for label, mode in zip(("跟随系统", "浅色", "深色"), MODES)],
                             value=self.theme_mode, allow_blank=False, id="theme-mode")
        yield Static("", id="ribbon")
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
                    field = ShareLinkInput(placeholder="粘贴视频号分享链接", disabled=True, classes="empty")
                    field.cursor_blink = False
                    yield field
                yield Static("", id="result", markup=False)
                with Collapsible(title="查看失败详情", collapsed=True, id="details"):
                    yield Static("", id="error-details", markup=False)
                with Horizontal(id="actions"):
                    yield Button("下载 · Enter", id="download", disabled=True)
                    yield Button("重试 · Ctrl+R", id="retry")
                    yield Button("下载目录 · Ctrl+O", id="folder", disabled=True)
        with Vertical(id="bottom"):
            with Horizontal(id="utility"):
                yield Link("GitHub · MuZiJin701/wechat-channels-downloader ↗",
                           url="https://github.com/MuZiJin701/wechat-channels-downloader", id="repository")
                yield Button("退出 · Ctrl+Q", id="quit")

    def show_status(self, message: str) -> None:
        if self.qr_image is not None and self.query_one("#qr-wrap").display:
            self.qr_status = message
            if self.qr_warning:
                message = "请增大终端窗口，完整显示下方二维码后用微信扫码。"
        self.query_one("#status", Static).update(message)

    def show_stage(self, message: str, state: str = "") -> None:
        stage = self.query_one("#stage", Static)
        stage.update(message)
        stage.set_classes(state)

    def on_mount(self) -> None:
        self.update_layout(self.size)
        self.update_brand()
        self.refresh_system_theme()
        self.set_interval(2, self.refresh_system_theme)
        if sys.platform == "linux":
            try:
                refresh_desktop_icon(self.session.root)
            except OSError:
                self.notify("无法更新桌面入口图标；请检查程序目录的写入权限。", severity="warning")
        self.connect()

    def on_resize(self, event: events.Resize) -> None:
        self.update_layout(event.size)
        if self.query("#logo"):
            self.call_after_refresh(self.update_brand)

    def update_layout(self, size: Size) -> None:
        self.screen.set_class(size.width < 76, "compact")
        self.screen.set_class(size.width < 52, "narrow")
        self.screen.set_class(size.height < 32, "short")

    def update_brand(self) -> None:
        small = self.size.width < 76 or self.size.height < 32
        logo = self.query_one("#logo", Static)
        logo.styles.width, logo.styles.height = (8, 4) if small else (14, 7)
        logo.update(terminal_logo(self.current_theme.background or "#88a28c", 8 if small else 14))
        colors = self.current_theme.variables
        self.query_one("#ribbon", Static).update(LinearGradient(0, [
            (0, colors["gradient-start"]), (1, colors["gradient-end"])]))

    def apply_appearance(self, dark: bool) -> None:
        name = "channels-dark" if dark else "channels-light"
        if self.theme != name:
            self.theme = name
            self.update_brand()

    @work(exclusive=True, group="appearance")
    async def refresh_system_theme(self) -> None:
        if self.theme_mode == "system":
            dark = await asyncio.to_thread(system_dark)
            if self.theme_mode == "system":
                self.apply_appearance(dark)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "theme-mode" or event.value not in MODES or event.value == self.theme_mode:
            return
        self.theme_mode = str(event.value)
        if self.theme_mode == "system":
            self.refresh_system_theme()
        else:
            self.apply_appearance(self.theme_mode == "dark")
        try:
            save_mode(self.session.root, self.theme_mode)
        except OSError:
            self.notify("主题已切换，但无法保存偏好；请检查程序旁 data 目录的写入权限。", severity="warning")

    def native_cursor_position(self) -> Offset | None:
        field = self.focused
        if isinstance(field, ShareLinkInput) and not field.disabled and field.is_on_screen:
            position = field.cursor_screen_offset
            if field.scrollable_content_region.contains(*position):
                try:
                    if self.get_widget_at(*position)[0] is field:
                        return position
                except NoWidget:
                    pass
        return None

    def post_display_hook(self) -> None:
        if self.is_running and self.qr_image is not None:
            self.check_qr_size()
        # shortcut: Textual 8 has no native caret API; revisit this driver access on upgrades.
        if self._driver is None or self.is_headless or not self.is_running:
            return
        position = self.native_cursor_position()
        sequence = "\x1b[?25l"
        if position is not None:
            color = self.current_theme.foreground
            if sys.platform == "win32" and color != self.native_cursor_color:
                # A light terminal's fixed cursor color may disappear on the app's dark input.
                sequence += f"\x1b]12;{color}\x07"
                self.native_cursor_color = color
            if not self.native_cursor_visible:
                sequence += "\x1b[5 q"
            sequence += f"\x1b[{position.y + 1};{position.x + 1}H\x1b[?25h"
        self._driver.write(sequence)
        self._driver.flush()
        self.native_cursor_visible = position is not None

    def open_url(self, url: str, *, new_tab: bool = True) -> None:
        try:
            if not webbrowser.open(url, new=2 if new_tab else 0):
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
        self.show_stage("微信扫码")
        self.query_one("#qr-wrap").display = True
        self.qr_image = image
        if max(line.cell_len for line in image.split("\n")) > self.query_one("#content").content_size.width:
            raise UserError("登录失败：终端过窄，请放大窗口后重新登录。")
        self.query_one("#qr", Static).update(image)

    def check_qr_size(self) -> None:
        if self.qr_image is not None:
            qr = self.query_one("#qr")
            if qr.region.height:
                warning = not self.query_one("#body").scrollable_content_region.contains_region(qr.region)
                if warning != self.qr_warning:
                    self.qr_warning = warning
                    self.query_one("#status", Static).update(
                        "请增大终端窗口，完整显示下方二维码后用微信扫码。" if warning else self.qr_status)

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
            self.show_stage("环境检测")
            self.show_status("环境检测中…")
            self.query_one(Input).disabled = True
            self.query_one("#download", Button).disabled = True
            self.approval.clear()
            self.qr_image = None
            self.qr_warning = None
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
            self.qr_image = None
            self.query_one("#terms").display = False
            self.query_one("#approve").display = False
            self.show_status("登录态有效，请输入视频号分享链接。")
            self.show_stage("准备就绪", "success")
            self.query_one("#entry").display = True
            self.query_one("#download").display = True
            self.query_one(Input).disabled = False
            self.query_one("#download", Button).disabled = False
            self.query_one(Input).focus()
        except Exception as error:
            self.qr_image = None
            self.show_status(str(error) if isinstance(error, UserError) else "环境检测或登录失败，请检查网络和程序文件后重试。")
            self.show_stage("暂时无法继续", "error")
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
        self.show_stage("正在下载")
        self.query_one(Input).disabled = True
        self.query_one("#download", Button).disabled = True
        try:
            archive = await self.session.download(link, self.show_status)
            errors = archive.errors + [f"{item.label}：{item.error}" for item in archive.media if item.error]
            self.show_stage("下载" + archive.state, "success" if archive.state == "完成" else "warning" if archive.state == "部分完成" else "error")
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
            self.show_stage("下载未完成", "error")
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
        try:
            await self.session.close()
        finally:
            if self._driver is not None and not self.is_headless:
                self._driver.write("\x1b[0 q\x1b[?25h" + ("\x1b]112\x07" if self.native_cursor_color else ""))
                self._driver.flush()


def main() -> None:
    DownloaderApp().run()
