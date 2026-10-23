"""Draw the static Royal Violet project poster with the existing Pillow dependency."""

import argparse
import base64
import io
import math
import os
from pathlib import Path
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
SIZE = (1800, 2400)
URL = "https://github.com/MuZiJin701/wechat-channels-downloader"
OUTPUT = ROOT / "docs/images/宣传海报.png"
# Fixed URL, version 4-M, four-module quiet zone; encoded once with npm's qrcode-terminal.
QR_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAACkAAAApAQAAAACAGz1bAAABBUlEQVR4nGP8z8DAwNDIBCIZGNCoj8IOuhwM"
    "jN/v3/0U1Mn0t+PgBQUGJobP/h0gJRy3fzAwMDG37dF4wMD00+y3uQADw/8Pv57/b2D6Ouu+3AoGxi/s"
    "Dydov2T8E8VcGhnJ+Onzxie2J5m4Xl7x6GBg+pd15ksAA9MfxQ//ChhYOELvtbxmYPwpoX9SLJGJTe2Z"
    "BQcDE4Og41UNBqZfc3eelmBgYiqzvGfBwPQ9RDDPgoGJS533twAD0x+vBzYnGJj+mWnHdDAw/v+4q5fD"
    "kemjqsY7BwaG79dD2dkbmP42mf50YGBi+PFRrwDksSY9DQbG7w9PKJV6Mv20efBcg4ERTxAAAIvgXHFU"
    "VslyAAAAAElFTkSuQmCC"
)


def sky() -> Image.Image:
    image = Image.new("RGB", SIZE, "#030206")
    draw = ImageDraw.Draw(image)
    rng = random.Random(701)
    for _ in range(310):
        x, y = rng.randrange(SIZE[0]), rng.randrange(SIZE[1])
        brightness = rng.randrange(40, 135)
        radius = rng.choice((0, 0, 0, 1, 1, 2))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     fill=(brightness, brightness, min(255, brightness + 25)))

    # A huge planet extends beyond the canvas; only its luminous lower rim is visible.
    rim = [(x, -800 + 1160 * math.sqrt(1 - ((x - 900) / 1480) ** 2))
           for x in range(-40, 1841, 3)]
    draw.polygon([(-40, 0), (1840, 0), *reversed(rim)], fill="#030206")
    for width, blur, color in ((45, 100, "#5616ab"), (25, 42, "#9312ff"),
                                (9, 14, "#b750ff"), (3, 1, "#ecc8ff")):
        edge = Image.new("RGB", (3600, 1000))
        ImageDraw.Draw(edge).line([(x * 2, y * 2) for x, y in rim],
                                 fill=color, width=width * 2, joint="curve")
        layer = Image.new("RGB", SIZE)
        layer.paste(edge.resize((1800, 500), Image.Resampling.LANCZOS))
        image = ImageChops.screen(image, layer.filter(ImageFilter.GaussianBlur(blur)))

    glow = Image.new("RGB", SIZE)
    ImageDraw.Draw(glow).ellipse((50, 980, 1750, 1900), fill="#32115c")
    return ImageChops.screen(image, glow.filter(ImageFilter.GaussianBlur(170)))


def panel(image: Image.Image, source: str, box: tuple[int, int, int, int],
          x: int, y: int, width: int, title: str, font: ImageFont.FreeTypeFont) -> None:
    with Image.open(ROOT / "docs/images" / source) as original:
        assert 0 <= box[0] < box[2] <= original.width
        assert 0 <= box[1] < box[3] <= original.height
        screenshot = original.crop(box).convert("RGB")
    header, padding = 56, 6
    height = round(screenshot.height * (width - 2 * padding) / screenshot.width)
    assert x >= 0 and y >= 0 and x + width <= SIZE[0] and y + header + height + padding <= 2120
    frame_box = (x, y, x + width, y + header + height + padding)
    shadow = Image.new("RGBA", SIZE)
    ImageDraw.Draw(shadow).rounded_rectangle(frame_box, radius=22, fill=(0, 0, 0, 220))
    image.paste(Image.alpha_composite(image.convert("RGBA"),
                shadow.filter(ImageFilter.GaussianBlur(28))).convert("RGB"))
    glow = Image.new("RGB", SIZE)
    ImageDraw.Draw(glow).rounded_rectangle(frame_box, radius=22, outline="#9312ff", width=5)
    image.paste(ImageChops.screen(image, glow.filter(ImageFilter.GaussianBlur(16))))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(frame_box, radius=22, fill="#100b1b", outline="#8550c2", width=2)
    for index, color in enumerate(("#704b87", "#9360ad", "#bf85d8")):
        dot_x = x + 27 + index * 21
        draw.ellipse((dot_x - 4, y + 24, dot_x + 4, y + 32), fill=color)
    draw.text((x + width - 24, y + 17), title, font=font, fill="#cfb7e9", anchor="rt")
    image.paste(screenshot.resize((width - 2 * padding, height), Image.Resampling.LANCZOS),
                (x + padding, y + header))
    draw.line((x + 25, y, x + width - 25, y), fill="#cf9cff", width=2)


