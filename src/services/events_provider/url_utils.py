from urllib.parse import parse_qs, urlparse


def extract_cursor(url: str) -> str | None:
    """Достать cursor из абсолютного URL поля `next`."""
    values = parse_qs(urlparse(url).query).get("cursor")
    return values[0] if values else None
