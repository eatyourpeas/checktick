"""
QR Code utilities for survey invitations.

Generates QR codes for survey links that can be embedded in emails
and displayed on the publish page.
"""

import base64
import io
import logging

import qrcode
from qrcode.image.pil import PilImage

logger = logging.getLogger(__name__)


def generate_qr_code_base64(url: str, size: int = 200) -> str:
    """Generate a QR code for a URL and return it as a base64-encoded PNG.

    Args:
        url: The URL to encode in the QR code
        size: The size of the QR code in pixels (default 200x200)

    Returns:
        Base64-encoded PNG image string (without data URI prefix)
    """
    try:
        # Create QR code with appropriate error correction
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version based on data
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # ~15% error correction
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Generate image
        img: PilImage = qr.make_image(fill_color="black", back_color="white")

        # Resize to requested size
        img = img.resize((size, size))

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to generate QR code for URL {url}: {e}")
        return ""


def generate_qr_code_data_uri(url: str, size: int = 200) -> str:
    """Generate a QR code for a URL and return it as a data URI.

    Args:
        url: The URL to encode in the QR code
        size: The size of the QR code in pixels (default 200x200)

    Returns:
        Data URI string (data:image/png;base64,...) or empty string on error
    """
    base64_data = generate_qr_code_base64(url, size)
    if base64_data:
        return f"data:image/png;base64,{base64_data}"
    return ""
