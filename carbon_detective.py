"""Transparent energy-intensity anomaly detector for monthly factory records."""

from __future__ import annotations

from decimal import Decimal
from statistics import median
from typing import Any, Mapping, Sequence
from .carbon_calculator import _nonnegative_decimal, _display


def detect_carbon_anomaly(
    records: Sequence[Mapping[str, Any]], threshold_pct: float = 20,
) -> dict:
    """Detect unusual electricity consumed per manufactured item.

    Input records must be sorted oldest to newest and refer to comparable
    monthly periods/products. >=3 months required; previous months define
    a median baseline. Threshold is an illustrative configurable heuristic.
    """
    if not isinstance(records, (list, tuple)) or len(records) < 3:
        raise ValueError("Supply at least 3 comparable monthly records, oldest first")
    threshold = _nonnegative_decimal(threshold_pct, "threshold_pct")
    if threshold > 10000:
        raise ValueError("threshold_pct is unexpectedly large")
    intensities = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"Record {index + 1} must be an object")
        electricity = _nonnegative_decimal(record.get("electricity_kwh"), "electricity_kwh")
        products = _nonnegative_decimal(record.get("products"), "products")
        if products == 0:
            raise ValueError(f"Record {index + 1}: products must be greater than zero")
        intensities.append(electricity / products)

    baseline = Decimal(str(median(intensities[:-1])))
    current = intensities[-1]
    if baseline <= 0:
        raise ValueError("Baseline consumption must be greater than zero")
    change_pct = (current - baseline) / baseline * Decimal("100")
    alert = change_pct > threshold
    return {
        "alert": alert,
        "severity": "investigate" if alert else "normal",
        "baseline_kwh_per_product": _display(baseline),
        "current_kwh_per_product": _display(current),
        "change_percent": _display(change_pct),
        "threshold_percent": _display(threshold),
        "months_compared": len(records),
        "possible_causes_to_investigate": (
            ["Longer machine idle time", "Maintenance or equipment efficiency issues",
             "Different product mix or processing requirements", "Metering or billing-data error"]
            if alert else []
        ),
        "method": (
            "Current month electricity_kwh/products versus median of all previous months; "
            "flag if percentage increase exceeds configurable threshold."
        ),
        "limitations": (
            "This is a simple heuristic, not proof of a carbon leak or its cause. "
            "Check seasonality, product mix, changes in operations, and data quality."
        ),
    }
