# test_fleet_report.py
import pytest
from unittest.mock import patch
from fleet_report import fleet_summary, print_report

SAMPLE = [
    {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    {"id": "VOS-2210", "odometer": 48400, "last_service_km": 45000},
]


def test_summary_counts_due_cars():
    # Only VOS-4471 is nearly worn, so exactly one car is due.
    assert fleet_summary(SAMPLE)["due"] == 1


def test_summary_no_crash_with_missing_last_service_km():
    # VOS-7788 has no last_service_km; fleet_summary must not crash and no_reading must be 1.
    fleet = [
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
        {"id": "VOS-7788", "odometer": 92000},
    ]
    result = fleet_summary(fleet)
    assert result["no_reading"] == 1


def test_average_wear_true_division():
    # car A: 14900 km since service → 99.333...%
    # car B:  3000 km since service → 20.000...%
    # average = (99.333 + 20.000) / 2 = 59.666... ≈ 59.67
    fleet = [
        {"id": "A", "odometer": 14900, "last_service_km": 0},
        {"id": "B", "odometer": 18000, "last_service_km": 15000},
    ]
    result = fleet_summary(fleet)
    assert result["average_wear"] == pytest.approx(59.67, abs=0.01)


def test_print_report_no_crash_all_no_reading():
    # A fleet where no car has a last_service_km must not crash print_report().
    # flush_log is patched so no log file is written to disk.
    fleet = [
        {"id": "VOS-7788", "odometer": 92000},
        {"id": "VOS-9001", "odometer": 31000},
    ]
    with patch("fleet_report.flush_log"):
        print_report(fleet)   # must not raise


def test_null_last_service_km_counted_as_no_reading():
    # A car whose last_service_km is present but None must be counted under no_reading,
    # not crash and not contribute to the average.
    fleet = [
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
        {"id": "VOS-7788", "odometer": 92000, "last_service_km": None},
    ]
    result = fleet_summary(fleet)
    assert result["no_reading"] == 1
    assert result["count"] == 2
