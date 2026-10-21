"""Offline packaged-entry check; no real account or application data is used."""

import json
import tempfile
from pathlib import Path
from typing import Any

import httpx
from playwright.async_api import BrowserContext, Route
from textual.pilot import Pilot
from textual.widgets import Input

from .app import DownloaderApp


async def smoke(*, terminal: bool = False) -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "data").mkdir()
        (root / "data" / "session.json").write_text(json.dumps({
            "cookies": [{"name": "session", "value": "offline-fixture", "domain": "yuanbao.tencent.com",
                         "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"}],
            "origins": [],
        }), encoding="utf-8")

        async def setup(context: BrowserContext) -> None:
            async def route(request: Route) -> None:
                await request.fulfill(content_type="text/html", body="<html></html>")
            await context.route("**/*", route)

        def external(request: httpx.Request) -> httpx.Response:
            if request.url.path != "/api/getuserinfo":
                raise AssertionError("Unexpected external request in offline smoke test")
            return httpx.Response(200, json={"userId": "offline-fixture", "anonUser": {"isAnon": False}})

        app = DownloaderApp(root=root, transport=httpx.MockTransport(external), browser_setup=setup)

        async def check(pilot: Pilot[Any]) -> None:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.query_one(Input).disabled, "Packaged browser/TUI failed to reach link input"
            if terminal:
                await pilot.press("ctrl+q")

        if terminal:
            await app.run_async(auto_pilot=check, size=(100, 40))
        else:
            async with app.run_test(size=(100, 40)) as pilot:
                await check(pilot)
