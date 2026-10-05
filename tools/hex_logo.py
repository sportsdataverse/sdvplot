"""Draw the sdvplot hex logo with matplotlib and sdvplot itself, and the docs favicon from it.

Usage: uv run python tools/hex_logo.py

Writes docs/static/img/sdvplot-logo.png (1036 x 1200) and docs/static/img/favicon.ico (16, 32, 48 px). The design is
sdvplotR's "Axis" hex (sdvplotR data-raw/hex_logo.R) ported to Python: the SportsDataverse starfield masked to the org's
hex, the wordmark in Russo One with the SDV blue-to-cyan gradient, and a bar chart in eight teams' own colors (one team
per league, different teams and bar heights from sdvplotR's) with their logos under the axis, all inside a 30 px
print-safe inset. Colors come from sdvplot.team_colors() and the logos are drawn by sdvplot.add_logos(), so drawing
downloads the eight logos (network). The starfield and the font (SIL OFL 1.1, see OFL.txt) live in tools/brand/.
Needs the mpl and svg extras (uv sync --all-extras).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import PathPatch, Polygon  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import sdvplot  # noqa: E402

BRAND = ROOT / "tools" / "brand"
OUT = ROOT / "docs" / "static" / "img"
W, H, DPI = 1036, 1200, 300
SS = 4  # drawn SS times larger, then downsampled: Agg does not antialias clip paths (the hex, the wordmark)
XHALF = W / H  # plot units: y spans -1..1 (600 px per unit), x spans -XHALF..XHALF
SAFE_R = 1 - (30 / 600) * 2 / np.sqrt(3)  # print-safe inner hex, 30 px in from every edge
EDGE, ICE, GRADIENT = "#071224", "#9CCBFF", ("#3346F0", "#7FE6DC")
# one team per league, marks that read on a dark ground; sdvplotR's hex uses KC BOS NY LAD PHI FSU PUR SC
TEAMS = [("nfl", "MIA"), ("nba", "GS"), ("wnba", "CHI"), ("mlb", "CIN"),
         ("nhl", "DAL"), ("cfb", "TENN"), ("mbb", "KU"), ("wbb", "LSU")]  # fmt: skip
HEIGHTS = [0.52, 0.7, 0.44, 0.78, 0.6, 0.48, 0.8, 0.66]  # sdvplotR: 0.62 0.48 0.74 0.4 0.56 0.68 0.45 0.8
BASE, SPAN = -0.48, 0.78  # the axis line's y, and the y span of a full-height bar
LOGO_BOX = 76  # px: each logo fits a square this size, centred 0.09 below the axis


def hex_xy(r: float = 1.0) -> np.ndarray:
    """A pointy-top hexagon of circumradius r, as six (x, y) vertices."""
    a = np.pi / 2 + np.arange(6) * np.pi / 3
    return np.column_stack([r * np.cos(a), r * np.sin(a)])


def safe_halfwidth(y: float) -> float:
    return max(0.0, (SAFE_R - abs(y)) * np.sqrt(3))


def starfield() -> np.ndarray:
    """sdvplotR's ground: the starfield cropped to 1040 x 1200, its middle band (behind the chart) replaced by a
    gain-matched copy of the clean top strip, feathered at the edges."""
    sky = np.asarray(Image.open(BRAND / "sdv-starfield.png").convert("RGB"), dtype=float)[:, 80:1120]
    rows, cols = slice(399, 829), slice(79, 999)

    def ramp(n: int, edge: int) -> np.ndarray:
        i = np.arange(n)
        return np.minimum(1, np.minimum(i, n - 1 - i) / edge)

    w = np.outer(ramp(430, 40), ramp(920, 60))
    ring = w < 0.25  # the blend zone, outside the mark in both images
    for k in range(3):
        src, dst = sky[:430, cols, k], sky[rows, cols, k]
        src = np.minimum(255, src * dst[ring].mean() / src[ring].mean())
        sky[rows, cols, k] = w * src + (1 - w) * dst
    return sky.astype(np.uint8)


def draw() -> Image.Image:
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI * SS)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-XHALF, XHALF)
    ax.set_ylim(-1, 1)
    ax.axis("off")
    half = np.sqrt(3) / 2
    hexagon = Polygon(hex_xy(), closed=True, transform=ax.transData)
    ax.imshow(starfield(), extent=(-half, half, -1, 1), clip_path=hexagon, interpolation="lanczos", zorder=0)

    x = np.linspace(-0.46, 0.46, len(TEAMS))
    grid = BASE + np.array([0.2, 0.4, 0.6, 0.8]) * SPAN
    halves = np.array([safe_halfwidth(y) - 0.04 for y in grid])
    ax.hlines(grid, -halves, halves, colors=ICE, alpha=0.18, linewidth=0.85, zorder=1)
    colors = [sdvplot.team_colors(league, [team])[0] for league, team in TEAMS]
    ax.bar(x, np.array(HEIGHTS) * SPAN, width=0.08, bottom=BASE, color=colors, alpha=0.95, zorder=2)
    ax.plot([-0.58, 0.58], [BASE, BASE], color=ICE, alpha=0.7, linewidth=1.28, solid_capstyle="butt", zorder=2)
    for xi, (league, team) in zip(x, TEAMS, strict=True):
        img = sdvplot.logo_image(team, league, variant="dark")
        assert img is not None, f"no logo for {league} {team}"
        box = LOGO_BOX * min(1, img.height / img.width)  # a wide logo is shorter, so it fits the box
        sdvplot.add_logos(ax, [xi], [BASE - 0.09], [team], league=league, variant="dark", height=box / H)

    # the wordmark at sdvplotR's type size (its "sdvplotR" spans 583 px) with the same ink top (y 0.627)
    font = FontProperties(fname=BRAND / "RussoOne-Regular.ttf")
    ref = TextPath((0, 0), "sdvplotR", size=1, prop=font).get_extents()
    word = TextPath((0, 0), "sdvplot", size=1, prop=font)
    ink = word.get_extents()
    scale = (583 / 600) / ref.width
    path = Affine2D().translate(-ink.x0 - ink.width / 2, -ink.y1).scale(scale).translate(0, 0.627).transform_path(word)
    top, bottom = 0.627, 0.627 - ink.height * scale
    text = PathPatch(path, facecolor="none", edgecolor="none", transform=ax.transData)
    ax.add_patch(text)
    ramp = np.linspace(0, 1, 256)[:, None]  # row 0 (the top of the ink) is the gradient's first color
    rgb = np.array([[int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)] for c in GRADIENT])
    gradient = (1 - ramp)[..., None] * rgb[0] + ramp[..., None] * rgb[1]
    span = ink.width * scale / 2
    ax.imshow(gradient, extent=(-span, span, bottom, top), clip_path=text, aspect="auto", zorder=4)

    ax.add_patch(Polygon(hex_xy(), closed=True, facecolor="none", edgecolor=EDGE, linewidth=1.92,
                         joinstyle="round", zorder=5))  # fmt: skip
    ax.set_xlim(-XHALF, XHALF)  # imshow resets the limits
    ax.set_ylim(-1, 1)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI * SS, transparent=True)
    plt.close(fig)
    big = Image.open(buf).convert("RGBA")
    assert big.size == (W * SS, H * SS), big.size
    return big.resize((W, H), Image.Resampling.LANCZOS)


def favicon(logo: Image.Image) -> Image.Image:
    """The hex trimmed of its transparent border, centred on a transparent square."""
    hexagon = logo.crop(logo.getbbox())
    side = max(hexagon.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(hexagon, ((side - hexagon.width) // 2, (side - hexagon.height) // 2))
    return square


def main() -> None:
    logo = draw()
    assert logo.size == (W, H), logo.size
    logo.save(OUT / "sdvplot-logo.png", optimize=True)
    favicon(logo).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"wrote {OUT / 'sdvplot-logo.png'} ({W} x {H}) with {' '.join(t for _, t in TEAMS)}, and favicon.ico")


if __name__ == "__main__":
    main()
