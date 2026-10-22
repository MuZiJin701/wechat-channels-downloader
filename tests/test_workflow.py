import json
import io
import asyncio
import sys
import subprocess
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

import httpx
from PIL import Image, ImageDraw
from textual import events
from textual.widgets import Button, Input, Link, Select, Static
from textual.color import Color

from downloader.app import DownloaderApp
from downloader.appearance import terminal_logo


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "data").mkdir()
        self.state = self.root / "data" / "session.json"
        self.state.write_text(json.dumps({
            "cookies": [{"name": "session", "value": "test-secret", "domain": "yuanbao.tencent.com",
                         "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"}],
            "origins": [],
        }), encoding="utf-8")
        self.feed = {"desc": "测试视频", "h264VideoInfo": {"videoUrl": "https://media.weixin.qq.com/video.mp4"}}
        self.parse_data = {"playable_url": "https://channels.weixin.qq.com/finder-preview/pages/feed?token=fixture&eid=fixture"}
        self.author_info = {}
        self.media_requests = []
        self.media_status = {}
        self.feed_status = 200
        self.parse_status = 200
        self.media = {"/video.mp4": (b"complete-video", "video/mp4")}
        self.info_status = 200
        self.info_html = False
        self.identity = {"userId": "fixture", "anonUser": {"isAnon": False}}
        self.login_mode = False
        self.scanned = False
        self.media_length = None
        self.redirect = None
        self.qr_expired = False
        self.require_registration = False
        self.registered = False
        self.feed_error = None
        self.guest_initial = False
        self.additional_verification = False
        self.delayed_login_dialog = False
        self.login_entry_required = False

    async def browser_setup(self, context):
        async def route(request):
            if request.request.url.startswith(self.root.as_uri() + "/"):
                await request.continue_()
                return
            if request.request.url.endswith("/fixture/scanned"):
                headers = ({"set-cookie": "session=scan-secret; Path=/; Secure; HttpOnly; SameSite=Lax"}
                           if self.scanned and not self.additional_verification else {})
                await request.fulfill(json={"scanned": self.scanned}, headers=headers)
            elif request.request.url.endswith("/api/joint/login"):
                await request.fulfill(status=400, json={"safeVerifyTypes": ["fixture-verification"]})
            elif request.request.url.endswith("/fixture/approve"):
                self.registered = True
                await request.fulfill(json={"ok": True})
            elif "open.weixin.qq.com" in request.request.url:
                body = '二维码已过期' if self.qr_expired else '<img class="qrcode js_qrcode_img" src="/connect/qrcode/fixture">'
                await request.fulfill(content_type="text/html; charset=utf-8", body=body)
            elif self.login_mode:
                registration = ('<button onclick="fetch(\'/fixture/approve\');this.remove()">同意并注册</button>'
                                if self.require_registration and not self.registered else '')
                if self.additional_verification:
                    registration += '''<script>async function pollVerification() {
                        if ((await (await fetch('/fixture/scanned')).json()).scanned)
                            await fetch('/api/joint/login', {method:'POST'});
                        setTimeout(pollVerification, 100);
                    } pollVerification();</script>'''
                if self.delayed_login_dialog:
                    await request.fulfill(content_type="text/html; charset=utf-8", body='''<button>登录</button>
                        <div id="overlay" style="position:fixed;inset:0;z-index:10;background:white"></div>
                        <script>setTimeout(() => {
                            document.querySelector('#overlay').innerHTML = '<h2>微信登录</h2>' +
                                '<iframe src="https://open.weixin.qq.com/connect/qrconnect"></iframe>';
                        }, 300);</script>''')
                    return
                if self.login_entry_required:
                    await request.fulfill(content_type="text/html; charset=utf-8", body='''
                        <button id="login">登录</button><div id="dialog"></div><script>
                        document.querySelector('#login').onclick = () => {
                            document.querySelector('#dialog').innerHTML = '<button id="wechat">微信</button>';
                            document.querySelector('#wechat').onclick = () => {
                                document.querySelector('#dialog').innerHTML = '<h2>微信登录</h2>' +
                                    '<iframe src="https://open.weixin.qq.com/connect/qrconnect"></iframe>';
                            };
                        };</script>''')
                    return
                await request.fulfill(content_type="text/html; charset=utf-8", body=registration + '''<html><button>微信登录</button>
                    <iframe src="https://open.weixin.qq.com/connect/qrconnect"></iframe>
                    <script>async function pollScan() {
                        await fetch('/fixture/scanned');
                        setTimeout(pollScan, 100);
                    } pollScan();</script></html>''')
            else:
                await request.fulfill(status=200, content_type="text/html", body="<html></html>")
        await context.route("**/*", route)

    def external(self, request):
        if request.url.path == "/api/getuserinfo":
            if self.info_html:
                return httpx.Response(200, text="<html>login required</html>", headers={"content-type": "text/html"})
            status = (200 if "scan-secret" in request.headers.get("cookie", "") else 401) if self.login_mode else self.info_status
            if self.require_registration and not self.registered:
                status = 401
            guest = self.guest_initial and "scan-secret" not in request.headers.get("cookie", "")
            return httpx.Response(200 if guest else status,
                                  json={"userId": "visitor", "anonUser": {"isAnon": True}} if guest else self.identity)
        if request.url.path == "/connect/qrcode/fixture":
            image = Image.new("RGB", (29, 29), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((4, 4, 10, 10), fill="black")
            draw.rectangle((18, 4, 24, 10), fill="black")
            draw.rectangle((4, 18, 10, 24), fill="black")
            draw.rectangle((5, 5, 9, 9), fill="white")
            draw.rectangle((6, 6, 8, 8), fill="black")
            data = io.BytesIO()
            image.save(data, format="PNG")
            return httpx.Response(200, content=data.getvalue(), headers={"content-type": "image/png"})
        if request.url.path == "/api/weixin/get_parse_result":
            self.assertEqual(request.headers.get("cookie"), "session=scan-secret" if self.login_mode else "session=test-secret")
            return httpx.Response(self.parse_status, json={"code": 0, "data": self.parse_data})
        if request.url.path == "/finder-preview/api/feed/get_feed_info":
            self.assertNotIn("cookie", request.headers)
            if self.feed_status != 200:
                return httpx.Response(self.feed_status)
            return httpx.Response(200, json={"errCode": 0, "data": {
                "feedInfo": self.feed, "authorInfo": self.author_info, "errMsg": self.feed_error}})
        if request.url.host in ("media.weixin.qq.com", "wx.music.tc.qq.com"):
            self.assertNotIn("cookie", request.headers)
            self.media_requests.append(str(request.url))
            if request.url.path in self.media_status:
                return httpx.Response(self.media_status[request.url.path])
            if self.redirect:
                return httpx.Response(302, headers={"location": self.redirect})
            body, mime = self.media[request.url.path]
            headers = {"content-type": mime}
            if self.media_length:
                headers["content-length"] = str(self.media_length)
            if isinstance(body, httpx.AsyncByteStream):
                return httpx.Response(200, stream=body, headers=headers)
            return httpx.Response(200, content=body, headers=headers)
        raise AssertionError("Unexpected external request")

    @asynccontextmanager
    async def running(self, size=(110, 50), *, notifications=False):
        app = DownloaderApp(root=self.root, transport=httpx.MockTransport(self.external), browser_setup=self.browser_setup)
        self.active_app = app
        async with app.run_test(size=size, notifications=notifications) as pilot:
            yield app, pilot

    def status(self, app):
        return str(app.query_one("#status", Static).render())

    async def wait_for(self, pilot, condition):
        for _ in range(400):
            await pilot.pause(0.02)
            if condition():
                return
        self.fail("TUI did not reach the expected visible result: " + self.status(self.active_app))

    async def submit(self, app, pilot, link="https://weixin.qq.com/sph/fixture"):
        await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
        app.query_one(Input).value = link
        await pilot.press("enter")
        await self.wait_for(pilot, lambda: "完成" in self.status(app) or "失败" in self.status(app) or "请输入" in self.status(app))

    async def test_valid_session_downloads_a_complete_video_through_tui(self):
        self.parse_data.update({"author": "发布者", "yuanbao_only": "第一步独有信息"})
        old = self.root / "downloads" / "old" / "yuanbao.json"
        old.parent.mkdir(parents=True)
        old.write_bytes(b"preserve-old-archive")
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            archive = self.root / "downloads" / "发布者_测试视频"
            self.assertTrue(archive.is_dir(), self.status(app))
            self.assertEqual(next(archive.glob("发布者_测试视频*.mp4")).read_bytes(), b"complete-video")
            self.assertEqual(json.loads((archive / "parse.json").read_text(encoding="utf-8"))["data"], self.parse_data)
            self.assertEqual(json.loads((archive / "feed.json").read_text(encoding="utf-8"))["data"]["feedInfo"], self.feed)
            self.assertFalse(list(archive.glob("*.txt")))
            page = await app.session.context.new_page()
            page.set_default_timeout(3000)
            await page.goto((archive / "index.html").as_uri())
            self.assertEqual(await page.locator("#description").inner_text(), "测试视频")
            self.assertEqual(await page.locator("video").count(), 1)
            self.assertEqual(await page.locator("#result").inner_text(), "完成")
            self.assertFalse((await page.locator("video").get_attribute("src")).startswith("https:"))
            self.assertIn("完成", self.status(app))
            self.assertEqual(await page.get_by_role("link", name="解析原始数据", exact=True).get_attribute("href"), "parse.json")
            self.assertEqual(app.query_one(Input).value, "")
            self.assertEqual(old.read_bytes(), b"preserve-old-archive")

    async def test_tui_has_its_own_theme_and_keyboard_actions_without_function_keys(self):
        async with self.running(notifications=True) as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertEqual(app.screen.styles.background, Color.parse(app.current_theme.background))
            self.assertEqual(app.query_one("#qr").styles.background, Color.parse("white"))
            self.assertEqual(app.query_one("#qr").styles.color, Color.parse("black"))
            self.assertTrue(app.query_one(Input).display)
            repository = app.query_one("#repository", Link)
            self.assertEqual(repository.text, "GitHub · MuZiJin701/wechat-channels-downloader ↗")
            self.assertFalse(app.query("#github"))
            with patch("webbrowser.open") as opened:
                await pilot.press("ctrl+g")
                opened.assert_not_called()
                await pilot.click(repository)
                opened.assert_called_once_with("https://github.com/MuZiJin701/wechat-channels-downloader", new=2)
                opened.reset_mock()
                await pilot.press("tab", "shift+tab", "enter")
                opened.assert_called_once_with("https://github.com/MuZiJin701/wechat-channels-downloader", new=2)
            with patch("webbrowser.open", return_value=False):
                await pilot.press("enter")
                await self.wait_for(pilot, lambda: bool(app.query("Toast")))
                self.assertIn("github.com/MuZiJin701/wechat-channels-downloader", str(app.query_one("Toast", Static).render()))
            self.assertNotIn("元宝", self.status(app))
            with patch("os.startfile", create=True) as windows_open, patch("subprocess.Popen") as unix_open:
                await pilot.press("ctrl+o")
                if sys.platform == "win32":
                    windows_open.assert_called_once_with(self.root / "downloads")
                else:
                    self.assertEqual(unix_open.call_args.args[0][-1], str(self.root / "downloads"))

    def operating_system_appearance(self, dark):
        if sys.platform == "win32":
            return patch("winreg.QueryValueEx", return_value=(0 if dark else 1, 4),
                         side_effect=OSError("unavailable") if dark is None else None)
        return patch("subprocess.run", return_value=subprocess.CompletedProcess(
            [], 0, ("Dark" if sys.platform == "darwin" else "'prefer-dark'") if dark else "'prefer-light'"),
                     side_effect=OSError("unavailable") if dark is None else None)

    async def choose_theme(self, pilot, mode):
        await pilot.click("#theme-mode")
        await pilot.press("home", *(["down"] * ("system", "light", "dark").index(mode)), "enter")
        await pilot.pause()

    async def test_logo_and_controls_use_high_contrast_and_symmetric_borders(self):
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            for mode in ("light", "dark"):
                await self.choose_theme(pilot, mode)
                for small, dimensions in ((False, (110, 40)), (True, (60, 20))):
                    await pilot.resize_terminal(*dimensions)
                    await pilot.pause()
                    drawing = terminal_logo(app.current_theme.accent, small=small)
                    self.assertNotIn("▀", drawing.plain)
                    self.assertEqual(drawing.style, app.current_theme.accent)
                    self.assertEqual(len(drawing.plain.splitlines()), 4 if small else 7)
                    self.assertLessEqual(max(map(len, drawing.plain.splitlines())), 8 if small else 14)
                    for control in app.query("Button, SelectCurrent, SelectOverlay"):
                        for edge in ("top", "bottom", "left", "right"):
                            self.assertEqual(getattr(control.styles, "border_" + edge)[0], "solid")
                    button = app.query_one("#download", Button)
                    button.focus()
                    await pilot.pause()
                    self.assertEqual(button.styles.border_left[0], "solid")

    async def test_theme_selection_is_immediate_saved_and_does_not_change_session_or_input(self):
        before = self.state.read_bytes()
        with self.operating_system_appearance(False):
            async with self.running() as (app, pilot):
                await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
                self.assertEqual(app.theme, "channels-light")
                self.assertEqual(app.query_one("#theme-mode", Select).value, "system")
                app.query_one(Input).value = "https://weixin.qq.com/sph/fixture"
                await self.choose_theme(pilot, "dark")
                self.assertEqual(app.theme, "channels-dark")
                self.assertEqual(app.screen.styles.background, Color.parse("#283e2c"))
                self.assertEqual(app.query_one(Input).value, "https://weixin.qq.com/sph/fixture")
                self.assertFalse(app.query_one(Input).disabled)
                self.assertEqual(json.loads((self.root / "data" / "appearance.json").read_text())["theme"], "dark")
                self.assertEqual(self.state.read_bytes(), before)
                await pilot.click(app.query_one(Input))
                await pilot.press("enter")
                await self.wait_for(pilot, lambda: "下载完成" in self.status(app))
                result = str(app.query_one("#result", Static).render())
                await self.choose_theme(pilot, "light")
                self.assertEqual(app.theme, "channels-light")
                self.assertEqual(str(app.query_one("#result", Static).render()), result)
            async with self.running() as (app, pilot):
                await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
                self.assertEqual(app.query_one("#theme-mode", Select).value, "light")
                await self.choose_theme(pilot, "system")
                self.assertEqual(json.loads((self.root / "data" / "appearance.json").read_text())["theme"], "system")
        with self.operating_system_appearance(True):
            async with self.running() as (app, pilot):
                await self.wait_for(pilot, lambda: not app.query_one(Input).disabled and app.theme == "channels-dark")
                self.assertEqual(app.query_one("#theme-mode", Select).value, "system")

    async def test_automatic_theme_tracks_os_changes_and_handles_unavailable_or_invalid_preferences(self):
        (self.root / "data" / "appearance.json").write_text('{"theme": ["invalid"]}', encoding="utf-8")
        with self.operating_system_appearance(None):
            async with self.running() as (app, pilot):
                await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
                self.assertEqual(app.theme_mode, "system")
                self.assertEqual(app.theme, "channels-light")
                with self.operating_system_appearance(True):
                    await self.wait_for(pilot, lambda: app.theme == "channels-dark")
                await self.wait_for(pilot, lambda: app.theme == "channels-light")
                await self.choose_theme(pilot, "dark")
                await pilot.pause(2.1)
                self.assertEqual(app.theme, "channels-dark")

    async def test_theme_save_failure_is_visible_and_does_not_disrupt_download(self):
        (self.root / "data" / "appearance.json").mkdir()
        before = self.state.read_bytes()
        async with self.running(notifications=True) as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            await self.choose_theme(pilot, "dark")
            self.assertEqual(app.theme, "channels-dark")
            await self.wait_for(pilot, lambda: bool(app.query("Toast")))
            self.assertIn("无法保存偏好", str(app.query_one("Toast", Static).render()))
            self.assertEqual(self.state.read_bytes(), before)
            await pilot.click(app.query_one(Input))
            await self.submit(app, pilot)
            self.assertIn("下载完成", self.status(app))

    async def test_switching_theme_during_download_keeps_the_active_transfer(self):
        gate = asyncio.Event()

        class Transfer(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"first-"
                await gate.wait()
                yield b"second"

        self.media["/video.mp4"] = (Transfer(), "video/mp4")
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            app.query_one(Input).value = "https://weixin.qq.com/sph/fixture"
            await pilot.press("enter")
            await self.wait_for(pilot, lambda: bool(self.media_requests))
            await self.choose_theme(pilot, "dark")
            self.assertTrue(app.busy)
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(app.query_one(Input).value, "https://weixin.qq.com/sph/fixture")
            gate.set()
            await self.wait_for(pilot, lambda: "下载完成" in self.status(app))
            self.assertEqual(next((self.root / "downloads").rglob("*.mp4")).read_bytes(), b"first-second")

    @unittest.skipUnless(sys.platform == "linux", "Linux portable Desktop Entry icon relocation")
    async def test_linux_launcher_icon_is_refreshed_in_the_portable_directory(self):
        launcher = self.root / "wechat-channels-downloader.desktop"
        launcher.write_text("[Desktop Entry]\nType=Application\nIcon=/old-location/logo.png\nTerminal=true\n", encoding="utf-8")
        launcher.chmod(0o755)
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            text = launcher.read_text(encoding="utf-8")
            self.assertNotIn("old-location", text)
            self.assertIn("Icon=" + str(Path(__file__).resolve().parents[1] / "downloader" / "assets" / "logo.png"), text)
            self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)


    async def test_resizing_and_native_caret_keep_normal_input_editing_and_keyboard_download(self):
        async with self.running() as (app, pilot):
            field = app.query_one(Input)
            await self.wait_for(pilot, lambda: not field.disabled)
            field.value = "微信abc"
            await pilot.press("home")
            self.assertEqual(app.native_cursor_position(), field.content_region.offset)
            await pilot.press("end")
            self.assertEqual(app.native_cursor_position().x, field.content_region.x + 7)
            await pilot.press("tab")
            self.assertIsNone(app.native_cursor_position())
            widths = []
            for width, height in ((160, 50), (80, 24), (60, 20), (44, 20), (110, 40)):
                await pilot.resize_terminal(width, height)
                await pilot.pause()
                self.assertEqual(app.screen.has_class("compact"), width < 76)
                self.assertEqual(app.screen.has_class("narrow"), width < 52)
                self.assertEqual(app.screen.has_class("short"), height < 32)
                widths.append(app.query_one("#content").size.width)
                self.assertLessEqual(app.query_one("#quit").region.bottom, height)
                await self.choose_theme(pilot, "dark")
                await pilot.press("tab", "tab")
                await pilot.press("ctrl+a")
                field.post_message(events.Paste("https://weixin.qq.com/sph/" + "a" * 250))
                await pilot.pause()
                self.assertIsNotNone(app.native_cursor_position(),
                                     (width, height, app.focused, field.region, field.scroll_offset, field.cursor_screen_offset))
                self.assertGreater(field.scroll_x, 0)
            self.assertGreater(widths[0], 100)
            self.assertGreater(widths[0], widths[1])
            await pilot.press("ctrl+a")
            field.post_message(events.Paste("https://weixin.qq.com/sph/fixture"))
            await pilot.pause()
            await pilot.press("enter")
            await self.wait_for(pilot, lambda: "下载完成" in self.status(app))

    async def test_share_link_input_supports_normal_editing_without_opening_links(self):
        async with self.running() as (app, pilot):
            field = app.query_one(Input)
            await self.wait_for(pilot, lambda: not field.disabled)
            self.assertEqual(field.placeholder, "粘贴视频号分享链接")
            with patch("webbrowser.open") as opened:
                await pilot.click(field)
                await pilot.press("a", "b", "c", "ctrl+a", "x")
                self.assertEqual(field.value, "x")
                await pilot.press("home", "delete", "a", "b", "c", "home", "right", "shift+end", "ctrl+c")
                self.assertEqual(app.clipboard, "bc")
                await pilot.press("ctrl+x")
                self.assertEqual(field.value, "a")
                await pilot.press("ctrl+v", "end", "backspace")
                self.assertEqual(field.value, "ab")
                await pilot.press("ctrl+a")
                field.post_message(events.Paste("https://weixin.qq.com/sph/fixture"))
                await pilot.pause()
                self.assertEqual(field.value, "https://weixin.qq.com/sph/fixture")
                await pilot.click(field, offset=(5, 1))
                self.assertTrue(field.has_focus)
                await pilot.mouse_down(field, offset=(2, 1))
                await pilot.hover(field, offset=(8, 1))
                await pilot.mouse_up(field, offset=(8, 1))
                self.assertTrue(field.selected_text)
                opened.assert_not_called()

    async def test_image_post_saves_all_images_in_order_and_text(self):
        self.feed = {"description": "图文正文", "picInfo": [
            {"url": "https://media.weixin.qq.com/first.jpg"}, {"url": "https://media.weixin.qq.com/second.png"}]}
        self.media = {"/first.jpg": (b"first-image", "image/jpeg"), "/second.png": (b"second-image", "image/png")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            posts = list((self.root / "downloads").iterdir())
            self.assertEqual(len(posts), 1, self.status(app))
            self.assertEqual(next(posts[0].glob("*_图片_001.jpg")).read_bytes(), b"first-image")
            self.assertEqual(next(posts[0].glob("*_图片_002.png")).read_bytes(), b"second-image")
            self.assertIn("图文正文", (posts[0] / "index.html").read_text(encoding="utf-8"))
            self.assertFalse(list(posts[0].glob("*.txt")))

    async def test_archive_keeps_all_media_versions_attachments_and_local_information(self):
        image = io.BytesIO()
        Image.new("RGB", (4, 3), "red").save(image, format="PNG")
        png = image.getvalue()
        avatar = "https://media.weixin.qq.com/avatar.png?urlToken=fixture-private"
        self.parse_data.update({"author": "发布者", "author_icon": avatar,
                                "author_certification_icon": "https://media.weixin.qq.com/icon.png",
                                "cover_url": "https://media.weixin.qq.com/parse-cover.png"})
        self.author_info = {"nickname": "发布者", "headImgUrl": avatar}
        self.feed = {"description": "全部资源", "h264VideoInfo": {"videoUrl": "https://media.weixin.qq.com/video.mp4"},
                     "h265VideoInfo": {"videoUrl": "https://media.weixin.qq.com/hevc.mp4"},
                     "videoUrl": "https://media.weixin.qq.com/video.mp4",
                     "picInfo": [{"url": "https://media.weixin.qq.com/first.png"},
                                 {"url": "https://media.weixin.qq.com/cover.png"}],
                     "coverUrl": "https://media.weixin.qq.com/cover.png", "createtime": 1704067200,
                     "favCountFmt": "1万", "jumpInfo": {"wording": "杭州"},
                     "bgmInfo": {"bgmUrl": "http://wx.music.tc.qq.com/background.m4a"},
                     "future_field": {"unchanged": True}}
        self.media.update({"/hevc.mp4": (b"hevc-video", "video/mp4"),
                           "/background.m4a": (b"original-audio", "audio/mp4"),
                           **{f"/{name}.png": (png, "image/png")
                              for name in ("first", "cover", "parse-cover", "avatar", "icon")}})
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            archive = self.root / "downloads" / "发布者_全部资源"
            self.assertEqual(len(list(archive.glob("*.mp4"))), 2)
            self.assertEqual(next(archive.glob("*.m4a")).read_bytes(), b"original-audio")
            self.assertEqual(len(list(archive.glob("*.png"))), 5)
            self.assertEqual(len(self.media_requests), 8)
            self.assertIn("https://wx.music.tc.qq.com/background.m4a", self.media_requests)
            self.assertEqual(json.loads((archive / "feed.json").read_text(encoding="utf-8"))["data"]["feedInfo"], self.feed)
            page = await app.session.context.new_page()
            page.set_default_timeout(3000)
            await page.goto((archive / "index.html").as_uri())
            self.assertEqual(await page.locator("video").count(), 3)
            self.assertEqual(await page.locator("audio").count(), 1)
            self.assertIn("1万", await page.locator("body").inner_text())
            self.assertIn("杭州", await page.locator("body").inner_text())
            self.assertIn("2024-01-01", await page.locator("body").inner_text())
            self.assertIn("UTC", await page.locator("body").inner_text())
            self.assertNotIn("fixture-private", await page.content())
            for image in await page.locator("img").all():
                await image.scroll_into_view_if_needed()
                await image.evaluate("image => image.decode()")
            self.assertTrue(await page.locator("img").evaluate_all("items => items.every(i => i.complete && i.naturalWidth === 4)"))

    async def test_failed_attachment_keeps_other_resources_and_reports_partial_archive(self):
        self.feed.update({"coverUrl": "https://media.weixin.qq.com/broken.jpg",
                          "bgmInfo": {"bgmUrl": "https://media.weixin.qq.com/music.m4a"}})
        self.media_status["/broken.jpg"] = 503
        self.media["/music.m4a"] = (b"music-after-failure", "audio/mp4")
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("部分完成", self.status(app))
            self.assertEqual(app.query_one(Input).value, "https://weixin.qq.com/sph/fixture")
            self.assertTrue(app.query_one("#details").display)
            self.assertTrue(app.query_one("#details").collapsed)
            archive = self.root / "downloads" / "测试视频"
            self.assertEqual(next(archive.glob("*.mp4")).read_bytes(), b"complete-video")
            self.assertEqual(next(archive.glob("*.m4a")).read_bytes(), b"music-after-failure")
            self.assertFalse(list(archive.glob("*.part")))
            self.assertEqual(len(list(archive.glob("*.json"))), 2)
            page = await app.session.context.new_page()
            page.set_default_timeout(3000)
            await page.goto((archive / "index.html").as_uri())
            self.assertEqual(await page.locator("#result").inner_text(), "部分完成")
            self.assertIn("封面", await page.locator("body").inner_text())
            self.assertIn("失败", await page.locator("body").inner_text())
            self.assertNotIn("https://media", await page.content())
            self.media_status.clear()
            self.media["/broken.jpg"] = (b"recovered-cover", "image/jpeg")
            await pilot.press("ctrl+r")
            await self.wait_for(pilot, lambda: self.status(app).startswith("下载完成"))
            self.assertEqual(app.query_one(Input).value, "")
            self.assertEqual(len(list((self.root / "downloads").iterdir())), 2)

    async def test_second_parse_failure_preserves_the_first_response_and_explanation(self):
        self.parse_data.update({"author": "发布者", "desc": "仅元宝说明", "extra": {"keep": True}})
        self.feed_status = 503
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("失败", self.status(app))
            archive = self.root / "downloads" / "发布者_仅元宝说明"
            self.assertTrue((archive / "index.html").exists())
            self.assertEqual(json.loads((archive / "parse.json").read_text(encoding="utf-8"))["data"], self.parse_data)
            self.assertFalse((archive / "feed.json").exists())
            self.assertNotIn("test-secret", (archive / "index.html").read_text(encoding="utf-8"))

    async def test_quitting_during_transfer_keeps_completed_files_and_marks_interrupted(self):
        started = asyncio.Event()

        class SlowMedia(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"incomplete-image"
                started.set()
                await asyncio.Event().wait()

        self.feed = {"description": "中断测试", "picInfo": [{"url": "https://media.weixin.qq.com/first.jpg"},
                                                          {"url": "https://media.weixin.qq.com/slow.jpg"}]}
        self.media = {"/first.jpg": (b"complete-first", "image/jpeg"), "/slow.jpg": (SlowMedia(), "image/jpeg")}
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            app.query_one(Input).value = "https://weixin.qq.com/sph/fixture"
            await pilot.press("enter")
            await self.wait_for(pilot, started.is_set)
            await pilot.press("ctrl+q")
        archive = self.root / "downloads" / "中断测试"
        self.assertEqual(next(archive.glob("*_图片_001.jpg")).read_bytes(), b"complete-first")
        self.assertFalse(list(archive.glob("*_图片_002.jpg")))
        self.assertFalse(list(archive.glob("*.part")))
        self.assertEqual(len(list(archive.glob("*.json"))), 2)
        self.assertIn("已中断", (archive / "index.html").read_text(encoding="utf-8"))

    async def test_missing_session_shows_qr_then_downloads_and_reuses_new_session(self):
        self.state.unlink()
        self.login_mode = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "扫码" in self.status(app))
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            self.assertFalse(app.query_one("#entry").display)
            self.assertFalse(app.query_one("#terms").display)
            self.assertNotIn("元宝", self.status(app))
            self.assertFalse(self.state.exists())
            self.scanned = True
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))
            self.assertIn("scan-secret", self.state.read_text(encoding="utf-8"))
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertIn("有效", self.status(app))

    async def test_login_html_is_not_mistaken_for_a_valid_session(self):
        self.info_html = True
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "失败" in self.status(app) or "有效" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(self.state.read_bytes(), original)

    async def test_delayed_automatic_login_dialog_shows_qr_without_clicking_behind_it(self):
        self.state.unlink()
        self.login_mode = True
        self.delayed_login_dialog = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            self.assertFalse(self.state.exists())
            self.assertTrue(app.query_one(Input).disabled)

    async def test_login_entry_and_wechat_tab_can_still_be_opened(self):
        self.state.unlink()
        self.login_mode = True
        self.login_entry_required = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            self.assertFalse(self.state.exists())

    async def test_network_failure_preserves_session_and_retry_recovers(self):
        self.info_status = 503
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "无法检查" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(self.state.read_bytes(), original)
            self.assertNotIn("█", str(app.query_one("#qr", Static).render()))
            self.info_status = 200
            await pilot.press("ctrl+r")
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertIn("有效", self.status(app))

    async def test_expired_session_during_download_can_scan_again_without_losing_link(self):
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.parse_status = 401
            app.query_one(Input).value = "https://weixin.qq.com/sph/fixture"
            await pilot.press("enter")
            await self.wait_for(pilot, lambda: "过期" in self.status(app))
            self.assertFalse(app.query_one("#entry").display)
            self.login_mode = True
            self.parse_status = 200
            await pilot.press("ctrl+r")
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr").render()))
            self.scanned = True
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertEqual(app.query_one(Input).value, "https://weixin.qq.com/sph/fixture")

    async def test_image_post_without_text_downloads_normally(self):
        self.feed = {"picInfo": [{"url": "https://media.weixin.qq.com/one.jpg"}]}
        self.media = {"/one.jpg": (b"image-only", "image/jpeg")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))
            archive = self.root / "downloads" / "fixture"
            self.assertEqual(next(archive.glob("*.jpg")).read_bytes(), b"image-only")
            self.assertIn('<p id="description"></p>', (archive / "index.html").read_text(encoding="utf-8"))

    async def test_invalid_link_does_not_start_a_download(self):
        async with self.running() as (app, pilot):
            await self.submit(app, pilot, "https://evil.invalid/sph/fixture")
            self.assertIn("请输入", self.status(app))
            self.assertEqual(list((self.root / "downloads").iterdir()), [])

    async def test_incomplete_media_is_removed_but_information_and_existing_content_survive(self):
        self.media_length = 1000
        existing = self.root / "downloads" / "existing"
        existing.mkdir(parents=True)
        (existing / "video.mp4").write_bytes(b"keep-me")
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("不完整", self.status(app))
            archive = self.root / "downloads" / "测试视频"
            self.assertIn("失败", self.status(app))
            self.assertTrue((archive / "index.html").exists())
            self.assertEqual(len(list(archive.glob("*.json"))), 2)
            self.assertFalse(list(archive.glob("*.mp4")))
            self.assertFalse(list(archive.glob("*.part")))
            self.assertEqual((existing / "video.mp4").read_bytes(), b"keep-me")

    async def test_unknown_binary_content_is_not_mislabelled_as_a_video(self):
        self.media = {"/video.mp4": (b"<html>not a video</html>", "application/octet-stream")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("失败", self.status(app))
            archive = self.root / "downloads" / "测试视频"
            self.assertFalse(list(archive.glob("*.mp4")))
            self.assertFalse(list(archive.glob("*.part")))

    async def test_binary_video_header_can_span_network_chunks(self):
        content = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00complete-video"

        class FragmentedVideo(httpx.AsyncByteStream):
            async def __aiter__(self):
                for byte in content:
                    yield bytes([byte])

        self.media = {"/video.mp4": (FragmentedVideo(), "application/octet-stream")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertNotIn("失败", self.status(app))
            self.assertEqual(next((self.root / "downloads").glob("*/*.mp4")).read_bytes(), content)

    async def test_archive_names_are_portable_and_repeated_downloads_preserve_safe_original_text(self):
        self.parse_data["author"] = "发布/者"
        body = '正文开头：' + '内容' * 150 + '\n<script>window.compromised=true</script>&原文'
        self.feed["desc"] = body
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            first = next((self.root / "downloads").iterdir())
            original = next(first.glob("*.mp4")).read_bytes()
            await self.submit(app, pilot)
            archives = list((self.root / "downloads").iterdir())
            self.assertEqual(len(archives), 2)
            second = next(path for path in archives if path != first)
            self.assertEqual(second.name, first.name + "_2")
            self.assertTrue(first.name.startswith("发布_者_正文开头："))
            self.assertEqual(next(first.glob("*.mp4")).read_bytes(), original)
            for file in self.root.rglob("*"):
                self.assertLessEqual(len(file.name.encode("utf-8")), 255)
                self.assertNotRegex(file.name, r'[<>:"/\\|?*\x00-\x1f]')
            page = await app.session.context.new_page()
            page.set_default_timeout(3000)
            requests = []
            page.on("request", lambda request: requests.append(request.url))
            await page.goto((first / "index.html").as_uri())
            self.assertEqual(await page.locator("#description").inner_text(), body)
            self.assertTrue(await page.evaluate("window.compromised === undefined"))
            self.assertTrue(all(url.startswith("file:") for url in requests))

    async def test_media_redirect_cannot_send_session_to_another_site(self):
        self.redirect = "https://evil.invalid/collect"
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("受支持", self.status(app))
            archive = self.root / "downloads" / "测试视频"
            self.assertFalse(list(archive.glob("*.mp4")))
            self.assertTrue((archive / "index.html").exists())
            self.assertNotIn("test-secret", self.status(app))

    async def test_failed_session_save_preserves_previous_state(self):
        self.login_mode = True
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            with patch("os.replace", side_effect=PermissionError("test-secret")):
                self.scanned = True
                await self.wait_for(pilot, lambda: "失败" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(self.state.read_bytes(), original)
            self.assertNotIn("test-secret", self.status(app))

    async def test_unwritable_data_location_is_reported_without_fallback(self):
        import shutil
        shutil.rmtree(self.root / "data")
        (self.root / "data").write_bytes(b"existing-file")
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "失败" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual((self.root / "data").read_bytes(), b"existing-file")

    async def test_unwritable_archive_location_explains_storage_failure_without_overwrite(self):
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            downloads = self.root / "downloads"
            downloads.rmdir()
            downloads.write_bytes(b"preserve-existing-file")
            await self.submit(app, pilot)
            self.assertIn("写入", self.status(app))
            self.assertIn("空间", self.status(app))
            self.assertEqual(downloads.read_bytes(), b"preserve-existing-file")

    async def test_expired_qr_reports_failure_without_replacing_saved_session(self):
        self.login_mode = True
        self.qr_expired = True
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "过期" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(self.state.read_bytes(), original)
            self.assertNotIn("test-secret", self.status(app))

    async def test_registration_is_not_accepted_until_user_confirms_in_tui(self):
        self.login_mode = True
        self.require_registration = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: app.query_one("#approve").display)
            self.assertFalse(self.registered)
            await pilot.pause()
            self.assertTrue(await pilot.click("#approve"))
            self.scanned = True
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertTrue(self.registered)
            self.assertIn("有效", self.status(app))

    async def test_unknown_identity_json_does_not_unlock_download(self):
        self.identity = {"error": "not logged in"}
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "失败" in self.status(app) or "有效" in self.status(app))
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(self.state.read_bytes(), original)

    async def test_empty_feed_error_envelope_is_a_successful_response(self):
        self.feed_error = {"type": 0, "title": "", "content": ""}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))

    async def test_explicit_guest_identity_can_scan_to_a_real_session(self):
        self.login_mode = True
        self.guest_initial = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "失败" in self.status(app) or "█" in str(app.query_one("#qr", Static).render()))
            self.assertIn("█", str(app.query_one("#qr", Static).render()), self.status(app))
            self.scanned = True
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertIn("有效", self.status(app))

    async def test_extra_security_verification_is_reported_without_saving_state(self):
        self.login_mode = True
        self.additional_verification = True
        original = self.state.read_bytes()
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            self.scanned = True
            await self.wait_for(pilot, lambda: "额外安全验证" in self.status(app))
            self.assertIn("额外安全验证", self.status(app))
            self.assertEqual(self.state.read_bytes(), original)

    async def test_small_terminal_explains_how_to_show_the_complete_qr(self):
        self.login_mode = True
        async with self.running(size=(80, 24)) as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            await self.wait_for(pilot, lambda: "增大" in self.status(app))
            self.assertIn("增大", self.status(app))
            await self.choose_theme(pilot, "dark")
            self.assertTrue(app.query_one(Input).disabled)
            self.assertEqual(app.query_one("#qr").styles.background, Color.parse("white"))
            self.assertEqual(app.query_one("#qr").styles.color, Color.parse("black"))
            await pilot.resize_terminal(110, 60)
            await self.wait_for(pilot, lambda: "增大" not in self.status(app))
            self.assertTrue(app.query_one("#body").scrollable_content_region.contains_region(app.query_one("#qr").region))

    async def test_image_jpg_content_type_saves_jpeg_content(self):
        self.feed = {"picInfo": [{"url": "https://media.weixin.qq.com/photo"}]}
        self.media = {"/photo": (b"jpeg-content", "image/jpg")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))
            self.assertEqual(next((self.root / "downloads").glob("*/*_图片_001.jpg")).read_bytes(), b"jpeg-content")
