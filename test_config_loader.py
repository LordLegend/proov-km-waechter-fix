# test_config_loader.py
from config_loader import load_settings


def test_value_containing_equals_sign(tmp_path):
    # A value that itself contains "=" must be kept whole, not truncated at the second "=".
    cfg = tmp_path / "test.cfg"
    cfg.write_text("report_title = a = b\n")
    settings = load_settings(str(cfg))
    assert settings["report_title"] == "a = b"
