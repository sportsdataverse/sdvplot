---
title: logo_image
sidebar_label: logo_image
sidebar_position: 7
---

# logo_image

<div class="sdv-signature">

```python
logo_image(
    team: Any,
    league: str,
    season: Any = None,
    variant: str = 'default',
    mark_type: str = 'logo',
    size: int | None = None,
) -> PIL.Image.Image | None
```

</div>

The team's mark as a PIL image (downloaded once, then cached).

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | A season year; None picks the current mark. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `size` | `int \| None` | The longest side in pixels. Rasters are only scaled down; SVGs are rasterized at it (default 512). |

## Returns

PIL.Image.Image | None: The image, or None when the team does not resolve or has no mark.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `OptionalDependencyError`: If the mark is an SVG and the ``svg`` extra is not installed.
- `OfflineError`: If the download fails and no cached copy exists.
- `requests.HTTPError`: If the CDN refuses the file (a 4xx response).
- `OSError`: If the download does not match the manifest's sha256, or is not an image PIL can decode (``PIL.UnidentifiedImageError`` subclasses OSError).
- `ValueError`: If ``league`` is unknown, ``mark_type`` is not "logo"/"wordmark", or an SVG cannot be parsed.

## Example

```python
import sdvplot

img = sdvplot.logo_image("KC", "nfl", size=64)
img.size   # (64, 64)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)
