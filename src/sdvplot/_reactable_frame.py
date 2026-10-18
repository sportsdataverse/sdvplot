"""Table furniture for reactable-py: a title, subtitle, source line, color or icon legend and Google font around a
``Reactable``, ported from reactablefmtr's ``add_title``/``add_subtitle``/``add_source``/``add_legend``/
``add_icon_legend``/``google_font``.

reactable-py shows a table as a Jupyter widget, so the frame is an ``htmltools.TagList`` that shows itself the same
way (reactable's own ``to_widget`` turns the tags into React elements around the table). Two consequences shape the
markup: a ``style`` attribute is split on ``;`` and ``:`` into a React style object, so no declaration may hold a
second colon (no ``url(https://...)``), raw HTML strings show as text, so icons are SVG tags, not markup, and a void
element such as ``<link>`` breaks React (it is handed a children list), so the font is a ``<style>`` @import.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from sdvplot._errors import InputError, requires_extra

with requires_extra("reactable"):
    import htmltools
    from htmltools import Tag, TagList, tags

from sdvplot._contrast import hex6, mix

__all__ = ["reactable_sdv_frame", "reactable_sdv_icon_legend", "reactable_sdv_legend"]

_ALIGN = ("left", "center", "right")
# ponytail: a handful of shapes, enough for a legend; the Tier 1 icon set can replace this when it lands
_SHAPES = {
    "circle": lambda c: Tag("circle", cx="8", cy="8", r="7", fill=c),
    "square": lambda c: Tag("rect", x="1", y="1", width="14", height="14", fill=c),
    "triangle": lambda c: Tag("polygon", points="8,1 15,15 1,15", fill=c),
    "diamond": lambda c: Tag("polygon", points="8,0 16,8 8,16 0,8", fill=c),
    "star": lambda c: Tag(
        "polygon", points="8,0.5 10.2,5.6 15.6,6 11.5,9.6 12.8,15 8,12.1 3.2,15 4.5,9.6 0.4,6 5.8,5.6", fill=c
    ),  # fmt: skip
}


class _Framed(TagList):
    """A TagList that displays in Jupyter as reactable displays its tables: one widget holding the tags and table."""

    def _repr_mimebundle_(self, **kwargs: Any) -> Any:
        from reactable.tags import to_widget

        return to_widget(self)._repr_mimebundle_(**kwargs)


def _style(**decls: Any) -> str:
    """A ``style`` string from ``font_size="32px"`` style keywords; None values are left out."""
    return ";".join(f"{k.replace('_', '-')}:{v}" for k, v in decls.items() if v is not None)


def _check_colors(colors: Any) -> list[str]:
    if isinstance(colors, str) or not colors:
        raise InputError(f"colors must be a non-empty list of hex colors, got {colors!r}")
    return [hex6(c) for c in colors]


def _labels(labels: Any, n: int) -> list[str]:
    out = [] if labels is None else [str(x) for x in labels]
    if labels is not None and len(out) != n:
        raise InputError(f"labels must have one entry per swatch ({n}), got {len(out)}")
    return out


def _caption(title: Any, footer: Any) -> tuple[Tag | None, Tag | None]:
    head = tags.div(title, style=_style(margin_bottom="6px", font_weight="bold", font_size="90%")) if title else None
    foot = tags.div(footer, style=_style(font_size="70%", color="#999999", margin_top="2px")) if footer else None
    return head, foot


def reactable_sdv_legend(
    *,
    colors: Any,
    labels: Any = None,
    bins: int | None = None,
    title: Any = None,
    footer: Any = None,
) -> Tag:
    """A color legend: a row of swatches with a label under each, for ``reactable_sdv_frame(legend=...)``.

    Args:
        colors: The legend's colors, low to high, as hex strings.
        labels: One label per swatch (numbers or text); None for swatches alone.
        bins: The number of swatches, spread evenly along ``colors`` as a ramp (reactablefmtr's ``bins``); None for one
            swatch per color.
        title: Text above the swatches.
        footer: Small grey text under them.

    Returns:
        htmltools.Tag: The legend.

    Raises:
        InputError: (a ValueError) If ``colors`` is empty or not hex colors, ``bins`` is not a whole number of at
            least 2, or ``labels`` does not have one entry per swatch.

    Example:
        ::

            from sdvplot.reactable import reactable_sdv_legend

            reactable_sdv_legend(colors=["#15607a", "#ffffff", "#fa8c00"], bins=5, labels=[-0.2, -0.1, 0, 0.1, 0.2],
                                 title="EPA per play", footer="lower is better on defense")

    See Also:
        Equivalent of reactablefmtr::add_legend (the swatches are given, not computed from a column):
        https://kcuilla.github.io/reactablefmtr/reference/add_legend.html
    """
    cols = _check_colors(colors)
    if bins is not None:
        if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
            raise InputError(f"bins must be a whole number of at least 2, got {bins!r}")
        steps = [i * (len(cols) - 1) / (bins - 1) for i in range(bins)]
        cols = [mix(cols[int(s)], cols[min(int(s) + 1, len(cols) - 1)], s - int(s)) for s in steps]
    texts = _labels(labels, len(cols))
    items = [
        tags.div(
            tags.span(style=_style(display="block", height="14px", width="100%", background=c)),
            texts[i] if texts else None,
            style=_style(
                display="inline-block",
                min_width="30px",
                padding="0 2px",
                text_align="center",
                font_size="80%",
                vertical_align="top",
            ),  # fmt: skip
        )
        for i, c in enumerate(cols)
    ]
    head, foot = _caption(title, footer)
    return tags.div(head, tags.div(*items, style=_style(line_height="1.3")), foot,
                    style=_style(display="inline-block", margin="8px 0", text_align="left"))  # fmt: skip


def reactable_sdv_icon_legend(*, icons: Any, colors: Any, labels: Any, title: Any = None, footer: Any = None) -> Tag:
    """An icon legend: each icon, in its color, before its label, for ``reactable_sdv_frame(legend=...)``.

    Args:
        icons: One shape per entry: "circle", "square", "triangle", "diamond" or "star" (drawn as inline SVG, no icon
            font), or a single shape for all.
        colors: One hex color per entry, or a single color for all.
        labels: One label per entry.
        title: Text above the icons.
        footer: Small grey text under them.

    Returns:
        htmltools.Tag: The legend.

    Raises:
        InputError: (a ValueError) If a shape is unknown, a color is not a hex color, or ``icons``/``colors`` do not
            have one entry per label.

    Example:
        ::

            from sdvplot.reactable import reactable_sdv_icon_legend

            reactable_sdv_icon_legend(icons="circle", colors=["#1a9641", "#d7191c"], labels=["won", "lost"])

    See Also:
        Equivalent of reactablefmtr::add_icon_legend (inline SVG shapes instead of Font Awesome):
        https://kcuilla.github.io/reactablefmtr/reference/add_icon_legend.html
    """
    texts = [str(x) for x in labels] if not isinstance(labels, str) else [labels]
    n = len(texts)
    shapes = [icons] * n if isinstance(icons, str) else list(icons)
    cols = _check_colors([colors] * n if isinstance(colors, str) else colors)
    if len(shapes) != n or len(cols) != n:
        raise InputError(f"icons and colors need one entry per label ({n}), got {len(shapes)} and {len(cols)}")
    bad = sorted({s for s in shapes if s not in _SHAPES})
    if bad:
        raise InputError(f"unknown icon {', '.join(map(repr, bad))}; the icons are {', '.join(_SHAPES)}")
    items = [
        tags.span(
            Tag(
                "svg",
                _SHAPES[s](c),
                viewBox="0 0 16 16",
                width="14",
                height="14",
                role="img",
                aria_hidden="true",
                style=_style(vertical_align="-2px", margin_right="4px"),
            ),  # fmt: skip
            text,
            style=_style(margin_right="14px", font_size="13px", white_space="nowrap"),
        )
        for s, c, text in zip(shapes, cols, texts, strict=True)
    ]
    head, foot = _caption(title, footer)
    return tags.div(head, tags.div(*items), foot, style=_style(display="inline-block", margin="8px 0",
                                                              text_align="left"))  # fmt: skip


def reactable_sdv_frame(
    table: Any,
    *,
    title: Any = None,
    subtitle: Any = None,
    source: Any = None,
    legend: Any = None,
    font: str | None = None,
    align: str = "left",
) -> htmltools.TagList:
    """A ``Reactable`` with a title and subtitle above it and a legend and source line under it, in a Google font.

    The result shows in a notebook just as a ``Reactable`` does (call ``reactable.embed_css()`` once first). Its
    sizes are reactablefmtr's: a 32 px bold title, a 24 px bold subtitle and a 16 px source line, no margins; the
    text color is inherited from the page rather than reactablefmtr's black, so a dark page keeps it readable.

    Args:
        table: The ``reactable.Reactable``.
        title: The title text (or an htmltools tag).
        subtitle: The subtitle text (or tag).
        source: The source line under the table, e.g. "Data: sportsdataverse-py".
        legend: A legend from ``reactable_sdv_legend`` or ``reactable_sdv_icon_legend`` (any htmltools tag),
            shown under the table.
        font: A Google Fonts family name, e.g. "Poppins" or "Roboto Condensed", for the title, table and source;
            None keeps the page's font. The font is loaded from fonts.googleapis.com when the page is shown.
        align: "left", "center" or "right", for the title, subtitle, legend and source.

    Returns:
        htmltools.TagList: The framed table.

    Raises:
        InputError: (a ValueError) If ``align`` is not "left", "center" or "right", or ``font`` is not a font name.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_frame, reactable_sdv_legend

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            reactable_sdv_frame(
                Reactable(df),
                title="AFC leaders",
                subtitle="2025 regular season",
                source="Data: sportsdataverse-py",
                legend=reactable_sdv_legend(colors=["#ffffff", "#1a9641"], labels=["fewer", "more"]),
                font="Poppins",
            )

    See Also:
        Equivalent of reactablefmtr::add_title, add_subtitle, add_source and google_font:
        https://kcuilla.github.io/reactablefmtr/reference/add_title.html
    """
    if align not in _ALIGN:
        raise InputError(f"align must be one of {', '.join(_ALIGN)}, got {align!r}")
    if font is not None and (not isinstance(font, str) or not font.strip() or any(c in font for c in ";:'\"<>")):
        raise InputError(f"font must be a Google Fonts family name such as 'Poppins', got {font!r}")
    parts: list[Any] = []
    if font:
        href = f"https://fonts.googleapis.com/css2?family={quote_plus(font.strip())}:wght@400;700"
        # an @import, not a <link>: the widget hands every element a children list, and React refuses one on a void tag.
        # A plain str child (the widget state must be JSON) with nothing htmltools would escape: no quotes, no "&".
        parts.append(tags.style(f"@import url({href});"))
    if title is not None:
        parts.append(tags.h1(title, style=_style(font_size="32px", font_weight="bold", line_height="1.2",
                                                 margin="0", text_align=align)))  # fmt: skip
    if subtitle is not None:
        parts.append(tags.h2(subtitle, style=_style(font_size="24px", font_weight="bold", line_height="1.2",
                                                    margin="0 0 8px 0", text_align=align)))  # fmt: skip
    parts.append(table)
    if legend is not None:
        parts.append(tags.div(legend, style=_style(text_align=align)))
    if source is not None:
        parts.append(tags.p(source, style=_style(font_size="16px", font_weight="normal", margin="6px 0 0 0",
                                                 text_align=align)))  # fmt: skip
    family = f"{font.strip()}, sans-serif" if font else None
    return _Framed(tags.div(*parts, style=_style(font_family=family) or None))
