"""Shared behaviour every adapter must have. Adapter test suites call check_adapter_contract().

An adapter module must expose add_logos, add_wordmarks, add_headshots and axis_logos, and the test hook

    drawn_marks(target) -> list[tuple]

returning one tuple per drawn image, in draw order: (team_id, x, y, height) or (team_id, x, y, height, url). team_id
is the canonical team id (str; the player id for headshots), x and y are the caller's position values for that image,
height is the fraction of the plot height the adapter actually used (not the value it was asked for), and url, when
present, is the image source the adapter used (so the harness can check it drew the right mark).

An adapter that draws axis logos sets SUPPORTS_AXIS_LOGOS = True (the default when the attribute is absent) and
exposes two more hooks:

    drawn_axis_marks(target, axis) -> list[tuple[str, Any]]   # (team_id, tick position) per axis image, tick order
    visible_axis_labels(target, axis) -> list[str]            # the tick labels still shown as text

An adapter that cannot (a map, a table) sets SUPPORTS_AXIS_LOGOS = False and raises TypeError from axis_logos.

add_* must return the object that was drawn on. Libraries that mutate the target (matplotlib) return it; libraries that
build a new object (plotnine, altair, tables) return the new one. The harness reads hooks from the returned object when
it is not None, and from the target otherwise.

The contract can fail: each rule below raises an AssertionError whose message starts with "rule N". The rules use
coordinates that are not row positions (x=[10, 20], y=[-3, -7]) so swapped, shared or positional x/y are caught.

0. Registration: sdvplot's front door routes make_target() to this adapter.
1. Resolution: the canonical ids of the teams passed, at their own x/y (and the team's own mark, when url is drawn).
2. Warn and skip: an unknown team is dropped together with its own x/y, with an SdvplotWarning, never a raise.
3. pandas/polars parity: a pandas Series with a non-default index draws the same marks as a polars Series.
4. Height semantics: height is the fraction drawn; 0 and values above 1 raise ValueError.
5. Wordmarks: add_wordmarks follows rules 1, 2 and 4.
6. Headshots: add_headshots draws player ids at their own x/y, skips an unknown id with a warning, honours height.
7. Axis logos: known team categories become images in tick order, an unknown one warns and stays readable text;
   or, without axis support, axis_logos raises TypeError.
8. Alpha: alpha outside [0, 1] raises ValueError.

Table adapters (great_tables) have rows, columns and pixel heights instead, so they get their own harness,
check_table_adapter_contract(), with rules T0-T6 (messages start with "rule T<n>"). A table adapter's add_* take
(table, columns, *, league, height=<pixels>) and return the new table, and it exposes two hooks:

    drawn_cells(table) -> list[tuple]   # (team_id, row, column, height_px[, src]) per image, in display order
    rendered_html(table) -> str         # the table as it renders

In drawn_cells, row is the 0-based display row of a body cell and -1 for a column label.

T0. Registration: the front door routes the table to this adapter.
T1. Resolution: a column ["LV", "LAR"] renders both teams' canonical ids at rows 0 and 1 (and their own marks).
T2. Warn and keep: ["XXX", "LV"] renders LV at row 1, keeps "XXX" as text, warns once when called and never when
    rendered; all-unknown input renders no image.
T3. pandas/polars parity: a pandas frame with a non-default index renders the same cells as a polars frame.
T4. Height: height=24 is 24 px on every image; 0, negative and non-numeric heights raise ValueError.
T5. Wordmarks: add_wordmarks satisfies T1-T4.
T6. Headshots: add_headshots satisfies T1-T4 for player ids.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Sequence
from types import ModuleType
from typing import Any

from sdvplot._errors import SdvplotWarning
from sdvplot._resolve import resolve


def _fail(rule: str, msg: str) -> None:
    raise AssertionError(f"{rule}: {msg}")


def _call(
    adapter: ModuleType, verb: str, make_target: Callable[[], Any], rule: str, *args: Any, **kw: Any
) -> tuple[list[tuple[Any, ...]], list[warnings.WarningMessage]]:
    """Run adapter.<verb> on a fresh target; return (drawn marks, warnings). A raise becomes a named AssertionError.

    Marks are read from the object the verb returns (None means it mutated the target in place).
    """
    t = make_target()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            out = getattr(adapter, verb)(t, *args, **kw)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"{rule}: {verb} raised {e!r}") from e
        marks = [tuple(m) for m in adapter.drawn_marks(t if out is None else out)]
    return marks, rec


def _warned(rec: list[warnings.WarningMessage]) -> bool:
    return any(issubclass(w.category, SdvplotWarning) for w in rec)


def _xyz(marks: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    return [m[:3] for m in marks]


def _check_urls(rule: str, marks: list[tuple[Any, ...]], want: dict[str, Callable[[], str | None]]) -> None:
    """Only adapters that report the url (5-tuples) are checked; the expected url is looked up lazily."""
    for m in marks:
        if len(m) >= 5 and m[0] in want and m[4] != (expected := want[m[0]]()):
            _fail(rule, f"{m[0]!r} was drawn with {m[4]!r}, expected its mark {expected!r}")


def _check_marks(
    adapter: ModuleType,
    verb: str,
    make_target: Callable[[], Any],
    league: str,
    pair: Sequence[str],
    ids: Sequence[str],
    urls: dict[str, Callable[[], str | None]],
    names: tuple[str, str],
) -> None:
    """Rules 1 and 2 (named by ``names``) for one verb."""
    r1, r2 = names
    a, b = pair
    id_a, id_b = ids
    xs, ys = [10.0, 20.0], [-3.0, -7.0]
    want_two = [(id_a, 10, -3), (id_b, 20, -7)]

    marks, _ = _call(adapter, verb, make_target, r1, xs, ys, [a, b], league=league)
    if _xyz(marks) != want_two:
        _fail(r1, f"expected marks {want_two}, drew {_xyz(marks)}")
    _check_urls(r1, marks, urls)

    marks, rec = _call(adapter, verb, make_target, r2, xs, ys, ["XXX", a], league=league)
    if _xyz(marks) != [(id_a, 20, -7)]:
        _fail(
            r2, f"an unknown team must be skipped with its own x/y; expected [({id_a!r}, 20, -7)], drew {_xyz(marks)}"
        )
    if not _warned(rec):
        _fail(r2, "an unknown team must warn (SdvplotWarning)")
    marks, rec = _call(adapter, verb, make_target, r2, xs, ys, ["XXX", "YYY"], league=league)
    if marks:
        _fail(r2, f"all-unknown input must draw nothing, drew {marks}")
    if not _warned(rec):
        _fail(r2, "all-unknown input must warn (SdvplotWarning)")


def _check_height(
    adapter: ModuleType, verb: str, make_target: Callable[[], Any], league: str, pair: Sequence[str], rule: str
) -> None:
    """Rule 4 (named by ``rule``) for one verb: height is the fraction drawn; 0 and values above 1 raise."""
    xs, ys = [10.0, 20.0], [-3.0, -7.0]
    for h in (0.1, 0.25):
        marks, _ = _call(adapter, verb, make_target, rule, xs, ys, list(pair), league=league, height=h)
        if not marks or not all(math.isclose(m[3], h) for m in marks):
            _fail(rule, f"height={h} must be the height of every drawn mark, drew heights {[m[3] for m in marks]}")
    for bad in (0, 1.5):
        try:
            getattr(adapter, verb)(make_target(), [0], [0], [pair[0]], league=league, height=bad)
        except ValueError:
            pass
        else:
            _fail(rule, f"height={bad} must raise ValueError (height is a fraction in (0, 1])")


def check_adapter_contract(
    adapter: ModuleType,
    make_target: Callable[[], Any],
    *,
    league: str = "nfl",
    known: tuple[str, str] = ("LV", "LAR"),
    known_wordmarks: tuple[str, str] = ("LV", "LAC"),
    players: tuple[str, str] = ("3139477", "4241479"),
    make_axis_target: Callable[[list[str]], Any] | None = None,
) -> None:
    """Raise an AssertionError naming the broken rule if the adapter breaks the sdvplot adapter contract.

    ``make_axis_target(categories)`` must build a target whose x axis shows those categories, in order. It is
    required when the adapter supports axis logos (rule 7).
    """
    import pandas as pd
    import polars as pl

    from sdvplot._dispatch import adapter_for
    from sdvplot._headshots import headshot_url
    from sdvplot._marks import logo_url

    # rule 0: the front door reaches this adapter
    r0 = "rule 0 (registration)"
    routed = adapter_for(make_target())
    if routed is not adapter:
        _fail(r0, f"sdvplot routes this target to {routed.__name__}, not {adapter.__name__}")

    a, b = known
    id_a, id_b = resolve([a, b], league)
    urls = {id_a: lambda: logo_url(a, league), id_b: lambda: logo_url(b, league)}
    _check_marks(
        adapter, "add_logos", make_target, league, known, (id_a, id_b), urls,
        ("rule 1 (resolution)", "rule 2 (unknown team: warn and skip)"),
    )  # fmt: skip

    # rule 3: pandas (non-default index) and polars inputs draw identical marks
    r3 = "rule 3 (pandas/polars parity)"
    xs, ys = [10.0, 20.0], [-3.0, -7.0]
    want_two = [(id_a, 10, -3), (id_b, 20, -7)]
    pmarks, _ = _call(
        adapter, "add_logos", make_target, r3,
        pd.Series(xs, index=[5, 6]), pd.Series(ys, index=[5, 6]), pd.Series([a, b], index=[5, 6]), league=league,
    )  # fmt: skip
    lmarks, _ = _call(
        adapter, "add_logos", make_target, r3, pl.Series(xs), pl.Series(ys), pl.Series([a, b]), league=league
    )
    if _xyz(pmarks) != _xyz(lmarks) or _xyz(lmarks) != want_two:
        _fail(r3, f"pandas (index [5, 6]) drew {_xyz(pmarks)}, polars drew {_xyz(lmarks)}, expected {want_two}")

    _check_height(adapter, "add_logos", make_target, league, known, "rule 4 (height semantics)")

    # rule 5: wordmarks follow rules 1, 2 and 4
    wa, wb = known_wordmarks
    wid_a, wid_b = resolve([wa, wb], league)
    wurls = {
        wid_a: lambda: logo_url(wa, league, mark_type="wordmark"),
        wid_b: lambda: logo_url(wb, league, mark_type="wordmark"),
    }
    _check_marks(
        adapter, "add_wordmarks", make_target, league, known_wordmarks, (wid_a, wid_b), wurls,
        ("rule 5 (wordmarks: resolution)", "rule 5 (wordmarks: warn and skip)"),
    )  # fmt: skip
    _check_height(adapter, "add_wordmarks", make_target, league, known_wordmarks, "rule 5 (wordmarks: height)")

    # rule 6: headshots
    r6 = "rule 6 (headshots)"
    p, q = players
    marks, _ = _call(adapter, "add_headshots", make_target, r6, xs, ys, [p, q], league=league)
    if _xyz(marks) != [(p, 10, -3), (q, 20, -7)]:
        _fail(r6, f"expected headshots [({p!r}, 10, -3), ({q!r}, 20, -7)], drew {_xyz(marks)}")
    _check_urls(r6, marks, {p: lambda: headshot_url(p, league), q: lambda: headshot_url(q, league)})
    marks, rec = _call(adapter, "add_headshots", make_target, r6, xs, ys, ["not-an-id", p], league=league)
    if _xyz(marks) != [(p, 20, -7)] or not _warned(rec):
        _fail(r6, f"an unknown player id must be skipped with its own x/y and warn, drew {_xyz(marks)}")
    marks, _ = _call(adapter, "add_headshots", make_target, r6, xs, ys, [p, q], league=league, height=0.25)
    if not marks or not all(math.isclose(m[3], 0.25) for m in marks):
        _fail(r6, f"height=0.25 must be the height of every headshot, drew {[m[3] for m in marks]}")

    # rule 7: axis logos
    r7 = "rule 7 (axis logos)"
    if getattr(adapter, "SUPPORTS_AXIS_LOGOS", True):
        if make_axis_target is None:
            _fail(r7, "make_axis_target is required for an adapter that supports axis logos")
        assert make_axis_target is not None
        t = make_axis_target([a, "XXX", b])
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            try:
                out = adapter.axis_logos(t, "x", league=league)
            except Exception as e:  # noqa: BLE001
                raise AssertionError(f"{r7}: axis_logos raised {e!r}") from e
            drawn = out if out is not None else t
            axis_marks = [tuple(m) for m in adapter.drawn_axis_marks(drawn, "x")]
            shown = list(adapter.visible_axis_labels(drawn, "x"))
        if [m[0] for m in axis_marks] != [id_a, id_b]:
            _fail(r7, f"expected axis images for [{id_a!r}, {id_b!r}] in tick order, drew {axis_marks}")
        if not axis_marks[0][1] < axis_marks[1][1]:
            _fail(r7, f"axis images must sit at increasing tick positions, got {axis_marks}")
        if not _warned(rec):
            _fail(r7, "an unknown axis category must warn (SdvplotWarning)")
        if "XXX" not in shown or a in shown or b in shown:
            _fail(r7, f"only the unknown category may stay as text, visible labels are {shown}")
    else:
        try:
            adapter.axis_logos(make_target(), "x", league=league)
        except TypeError:
            pass
        else:
            _fail(r7, "an adapter without axis-logo support must raise TypeError from axis_logos")

    # rule 8: alpha
    r8 = "rule 8 (alpha)"
    for bad in (-0.1, 1.5):
        try:
            adapter.add_logos(make_target(), [0], [0], [a], league=league, alpha=bad)
        except ValueError:
            pass
        else:
            _fail(r8, f"alpha={bad} must raise ValueError (alpha is an opacity in [0, 1])")


def _table_call(
    adapter: ModuleType, verb: str, make_table: Callable[[Any], Any], rule: str, frame: Any, **kw: Any
) -> tuple[list[tuple[Any, ...]], int, int, str]:
    """Run adapter.<verb> on the "team" column of a table built from frame; return (cells, warnings when called,
    warnings when rendered, rendered html). A raise becomes a named AssertionError."""
    t = make_table(frame)
    with warnings.catch_warnings(record=True) as called:
        warnings.simplefilter("always")
        try:
            out = getattr(adapter, verb)(t, "team", **kw)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"{rule}: {verb} raised {e!r}") from e
    drawn = t if out is None else out
    with warnings.catch_warnings(record=True) as rendered:
        warnings.simplefilter("always")
        cells = [tuple(c) for c in adapter.drawn_cells(drawn)]
        text = adapter.rendered_html(drawn)
    count = sum(issubclass(w.category, SdvplotWarning) for w in called)
    late = sum(issubclass(w.category, SdvplotWarning) for w in rendered)
    return cells, count, late, text


def _check_table_verb(
    adapter: ModuleType,
    verb: str,
    make_table: Callable[[Any], Any],
    league: str,
    pair: Sequence[str],
    ids: Sequence[str],
    unknown: str,
    urls: dict[str, Callable[[], str | None]],
    rules: tuple[str, str, str, str],
) -> None:
    """Rules T1-T4 (named by ``rules``) for one verb."""
    import pandas as pd
    import polars as pl

    r1, r2, r3, r4 = rules
    a, b = pair
    want = [(ids[0], 0, "team"), (ids[1], 1, "team")]

    cells, _, _, _ = _table_call(adapter, verb, make_table, r1, pl.DataFrame({"team": [a, b], "v": [1, 2]}),
                                 league=league)  # fmt: skip
    if [c[:3] for c in cells] != want:
        _fail(r1, f"expected cells {want}, rendered {[c[:3] for c in cells]}")
    _check_urls(r1, cells, urls)

    frame = pl.DataFrame({"team": [unknown, a], "v": [1, 2]})
    cells, count, late, text = _table_call(adapter, verb, make_table, r2, frame, league=league)
    if [c[:3] for c in cells] != [(ids[0], 1, "team")]:
        _fail(r2, f"expected only [({ids[0]!r}, 1, 'team')], rendered {[c[:3] for c in cells]}")
    if count != 1:
        _fail(r2, f"an unknown value must warn exactly once when called, warned {count} times")
    if late:
        _fail(r2, "rendering must not warn: unknown values are reported when the function is called")
    if unknown not in text:
        _fail(r2, f"an unknown value must stay as text, {unknown!r} is not in the rendered table")
    frame = pl.DataFrame({"team": [unknown, unknown + "2"], "v": [1, 2]})
    cells, count, _, _ = _table_call(adapter, verb, make_table, r2, frame, league=league)
    if cells or not count:
        _fail(r2, f"all-unknown input must render no image and warn, rendered {cells}")

    pcells, _, _, _ = _table_call(adapter, verb, make_table, r3,
                                  pd.DataFrame({"team": [a, b], "v": [1, 2]}, index=[5, 6]), league=league)  # fmt: skip
    lcells, _, _, _ = _table_call(adapter, verb, make_table, r3, pl.DataFrame({"team": [a, b], "v": [1, 2]}),
                                  league=league)  # fmt: skip
    if pcells != lcells or [c[:3] for c in lcells] != want:
        _fail(r3, f"pandas (index [5, 6]) rendered {pcells}, polars rendered {lcells}, expected {want}")

    cells, _, _, _ = _table_call(adapter, verb, make_table, r4, pl.DataFrame({"team": [a, b]}), league=league,
                                 height=24)  # fmt: skip
    if len(cells) != 2 or not all(math.isclose(c[3], 24) for c in cells):
        _fail(r4, f"height=24 must be 24 px on every image, rendered heights {[c[3] for c in cells]}")
    for bad in (0, -5, "30px"):
        try:
            getattr(adapter, verb)(make_table(pl.DataFrame({"team": [a]})), "team", league=league, height=bad)
        except ValueError:
            pass
        else:
            _fail(r4, f"height={bad!r} must raise ValueError (height is a number of pixels > 0)")


def check_table_adapter_contract(
    adapter: ModuleType,
    make_table: Callable[[Any], Any],
    *,
    league: str = "nfl",
    known: tuple[str, str] = ("LV", "LAR"),
    known_wordmarks: tuple[str, str] = ("LV", "LAC"),
    players: tuple[str, str] = ("3139477", "4241479"),
) -> None:
    """Raise an AssertionError naming the broken rule (T0-T6) if a table adapter breaks the table contract.

    ``make_table(frame)`` builds the adapter's table from a pandas or polars DataFrame (for great_tables: ``GT``).
    The rules and hooks are in this module's docstring.
    """
    import polars as pl

    from sdvplot._dispatch import adapter_for
    from sdvplot._headshots import headshot_url
    from sdvplot._marks import logo_url

    r0 = "rule T0 (registration)"
    try:
        routed = adapter_for(make_table(pl.DataFrame({"team": list(known)})))
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"{r0}: sdvplot cannot route this table: {e!r}") from e
    if routed is not adapter:
        _fail(r0, f"sdvplot routes this table to {routed.__name__}, not {adapter.__name__}")

    a, b = known
    ids = resolve([a, b], league)
    _check_table_verb(
        adapter, "add_logos", make_table, league, known, ids, "XXX",
        {ids[0]: lambda: logo_url(a, league), ids[1]: lambda: logo_url(b, league)},
        ("rule T1 (resolution)", "rule T2 (unknown value: warn and keep)", "rule T3 (pandas/polars parity)",
         "rule T4 (height in pixels)"),
    )  # fmt: skip

    wa, wb = known_wordmarks
    wids = resolve([wa, wb], league)
    _check_table_verb(
        adapter, "add_wordmarks", make_table, league, known_wordmarks, wids, "XXX",
        {wids[0]: lambda: logo_url(wa, league, mark_type="wordmark"),
         wids[1]: lambda: logo_url(wb, league, mark_type="wordmark")},
        ("rule T5 (wordmarks: resolution)", "rule T5 (wordmarks: warn and keep)", "rule T5 (wordmarks: parity)",
         "rule T5 (wordmarks: height)"),
    )  # fmt: skip

    p, q = players
    _check_table_verb(
        adapter, "add_headshots", make_table, league, players, players, "not-an-id",
        {p: lambda: headshot_url(p, league), q: lambda: headshot_url(q, league)},
        ("rule T6 (headshots: resolution)", "rule T6 (headshots: warn and keep)", "rule T6 (headshots: parity)",
         "rule T6 (headshots: height)"),
    )  # fmt: skip
