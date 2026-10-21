"""Local browser session, fixed upstream APIs and transactional downloads."""

from __future__ import annotations

import json
import asyncio
import io
import math
import os
import re
import tempfile
from collections.abc import Awaitable, Callable
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from playwright.async_api import Browser, BrowserContext, Playwright, Response, TimeoutError as BrowserTimeoutError, async_playwright
from PIL import Image
from rich.text import Text

from .archive import Archive, Media

YUANBAO = "https://yuanbao.tencent.com/"
USER_INFO = YUANBAO + "api/getuserinfo"
PARSE_API = YUANBAO + "api/weixin/get_parse_result"
FEED_API = "https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info"
TERMS = "https://rule.tencent.com/rule/202403110001"
PRIVACY = "https://privacy.qq.com/document/preview/eb9be56572ab4886b6ca124e72abf413"
BrowserSetup = Callable[[BrowserContext], Awaitable[None]]


class UserError(Exception):
    """A message safe to display without upstream URLs or credentials."""


def terminal_qr(data: bytes) -> Text:
    # Module detection and half-block rendering adapted from wx-video-account-notes (MIT).
    with Image.open(io.BytesIO(data)) as image:
        if image.width != image.height or not 21 <= image.width <= 1000:
            raise UserError("登录失败：二维码图片格式发生变化。")
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        gray = Image.alpha_composite(background, rgba).convert("L")
        pixels = gray.tobytes()
        rows = [[pixels[y * image.width + x] < 128 for x in range(image.width)] for y in range(image.height)]
    runs: Counter[int] = Counter()
    for row in rows:
        start = 0
        for x in range(1, len(row) + 1):
            if x == len(row) or row[x] != row[start]:
                if row[start]:
                    runs[x - start] += 1
                start = x
    unit = math.gcd(*(length for length, count in runs.items() if count >= 3))
    if unit < 1 or len(rows) % unit or not 21 <= len(rows) // unit <= 110:
        raise UserError("登录失败：无法识别二维码像素，请重试。")
    grid = [[row[x] for x in range(unit // 2, len(row), unit)] for row in rows[unit // 2::unit]]
    blank = [False] * (len(grid[0]) + 8)
    grid = [blank[:] for _ in range(4)] + [[False] * 4 + row + [False] * 4 for row in grid] + [blank[:] for _ in range(4)]
    if len(grid) % 2:
        grid.append(blank[:])
    chars = {(False, False): " ", (True, False): "▀", (False, True): "▄", (True, True): "█"}
    return Text("\n".join("".join(chars[a, b] for a, b in zip(grid[y], grid[y + 1]))
                          for y in range(0, len(grid), 2)), style="black on white", no_wrap=True)


class Session:
    def __init__(self, root: Path, transport: httpx.AsyncBaseTransport | None = None,
                 browser_setup: BrowserSetup | None = None) -> None:
        self.root = root
        self.transport = transport
        self.browser_setup = browser_setup
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.client = httpx.AsyncClient(transport=transport, timeout=30, follow_redirects=False)
        self.media_client = httpx.AsyncClient(transport=transport, timeout=60, follow_redirects=False)

    async def open(self) -> None:
        for name in ("data", "downloads"):
            folder = self.root / name
            folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.TemporaryFile(dir=folder):
                pass
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            channel="chromium", headless=True, ignore_default_args=["--enable-logging"])
        state = self.root / "data" / "session.json"
        self.context = await self.browser.new_context(
            storage_state=str(state) if state.exists() else None, locale="zh-CN")
        if self.browser_setup:
            await self.browser_setup(self.context)
        page = await self.context.new_page()
        await page.goto(YUANBAO, wait_until="domcontentloaded", timeout=45000)

    async def close(self) -> None:
        try:
            if self.browser:
                await self.browser.close()
        finally:
            if self.playwright:
                await self.playwright.stop()
            await self.client.aclose()
            await self.media_client.aclose()

    async def cookie(self) -> str:
        assert self.context is not None
        return "; ".join(f"{item['name']}={item['value']}" for item in await self.context.cookies(PARSE_API))

    async def authenticated(self) -> bool:
        cookie = await self.cookie()
        if not cookie:
            return False
        response = await self.client.get(USER_INFO, headers={"Cookie": cookie, "Referer": YUANBAO})
        if response.status_code == 401:
            return False
        if response.status_code != 200:
            raise UserError("暂时无法检查登录态，请检查网络后重试；已保存的登录态未修改。")
        try:
            identity = response.json()
        except ValueError:
            raise UserError("登录检查失败：元宝返回内容无法确认身份，已保存的登录态未修改。") from None
        if not isinstance(identity, dict) or not identity or identity.get("code", 0) not in (0, 200):
            raise UserError("登录检查失败：元宝身份响应发生变化，已保存的登录态未修改。")
        anonymous = identity.get("anonUser")
        if isinstance(anonymous, dict) and anonymous.get("isAnon") is True:
            return False
        if (not isinstance(identity.get("userId"), str) or not identity["userId"].strip()
                or not isinstance(anonymous, dict) or anonymous.get("isAnon") is not False):
            raise UserError("登录检查失败：未取得可确认的非访客身份，已保存的登录态未修改。")
        return True

    async def login(self, status: Callable[[str], None], qr: Callable[[Text], None],
                    confirm: Callable[[], None], approval: asyncio.Event) -> None:
        assert self.context is not None
        page = self.context.pages[0]
        status("正在等待元宝微信登录界面…")
        login_deadline = asyncio.get_running_loop().time() + 15
        while not await page.get_by_text("微信登录", exact=True).is_visible():
            if asyncio.get_running_loop().time() >= login_deadline:
                raise UserError("登录失败：未等到元宝微信登录界面，请检查网络或稍后重试。")
            try:
                if await page.get_by_text("微信", exact=True).is_visible():
                    await page.get_by_text("微信", exact=True).click(timeout=500)
                else:
                    await page.get_by_role("button", name="登录", exact=True).click(timeout=500)
            except BrowserTimeoutError:
                # An automatically opened login dialog can cover the homepage button during the click.
                pass
            await asyncio.sleep(0.1)
        status("请用微信扫码，并在手机上确认元宝登录。等待最多 3 分钟。")
        deadline = asyncio.get_running_loop().time() + 180
        displayed = ""
        next_check = 0.0
        failure = ""

        async def received(response: Response) -> None:
            nonlocal failure
            target = urlsplit(response.url)
            if target.hostname == "yuanbao.tencent.com" and target.path == "/api/joint/login" and response.status >= 400:
                message = "登录失败：元宝拒绝本次登录，请重新登录。"
                try:
                    if (await response.json()).get("safeVerifyTypes"):
                        message = "登录失败：元宝要求额外安全验证，当前无法继续，请稍后重试。"
                except Exception:
                    pass
                failure = message

        page.on("response", received)
        try:
            while asyncio.get_running_loop().time() < deadline:
                if failure:
                    raise UserError(failure)
                now = asyncio.get_running_loop().time()
                if now >= next_check:
                    if await self.authenticated():
                        await self.save_state()
                        return
                    next_check = now + 2
                for frame in page.frames:
                    host = urlsplit(frame.url).hostname or ""
                    if host.endswith(("captcha.qq.com", "captcha.qcloud.com")):
                        raise UserError("登录失败：元宝要求额外安全验证，当前无法继续，请稍后重试。")
                    if host != "open.weixin.qq.com":
                        continue
                    if await frame.locator(".js_wx_after_cancel:visible").count():
                        raise UserError("登录失败：手机端已取消，请重新登录。")
                    image = frame.locator("img.qrcode.js_qrcode_img:visible").first
                    if await image.count():
                        source = urljoin("https://open.weixin.qq.com/", await image.get_attribute("src") or "")
                        target = urlsplit(source)
                        if (target.scheme != "https" or target.hostname != "open.weixin.qq.com" or target.username
                                or target.password or target.port not in (None, 443)
                                or not target.path.startswith("/connect/qrcode/")):
                            raise UserError("登录失败：微信二维码来源发生变化。")
                        if source != displayed:
                            response = await self.media_client.get(source)
                            if response.status_code != 200 or len(response.content) > 1_000_000:
                                raise UserError("登录失败：无法取得微信二维码。")
                            rendered = terminal_qr(response.content)
                            image_path = self.root / "data" / "login-qr.png"
                            image_path.write_bytes(response.content)
                            image_path.chmod(0o600)
                            qr(rendered)
                            displayed = source
                    expired = frame.get_by_text(re.compile(r"二维码已(?:过期|失效)|二维码过期"))
                    if any([await item.is_visible() for item in await expired.all()]):
                        refresh = frame.locator(".js_refresh_qrcode:visible, .js_web_qrcode_reload:visible").first
                        if not await refresh.count():
                            raise UserError("登录失败：微信二维码已过期，请重新登录。")
                        await refresh.click(timeout=3000)
                        displayed = ""
                registration = page.get_by_role("button", name=re.compile(r"^(同意并注册|注册并登录|同意并登录)$"))
                if await registration.count() and await registration.first.is_visible():
                    status("元宝要求确认协议后注册/登录，请阅读协议并选择是否同意。")
                    confirm()
                    await asyncio.wait_for(approval.wait(), max(1, deadline - asyncio.get_running_loop().time()))
                    approval.clear()
                    await registration.first.click(timeout=5000)
                binding = page.get_by_text(re.compile(r"^跳过[，,、\s]*直接登录$"))
                if await binding.count() and await binding.first.is_visible():
                    await binding.first.click(timeout=3000)
                await asyncio.sleep(0.25)
            raise UserError("登录失败：等待扫码超时，请重新登录。")
        finally:
            page.remove_listener("response", received)
            (self.root / "data" / "login-qr.png").unlink(missing_ok=True)

    async def save_state(self) -> None:
        assert self.context is not None
        value = await self.context.storage_state(indexed_db=True)
        descriptor, name = tempfile.mkstemp(prefix=".session-", dir=self.root / "data")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(value, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.root / "data" / "session.json")
        finally:
            temporary.unlink(missing_ok=True)

    async def download(self, link: str, status: Callable[[str], None]) -> Archive:
        if not re.fullmatch(r"https://weixin\.qq\.com/sph/[A-Za-z0-9_-]+/?", link):
            raise UserError("请输入 https://weixin.qq.com/sph/... 视频号分享链接。")
        status("正在解析视频号内容…")
        responses: dict[str, Any] = {}
        first: dict[str, Any] = {}
        feed: dict[str, Any] = {}
        author_info: dict[str, Any] = {}
        errors: list[str] = []
        interrupted = False
        try:
            response = await self.client.post(
                PARSE_API, json={"type": "video_channel_url", "url": link, "scene": 1},
                headers={"Cookie": await self.cookie(), "Referer": YUANBAO, "Origin": YUANBAO.rstrip("/")})
            if response.status_code == 401:
                raise UserError("登录态已过期，请重新登录后下载。")
            response.raise_for_status()
            value = response.json()
            responses["yuanbao"] = value
            if not isinstance(value, dict) or value.get("code") != 0 or not isinstance(value.get("data"), dict):
                raise UserError("解析失败：元宝未能取得该视频号内容。")
            first = value["data"]
            if not isinstance(first.get("playable_url"), str):
                raise UserError("解析失败：视频号返回地址发生变化。")
            playable = urlsplit(first["playable_url"])
            if (playable.scheme != "https" or playable.hostname != "channels.weixin.qq.com"
                    or playable.username or playable.password or playable.port not in (None, 443)):
                raise UserError("解析失败：视频号返回地址发生变化。")
            query = parse_qs(playable.query)
            if not query.get("token") or not query.get("eid"):
                raise UserError("解析失败：缺少视频号访问参数。")
            response = await self.client.post(
                FEED_API, json={"baseReq": {"generalToken": query["token"][0]}, "exportId": query["eid"][0]},
                headers={"Referer": "https://channels.weixin.qq.com/finder-preview/pages/feed",
                         "Origin": "https://channels.weixin.qq.com"})
            response.raise_for_status()
            payload = response.json()
            responses["feed"] = payload
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
                raise UserError("解析失败：视频号响应格式发生变化。")
            data = payload["data"]
            error = data.get("errMsg") or {}
            if (payload.get("errCode", 0) != 0 or not isinstance(error, dict)
                    or error.get("type", 0) != 0 or error.get("title") or error.get("content")):
                raise UserError("解析失败：视频号内容不可用。")
            if not isinstance(data.get("feedInfo"), dict):
                raise UserError("解析失败：动态信息格式发生变化。")
            feed = data["feedInfo"]
            author = data.get("authorInfo") or {}
            if isinstance(author, dict):
                author_info = author
            else:
                errors.append("作者信息格式发生变化。")
        except asyncio.CancelledError:
            interrupted = True
        except Exception as error:
            if not responses:
                raise
            errors.append(str(error) if isinstance(error, UserError) else f"解析失败（{type(error).__name__}）")
        if not responses:
            raise asyncio.CancelledError
        description = feed.get("description") or feed.get("desc") or feed.get("title") or first.get("desc") or ""
        if not isinstance(description, str):
            errors.append("图文正文格式发生变化。")
            description = ""
        author = author_info.get("nickname") or feed.get("nickname") or feed.get("authorName") or first.get("author") or ""
        if not isinstance(author, str):
            errors.append("作者名称格式发生变化。")
            author = ""
        archive = Archive(self.root / "downloads", description, author, link.rstrip("/").rsplit("/", 1)[-1])
        archive.responses = responses
        archive.information = feed
        archive.errors = errors

        def add(label: str, kind: str, url: Any) -> None:
            if url is None or url == "":
                return
            if isinstance(url, str):
                archive.media.append(Media(label, kind, url))
            else:
                archive.errors.append(f"{label}地址格式发生变化。")

        for key, label in (("h264VideoInfo", "视频 h264"), ("h265VideoInfo", "视频 h265")):
            video = feed.get(key)
            if isinstance(video, dict):
                add(label, "video", video.get("videoUrl"))
            elif video is not None:
                archive.errors.append(f"{label}信息格式发生变化。")
        add("视频", "video", feed.get("videoUrl"))
        images = feed.get("picInfo") or []
        if not isinstance(images, list):
            archive.errors.append("图片列表格式发生变化。")
            images = []
        for index, image in enumerate(images, 1):
            if isinstance(image, dict):
                add(f"图片 {index:03d}", "image", image.get("url"))
            else:
                archive.errors.append(f"图片 {index:03d}信息格式发生变化。")
        for label, primary, secondary in (("封面", feed.get("coverUrl"), first.get("cover_url")),
                                           ("头像", author_info.get("headImgUrl"), first.get("author_icon")),
                                           ("认证图标", author_info.get("authIconUrl"), first.get("author_certification_icon"))):
            add(label, "image", primary)
            if secondary != primary:
                add(label + " 元宝", "image", secondary)
        bgm = feed.get("bgmInfo")
        if isinstance(bgm, dict):
            add("背景音乐", "audio", bgm.get("bgmUrl"))
            if bgm.get("mediaStreamingUrl") != bgm.get("bgmUrl"):
                add("背景音乐 备用", "audio", bgm.get("mediaStreamingUrl"))
        elif bgm is not None:
            archive.errors.append("背景音乐信息格式发生变化。")
        saved: dict[str, Path] = {}
        failed: dict[str, str] = {}
        try:
            if interrupted:
                raise asyncio.CancelledError
            for item in archive.media:
                status(f"正在下载{item.label}…")
                if item.url not in saved and item.url not in failed:
                    try:
                        saved[item.url] = await self.save_media(
                            item.url, archive.path / f"{archive.name}_{item.label.replace(' ', '_')}", kind=item.kind)
                    except Exception as error:
                        failed[item.url] = (str(error) if isinstance(error, UserError)
                                            else f"下载失败（{type(error).__name__}）")
                item.path = saved.get(item.url)
                item.error = failed.get(item.url, "")
            archive.state = "部分完成" if saved and (failed or archive.errors) else "完成" if saved else "失败"
            if not archive.media:
                archive.errors.append("没有可下载的视频、图片或音频。")
        finally:
            archive.write()
        return archive

    async def save_media(self, url: str, destination: Path, *, kind: str) -> Path:
        for _ in range(6):
            parts = urlsplit(url)
            if (kind == "audio" and parts.scheme == "http" and parts.hostname == "wx.music.tc.qq.com"
                    and not parts.username and not parts.password and parts.port in (None, 80)):
                parts = parts._replace(scheme="https", netloc="wx.music.tc.qq.com")
                url = urlunsplit(parts)
            host = parts.hostname or ""
            if (parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443)
                    or not any(host == suffix or host.endswith("." + suffix)
                               for suffix in ("qq.com", "weixin.qq.com", "qpic.cn", "qlogo.cn", "gtimg.com"))):
                raise UserError("下载失败：媒体地址不是受支持的腾讯 HTTPS 地址。")
            if kind == "video" and "X-snsvideoflag" in parse_qs(parts.query):
                query = urlencode([(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                                   if key != "X-snsvideoflag"])
                url = urlunsplit(parts._replace(query=query))
            async with self.media_client.stream("GET", url, headers={"Accept-Encoding": "identity"}) as media:
                if media.is_redirect:
                    url = urljoin(url, media.headers["location"])
                    continue
                media.raise_for_status()
                mime = media.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                stream = media.aiter_bytes()
                head = await anext(stream, b"")
                while mime == "application/octet-stream" and len(head) < 12:
                    chunk = await anext(stream, b"")
                    if not chunk:
                        break
                    head += chunk
                extensions = {"video": {"video/mp4": ".mp4", "video/webm": ".webm"},
                              "audio": {"audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/mpeg": ".mp3", "audio/aac": ".aac",
                                        "audio/ogg": ".ogg", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/flac": ".flac"},
                              "image": {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                                        "image/gif": ".gif", "image/avif": ".avif"}}[kind]
                extension = extensions.get(mime)
                if kind == "video" and mime == "application/octet-stream":
                    extension = ".mp4" if head[4:8] == b"ftyp" else ".webm" if head.startswith(b"\x1aE\xdf\xa3") else None
                if extension is None:
                    raise UserError("下载失败：媒体服务返回的不是受支持的媒体格式。")
                target = Path(str(destination) + extension)
                temporary = Path(str(target) + ".part")
                try:
                    with temporary.open("xb") as output:
                        size = output.write(head)
                        async for chunk in stream:
                            size += output.write(chunk)
                    expected = media.headers.get("content-length")
                    if not size or (expected and not media.headers.get("content-encoding") and size != int(expected)):
                        raise UserError("下载失败：媒体文件不完整。")
                    temporary.rename(target)
                finally:
                    temporary.unlink(missing_ok=True)
                return target
        raise UserError("下载失败：媒体重定向次数过多。")
