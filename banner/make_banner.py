#!/usr/bin/env python3
"""Warstwa banera: podpis na zdjeciu + doklejony panel z licznikiem technologii.

Jeden PNG nakladany na kazda klatke gifa, zamiast osobnego obrazka pod banerem
- inaczej GitHub wstawia miedzy obrazki odstep i szew widac.

Gorna krawedz panelu bierze kolory z ostatniego rzedu pikseli kadru, wiec
przejscie zdjecie -> panel nie ma widocznej linii.

    python3 make_banner.py edge.png stats.json banner.png
"""

import json
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = 1010
PHOTO_H = 342
PANEL_H = 150
H = PHOTO_H + PANEL_H

K = W / 880  # podpis projektowany na 880px, reszta skaluje sie proporcjonalnie
PAD = round(46 * K)

SCRIM_END = 0.62  # gdzie cien na zdjeciu zanika - dalej ma zostac czyste
SCRIM_MAX = 205

CREAM = (255, 243, 226)
AMBER = (255, 196, 107)
EMBER = (242, 107, 58)
MUTED = (201, 161, 135)
PANEL_BASE = (26, 14, 10)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

NAME = "Kaja Thiel"
TAGLINE = "python · ai · web"
PANEL_TITLE = "CZYM SIĘ ZAJMUJĘ"

BAR_H = 16
LEGEND_ROWS = 2
LEGEND_COLUMNS = 5
MERGE_BELOW = 1.0  # jezyki ponizej tego procenta ida do jednego wycinka
MAX_SLICES = LEGEND_ROWS * LEGEND_COLUMNS - 1  # ostatnie miejsce trzyma "inne"
OTHERS = "inne"

# paleta idzie po kolejnosci wycinkow, a nie po nazwach jezykow - inaczej
# pierwszy nowy jezyk w profilu wywala generator na braku koloru.
# Jasne i ciemne na przemian, zeby sasiednie wycinki dalo sie rozroznic.
PALETTE = [
    (232, 84, 47),
    (255, 196, 107),
    (193, 68, 14),
    (242, 147, 74),
    (138, 51, 36),
    (255, 164, 91),
    (107, 58, 42),
    (217, 164, 65),
    (166, 74, 40),
    (255, 218, 160),
]
OTHERS_COLOR = (74, 46, 36)


def color_of(index: int, name: str) -> tuple:
    if name == OTHERS:
        return OTHERS_COLOR
    return PALETTE[index % len(PALETTE)]


def paint_scrim(canvas: Image.Image) -> None:
    row = Image.new("L", (W, 1))
    for x in range(W):
        fade = max(0.0, 1.0 - x / (W * SCRIM_END))
        row.putpixel((x, 0), int(SCRIM_MAX * fade**1.5))
    canvas.paste(
        Image.new("RGBA", (W, PHOTO_H), (18, 10, 8, 255)),
        (0, 0),
        row.resize((W, PHOTO_H)),
    )


def paint_panel(canvas: Image.Image, edge: Image.Image) -> None:
    bottom_row = edge.crop((0, PHOTO_H - 1, W, PHOTO_H)).convert("RGB")
    bleed = Image.blend(
        bottom_row.resize((W, PANEL_H)).filter(ImageFilter.GaussianBlur(6)),
        Image.new("RGB", (W, PANEL_H), PANEL_BASE),
        0.45,  # jasna prawa strona kadru zjadala kontrast napisow w panelu
    )

    settle = Image.new("L", (1, PANEL_H))
    for y in range(PANEL_H):
        settle.putpixel((0, y), min(255, int(255 * (y / 34) ** 0.7)))

    panel = Image.composite(
        Image.new("RGB", (W, PANEL_H), PANEL_BASE),
        bleed,
        settle.resize((W, PANEL_H)),
    )
    canvas.paste(panel.convert("RGBA"), (0, PHOTO_H))


def draw_tracked(draw, xy, text, font, fill, tracking, shadow=True):
    x, y = xy
    for char in text:
        if shadow:
            draw.text((x + 2, y + 2), char, font=font, fill=(20, 10, 6, 190))
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + tracking
    return x


