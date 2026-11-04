"""Privacy-aware recommendations: works offline; LLM explanation is optional."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

SYSTEM_PROMPT = """You are CarbonEase's sustainability information assistant for small businesses.
Use ONLY the numerical facts supplied. Never invent emission factors, savings,
measurements, equipment conditions, verified certifications or legal compliance.
Explain possible reasons for anomalies as hypotheses to investigate, not facts.
Recommend practical, low-risk efficiency checks. Mention that changes require
measurement and that business reports need verified factors and reviewed data.
Reply in simple English: 1 short summary and 3 numbered actionable suggestions.
Do not request identifying information about workers or customers.
"""


def generate_recommendations(
    emissions: Mapping[str, Any], detective: Mapping[str, Any] | None = None
) -> list[dict[str, str]]:
    """Deterministic suggestions for a demo (no AI account required)."""
    suggestions = []
    if detective and detective.get("alert"):
        suggestions.append({
            "title": "Investigate energy-intensity increase",
            "priority": "high",
            "action": "Check machine idle hours, production mix, recent maintenance, and meter readings before deciding on the cause.",
            "how_to_verify": "Compare next month's kWh per comparable product against the historical median.",
        })
    for item in emissions.get("line_items", []):
        if item.get("activity") == "electricity_kwh" and item.get("quantity", 0) > 0:
            suggestions.append({
                "title": "Review electricity-use patterns",
                "priority": "medium",
                "action": "Inspect equipment schedules and identify avoidable idle-time usage; check feasibility of maintenance improvements.",
                "how_to_verify": "Track metered kWh and kWh per unit of comparable output each month.",
            })
        if item.get("activity") == "diesel_litres" and item.get("quantity", 0) > 0:
            suggestions.append({
                "title": "Review diesel use",
                "priority": "medium",
                "action": "Review routing, equipment operating hours, and maintenance records for efficiency opportunities.",
                "how_to_verify": "Compare actual litres consumed for similar activity levels after any change.",
            })
    if not suggestions:
        suggestions.append({
            "title": "Start a reliable activity log",
            "priority": "medium",
            "action": "Record actual electricity and fuel quantities monthly and retain invoice evidence.",
            "how_to_verify": "Check that every reporting month has reviewed source records.",
        })
    return suggestions


def build_ai_prompt(
    emissions: Mapping[str, Any], detective: Mapping[str, Any] | None = None
) -> str:
    """Send ONLY aggregated quantities; never include original bill text/PII."""
    minimized = {
        "total_kg_co2e": emissions.get("total_kg_co2e"),
        "scope_1_kg_co2e": emissions.get("scope_1_kg_co2e"),
        "scope_2_kg_co2e": emissions.get("scope_2_kg_co2e"),
        "operational_intensity_kg_co2e_per_unit": emissions.get("operational_intensity_kg_co2e_per_unit"),
        "factors_verified": emissions.get("all_factors_marked_verified"),
        "anomaly_detected": bool(detective and detective.get("alert")),
        "electricity_intensity_change_percent": (
            detective.get("change_percent") if detective else None
        ),
    }
    return (
        "Explain these calculated demo results to a small business owner. "
        "Mention uncertainty and avoid unsupported claims.\n"
        + json.dumps(minimized, indent=2)
    )


def explain_with_llm(
    emissions: Mapping[str, Any], detective: Mapping[str, Any] | None = None,
) -> str:
    """Optional OpenAI integration; credentials must stay on the backend.

    Set OPENAI_API_KEY and OPENAI_MODEL and install `openai`. No bills or
    identifying customer information are sent; only summarized metrics.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY on the backend to enable the optional LLM")
    model = os.getenv("OPENAI_MODEL")
    if not model:
        raise RuntimeError("Set OPENAI_MODEL to a model enabled for your account")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the optional SDK: pip install -r requirements-ai.txt") from exc
    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=build_ai_prompt(emissions, detective),
        max_output_tokens=350,
    )
    return response.output_text
