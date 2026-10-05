# fleet_utils.py
# Utility helpers for the Vossberg Mobility fleet nightly run.

MILES_PER_KM = 0.621371  # 1 km = 0.621371 miles


def km_to_miles(km: float) -> float:
    """Convert kilometres to miles for the UK partner report."""
    return km * MILES_PER_KM


def format_number(value: float) -> str:
    """Format a number to one decimal place."""
    return f"{value:.1f}"
