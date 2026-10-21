import json
import io
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

import httpx
from PIL import Image, ImageDraw
from textual.widgets import Input, Static

from downloader.app import DownloaderApp


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
                    registration += '''<script>setInterval(async () => {
                        if ((await (await fetch('/fixture/scanned')).json()).scanned)
                            fetch('/api/joint/login', {method:'POST'});
                    }, 100);</script>'''
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
                    <script>setInterval(async () => {
                        if ((await (await fetch('/fixture/scanned')).json()).scanned)
                            document.cookie='session=scan-secret; path=/; secure';
                    }, 100);</script></html>''')
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
            return httpx.Response(200, json={"code": 0, "data": {
                "playable_url": "https://channels.weixin.qq.com/finder-preview/pages/feed?token=fixture&eid=fixture"
            }})
        if request.url.path == "/finder-preview/api/feed/get_feed_info":
            self.assertNotIn("cookie", request.headers)
            return httpx.Response(200, json={"errCode": 0, "data": {"feedInfo": self.feed, "errMsg": self.feed_error}})
        if request.url.host == "media.weixin.qq.com":
            self.assertNotIn("cookie", request.headers)
            if self.redirect:
                return httpx.Response(302, headers={"location": self.redirect})
            body, mime = self.media[request.url.path]
            headers = {"content-type": mime}
            if self.media_length:
                headers["content-length"] = str(self.media_length)
            return httpx.Response(200, content=body, headers=headers)
        raise AssertionError("Unexpected external request")

    @asynccontextmanager
    async def running(self, size=(110, 50)):
        app = DownloaderApp(root=self.root, transport=httpx.MockTransport(self.external), browser_setup=self.browser_setup)
        self.active_app = app
        async with app.run_test(size=size) as pilot:
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
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            files = list((self.root / "downloads").glob("*/video.mp4"))
            self.assertEqual(len(files), 1, self.status(app))
            self.assertEqual(files[0].read_bytes(), b"complete-video")
            self.assertIn("完成", self.status(app))

    async def test_image_post_saves_all_images_in_order_and_text(self):
        self.feed = {"description": "图文正文", "picInfo": [
            {"url": "https://media.weixin.qq.com/first.jpg"}, {"url": "https://media.weixin.qq.com/second.png"}]}
        self.media = {"/first.jpg": (b"first-image", "image/jpeg"), "/second.png": (b"second-image", "image/png")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            posts = list((self.root / "downloads").iterdir())
            self.assertEqual(len(posts), 1, self.status(app))
            self.assertEqual((posts[0] / "001.jpg").read_bytes(), b"first-image")
            self.assertEqual((posts[0] / "002.png").read_bytes(), b"second-image")
            self.assertEqual((posts[0] / "正文.txt").read_text(encoding="utf-8"), "图文正文")

    async def test_missing_session_shows_qr_then_downloads_and_reuses_new_session(self):
        self.state.unlink()
        self.login_mode = True
        async with self.running() as (app, pilot):
            await self.wait_for(pilot, lambda: "扫码" in self.status(app))
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
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
            await pilot.click("#retry")
            await self.wait_for(pilot, lambda: not app.query_one(Input).disabled)
            self.assertIn("有效", self.status(app))

    async def test_image_post_without_text_downloads_normally(self):
        self.feed = {"picInfo": [{"url": "https://media.weixin.qq.com/one.jpg"}]}
        self.media = {"/one.jpg": (b"image-only", "image/jpeg")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))
            text = next((self.root / "downloads").glob("*/正文.txt"))
            self.assertEqual(text.read_text(encoding="utf-8"), "")

    async def test_invalid_link_does_not_start_a_download(self):
        async with self.running() as (app, pilot):
            await self.submit(app, pilot, "https://evil.invalid/sph/fixture")
            self.assertIn("请输入", self.status(app))
            self.assertEqual(list((self.root / "downloads").iterdir()), [])

    async def test_partial_download_is_not_published_and_existing_content_survives(self):
        self.media_length = 1000
        existing = self.root / "downloads" / "existing"
        existing.mkdir(parents=True)
        (existing / "video.mp4").write_bytes(b"keep-me")
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("不完整", self.status(app))
            self.assertEqual(list((self.root / "downloads").iterdir()), [existing])
            self.assertEqual((existing / "video.mp4").read_bytes(), b"keep-me")

    async def test_media_redirect_cannot_send_session_to_another_site(self):
        self.redirect = "https://evil.invalid/collect"
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("受支持", self.status(app))
            self.assertEqual(list((self.root / "downloads").iterdir()), [])
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
            await pilot.pause(1)
            self.assertIn("额外安全验证", self.status(app))
            self.assertEqual(self.state.read_bytes(), original)

    async def test_small_terminal_explains_how_to_show_the_complete_qr(self):
        self.login_mode = True
        async with self.running(size=(80, 24)) as (app, pilot):
            await self.wait_for(pilot, lambda: "█" in str(app.query_one("#qr", Static).render()))
            self.assertIn("增大", self.status(app))

    async def test_image_jpg_content_type_saves_jpeg_content(self):
        self.feed = {"picInfo": [{"url": "https://media.weixin.qq.com/photo"}]}
        self.media = {"/photo": (b"jpeg-content", "image/jpg")}
        async with self.running() as (app, pilot):
            await self.submit(app, pilot)
            self.assertIn("完成", self.status(app))
            self.assertEqual(next((self.root / "downloads").glob("*/001.jpg")).read_bytes(), b"jpeg-content")
