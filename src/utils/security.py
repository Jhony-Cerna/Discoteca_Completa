# src/utils/security.py
from urllib.parse import urlparse, urljoin
from flask import request

def is_safe_url(target):
    """Valida que la URL de redirección sea segura (mismo host)"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc