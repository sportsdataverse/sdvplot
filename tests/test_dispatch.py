import sys
import types
import warnings

import pytest

import sdvplot._dispatch as d
from sdvplot._errors import OptionalDependencyError, SdvplotWarning, UnsupportedTargetError
from sdvplot._resolve import resolve
from sdvplot.testing import check_adapter_contract


class Canvas(list):
    """A pretend plot object from a pretend library called 'fakeplot'."""


Canvas.__module__ = "fakeplot.canvas"


def _dummy_adapter():
    mod = types.ModuleType("sdvplot_dummy_adapter")

    def add_logos(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default"):
        if not 0 < height <= 1:
            raise ValueError("height is a fraction of the plot height")
        if not 0 <= alpha <= 1:
            raise ValueError("alpha is an opacity")
        # positional values, never index labels; x, y and teams are filtered together
        for xi, yi, team_id in zip(list(x), list(y), resolve(list(teams), league, season=season), strict=True):
            if team_id is not None:
                target.append((team_id, xi, yi, height))
        return target

    def add_headshots(target, x, y, players, *, league, height=0.1, alpha=1.0):
        if not 0 < height <= 1:
            raise ValueError("height is a fraction of the plot height")
        if not 0 <= alpha <= 1:
            raise ValueError("alpha is an opacity")
        bad = [p for p in players if not str(p).isdigit()]
        if bad:
            warnings.warn(f"no headshot for {bad}", SdvplotWarning, stacklevel=2)
        for xi, yi, pid in zip(list(x), list(y), list(players), strict=True):
            if str(pid).isdigit():
                target.append((str(pid), xi, yi, height))
        return target

    def axis_logos(target, axis, *, league, **kw):
        raise TypeError("the dummy adapter draws no axis logos")

    mod.add_logos = add_logos
    mod.add_wordmarks = add_logos  # the dummy resolves only, so a wordmark is drawn like a logo
    mod.add_headshots = add_headshots
    mod.axis_logos = axis_logos
    mod._SUPPORTS_AXIS_LOGOS = False
    mod._drawn_marks = list
    return mod


@pytest.fixture
def dummy(monkeypatch):
    mod = _dummy_adapter()
    monkeypatch.setitem(sys.modules, "sdvplot_dummy_adapter", mod)
    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_dummy_adapter", "fakeplot"))
    return mod


def test_front_door_dispatches_on_the_targets_library(dummy):
    assert d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl") == [("13", 0, 0, 0.1)]


def test_a_subclass_defined_elsewhere_still_dispatches_to_its_base_librarys_adapter(dummy):
    class Sub(Canvas):
        pass

    Sub.__module__ = "__main__"
    assert d.add_logos(Sub(), [0], [0], ["LV"], league="nfl") == [("13", 0, 0, 0.1)]


def test_unknown_target_lists_what_is_supported(dummy):
    with pytest.raises(UnsupportedTargetError, match="fakeplot"):
        d.add_logos(object(), [0], [0], ["LV"], league="nfl")


def test_missing_adapter_module_names_the_extra(monkeypatch):
    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_not_installed_xyz", "fakeplot"))
    with pytest.raises(OptionalDependencyError, match=r"pip install sdvplot\[fakeplot\]"):
        d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")


def test_an_unrelated_importerror_inside_the_adapter_is_not_mislabelled(monkeypatch, tmp_path):
    (tmp_path / "sdvplot_broken_adapter.py").write_text("raise ImportError('boom', name='some_unrelated_lib')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_broken_adapter", "fakeplot"))
    with pytest.raises(ImportError) as exc:
        d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")
    assert not isinstance(exc.value, OptionalDependencyError)
    assert exc.value.name == "some_unrelated_lib"


def test_the_dummy_adapter_passes_the_shared_contract(dummy):
    check_adapter_contract(dummy, make_target=Canvas)


