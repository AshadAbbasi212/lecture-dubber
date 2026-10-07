import io
import socket
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.ingest.ssrf import (
    validate_url_security,
    download_safe_url,
    is_ip_allowed,
    SSRFSecurityError,
    OversizeFileError,
)
import ipaddress


def test_blocked_ip_ranges():
    blocked_ips = [
        "127.0.0.1",
        "127.1.2.3",
        "10.0.0.1",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "192.168.100.50",
        "169.254.169.254",  # AWS/GCP/Azure metadata
        "169.254.1.1",      # Link-local
        "100.64.0.1",       # Carrier-grade NAT
        "0.0.0.0",
        "224.0.0.1",        # Multicast
        "255.255.255.255",  # Broadcast
        "::1",              # IPv6 loopback
        "fe80::1",          # IPv6 link-local
        "fc00::1",          # IPv6 ULA
    ]
    for ip_str in blocked_ips:
        ip_obj = ipaddress.ip_address(ip_str)
        assert not is_ip_allowed(ip_obj), f"IP {ip_str} should be blocked"


def test_allowed_public_ips():
    allowed_ips = [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",  # example.com
        "2606:4700:4700::1111",
    ]
    for ip_str in allowed_ips:
        ip_obj = ipaddress.ip_address(ip_str)
        assert is_ip_allowed(ip_obj), f"Public IP {ip_str} should be allowed"


def test_validate_url_security_rejections():
    # Scheme rejection
    with pytest.raises(SSRFSecurityError, match="Unsupported protocol scheme"):
        validate_url_security("file:///C:/Windows/win.ini")

    with pytest.raises(SSRFSecurityError, match="Unsupported protocol scheme"):
        validate_url_security("ftp://ftp.example.com/file.mp4")

    # Credentials rejection
    with pytest.raises(SSRFSecurityError, match="URLs containing credentials"):
        validate_url_security("http://admin:secret@publicsite.com/video.mp4")

    # Direct private IP rejection
    with pytest.raises(SSRFSecurityError, match="Access to private/restricted IP"):
        validate_url_security("http://127.0.0.1/secret")

    with pytest.raises(SSRFSecurityError, match="Access to private/restricted IP"):
        validate_url_security("http://192.168.1.1:8080/router")

    with pytest.raises(SSRFSecurityError, match="Access to private/restricted IP"):
        validate_url_security("http://169.254.169.254/latest/meta-data/")

    # Localhost hostname rejection
    with pytest.raises(SSRFSecurityError, match="forbidden"):
        validate_url_security("http://localhost/api")


@patch("socket.getaddrinfo")
def test_dns_resolution_to_private_ip_blocked(mock_getaddrinfo):
    # Simulate a domain that resolves to a private IP (e.g. DNS rebinding or internal DNS)
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 80))
    ]
    with pytest.raises(SSRFSecurityError, match="resolves to blocked/private IP"):
        validate_url_security("http://evil-rebound-internal.com/video.mp4")


@patch("socket.getaddrinfo")
def test_dns_resolution_dual_homed_trick_blocked(mock_getaddrinfo):
    # Simulate a domain returning one public IP and one private IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))
    ]
    with pytest.raises(SSRFSecurityError, match="resolves to blocked/private IP"):
        validate_url_security("http://dual-homed-trick.com/video.mp4")


@patch("backend.app.ingest.ssrf.validate_url_security")
@patch("socket.create_connection")
def test_download_safe_url_redirect_to_private_ip_blocked(mock_create_conn, mock_val):
    # Step 1: Initial URL validates as public
    mock_val.side_effect = [
        ("http", "example.com", 80, "93.184.216.34"),
        # Step 2: Redirect target URL raises SSRF security error
        SSRFSecurityError("Access to private/restricted IP address '127.0.0.1' is blocked.")
    ]

    mock_sock = MagicMock()
    mock_create_conn.return_value = mock_sock

    mock_resp = MagicMock()
    mock_resp.status = 302
    mock_resp.getheader.side_effect = lambda h, default=None: "http://127.0.0.1/admin" if h == "Location" else default

    with patch("http.client.HTTPConnection") as mock_http:
        instance = mock_http.return_value
        instance.getresponse.return_value = mock_resp

        dest = Path("test_download.mp4")
        with pytest.raises(SSRFSecurityError, match="Access to private/restricted IP address '127.0.0.1' is blocked"):
            download_safe_url("http://example.com/redirect", dest)


@patch("backend.app.ingest.ssrf.validate_url_security")
@patch("socket.create_connection")
def test_download_safe_url_oversize_rejection(mock_create_conn, mock_val, tmp_path):
    mock_val.return_value = ("http", "example.com", 80, "93.184.216.34")

    mock_sock = MagicMock()
    mock_create_conn.return_value = mock_sock

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.getheader.side_effect = lambda h, default=None: "5000000000" if h == "Content-Length" else default

    with patch("http.client.HTTPConnection") as mock_http:
        instance = mock_http.return_value
        instance.getresponse.return_value = mock_resp

        dest = tmp_path / "oversize.mp4"
        with pytest.raises(OversizeFileError, match="exceeds maximum permitted limit"):
            download_safe_url("http://example.com/huge.mp4", dest, max_bytes=1000)