def repository_qr() -> Image.Image:
    with Image.open(io.BytesIO(base64.b64decode(QR_PNG))) as source:
        qr = source.convert("L")
    assert qr.size == (41, 41) and qr.getextrema() == (0, 255)
    for border in ((0, 0, 41, 4), (0, 37, 41, 41), (0, 0, 4, 41), (37, 0, 41, 41)):
        assert qr.crop(border).getextrema() == (255, 255), "QR quiet zone was damaged"
    return qr.resize((246, 246), Image.Resampling.NEAREST).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, help="Chinese TTF/TTC/OTF; defaults to Windows Microsoft YaHei")
    args = parser.parse_args()
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    regular = args.font or fonts / "msyh.ttc"
    bold = args.font or fonts / "msyhbd.ttc"
    if not regular.is_file() or not bold.is_file():
        parser.error("Chinese font not found; supply --font /path/to/Chinese-font.ttf")

    def font(size: int, heavy: bool = False) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(bold if heavy else regular), size)

    image = sky()
    draw = ImageDraw.Draw(image)

    def centered(y: int, text: str, size: int, color: str, heavy: bool = False) -> None:
        face = font(size, heavy)
        bounds = draw.textbbox((900, y), text, font=face, anchor="mt")
        assert 90 <= bounds[0] < bounds[2] <= 1710 and 0 <= bounds[1] < bounds[3] <= SIZE[1]
        draw.text((900, y), text, font=face, fill=color, anchor="mt")

    with Image.open(ROOT / "downloader/assets/logo.png") as original_logo:
        logo = original_logo.convert("RGBA").resize((66, 66), Image.Resampling.LANCZOS)
        image.paste(logo, (112, 77), logo)
    draw.text((200, 92), "微信视频号下载", font=font(34, True), fill="#f7f7f8", anchor="lt")
    draw.text((1688, 101), "LOCAL ARCHIVE", font=font(23), fill="#a698b9", anchor="rt")
    centered(416, "WECHAT CHANNELS DOWNLOADER", 24, "#b9a2d8")
    centered(492, "保存每一份，", 118, "#f7f7f8", True)

    mask = Image.new("L", SIZE)
    ImageDraw.Draw(mask).text((900, 650), "值得留下的内容。", font=font(118, True), fill=255, anchor="mt")
    title_bounds = mask.getbbox()
    assert title_bounds is not None and 90 <= title_bounds[0] < title_bounds[2] <= 1710
    assert 650 <= title_bounds[1] < title_bounds[3] <= 800
    ink = Image.new("RGB", SIZE)
    ink_draw = ImageDraw.Draw(ink)
    for y in range(650, 800):
        t = (y - 650) / 150
        ink_draw.line((0, y, SIZE[0], y), fill=(round(229 - 66 * t), round(195 - 112 * t), 255))
    image.paste(ink, (0, 0), mask)
    centered(818, "独立运行，无需打开电脑微信。", 42, "#f3e9ff", True)
    centered(891, "扫码登录、粘贴下载，一处完成。", 28, "#c8ace8")
    centered(951, "下载视频与图文，保留正文、作者和发布时间。", 27, "#a99dbb")

    panel(image, "深色模式使用截图.png", (6, 62, 1326, 735),
          110, 1045, 1470, "深色外观", font(23))
    panel(image, "浅色模式使用截图.png", (0, 52, 1357, 735),
          792, 1578, 898, "浅色外观", font(23))

    draw = ImageDraw.Draw(image)
    draw.line((112, 2130, 1380, 2130), fill="#34243f", width=2)
    draw.rounded_rectangle((112, 2190, 617, 2273), radius=41, fill="#8b20ed")
    draw.text((364, 2210), "前往 GitHub 获取  ↗", font=font(32, True), fill="#ffffff", anchor="mt")
    url_font = font(26)
    url_bounds = draw.textbbox((112, 2310), URL, font=url_font, anchor="lt")
    assert url_bounds[2] < 1398
    draw.text((112, 2310), URL, font=url_font, fill="#c5b4d9", anchor="lt")
    qr = repository_qr()
    image.paste(qr, (1442, 2114))
    draw.text((1565, 2372), "扫码访问项目仓库", font=font(18), fill="#b9a2d8", anchor="mt")

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", "微信视频号下载 · Royal Violet")
    metadata.add_text("Repository", URL)
    image.save(OUTPUT, pnginfo=metadata, optimize=True)
    with Image.open(OUTPUT) as result:
        assert result.size == SIZE and result.mode == "RGB"
        assert result.crop((1442, 2114, 1688, 2360)).tobytes() == qr.tobytes()
        assert result.info["Repository"] == URL
    print(f"POSTER_OK: {OUTPUT} ({SIZE[0]}x{SIZE[1]})")


if __name__ == "__main__":
    main()
