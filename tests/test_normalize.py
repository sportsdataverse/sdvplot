from sdvplot._normalize import norm_value
from sdvplot._resolve import resolve


def test_an_integral_float_literal_string_normalizes_like_the_number():  # Review Focus 1: float -> str id casts
    assert {norm_value(v) for v in (13, 13.0, "13", "13.0", " 13.00 ")} == {"13"}
    assert resolve("13.0", "nfl") == "13"
    assert norm_value("13.5") == "13.5" and norm_value("013") == "013"  # not integral / an exact id form: kept


def test_accents_curly_apostrophes_and_dashes_fold_like_sdvplotr():  # R43: sdvplotR's fold_accents
    assert norm_value("San José State") == norm_value("San Jose State") == "san jose state"
    assert norm_value("Montréal Canadiens") == "montreal canadiens"
    assert norm_value("Saint Mary’s") == norm_value("Saint Mary‘s") == "saint mary's"
    assert norm_value("Nevada–Las Vegas") == norm_value("Nevada—Las Vegas") == "nevada-las vegas"
    assert resolve("Las Végas Raiders", "nfl") == "13"  # alias values go through the same function in _lookup
