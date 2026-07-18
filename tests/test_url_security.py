import socket
import pytest
from src.url_security import URLSecurityError, normalize_url, validate_public_url


def test_normalize_adds_https():
    assert normalize_url("example.com") == "https://example.com/"


def test_rejects_dangerous_scheme():
    with pytest.raises(URLSecurityError):
        normalize_url("file:///etc/passwd")


def test_rejects_localhost_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("127.0.0.1", 0))])
    with pytest.raises(URLSecurityError):
        validate_public_url("http://localhost")


def test_rejects_private_ipv4():
    with pytest.raises(URLSecurityError):
        validate_public_url("http://192.168.1.10")


def test_rejects_loopback_ipv6():
    with pytest.raises(URLSecurityError):
        validate_public_url("http://[::1]/")


def test_rejects_link_local_ipv6():
    with pytest.raises(URLSecurityError):
        validate_public_url("http://[fe80::1]/")


def test_rejects_reserved_ip():
    with pytest.raises(URLSecurityError):
        validate_public_url("http://240.0.0.1/")


def test_allows_public_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("93.184.216.34", 0))])
    assert validate_public_url("https://example.com") == "https://example.com/"
