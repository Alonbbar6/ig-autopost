import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = (15, 23, 42)
ACCENT = (56, 189, 248)
TEXT = (248, 250, 252)
MUTED = (148, 163, 184)
HANDLE = "@bardaleslabs"
TAGLINE = "Websites + AI | Miami"

# Linux (GitHub Actions) first, then macOS, so previews work locally too.
FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FONT_REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def find_font(paths):
    for p in paths:
        if Path(p).exists():
            return p
    sys.exit(f"No font found, tried: {paths}")


FONT_BOLD = find_font(FONT_BOLD_PATHS)
FONT_REG = find_font(FONT_REG_PATHS)


def wrap(draw, text, font, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=font) <= max_w or not line:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def make_thumb(headline, subline, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    pad = 90
    d.rectangle([pad, pad, pad + 140, pad + 14], fill=ACCENT)

    size = 110
    while size > 50:
        font = ImageFont.truetype(FONT_BOLD, size)
        lines = wrap(d, headline, font, W - 2 * pad)
        widest = max(d.textlength(ln, font=font) for ln in lines)
        if len(lines) * size * 1.15 < H * 0.55 and widest <= W - 2 * pad:
            break
        size -= 6
    y = 260
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=TEXT)
        y += int(size * 1.15)

    if subline:
        sf = ImageFont.truetype(FONT_REG, 46)
        y += 40
        for ln in wrap(d, subline, sf, W - 2 * pad):
            d.text((pad, y), ln, font=sf, fill=MUTED)
            y += 60

    bf = ImageFont.truetype(FONT_BOLD, 40)
    tf = ImageFont.truetype(FONT_REG, 36)
    d.text((pad, H - pad - 40), HANDLE, font=bf, fill=ACCENT)
    d.text((W - pad - d.textlength(TAGLINE, font=tf), H - pad - 36), TAGLINE, font=tf, fill=MUTED)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=92)
    return out_path


if __name__ == "__main__":
    make_thumb(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "posts/test.jpg")
