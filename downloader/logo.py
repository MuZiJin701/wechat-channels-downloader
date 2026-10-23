"""Small pixel logo, with conservative terminal probing and a text-only fallback."""

from __future__ import annotations

import base64
import io
import os
import re
import sys
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image
from textual.geometry import Region, Size
from textual.widgets import Static

_CELL = re.compile(r"\x1b\[6;([0-9]+);([0-9]+)t")
_DA = re.compile(r"\x1b\[\?([\d;]+)c")
_KITTY = re.compile(r"\x1b_Gi=7319;[^\x1b]*\x1b\\")


def query_terminal(query: str) -> str:
    """Query before Textual owns stdin, always restoring the terminal modes."""
    source, target = sys.__stdin__, sys.__stdout__
    if source is None or target is None:
        return ""
    descriptor = source.fileno()
    if sys.platform == "win32":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        input_handle = msvcrt.get_osfhandle(descriptor)
        output_handle = msvcrt.get_osfhandle(target.fileno())
        input_mode, output_mode = wintypes.DWORD(), wintypes.DWORD()
        if not kernel.GetConsoleMode(input_handle, ctypes.byref(input_mode)):
            return ""
        if not kernel.GetConsoleMode(output_handle, ctypes.byref(output_mode)):
            return ""
        try:
            if not kernel.SetConsoleMode(output_handle, output_mode.value | 4):
                return ""
            if not kernel.SetConsoleMode(input_handle, 0x0200):
                return ""
            target.write(query)
            target.flush()
            reply = ""
            deadline = time.monotonic() + .3
            while time.monotonic() < deadline and len(reply) < 8192:
                if msvcrt.kbhit():
                    reply += msvcrt.getwch()
                    if _DA.search(reply):
                        break
                else:
                    time.sleep(.005)
            return reply
        finally:
            kernel.SetConsoleMode(input_handle, input_mode.value)
            kernel.SetConsoleMode(output_handle, output_mode.value)
    else:
        import select
        import termios
        import tty

        original = termios.tcgetattr(descriptor)
        try:
            tty.setcbreak(descriptor, termios.TCSANOW)
            target.write(query)
            target.flush()
            data = b""
            deadline = time.monotonic() + .3
            while len(data) < 8192:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([descriptor], [], [], remaining)[0]:
                    break
                data += os.read(descriptor, 8192 - len(data))
                if _DA.search(data.decode("utf-8", errors="replace")):
                    break
            return data.decode("utf-8", errors="replace")
        finally:
            termios.tcsetattr(descriptor, termios.TCSANOW, original)


def probe_terminal(*, enabled: bool) -> tuple[str, Size, str]:
    """Require a positive protocol reply and pixel cell size; never guess from OS."""
    empty = ("", Size(0, 0), "")
    terminal = os.environ.get("TERM", "")
    if (not enabled or "NO_COLOR" in os.environ or os.environ.get("TMUX") or os.environ.get("STY")
            or terminal == "dumb" or terminal.startswith(("screen", "tmux"))
            or os.environ.get("TERM_PROGRAM") == "Apple_Terminal"
            or not sys.__stdin__ or not sys.__stdout__
            or not sys.__stdin__.isatty() or not sys.__stdout__.isatty()):
        return empty
    kitty = ("kitty" in terminal or bool(os.environ.get("KITTY_WINDOW_ID"))
             or os.environ.get("TERM_PROGRAM") in ("ghostty", "WezTerm"))
    query = ("\x1b_Gi=7319,a=q,t=d,f=24,s=1,v=1;AAAA\x1b\\" if kitty else "")
    try:
        reply = query_terminal(query + "\x1b[16t\x1b[c")
    except (OSError, ValueError):
        return empty
    pending = _KITTY.sub("", _DA.sub("", _CELL.sub("", reply)))
    cell, attributes = _CELL.search(reply), _DA.search(reply)
    if cell is None or attributes is None or any(len(value) > 3 for value in cell.groups()):
        return "", Size(0, 0), pending
    height, width = map(int, cell.groups())
    if not (1 <= width <= 256 and 1 <= height <= 256):
        return "", Size(0, 0), pending
    protocol = ("kitty" if "\x1b_Gi=7319;OK\x1b\\" in reply else
                "sixel" if "4" in attributes[1].split(";") else "")
    return protocol, Size(width, height), pending