def draw_title(draw: ImageDraw.ImageDraw) -> None:
    draw_tracked(
        draw, (46 * K, 86 * K), NAME, ImageFont.truetype(BOLD, int(52 * K)),
        CREAM, K,
    )
    draw.line(
        [(50 * K, 162 * K), (232 * K, 162 * K)], fill=EMBER + (255,),
        width=round(3 * K),
    )
    draw_tracked(
        draw, (50 * K, 180 * K), TAGLINE, ImageFont.truetype(MONO, int(17 * K)),
        AMBER, 3 * K,
    )


def shares(langs: dict) -> list:
    """Udzialy procentowe, przyciete do tego, co miesci sie w legendzie."""
    total = sum(langs.values())
    ranked = sorted(
        ((k, 100 * v / total) for k, v in langs.items()), key=lambda kv: -kv[1]
    )
    shown = [(k, pct) for k, pct in ranked if pct >= MERGE_BELOW][:MAX_SLICES]
    rest = 100 - sum(pct for _, pct in shown)
    return shown + ([(OTHERS, rest)] if rest > 0.05 else [])


def draw_bar(canvas: Image.Image, top: int, ranked: list) -> None:
    span = W - 2 * PAD
    bar = Image.new("RGBA", (span, BAR_H))
    segments = ImageDraw.Draw(bar)

    x = 0.0
    for i, (name, share) in enumerate(ranked):
        width = span * share / 100
        segments.rectangle(
            [x, 0, x + width, BAR_H], fill=color_of(i, name) + (255,)
        )
        x += width

    rounded = Image.new("L", (span, BAR_H), 0)
    ImageDraw.Draw(rounded).rounded_rectangle(
        [0, 0, span - 1, BAR_H - 1], radius=BAR_H // 2, fill=255
    )
    canvas.paste(bar, (PAD, top), rounded)


def draw_legend(draw: ImageDraw.ImageDraw, top: int, ranked: list) -> None:
    label = ImageFont.truetype(MONO, 14)
    value = ImageFont.truetype(MONO_BOLD, 14)
    column = (W - 2 * PAD) / LEGEND_COLUMNS

    for i, (name, share) in enumerate(ranked):
        x = PAD + column * (i % LEGEND_COLUMNS)
        y = top + 30 * (i // LEGEND_COLUMNS)
        draw.ellipse([x, y + 4, x + 9, y + 13], fill=color_of(i, name) + (255,))
        draw.text((x + 17, y), name, font=label, fill=MUTED + (255,))
        draw.text(
            (x + 17, y + 15), f"{share:.1f}%".replace(".", ","),
            font=value, fill=CREAM + (255,),
        )


def draw_counters(draw: ImageDraw.ImageDraw, top: int, langs: dict, repos: int):
    draw_tracked(
        draw, (PAD, top), PANEL_TITLE, ImageFont.truetype(MONO_BOLD, 14),
        AMBER, 3, shadow=False,
    )
    summary = (
        f"{repos} repozytoriów · {len(langs)} języków · "
        f"{sum(langs.values()) / 1e6:.1f} MB kodu".replace(".", ",")
    )
    font = ImageFont.truetype(MONO, 14)
    draw.text(
        (W - PAD - draw.textlength(summary, font=font), top), summary,
        font=font, fill=MUTED + (255,),
    )


def build(edge_path: str, stats_path: str, out_path: str) -> None:
    with open(stats_path, encoding="utf-8") as handle:
        stats = json.load(handle)
    langs = stats["languages"]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    paint_scrim(canvas)
    paint_panel(canvas, Image.open(edge_path).convert("RGB"))

    draw = ImageDraw.Draw(canvas)
    draw_title(draw)

    ranked = shares(langs)
    draw_counters(draw, PHOTO_H + 22, langs, stats["repos"])
    draw_bar(canvas, PHOTO_H + 48, ranked)
    draw_legend(draw, PHOTO_H + 76, ranked)

    canvas.save(out_path)
    print(f"{out_path}: {W}x{H}, {len(ranked)} wycinkow")


if __name__ == "__main__":
    build(*sys.argv[1:4])
