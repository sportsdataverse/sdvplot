from sdvplot._normalize import norm_value
from sdvplot._resolve import resolve


def test_an_integral_float_literal_string_normalizes_like_the_number():  # Review Focus 1: float -> str id casts
    assert {norm_value(v) for v in (13, 13.0, "13", "13.0", " 13.00 ")} == {"13"}
    assert resolve("13.0", "nfl") == "13"
    assert norm_value("13.5") == "13.5" and norm_value("013") == "013"  # not integral / an exact id form: kept
