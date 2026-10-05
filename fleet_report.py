# fleet_report.py
# Prints the nightly fleet-health summary for Vossberg Mobility.

from km_wachter import wear_percent, needs_service, SERVICE_INTERVAL_KM
from config_loader import load_settings
from log_util import log, flush_log
import fleet_utils


def car_wear(car: dict) -> float | None:
    """Return wear percentage for car, or None if no service reading exists."""
    if "last_service_km" not in car or car["last_service_km"] is None:
        return None
    return wear_percent(car["odometer"] - car["last_service_km"], SERVICE_INTERVAL_KM)


def fleet_summary(fleet: list[dict]) -> dict:
    """Summarise wear, service due count, and no-reading count for the fleet."""
    total = 0.0
    due = 0
    no_reading = 0
    readings = 0
    for car in fleet:
        wear = car_wear(car)
        if wear is None:
            no_reading += 1
        else:
            total += wear
            readings += 1
        if needs_service(car):
            due += 1
    average = total / readings if readings > 0 else None
    return {"count": len(fleet), "due": due, "average_wear": average, "no_reading": no_reading}


def print_report(fleet: list[dict]) -> None:
    """Print the nightly fleet report and flush the log."""
    settings = load_settings()
    log(settings.get("report_title", "Nightly fleet report"))
    s = fleet_summary(fleet)
    print(f"Fleet: {s['count']} cars")
    print(f"Due for service: {s['due']}")
    if s["average_wear"] is None:
        print("Average wear: n/a")
    else:
        print(f"Average wear: {s['average_wear']:.1f}%")
    print(f"No reading: {s['no_reading']} cars")
    total_km = sum(car["odometer"] for car in fleet)
    # The partner garage in England wants the distance in miles (since 2015).
    print(f"Fleet distance: {fleet_utils.format_number(fleet_utils.km_to_miles(total_km))} miles")
    flush_log(settings.get("log_file", "km_wachter.log"))
