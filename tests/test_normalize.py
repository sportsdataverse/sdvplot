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


def test_latin_letters_nfkd_leaves_whole_fold_too():  # sdvplotR#70: "Køge" == "Koge"
    assert norm_value("Køge") == norm_value("KØGE") == norm_value("Koge") == "koge"
    assert norm_value("Malmö FF") == norm_value("Malmo FF") == "malmo ff"
    assert norm_value("Łódź") == norm_value("ŁÓDŹ") == "lodz"
    assert norm_value("Æbeltoft") == "aebeltoft" and norm_value("Sherbrooke Phœnix") == "sherbrooke phoenix"
    assert norm_value("ŒUVRE") == "oeuvre" and norm_value("Đakovo") == norm_value("Ðakovo") == "dakovo"
    assert norm_value("Þór Akureyri") == "thor akureyri" and norm_value("Iğdır") == "igdir"
    assert norm_value("ǿ") == "o" and norm_value("ǣ") == "ae"  # a folded letter under an accent folds after NFKD
    assert norm_value("Weißenfels") == "weissenfels"  # casefold's "ss"
