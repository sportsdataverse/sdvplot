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
        for team_id in resolve(list(teams), league, season=season):
            if team_id is not None:
                target.append(team_id)
        return target

    mod.add_logos = add_logos
    mod.count_marks = len
    return mod


@pytest.fixture
def dummy(monkeypatch):
    mod = _dummy_adapter()
    monkeypatch.setitem(sys.modules, "sdvplot_dummy_adapter", mod)
    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_dummy_adapter", "fakeplot"))
    return mod


def test_front_door_dispatches_on_the_targets_library(dummy):
    assert d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl") == ["13"]


def test_unknown_target_lists_what_is_supported(dummy):
    with pytest.raises(UnsupportedTargetError, match="fakeplot"):
        d.add_logos(object(), [0], [0], ["LV"], league="nfl")


def test_missing_adapter_module_names_the_extra(monkeypatch):
    monkeypatch.setattr(d, "ADAPTERS", {})
    d.register_adapter(d.Adapter("fakeplot", "fakeplot", "sdvplot_not_installed_xyz", "fakeplot"))
    with pytest.raises(OptionalDependencyError, match=r"pip install sdvplot\[fakeplot\]"):
        d.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")


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
