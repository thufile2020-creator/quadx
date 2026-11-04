"""CarbonEase Member 3: calculations, anomaly detection, OCR and suggestions."""

from .carbon_calculator import calculate_emissions, load_factors
from .carbon_detective import detect_carbon_anomaly
from .ocr import parse_bill_text, read_bill
from .recommendations import generate_recommendations, build_ai_prompt, explain_with_llm

__all__ = [
    "calculate_emissions",
    "load_factors",
    "detect_carbon_anomaly",
    "parse_bill_text",
    "read_bill",
    "generate_recommendations",
    "build_ai_prompt",
    "explain_with_llm",
]
