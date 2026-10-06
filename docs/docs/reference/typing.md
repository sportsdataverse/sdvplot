---
title: sdvplot.typing
sidebar_label: sdvplot.typing
sidebar_position: 31
---

# sdvplot.typing

Types for annotating code that calls sdvplot: the ``Literal`` aliases of its closed argument vocabularies.

| Name | What it is |
|---|---|
| [AxisMarkType](#axismarktype) | The values it accepts (a `Literal` alias). |
| [HeadshotIdSystem](#headshotidsystem) | The values it accepts (a `Literal` alias). |
| [IdSystem](#idsystem) | The values it accepts (a `Literal` alias). |
| [MarkType](#marktype) | The values it accepts (a `Literal` alias). |
| [Which](#which) | The values it accepts (a `Literal` alias). |

## AxisMarkType

<div class="sdv-signature">

```python
AxisMarkType = Literal['logo', 'wordmark', 'headshot']
```

</div>

## HeadshotIdSystem

<div class="sdv-signature">

```python
HeadshotIdSystem = Literal['espn', 'gsis']
```

</div>

## IdSystem

<div class="sdv-signature">

```python
IdSystem = Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']
```

</div>

## MarkType

<div class="sdv-signature">

```python
MarkType = Literal['logo', 'wordmark']
```

</div>

## Which

<div class="sdv-signature">

```python
Which = Literal['primary', 'secondary']
```

</div>
