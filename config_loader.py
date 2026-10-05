# config_loader.py
# Reads settings.cfg for Vossberg Mobility fleet configuration.

SETTINGS_FILE = "settings.cfg"

KNOWN_KEYS = [
    "service_interval_km",
    "warn_at_percent",
    "report_title",
    "history_file",
    "log_file",
    "mileage_unit",
]


def load_settings(path: str | None = None) -> dict[str, str]:
    """Parse a key = value settings file and return a dict of known keys."""
    if path is None:
        path = SETTINGS_FILE
    settings: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue  # malformed line — skip silently
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key in KNOWN_KEYS:
                settings[key] = value
            else:
                print(f"Warning: unknown settings key '{key}'")
    return settings


def get_int(settings: dict[str, str], key: str, fallback: int) -> int:
    """Return settings[key] as int, or fallback if missing or not an integer."""
    try:
        return int(settings[key])
    except (KeyError, ValueError):
        return fallback
