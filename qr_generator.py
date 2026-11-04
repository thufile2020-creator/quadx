"""Create a QR linking to the passport page, never to a secret document."""
from pathlib import Path
from urllib.parse import quote, urlsplit
import re
import qrcode


def make_passport_url(base_url: str, report_id: str) -> str:
    """base_url: e.g. https://yourdomain.com; local HTTP permitted for demo."""
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password:
        raise ValueError("base_url must be a plain http(s) address")
    if parts.scheme != "https" and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("For remote/public links use https; http is allowed only locally")
    if parts.query or parts.fragment:
        raise ValueError("base_url must not include query strings or fragments")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", report_id):
        raise ValueError("Invalid report_id")
    return base_url.rstrip("/") + "/passports/" + quote(report_id, safe="")


def generate_qr(url: str, output_path: str, title: str = "") -> str:
    parts = urlsplit(url)
    if parts.scheme not in ("https", "http") or not parts.netloc:
        raise ValueError("QR target must be a complete http(s) URL")
    if len(url) > 1000:
        raise ValueError("QR target is too long")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="#133d39", back_color="white").convert("RGB").save(target)
    return str(target)
