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
    *,
    season: Any = None,
    variant: str = 'default',
    mark_type: Literal['logo', 'wordmark'] = 'logo',
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
| `mark_type` | `Literal['logo', 'wordmark']` | "logo" or "wordmark". |
| `size` | `int \| None` | The longest side in pixels. Rasters are only scaled down; SVGs are rasterized at it (default 512). |

## Returns

PIL.Image.Image | None: The image, or None when the team does not resolve or has no mark.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `OptionalDependencyError`: If the mark is an SVG and the ``svg`` extra is not installed.
- `OfflineError`: If the download fails and no cached copy exists.
- `UnsafeDownloadError`: (an OSError) If the download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If the manifest's sha256 or extension for the mark would put the file outside the cache directory.
- `requests.HTTPError`: If the CDN refuses the file (a 4xx response).
- `OSError`: If the download does not match the manifest's sha256, or is not an image PIL can decode (``PIL.UnidentifiedImageError`` subclasses OSError).
- `InputError`: (a ValueError) If ``league`` is unknown, ``mark_type`` is not "logo"/"wordmark", ``variant`` is a name no mark in the archive has, or ``season`` is outside the seasons sdvplot knows for the league.
- `ValueError`: If an SVG cannot be parsed; an ``InputError`` if it is more than 64 times longer than it is wide, or ``size`` is over 4096 for an SVG.

## Example

```python
import sdvplot

img = sdvplot.logo_image("KC", "nfl", size=64)
img.size   # (64, 64)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)
