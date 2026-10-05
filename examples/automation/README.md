<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Social game-day graphics (automation example)](#social-game-day-graphics-automation-example)
  - [Quick start](#quick-start)
  - [Files](#files)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Social game-day graphics (automation example)

`sdvplot_social.py` makes social-media graphics from live data and posts them to Bluesky:

- **Leaderboards**: a season's leaders in any ESPN category, as a great_tables table with headshots and logos.
- **Final-score cards**: one per game, with both logos on their team colors.
- **A player-of-the-game card**: the headshot on the team's color.

It covers the NFL, college football, the NBA, the WNBA, MLB and the NHL. The data comes from ESPN through
sportsdataverse-py; nothing needs a key. Images are 1080 x 1080 or 1200 x 675.

The walk-through, with sample images, is the [Social graphics](https://sdvplot.sportsdataverse.org/docs/automation)
page of the docs.

## Quick start

```bash
uv sync --all-extras --all-groups
uv run python examples/automation/sdvplot_social.py leaderboard --league nfl
uv run python examples/automation/sdvplot_social.py gameday --league nba
uv run python examples/automation/sdvplot_social.py post --manifest out/<today>/manifest.json         # dry-run
uv run python examples/automation/sdvplot_social.py post --manifest out/<today>/manifest.json --post  # posts
```

Posting needs `BSKY_HANDLE` and `BSKY_APP_PASSWORD` (a Bluesky app password, never the account password).

## Files

| File | What |
| --- | --- |
| `sdvplot_social.py` | the script: `leaderboard`, `gameday` and `post` subcommands |
| `workflows/sdvplot-social.yml` | a GitHub Actions template to copy into your repository (weekly, posts on request) |

`tests/test_automation_example.py` tests the script offline. `.github/workflows/automation-example.yml` runs it weekly
on live data in dry-run mode. sdvplot itself never posts.
