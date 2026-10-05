---
title: The cache
sidebar_label: The cache
---

# The cache

The team index ships inside the package, so `resolve()`, `palette()`, `team_colors()` and `teams()` never touch the
network. The logo manifest, logo images, headshot images and nflverse's player table (for gsis ids) are downloaded, and
sdvplot caches them on disk.

## What is cached

| Subdirectory | Contents | Refreshed |
|---|---|---|
| `manifest/` | the logo manifest (`marks.csv`) | after the TTL, with an ETag check |
| `images/` | logo images, by sha256 | never: the content cannot change |
| `rasters/` | SVG marks rendered to PNG for `logo_image()` | never: one file per sha256, size and resvg-py version |
| `nflverse/` | nflverse's player table, for `headshot_url(..., id_system="gsis")` | after the TTL, with an ETag check |
| `urlimages/` | images by URL: headshots the matplotlib-family adapters draw (or a web adapter embeds), and the https images of `add_images`, `geom_from_path` and `title_image` | after the TTL, with an ETag check |

## Where it lives

| Variable | Meaning | Default |
|---|---|---|
| `SDVPLOT_CACHE_DIR` | the cache root | platformdirs' user cache directory for `sdvplot`, such as `~/.cache/sdvplot` on Linux |
| `SDVPLOT_CACHE_TTL` | how long the manifest, the player table and images by URL stay fresh, in **days** (fractions allowed) | `7` |

```bash
export SDVPLOT_CACHE_DIR=/data/sdvplot-cache
export SDVPLOT_CACHE_TTL=1
```

## Refreshing

When a cached manifest, player table or image by URL is older than the TTL, sdvplot asks the server again with
`If-None-Match`, sending the ETag it saved. A `304 Not Modified` just renews the copy's age. Otherwise sdvplot downloads
the file, writes it atomically and saves the new ETag. A truncated download, a manifest missing a column sdvplot reads,
or an image Pillow cannot read is rejected, and the old copy stays.

Image URLs in these tables end up in the HTML the web adapters write, so they must be plain https URLs. A manifest
row whose `archive_url` is not one is dropped, and an nflverse headshot that is not one counts as missing (the
player gets their ESPN headshot), each with one `SdvplotWarning`.

Images are named by their sha256. sdvplot downloads each one once, checks the hash and keeps it. A file whose hash does
not match is not cached: sdvplot raises `IntegrityError` (a `DownloadError`), as it does for an archived file Pillow
cannot decode.

Threads that ask for the same file at once share one download: one thread fetches it, the others wait and then find it
written, and a mark is decoded once the same way. A cached file found fresh is remembered for the session until its TTL
runs out, so a repeated lookup is a dictionary lookup and one file check instead of a read of its saved metadata.

## Working offline

- **A cached copy exists:** sdvplot uses it and warns once (`SdvplotWarning: could not refresh <url> (...); using the
  cached copy`). It does not retry that URL for the rest of the session.
- **No cached copy:** sdvplot raises `OfflineError` (a `RuntimeError`) that names the URL:

  ```text
  OfflineError: could not download <url> and there is no cached copy; connect once, or point SDVPLOT_CACHE_DIR at a
  directory that has one (...)
  ```

  When the server answered with an error status (a 4xx or 5xx response), the error is a `DownloadError`, an
  `OfflineError` that is also an `OSError`. `except sdvplot.OfflineError` catches every failed download. A download
  sdvplot refuses (larger than its byte cap, past its two-minute deadline, or redirected away from https) raises
  `UnsafeDownloadError`, an `OSError` but not an `OfflineError`, unless a cached copy exists. `except
  sdvplot.SdvplotError` catches every error sdvplot raises.

To work offline, call the functions you need once while connected, or copy a filled cache directory to the machine and
point `SDVPLOT_CACHE_DIR` at it.

## Clearing it

```python
import sdvplot

sdvplot.clear_cache()
```

`clear_cache()` deletes only sdvplot's own subdirectories (`manifest`, `images`, `rasters`, `nflverse`, `urlimages`)
and empties the copies held in memory (the parsed manifest, decoded images). Anything else in the cache root stays. In a
directory you chose with `SDVPLOT_CACHE_DIR`, it removes only the subdirectories sdvplot created (they hold a
`.sdvplot-cache` marker) and leaves a folder of your own with one of those names alone, with a warning, so pointing
`SDVPLOT_CACHE_DIR` at a shared directory is safe. The next call that needs a file downloads it again. A subdirectory
that is a symlink is unlinked in the default cache directory (what it points to is untouched) and left alone with a
warning in a directory you chose.

## `versions()`

A bug report needs to say what sdvplot was looking at. `versions()` returns:

```python
sdvplot.versions()
# {'sdvplot': '0.1.0', 'index': '1e20bbb90d63', 'manifest_last_modified': 'Thu, 01 Oct 2026 07:44:07 GMT'}
```

- `sdvplot` is the package version.
- `index` is the bundled index version.
- `manifest_last_modified` is the cached manifest's `Last-Modified` date, or `None` until the manifest has been
  downloaded.
