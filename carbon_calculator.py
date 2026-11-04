"""Explainable, factor-based operational emissions calculator.

This is an MVP calculation engine, NOT a certification or complete GHG inventory.
The bundled factor values are intentionally DEMO ONLY. Replace with documented,
appropriate factors before any real report is shared externally.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping

DEFAULT_FACTOR_FILE = Path(__file__).with_name("demo_factors.json")
QUANT = Decimal("0.01")
FIELDS = ("electricity_kwh", "diesel_litres")


def _nonnegative_decimal(value: Any, label: str) -> Decimal:
    """Accept real-world form values while rejecting negative/NaN/infinite data."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{label} must be a non-negative number")
    try:
        number = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError, AttributeError):
        raise ValueError(f"{label} must be a non-negative number") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"{label} must be a finite, non-negative number")
    return number


def _display(value: Decimal) -> float:
    return float(value.quantize(QUANT, rounding=ROUND_HALF_UP))


def load_factors(path: str | Path | None = None) -> dict:
    """Load factor metadata, keeping provenance available for every calculation."""
    factor_path = Path(path) if path is not None else DEFAULT_FACTOR_FILE
    with factor_path.open("r", encoding="utf-8") as file:
        result = json.load(file)
    if not isinstance(result, dict):
        raise ValueError("Factor file must contain a JSON object")
    for key in FIELDS:
        if key not in result or not isinstance(result[key], dict):
            raise ValueError(f"Missing factor metadata for {key}")
        meta = result[key]
        for required in ("factor", "unit", "scope", "source", "factor_year", "geography", "verified_for_reporting"):
            if required not in meta:
                raise ValueError(f"Missing '{required}' for {key}")
        factor = _nonnegative_decimal(meta["factor"], f"{key} emission factor")
        if factor <= 0:
            raise ValueError(f"Emission factor {key} must be greater than zero")
        if not isinstance(meta["verified_for_reporting"], bool):
            raise ValueError(f"{key} verified_for_reporting must be boolean")
    return result


def calculate_emissions(
    activity: Mapping[str, Any],
    factors: Mapping[str, dict] | None = None,
) -> dict:
    """Calculate Scope 1 diesel combustion + Scope 2 purchased electricity.

    Parameters
    ----------
    activity: {electricity_kwh: number, diesel_litres: number,
               production_units: optional number}
    factors: factor metadata mapping, default: bundled DEMO metadata.

    Diesel is classified Scope 1 ONLY for fuel burned by company-controlled
    vehicles/equipment. Third-party freight cannot automatically be Scope 1.
    Electricity figure is an illustrative location-based Scope 2 estimate.
    """
    if not isinstance(activity, Mapping):
        raise ValueError("activity must be a JSON-style object")
    if factors is None:
        factors = load_factors()
    if not isinstance(factors, Mapping):
        raise ValueError("factors must be a mapping")

    entries = []
    scope_totals = {"Scope 1": Decimal("0"), "Scope 2": Decimal("0")}
    all_verified = True
    total = Decimal("0")

    for field in FIELDS:
        quantity = _nonnegative_decimal(activity.get(field, 0), field)
        try:
            meta = factors[field]
            factor = _nonnegative_decimal(meta["factor"], f"{field} emission factor")
            if factor <= 0:
                raise ValueError(f"{field} emission factor must be positive")
            scope = meta["scope"]
            if scope not in scope_totals:
                raise ValueError(f"Unknown scope for {field}")
            source, unit, year, geography = (str(meta[key]) for key in
                                            ("source", "unit", "factor_year", "geography"))
            verified = meta["verified_for_reporting"] is True
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Missing/invalid factor metadata for {field}") from exc
        emissions = quantity * factor
        total += emissions
        scope_totals[scope] += emissions
        all_verified = all_verified and verified
        entries.append({
            "activity": field,
            "quantity": _display(quantity),
            "factor": float(factor),
            "factor_unit": unit,
            "scope": scope,
            "emissions_kg_co2e": _display(emissions),
            "factor_source": source,
            "factor_year": year,
            "factor_geography": geography,
            "factor_verified_for_reporting": verified,
            "formula": "activity_quantity × emission_factor",
        })

    intensity = None
    if "production_units" in activity and activity["production_units"] not in (None, ""):
        units = _nonnegative_decimal(activity["production_units"], "production_units")
        if units == 0:
            raise ValueError("production_units must be greater than zero when supplied")
        intensity = _display(total / units)

    return {
        "total_kg_co2e": _display(total),
        "scope_1_kg_co2e": _display(scope_totals["Scope 1"]),
        "scope_2_kg_co2e": _display(scope_totals["Scope 2"]),
        "operational_intensity_kg_co2e_per_unit": intensity,
        "line_items": entries,
        "all_factors_marked_verified": all_verified,
        "reporting_warning": (
            "Bundled DEMO emission factors; not suitable for external reports. "
            "Replace with appropriate, documented factors and check reporting boundaries."
            if not all_verified else
            "Factor metadata is marked verified, but independent review of boundaries, "
            "sources, data, and methodology is still required."
        ),
        "coverage": (
            "Only purchased electricity and combustion of diesel in company-controlled "
            "operations. Excludes other possible Scope 1/2 activities and all Scope 3."
        ),
    }
