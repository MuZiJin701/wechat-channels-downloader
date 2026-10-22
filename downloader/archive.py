"""A local dynamic archive: safe names, original responses and an offline page."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote


@dataclass
class Media:
    label: str
    kind: str
    url: str
    path: Path | None = None
    error: str = ""


class Archive:
    def __init__(self, parent: Path, description: str, author: str, share_id: str) -> None:
        self.description = description
        self.author = author
        name = "_".join(part for part in (author, description[:40] or share_id) if part)
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", name).strip(" .")
        name = name.encode("utf-8")[:90].decode("utf-8", errors="ignore").rstrip(" .") or share_id
        if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"{p}{n}" for p in ("COM", "LPT") for n in range(1, 10))}:
            name = "_" + name
        self.name = name
        for number in range(1, 1_000_000):
            self.path = parent / (name if number == 1 else f"{name}_{number}")
            try:
                self.path.mkdir(mode=0o700)
                break
            except FileExistsError:
                continue
        else:
            raise OSError("Too many archives with this name")
        self.responses: dict[str, Any] = {}
        self.media: list[Media] = []
        self.information: dict[str, Any] = {}
        self.errors: list[str] = []
        self.state = "已中断"

    def write(self) -> None:
        for name, response in self.responses.items():
            self.write_text(f"{name}.json", json.dumps(response, ensure_ascii=False, indent=2))
        resources = []
        for item in self.media:
            label = escape(item.label)
            if item.path is None:
                resources.append(f"<li>{label}：{escape(item.error or '未完成')}</li>")
                continue
            source = quote(item.path.name, safe="")
            if item.kind == "image":
                preview = f'<img src="{source}" alt="{label}" loading="lazy">'
            else:
                preview = f'<{item.kind} src="{source}" controls preload="none"></{item.kind}>'
            resources.append(f'<li><h2>{label}</h2>{preview}<p><a href="{source}" download>打开 / 保存文件</a></p></li>')
        errors = "".join(f"<li>{escape(error)}</li>" for error in self.errors)
        details = []
        timestamp = self.information.get("createtime")
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            try:
                details.append("时间（UTC）：" + datetime.fromtimestamp(timestamp, timezone.utc).isoformat())
            except (ValueError, OverflowError, OSError):
                pass
        for key, label in (("likeCountFmt", "点赞"), ("favCountFmt", "收藏"),
                           ("forwardCountFmt", "转发"), ("commentCountFmt", "评论")):
            value = self.information.get(key)
            if isinstance(value, (str, int)):
                details.append(f"{label}：{value}（查询时展示值）")
        jump = self.information.get("jumpInfo")
        if isinstance(jump, dict) and isinstance(jump.get("wording"), str):
            details.append(jump["wording"])
        information = "".join(f"<p>{escape(value)}</p>" for value in details)
        links = " · ".join(f'<a href="{name}.json">{label}</a>' for name, label in
                           (("parse", "解析原始数据"), ("feed", "动态原始数据")) if name in self.responses)
        self.write_text("index.html", f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{escape(self.name)}</title><style>
:root {{ color-scheme: light dark; font-family: system-ui,sans-serif; }}
body {{ max-width: 64rem; margin: auto; padding: 1.5rem; overflow-wrap: anywhere; }}
#description {{ white-space: pre-wrap; }} img,video {{ max-width: 100%; max-height: 75vh; }}
audio {{ max-width: 100%; }} ul {{ list-style: none; padding: 0; }} li {{ margin: 1.5rem 0; }}
</style></head><body><h1>{escape(self.name)}</h1><p id="result">{escape(self.state)}</p>
<p id="author">{escape(self.author)}</p><p id="description">{escape(self.description)}</p>
{information}<ul>{errors}</ul><ul>{''.join(resources)}</ul><p>{links}</p></body></html>''')

    def write_text(self, name: str, text: str) -> None:
        temporary = self.path / (name + ".part")
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(self.path / name)
        finally:
            temporary.unlink(missing_ok=True)
