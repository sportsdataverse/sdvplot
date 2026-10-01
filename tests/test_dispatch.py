import sys
import types

import pytest

import sdvplot._dispatch as d
from sdvplot._errors import OptionalDependencyError, UnsupportedTargetError
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
        # positional values, never index labels; x, y and teams are filtered together
        for xi, yi, team_id in zip(list(x), list(y), resolve(list(teams), league, season=season), strict=True):
            if team_id is not None:
                target.append((team_id, xi, yi, height))
        return target

    mod.add_logos = add_logos
    mod.drawn_marks = list
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
