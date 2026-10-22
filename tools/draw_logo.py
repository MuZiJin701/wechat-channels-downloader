"""Regenerate the shared PNG, Windows ICO and macOS ICNS with installed Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    folder = Path(__file__).resolve().parents[1] / "downloader" / "assets"
    folder.mkdir(exist_ok=True)
    size = 2048
    image = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(image)
    for y in range(size):
        blend = y / (size - 1)
        color = tuple(round(a + (b - a) * blend) for a, b in zip((31, 107, 64), (119, 213, 155)))
        draw.line((0, y, size, y), fill=(*color, 255))
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size * .22, fill=255)
    image.putalpha(mask)
    draw.polygon([(size * .36, size * .19), (size * .36, size * .49), (size * .66, size * .34)], fill="white")
    stroke = round(size * .055)
    draw.line([(size * .5, size * .53), (size * .5, size * .69)], fill="white", width=stroke)
    draw.line([(size * .4, size * .61), (size * .5, size * .71), (size * .6, size * .61)],
              fill="white", width=stroke, joint="curve")
    draw.line([(size * .25, size * .70), (size * .25, size * .81),
               (size * .75, size * .81), (size * .75, size * .70)],
              fill="white", width=stroke, joint="curve")
    image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
    image.resize((512, 512), Image.Resampling.LANCZOS).save(folder / "logo.png")
    image.save(folder / "logo.ico", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    image.save(folder / "logo.icns")
    with Image.open(folder / "logo.png") as png, Image.open(folder / "logo.ico") as ico, Image.open(folder / "logo.icns") as icns:
        assert png.size == (512, 512) and png.getchannel("A").getextrema() == (0, 255)
        assert {(16, 16), (256, 256)} <= ico.info["sizes"]
        assert icns.size == (1024, 1024)
    print("LOGO_OK: PNG, ICO (16–256), ICNS (1024).")


if __name__ == "__main__":
    main()
