"""Build the README link buttons as self-contained SVGs.

The buttons copy enesyesil.me's retro style: a coloured icon tile, Space Mono
bold uppercase label, 2px border and a hard offset shadow (light theme only,
as on the site). Text is converted to outlines, so the buttons look the same
on every machine; GitHub can't load web fonts inside an <img>.

Setup, once (any scratch folder):

    pip install fonttools
    npm install @fontsource/space-mono@5 flowbite-svelte-icons@3

Run:

    python3 assets/buttons/build.py /path/to/that/folder/node_modules

Writes <name>-light.svg and <name>-dark.svg next to this file.
"""

import re
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent

# Site palette (tailwind.config.cjs and app.pcss of me-enesyesil-dotcom).
THEMES = {
    "light": {"bg": "#fffbeb", "line": "#111827", "text": "#111827", "shadow": "#000000"},
    "dark": {"bg": "#111827", "line": "#6b7280", "text": "#f9fafb", "shadow": None},
}

# name: label, icon (flowbite component, or "brand" for the site's "e" mark), tile colour per theme.
BUTTONS = {
    "website": ("enesyesil.me", "brand", {"light": "#16a34a", "dark": "#16a34a"}),
    "linkedin": ("LinkedIn", "LinkedinSolid", {"light": "#0a66c2", "dark": "#0a66c2"}),
    "email": ("Email", "EnvelopeSolid", {"light": "#dc2626", "dark": "#dc2626"}),
    "resume": ("Resume", "FileLinesSolid", {"light": "#d97706", "dark": "#d97706"}),
    "blog": ("Blog", "PenSolid", {"light": "#111827", "dark": "#374151"}),
}

H = 40  # button height
TILE = 40  # icon tile width
PAD = 14  # space either side of the label
SHADOW = 4  # hard shadow offset (light theme)
GAP = 6  # empty space under the button, so wrapped rows on phones don't touch
FONT_PX = 14
TRACKING = 0.05  # em, Tailwind's tracking-wider


def glyph_path(font, text, size, tracking_em=0.0):
    """Outline `text` with its baseline at y=0 and its left edge at x=0. Returns (d, advance_px)."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    x = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        # Font units are y-up; SVG is y-down.
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
        x += gs[name].width * scale + tracking_em * size
    return pen.getCommands(), x - tracking_em * size


def glyph_bounds(font, char, size):
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(char)]
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    s = size / font["head"].unitsPerEm
    x0, y0, x1, y1 = bp.bounds
    return x0 * s, -y1 * s, x1 * s, -y0 * s  # SVG coordinates


def flowbite_paths(node_modules, component):
    src = (node_modules / "flowbite-svelte-icons/dist" / f"{component}.svelte").read_text()
    body = src.split("{/if}")[-1].split("</svg>")[0]
    return re.sub(r"\s+", " ", body).strip()


def brand_mark(font):
    """The site's logo: a white bold 'e' tilted -40deg (Footer.svelte)."""
    size = 30  # the site sets a 24px "e" in a 32px tile; same ratio in a 40px tile
    d, _ = glyph_path(font, "e", size)
    x0, y0, x1, y1 = glyph_bounds(font, "e", size)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c = TILE / 2
    return (
        f'<path fill="#ffffff" transform="translate({c} {c}) rotate(-40) '
        f'translate({-cx:.2f} {-cy:.2f})" d="{d}"/>'
    )


def button(name, label, icon, tiles, theme, font, node_modules):
    t = THEMES[theme]
    text = label.upper()
    d, text_w = glyph_path(font, text, FONT_PX, TRACKING)
    w = round(TILE + PAD + text_w + PAD)
    cap = font["OS/2"].sCapHeight * FONT_PX / font["head"].unitsPerEm
    baseline = H / 2 + cap / 2

    if icon == "brand":
        mark = brand_mark(font)
    else:
        mark = (
            f'<g fill="#ffffff" transform="translate(10 10) scale({20 / 24:.4f})">'
            f"{flowbite_paths(node_modules, icon)}</g>"
        )

    shadow = (
        f'<rect x="{SHADOW}" y="{SHADOW}" width="{w}" height="{H}" fill="{t["shadow"]}"/>'
        if t["shadow"]
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w + SHADOW}" height="{H + SHADOW + GAP}" viewBox="0 0 {w + SHADOW} {H + SHADOW + GAP}" role="img" aria-label="{label}">
<title>{label}</title>
{shadow}
<rect width="{w}" height="{H}" fill="{t["bg"]}"/>
<rect width="{TILE}" height="{H}" fill="{tiles[theme]}"/>
{mark}
<path d="M{TILE - 1} 0V{H}" stroke="{t["line"]}" stroke-width="2"/>
<path fill="{t["text"]}" transform="translate({TILE + PAD} {baseline:.2f})" d="{d}"/>
<rect x="1" y="1" width="{w - 2}" height="{H - 2}" fill="none" stroke="{t["line"]}" stroke-width="2"/>
</svg>
"""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    node_modules = Path(sys.argv[1])
    font = TTFont(node_modules / "@fontsource/space-mono/files/space-mono-latin-700-normal.woff")
    for name, (label, icon, tiles) in BUTTONS.items():
        for theme in THEMES:
            svg = button(name, label, icon, tiles, theme, font, node_modules)
            (HERE / f"{name}-{theme}.svg").write_text(svg)
            print(f"{name}-{theme}.svg")


if __name__ == "__main__":
    main()
