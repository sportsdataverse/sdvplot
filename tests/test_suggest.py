from sdvplot._resolve import suggest


def test_suggest_offers_candidates_without_choosing():
    out = suggest("Las Vegas Raider", "nfl")
    assert out[0] == ("13", "Las Vegas Raiders")


def test_suggest_lists_every_team_behind_an_ambiguous_key():
    ids = {tid for tid, _ in suggest("Miami", "cfb", n=5)}
    assert {"2390", "193"} <= ids


def test_suggest_returns_nothing_for_nulls_and_nonsense():
    assert suggest(None, "nfl") == [] and suggest("zzzzzz", "nfl") == []
