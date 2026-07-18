from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

ALLOWED_SCHEMES = {"http", "https"}


class URLSecurityError(ValueError):
    """Raised when a URL is unsafe for server-side fetching."""


def normalize_url(raw_url: str) -> str:
    value = raw_url.strip()
    if not value:
        raise URLSecurityError("URL не может быть пустым")
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise URLSecurityError("Разрешены только http и https URL")
    if not parsed.hostname:
        raise URLSecurityError("Не удалось определить домен")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))


def _is_blocked_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return any((
        addr.is_private,
        addr.is_loopback,
        addr.is_link_local,
        addr.is_reserved,
        addr.is_multicast,
        addr.is_unspecified,
    ))


def _parse_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def validate_public_url(url: str) -> str:
    normalized = normalize_url(url)
    host = urlparse(normalized).hostname
    if host is None:
        raise URLSecurityError("Не удалось определить домен")
    direct_ip = _parse_ip(host)
    if direct_ip is not None and _is_blocked_ip(str(direct_ip)):
        raise URLSecurityError("Локальные и служебные IP-адреса запрещены")
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise URLSecurityError("Не удалось разрешить доменное имя") from exc
    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise URLSecurityError("Домен указывает на локальный или служебный IP-адрес")
    return normalized


def same_domain(url: str, base_url: str) -> bool:
    return (urlparse(url).hostname or "").lower() == (urlparse(base_url).hostname or "").lower()
