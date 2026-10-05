<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Security policy](#security-policy)
  - [Supported versions](#supported-versions)
  - [Reporting a vulnerability](#reporting-a-vulnerability)
  - [Scope](#scope)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes |

Security fixes land in the latest release of sdvplot.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability. Report it privately through GitHub security advisories:
<https://github.com/sportsdataverse/sdvplot/security/advisories/new>.

Include the sdvplot version (`sdvplot.versions()`), what you did and what happened. You can expect an acknowledgement
within a week.

## Scope

sdvplot downloads over HTTPS only: the logo manifest and mark images from the SportsDataverse logo archive, player
headshots from ESPN and through nflverse's player table, and any image URL a caller passes. It caches them in a
per-user directory (`SDVPLOT_CACHE_DIR`). Reports about how that data is fetched, size-limited, cached, parsed or
rendered are in scope.
