"""OCR and cautious field extraction for electricity and diesel bills.

TXT works with just Python; images require Pillow, pytesseract and the
Tesseract executable; PDFs additionally require PyMuPDF. Never blindly
accept values from OCR: all scanned records must be confirmed by a user.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

MAX_FILE_BYTES = 12 * 1024 * 1024
ALLOWED = {".txt", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".pdf"}
NUMBER = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"


def _number(raw: str) -> float:
    return float(raw.replace(",", ""))


def _first(patterns: list[str], text: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return _number(match.group(1))
    return None


def parse_bill_text(text: str) -> dict:
    """Extract activity values from OCR/plain text using conservative rules.

    It will often miss non-standard bills. A missing field should NEVER
    be guessed from an invoice amount or arbitrary number.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Bill text is empty")

    elec_patterns = [
        rf"\b(?:units?\s+(?:consumed|billed|used)|consumption\s*(?:in\s*)?(?:units?|kwh)|electricity\s+(?:use|usage|consumption)|energy\s+consumed)\s*(?:\(\s*kwh\s*\))?\s*[:=\-]?\s*{NUMBER}\s*(?:kwh|units?)?\b",
        rf"\b(?:total\s+units?)\s*[:=\-]\s*{NUMBER}\b",
        rf"\b(?:kwh\s+consumed|billed\s+kwh)\s*[:=\-]?\s*{NUMBER}\b",
    ]
    diesel_patterns = [
        rf"\bdiesel\s+(?:quantity|volume|litres?|liters?|purchased)\s*[:=\-]?\s*{NUMBER}\s*(?:l|litres?|liters?)?\b",
        rf"\bdiesel\s*[:=\-]\s*{NUMBER}\s*(?:l|litres?|liters?)\b",
    ]
    diesel_identifier = bool(re.search(r"\bdiesel\b", text, re.IGNORECASE))
    diesel = _first(diesel_patterns, text)
    if diesel is None and diesel_identifier:
        diesel = _first([
            rf"\b(?:fuel\s+)?quantity\s*(?:\(\s*(?:l|litres?|liters?)\s*\))?\s*[:=\-]\s*{NUMBER}\s*(?:l|litres?|liters?)?\b",
            rf"\b(?:litres?|liters?)\s+(?:purchased|sold|supplied)\s*[:=\-]?\s*{NUMBER}\b",
        ], text)
    electricity = _first(elec_patterns, text)

    date_match = re.search(r"\b(20\d{2}[-/]\d{2})\b", text)
    invoice_match = re.search(r"\b(?:invoice|bill)\s*(?:no\.?|number|#)\s*[:#-]?\s*([A-Za-z0-9-]{3,35})\b", text, re.IGNORECASE)
    values = {"electricity_kwh": electricity, "diesel_litres": diesel}
    found = [k for k, v in values.items() if v is not None]
    warnings = ["Always compare the extracted values with the original bill before saving."]
    if not found:
        warnings.append("No supported consumption quantity confidently detected; enter it manually.")
    if electricity is None:
        warnings.append("Electricity consumption not detected in this document.")
    if diesel is None:
        warnings.append("Diesel quantity not detected in this document.")

    return {
        "document_type": "electricity" if electricity is not None else ("diesel" if diesel is not None else "unknown"),
        "extracted": values,
        "billing_period": date_match.group(1).replace("/", "-") if date_match else None,
        "invoice_number": invoice_match.group(1) if invoice_match else None,
        "detected_fields": found,
        "needs_manual_review": True,
        "warnings": warnings,
        "extraction_method": "regex on bill/OCR text; values are unverified",
    }


def _image_ocr(image) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("Image OCR needs pytesseract: pip install -r requirements-ocr.txt") from exc
    exe = os.getenv("TESSERACT_CMD")
    if exe:
        pytesseract.pytesseract.tesseract_cmd = exe
    try:
        return pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    except Exception as exc:
        raise RuntimeError("Tesseract OCR failed. Install its separate executable and set TESSERACT_CMD if needed.") from exc


def _read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8-sig")
    if suffix == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PDF reading needs PyMuPDF: pip install -r requirements-ocr.txt") from exc
        snippets = []
        with fitz.open(path) as doc:
            for i in range(min(3, len(doc))):
                page = doc[i]
                selectable = page.get_text("text").strip()
                if len(selectable) >= 30:
                    snippets.append(selectable)
                else:
                    from PIL import Image
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    snippets.append(_image_ocr(img))
        return "\n".join(snippets)
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Image OCR needs Pillow: pip install -r requirements-ocr.txt") from exc
    with Image.open(path) as image:
        return _image_ocr(image.convert("RGB"))


def read_bill(filepath: str | Path) -> dict:
    """Read .txt / supported image / PDF, add file SHA256 for deduplication."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() not in ALLOWED:
        raise ValueError(f"Unsupported file extension: {path.suffix}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Bill file exceeds 12 MiB limit")
    raw = path.read_bytes()
    if not raw:
        raise ValueError("Uploaded bill is empty")
    text = _read_text(path)
    if not text.strip():
        raise ValueError("No readable text found; try a clearer image or manual entry")
    parsed = parse_bill_text(text)
    parsed["file_sha256"] = hashlib.sha256(raw).hexdigest()
    parsed["original_filename"] = path.name
    return parsed
