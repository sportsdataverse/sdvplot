---
title: suggest
sidebar_label: suggest
sidebar_position: 2
---

# suggest

<div class="sdv-signature">

```python
suggest(
    value: Any,
    league: str,
    n: int = 5,
) -> list[tuple[str, str]]
```

</div>

Up to n (team_id, name) candidates for a value that did not resolve, best first.

It never picks one for you: similar names can be different teams ("Bethany (KS)" and "Bethany (WV)").

## Arguments

| Name | Type | Description |
|---|---|---|
| `value` | `Any` | The team value that failed to resolve. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `n` | `int` | The most candidates to return. |

## Returns

`list[tuple[str, str]]` — ``(team_id, name)`` pairs, best match first; empty when nothing is close.

## Raises

- `ValueError`: If ``league`` is unknown.

## Example

```python
import sdvplot

sdvplot.suggest("Kansas Cty Chiefs", "nfl", n=2)   # [('12', 'Kansas City Chiefs')]
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)