def test_the_contract_catches_an_adapter_that_crashes_on_unknown_teams(dummy, monkeypatch):
    working = dummy.add_logos

    def fragile(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default"):
        if "XXX" in list(teams):
            raise KeyError("XXX")  # draws known teams fine (rule 1 passes), crashes on an unknown one (rule 2)
        return working(target, x, y, teams, league=league, season=season, height=height, alpha=alpha, variant=variant)

    monkeypatch.setattr(dummy, "add_logos", fragile)
    with pytest.raises(AssertionError, match="unknown team"):
        check_adapter_contract(dummy, make_target=Canvas)


def _mutant(dummy, monkeypatch, fn):
    monkeypatch.setattr(dummy, "add_logos", fn)


def test_rule_1_catches_an_adapter_that_draws_the_wrong_team(dummy, monkeypatch):
    working = dummy.add_logos

    def wrong(target, x, y, teams, *, league, **kw):
        return working(target, x, y, [list(teams)[0]] * len(list(teams)), league=league, **kw)  # same team twice

    _mutant(dummy, monkeypatch, wrong)
    with pytest.raises(AssertionError, match=r"rule 1 \(resolution\): expected marks"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_2_catches_an_adapter_that_crashes_on_unknown_teams(dummy, monkeypatch):
    working = dummy.add_logos

    def fragile(target, x, y, teams, *, league, **kw):
        if "XXX" in list(teams):
            raise KeyError("XXX")  # draws known teams fine (rule 1 passes), crashes on an unknown one (rule 2)
        return working(target, x, y, teams, league=league, **kw)

    _mutant(dummy, monkeypatch, fragile)
    with pytest.raises(AssertionError, match=r"rule 2 \(unknown team: warn and skip\): add_logos raised KeyError"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_2_catches_an_adapter_that_drops_the_name_but_not_the_xy(dummy, monkeypatch):
    def misaligned(target, x, y, teams, *, league, height=0.1, **kw):
        ids = [t for t in resolve(list(teams), league) if t is not None]
        for i, team_id in enumerate(ids):  # survivors take the first x/y, not their own
            target.append((team_id, list(x)[i], list(y)[i], height))
        return target

    _mutant(dummy, monkeypatch, misaligned)
    with pytest.raises(
        AssertionError,
        match=r"rule 2 \(unknown team: warn and skip\): an unknown team must be skipped with its own x/y",
    ):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_3_catches_an_adapter_that_indexes_pandas_by_label(dummy, monkeypatch):
    def by_label(target, x, y, teams, *, league, height=0.1, **kw):
        for i, team_id in enumerate(resolve(list(teams), league)):
            if team_id is not None:
                target.append((team_id, x[i], y[i], height))  # x[i] is a label lookup on a pandas Series
        return target

    _mutant(dummy, monkeypatch, by_label)
    with pytest.raises(AssertionError, match=r"rule 3 \(pandas/polars parity\): add_logos raised KeyError"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_4_catches_an_adapter_that_ignores_height(dummy, monkeypatch):
    working = dummy.add_logos

    def fixed(target, x, y, teams, *, league, height=0.1, **kw):
        return working(target, x, y, teams, league=league, height=0.1, **kw)  # always draws 0.1

    _mutant(dummy, monkeypatch, fixed)
    with pytest.raises(AssertionError, match=r"rule 4 \(height semantics\): height=0.25 must be the height"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_4_catches_an_adapter_that_checks_height_only_when_rendered(dummy, monkeypatch):
    working = dummy.add_logos

    def lazy(target, x, y, teams, *, league, height=0.1, **kw):  # accepts any height when called
        drawn = working(Canvas(), x, y, teams, league=league, **kw)
        return Canvas([*target, *((t, xi, yi, height) for t, xi, yi, _ in drawn)])

    def render(target):  # ... and only refuses a bad one when the marks are read
        if any(not 0 < m[3] <= 1 for m in target):
            raise ValueError("height is a fraction of the plot height")
        return list(target)

    _mutant(dummy, monkeypatch, lazy)
    monkeypatch.setattr(dummy, "_drawn_marks", render)
    with pytest.raises(AssertionError, match=r"rule 4 \(height semantics\): height=0 must raise ValueError"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_4_catches_an_adapter_that_accepts_a_height_above_one(dummy, monkeypatch):
    working = dummy.add_logos

    def lax(target, x, y, teams, *, league, height=0.1, **kw):
        if height == 0:
            raise ValueError("height")
        return working(target, x, y, teams, league=league, height=min(height, 1), **kw)

    _mutant(dummy, monkeypatch, lax)
    with pytest.raises(AssertionError, match=r"rule 4 \(height semantics\): height=1.5 must raise ValueError"):
        check_adapter_contract(dummy, make_target=Canvas)


@pytest.mark.parametrize("name", ["x_x", "y_x", "row_position"])
def test_rule_1_catches_wrong_coordinates(dummy, monkeypatch, name):
    def broken(target, x, y, teams, *, league, height=0.1, **kw):
        for i, (xi, yi, team_id) in enumerate(zip(list(x), list(y), resolve(list(teams), league), strict=True)):
            if team_id is not None:
                px, py = {"x_x": (xi, xi), "y_x": (yi, xi), "row_position": (i, i)}[name]
                target.append((team_id, px, py, height))
        return target

    _mutant(dummy, monkeypatch, broken)
    with pytest.raises(AssertionError, match=r"rule 1 \(resolution\): expected marks"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_an_adapter_that_returns_a_new_object_instead_of_mutating_passes_the_contract(dummy, monkeypatch):
    working = dummy.add_logos

    def immutable(target, x, y, teams, *, league, **kw):
        drawn = working(Canvas(), x, y, teams, league=league, **kw)  # draw on a fresh canvas, leave target alone
        return Canvas([*target, *drawn])

    monkeypatch.setattr(dummy, "add_logos", immutable)
    check_adapter_contract(dummy, make_target=Canvas)
    t = Canvas()
    assert d.add_logos(t, [1.0], [2.0], ["LV"], league="nfl") == [("13", 1.0, 2.0, 0.1)] and t == []


def test_a_removed_symbol_inside_an_installed_library_is_not_relabelled(monkeypatch):
    # An adapter whose import fails with a plain ImportError naming the target package (a symbol removed upstream)
    # must propagate unchanged; only a ModuleNotFoundError (the library is absent) becomes OptionalDependencyError.
    real = d.importlib.import_module  # capture before patching: d.importlib IS the importlib module

    def boom(name, *a, **k):
        if name == "sdvplot_symbol_gone":
            raise ImportError("cannot import name 'X' from 'fakeplot'", name="fakeplot")
        return real(name, *a, **k)

    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_symbol_gone", "fakeplot"))
    monkeypatch.setattr(d.importlib, "import_module", boom)
    with pytest.raises(ImportError) as exc:
        d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")
    assert not isinstance(exc.value, OptionalDependencyError)


def test_a_missing_target_library_still_names_the_extra(monkeypatch):
    real = d.importlib.import_module

    def gone(name, *a, **k):
        if name == "sdvplot_lib_missing":
            raise ModuleNotFoundError("No module named 'fakeplot'", name="fakeplot")
        return real(name, *a, **k)

    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_lib_missing", "fakeplot"))
    monkeypatch.setattr(d.importlib, "import_module", gone)
    with pytest.raises(OptionalDependencyError, match=r"pip install sdvplot\[fakeplot\]"):
        d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")


def test_rule_0_catches_a_target_that_routes_elsewhere(dummy, monkeypatch):
    other = _dummy_adapter()
    with pytest.raises(AssertionError, match=r"rule 0 \(registration\)"):
        check_adapter_contract(other, make_target=Canvas)  # Canvas routes to `dummy`, not to `other`


def test_rule_5_catches_an_adapter_whose_wordmarks_ignore_height(dummy, monkeypatch):
    working = dummy.add_logos

    def fixed(target, x, y, teams, *, league, height=0.1, **kw):
        return working(target, x, y, teams, league=league, height=0.1, **kw)

    monkeypatch.setattr(dummy, "add_wordmarks", fixed)
    with pytest.raises(AssertionError, match=r"rule 5 \(wordmarks: height\)"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_6_catches_an_adapter_that_drops_headshots(dummy, monkeypatch):
    monkeypatch.setattr(dummy, "add_headshots", lambda target, *a, **k: target)
    with pytest.raises(AssertionError, match=r"rule 6 \(headshots\)"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_7_catches_an_adapter_without_axis_support_that_does_not_raise(dummy, monkeypatch):
    monkeypatch.setattr(dummy, "axis_logos", lambda target, axis, **k: target)
    with pytest.raises(AssertionError, match=r"rule 7 \(axis logos\)"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_7_requires_an_axis_target_from_an_adapter_that_supports_axis_logos(dummy, monkeypatch):
    monkeypatch.setattr(dummy, "_SUPPORTS_AXIS_LOGOS", True)
    with pytest.raises(AssertionError, match="make_axis_target is required"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_8_catches_an_adapter_that_accepts_any_alpha(dummy, monkeypatch):
    working = dummy.add_logos

    def lax(target, x, y, teams, *, league, alpha=1.0, **kw):
        return working(target, x, y, teams, league=league, alpha=min(max(alpha, 0), 1), **kw)

    monkeypatch.setattr(dummy, "add_logos", lax)
    with pytest.raises(AssertionError, match=r"rule 8 \(alpha\)"):
        check_adapter_contract(dummy, make_target=Canvas)


@pytest.mark.parametrize("how", ["a second resolution", "one warning per value"])
def test_rule_2_catches_an_adapter_that_warns_more_than_once_per_call(dummy, monkeypatch, how):
    working = dummy.add_logos

    def noisy(target, x, y, teams, *, league, **kw):
        if how == "a second resolution":  # e.g. once per layer, or a retry: the resolver warns again
            resolve(list(teams), league)
            return working(target, x, y, teams, league=league, **kw)
        for xi, yi, team in zip(list(x), list(y), list(teams), strict=True):
            working(target, [xi], [yi], [team], league=league, **kw)  # one call, so one warning, per unknown value
        return target

    _mutant(dummy, monkeypatch, noisy)
    with pytest.raises(AssertionError, match=r"rule 2 \(unknown team: warn and skip\): .*exactly one SdvplotWarning"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_1_catches_an_adapter_that_warns_when_nothing_is_skipped(dummy, monkeypatch):
    working = dummy.add_logos

    def chatty(target, *a, **k):
        warnings.warn("drawing logos", SdvplotWarning, stacklevel=2)
        return working(target, *a, **k)

    _mutant(dummy, monkeypatch, chatty)
    with pytest.raises(AssertionError, match=r"rule 1 \(resolution\): known teams must not warn"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_6_catches_headshots_that_warn_twice_for_one_unknown_id(dummy, monkeypatch):
    working = dummy.add_headshots

    def noisy(target, x, y, players, **kw):
        if any(not str(p).isdigit() for p in players):
            warnings.warn("checking ids", SdvplotWarning, stacklevel=2)  # a validation pass that also warns
        return working(target, x, y, players, **kw)

    monkeypatch.setattr(dummy, "add_headshots", noisy)
    with pytest.raises(AssertionError, match=r"rule 6 \(headshots\): .*exactly one SdvplotWarning"):
        check_adapter_contract(dummy, make_target=Canvas)


@pytest.mark.parametrize("verb", ["add_wordmarks", "add_headshots"])
def test_rule_8_catches_a_verb_that_ignores_alpha(dummy, monkeypatch, verb):
    working = getattr(dummy, verb)

    def lax(target, x, y, teams, *, league, alpha=1.0, **kw):
        return working(target, x, y, teams, league=league, **kw)  # alpha is accepted and dropped

    monkeypatch.setattr(dummy, verb, lax)
    with pytest.raises(AssertionError, match=rf"rule 8 \(alpha\): alpha=-0.1 must raise ValueError from {verb}"):
        check_adapter_contract(dummy, make_target=Canvas)


def test_rule_6_catches_headshots_that_accept_a_height_above_one(dummy, monkeypatch):
    working = dummy.add_headshots

    def lax(target, x, y, players, *, league, height=0.1, **kw):
        return working(target, x, y, players, league=league, height=min(height, 1), **kw)

    monkeypatch.setattr(dummy, "add_headshots", lax)
    with pytest.raises(
        AssertionError, match=r"rule 6 \(headshots: height\): height=1.5 must raise ValueError from add_headshots"
    ):
        check_adapter_contract(dummy, make_target=Canvas)


def _axis_target(categories):
    t = Canvas()
    t.labels = list(categories)  # the x axis' tick labels, in tick order
    return t


@pytest.fixture
def axis_dummy(dummy, monkeypatch):
    """The dummy adapter with axis logos: each team label becomes an ("axis", team_id, tick, height) entry."""

    def axis_logos(target, axis, *, league, height=0.1, **kw):
        if not 0 < height <= 1:
            raise ValueError("height is a fraction of the plot height")
        for i, team_id in enumerate(resolve(list(target.labels), league)):
            if team_id is not None:
                target.append(("axis", team_id, float(i), height))
                target.labels[i] = ""
        return target

    monkeypatch.setattr(dummy, "axis_logos", axis_logos)
    monkeypatch.setattr(dummy, "_SUPPORTS_AXIS_LOGOS", True)
    monkeypatch.setattr(dummy, "_drawn_axis_marks", lambda t, axis: [m[1:] for m in t if m[0] == "axis"], raising=False)
    monkeypatch.setattr(dummy, "_visible_axis_labels", lambda t, axis: [lab for lab in t.labels if lab], raising=False)
    return dummy


def test_an_adapter_with_axis_logos_passes_the_contract(axis_dummy):
    check_adapter_contract(axis_dummy, make_target=Canvas, make_axis_target=_axis_target)


def test_rule_7_catches_axis_logos_that_ignore_height(axis_dummy, monkeypatch):
    working = axis_dummy.axis_logos
    monkeypatch.setattr(
        axis_dummy, "axis_logos", lambda t, axis, *, league, height=0.1: working(t, axis, league=league)
    )
    with pytest.raises(
        AssertionError, match=r"rule 7 \(axis logos: height\): height=0.25 must be the height of every mark axis_logos"
    ):
        check_adapter_contract(axis_dummy, make_target=Canvas, make_axis_target=_axis_target)


def test_rule_8_catches_axis_logos_that_take_alpha_and_ignore_it(axis_dummy, monkeypatch):
    working = axis_dummy.axis_logos
    monkeypatch.setattr(axis_dummy, "axis_logos", lambda t, axis, *, alpha=1.0, **kw: working(t, axis, **kw))
    with pytest.raises(AssertionError, match=r"rule 8 \(alpha\): alpha=-0.1 must raise ValueError from axis_logos"):
        check_adapter_contract(axis_dummy, make_target=Canvas, make_axis_target=_axis_target)


def test_rule_7_catches_axis_logos_that_warn_twice(axis_dummy, monkeypatch):
    working = axis_dummy.axis_logos

    def noisy(target, axis, **kw):
        resolve(list(target.labels), kw["league"])  # resolving the labels twice warns twice
        return working(target, axis, **kw)

    monkeypatch.setattr(axis_dummy, "axis_logos", noisy)
    with pytest.raises(AssertionError, match=r"rule 7 \(axis logos\): .*exactly one SdvplotWarning"):
        check_adapter_contract(axis_dummy, make_target=Canvas, make_axis_target=_axis_target)


def test_rule_4_measures_the_matplotlib_height_drawn_not_the_height_recorded(mark_images, headshot_images, monkeypatch):
    plt = pytest.importorskip("matplotlib.pyplot")
    import sdvplot.matplotlib as smpl

    real = smpl._AxesFractionImage.get_bbox
    # the image is drawn at half the height the adapter records in its _sdvplot_mark
    monkeypatch.setattr(smpl._AxesFractionImage, "get_bbox", lambda self, renderer: real(self, renderer).shrunk(1, 0.5))

    def axes():
        _, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.set(xlim=(0, 30), ylim=(-10, 0))
        return ax

    def bars(categories):
        _, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.bar(categories, range(1, len(categories) + 1))
        return ax

    try:
        with pytest.raises(
            AssertionError, match=r"rule 4 \(height semantics\): height=0.1 must be the height of every mark add_logos"
        ):
            check_adapter_contract(smpl, make_target=axes, make_axis_target=bars)
    finally:
        plt.close("all")


def test_rule_4_measures_the_matplotlib_height_after_the_layout_runs(mark_images, headshot_images, monkeypatch):
    # an image sized in pixels when it is added, before constrained layout resizes the Axes on draw, ends up the
    # wrong fraction of the Axes: only a hook that draws before it measures can see that
    plt = pytest.importorskip("matplotlib.pyplot")
    from matplotlib.transforms import Bbox

    import sdvplot.matplotlib as smpl

    real_init = smpl._AxesFractionImage.__init__

    def frozen(self, arr, ax, fraction, **kw):
        real_init(self, arr, ax, fraction, **kw)
        self._px = fraction * ax.bbox.height  # pixels fixed now, not the fraction of the Axes read at draw time

    monkeypatch.setattr(smpl._AxesFractionImage, "__init__", frozen)
    monkeypatch.setattr(smpl._AxesFractionImage, "get_bbox",
                        lambda self, renderer: Bbox.from_bounds(0, 0, self._px * self._sdv_cols / self._sdv_rows,
                                                                self._px))  # fmt: skip

    def axes():
        _, ax = plt.subplots(figsize=(6, 4), dpi=100, layout="constrained")
        ax.set(xlim=(0, 30), ylim=(-10, 0))
        return ax

    try:
        with pytest.raises(
            AssertionError, match=r"rule 4 \(height semantics\): height=0.1 must be the height of every mark add_logos"
        ):
            check_adapter_contract(smpl, make_target=axes)
    finally:
        plt.close("all")


def test_rule_4_measures_the_pygal_height_drawn_not_the_height_recorded(mark_images, headshot_images, monkeypatch):
    pygal = pytest.importorskip("pygal")
    import sdvplot.pygal as spg

    real = spg._MarksFilter.__call__

    def half(self, root):  # the render draws half the height add_logos was asked for (and recorded)
        root = real(self, root)
        for el in root.iter():
            if el.get(spg._MARK) is not None:
                el.set("height", f"{float(el.get('height')) / 2:.3f}")
        return root

    monkeypatch.setattr(spg._MarksFilter, "__call__", half)

    def chart():
        c = pygal.XY(stroke=False, show_legend=False)
        c.add("games", [(10, -3), (20, -7)])
        return c

    with pytest.raises(
        AssertionError, match=r"rule 4 \(height semantics\): height=0.1 must be the height of every mark add_logos"
    ):
        check_adapter_contract(spg, make_target=chart)