def sixel(image: Image.Image) -> str:
    """Encode this small opaque RGB image using a bounded 64-color palette."""
    indexed = image.quantize(colors=64)
    palette = indexed.getpalette()
    assert palette is not None
    pixels = indexed.tobytes()
    width, height = image.size
    parts = [f'\x1bP0;1q"1;1;{width};{height}']
    for index in sorted(set(pixels)):
        red, green, blue = (round(value * 100 / 255) for value in palette[index * 3:index * 3 + 3])
        parts.append(f"#{index};2;{red};{green};{blue}")
    for top in range(0, height, 6):
        band = pixels[top * width:(top + 6) * width]
        for index in sorted(set(band)):
            row = "".join(chr(63 + sum(1 << y for y in range(min(6, height - top))
                                       if band[y * width + x] == index)) for x in range(width)).rstrip("?")
            row = re.sub(r"(.)\1{3,}", lambda match: f"!{len(match[0])}{match[1]}", row)
            parts.append(f"#{index}{row}$")
        if top + 6 < height:
            parts.append("-")
    return "".join(parts) + "\x1b\\"


class TerminalLogo(Static):
    def __init__(self) -> None:
        super().__init__("", id="logo")
        self.protocol = ""
        # shortcut: measure pixels at startup; re-probe when adding live font/DPI changes.
        self.cell = Size(0, 0)
        self.image: Image.Image | None = None
        self.placements = 0

    def load(self, protocol: str, cell: Size) -> None:
        self.protocol, self.cell = protocol, cell
        if protocol:
            try:
                with Image.open(Path(__file__).with_name("assets") / "logo.png") as image:
                    self.image = image.convert("RGBA")
            except (OSError, ValueError):
                self.protocol = ""

    @lru_cache(maxsize=128)
    def encode(self, size: Size, crop: Region, background: str) -> str:
        assert self.image is not None
        canvas = Image.new("RGB", (size.width * self.cell.width, size.height * self.cell.height), background)
        side = min(canvas.size)
        icon = self.image.resize((side, side), Image.Resampling.LANCZOS)
        canvas.paste(icon, ((canvas.width - side) // 2, (canvas.height - side) // 2), icon)
        canvas = canvas.crop((crop.x * self.cell.width, crop.y * self.cell.height,
                              crop.right * self.cell.width, crop.bottom * self.cell.height))
        if self.protocol == "sixel":
            return sixel(canvas)
        stream = io.BytesIO()
        canvas.save(stream, format="PNG")
        return base64.b64encode(stream.getvalue()).decode("ascii")

    def clear(self) -> str:
        result = "".join(f"\x1b_Ga=d,d=I,i={7320 + index},q=2\x1b\\" for index in range(self.placements))
        self.placements = 0
        return result

    def draw(self) -> str:
        sequence = self.clear()
        if not self.protocol or not self.display or not self.is_on_screen:
            return sequence
        region = self.content_region
        background = self.background_colors[1].hex
        # Emit only uncovered cell runs, so overlays and clipping also apply to pixels.
        for row in range(region.height):
            start: int | None = None
            for column in range(region.width + 1):
                visible = (column < region.width and self.app.screen.region.contains(region.x + column, region.y + row)
                           and self.app.get_widget_at(region.x + column, region.y + row)[0] is self)
                if visible and start is None:
                    start = column
                elif not visible and start is not None:
                    crop = Region(start, row, column - start, 1)
                    sequence += f"\x1b[{region.y + row + 1};{region.x + start + 1}H"
                    data = self.encode(region.size, crop, background)
                    if self.protocol == "sixel":
                        sequence += data
                    else:
                        identifier = 7320 + self.placements
                        # PNG rows are small, but respect kitty's 4096-byte payload limit.
                        for offset in range(0, len(data), 4096):
                            more = int(offset + 4096 < len(data))
                            command = f"a=T,f=100,t=d,i={identifier},q=2,c={crop.width},r=1," if offset == 0 else ""
                            sequence += f"\x1b_G{command}m={more};{data[offset:offset + 4096]}\x1b\\"
                        self.placements += 1
                    start = None
        return sequence
