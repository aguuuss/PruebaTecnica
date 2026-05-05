from app.services.normalization import dedupe_key, normalize_text


def test_normalize_removes_accents_and_fillers():
    assert normalize_text("Bar Irlanda Tucuman!", remove_fillers=True) == "irlanda"


def test_dedupe_key_keeps_address_signal():
    assert dedupe_key("Irlanda Bar", "Catamarca 380") == "irlanda|catamarca 380"
