# -*- coding: utf-8 -*-
"""
Utility helper functions
"""
import uuid
import re
from datetime import datetime
from urllib.parse import urlparse


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{uuid.uuid4().hex[:12]}"


def format_datetime(dt: datetime = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime to string

    Args:
        dt: datetime object, defaults to now
        fmt: format string

    Returns:
        Formatted string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def validate_url(url: str) -> dict:
    """
    Validate URL format

    Args:
        url: URL string

    Returns:
        dict with 'valid' boolean and optional 'error' message
    """
    if not url:
        return {'valid': False, 'error': 'URL is empty'}

    if not url.startswith(('http://', 'https://')):
        return {'valid': False, 'error': 'URL must start with http:// or https://'}

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return {'valid': False, 'error': 'Invalid URL format'}

        return {'valid': True}

    except Exception as e:
        return {'valid': False, 'error': str(e)}


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Truncate string to max length with ellipsis

    Args:
        s: Input string
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + '...'


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing unsafe characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename


def parse_bool(value) -> bool:
    """
    Parse various value types to boolean

    Args:
        value: Input value

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def chunks(lst: list, n: int):
    """
    Split list into chunks of size n

    Args:
        lst: Input list
        n: Chunk size

    Yields:
        List chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def calculate_percent(current: int, total: int) -> float:
    """
    Calculate percentage

    Args:
        current: Current value
        total: Total value

    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return round((current / total) * 100, 1)