import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Matches the portfolio at alonso-portfolio.pages.dev: ink background, volt accent,
# Big Shoulders Display headlines, Hanken Grotesk body.
W, H = 1080, 1350
BG = (11, 11, 11)
ACCENT = (254, 214, 10)
TEXT = (250, 250, 250)
MUTED = (160, 160, 160)
HANDLE = "@bardaleslabs"
TAGLINE = "ALONSO BRYAN / WEBSITES, APPS + AI"
SITE = "alonso-portfolio.pages.dev"

FONTS = Path(__file__).parent / "fonts"
DISPLAY = FONTS / "BigShouldersDisplay.ttf"
BODY = FONTS / "HankenGrotesk.ttf"


def font(path, size, weight):
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_name(weight)
    return f


def wrap(draw, text, fnt, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=fnt) <= max_w or not line:
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
    max_w = W - 2 * pad

    d.text((pad, pad), TAGLINE, font=font(BODY, 30, "SemiBold"), fill=MUTED)
    d.rectangle([pad, pad + 64, pad + 140, pad + 78], fill=ACCENT)

    headline = headline.upper()
    size = 190
    while size > 70:
        hf = font(DISPLAY, size, "Black")
        lines = wrap(d, headline, hf, max_w)
        widest = max(d.textlength(ln, font=hf) for ln in lines)
        if len(lines) * size * 0.95 < H * 0.58 and widest <= max_w:
            break
        size -= 8
    y = 270
    for ln in lines:
        d.text((pad, y), ln, font=hf, fill=TEXT)
        y += int(size * 0.95)

    if subline:
        sf = font(BODY, 46, "Medium")
        y += 44
        for ln in wrap(d, subline, sf, max_w):
            d.text((pad, y), ln, font=sf, fill=MUTED)
            y += 62

    d.line([pad, H - pad - 80, W - pad, H - pad - 80], fill=(40, 40, 40), width=2)
    bf = font(BODY, 40, "Bold")
    tf = font(BODY, 34, "Medium")
    d.text((pad, H - pad - 44), HANDLE, font=bf, fill=ACCENT)
    d.text((W - pad - d.textlength(SITE, font=tf), H - pad - 40), SITE, font=tf, fill=MUTED)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=92)
    return out_path


if __name__ == "__main__":
    make_thumb(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "posts/test.jpg")
