"""Fakes for the great_tables export tests: synthetic page images in place of a headless Chrome."""

from PIL import Image

import sdvplot.great_tables._export as ex

BLACK, RED, WHITE, MAGENTA = (0, 0, 0), (255, 0, 0), (255, 255, 255), (255, 0, 255)


def img(w, h, bg="white", blocks=()):
    """A synthetic image: a bg canvas with (x, y, w, h, color) blocks pasted on."""
    im = Image.new("RGB", (w, h), bg)
    for x, y, bw, bh, color in blocks:
        im.paste(Image.new("RGB", (bw, bh), color), (x, y))
    return im


def fake_render(monkeypatch, sizes):
    """Replace gtsave: each call returns the next (w, h) black 'table' on a page with 10 px of white around it.

    Returns the list of (gt, zoom, expand) calls.
    """
    calls, it = [], iter(sizes)

    def render(gt, zoom, expand):
        calls.append((gt, zoom, expand))
        w, h = next(it)
        return img(w + 20, h + 20, blocks=[(10, 10, w, h, "black")])

    monkeypatch.setattr(ex, "_render_gt", render)
    return calls


def forbid_render(monkeypatch):
    """Fail the test if anything renders: argument checks must run first."""

    def boom(*args, **kwargs):
        raise AssertionError("rendered before the arguments were checked")

    monkeypatch.setattr(ex, "_render_gt", boom)
    monkeypatch.setattr(ex, "_render_html", boom)


def size(path):
    with Image.open(path) as im:
        return im.size
