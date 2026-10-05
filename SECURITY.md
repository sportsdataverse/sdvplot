# Security policy

## Supported versions

Security fixes land in the latest release of sdvplot.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability. Report it privately through GitHub security advisories:
<https://github.com/sportsdataverse/sdvplot/security/advisories/new>.

Include the sdvplot version, what you did and what happened. You can expect an acknowledgement within a week.

## Scope

sdvplot downloads logo images and index files over HTTPS from the SportsDataverse logo archive and from ESPN and
nflverse, and caches them in a per-user directory (`SDVPLOT_CACHE_DIR`). Reports about how that data is fetched,
cached, parsed or rendered are in scope.
