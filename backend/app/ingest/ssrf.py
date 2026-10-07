import ipaddress
import socket
import ssl
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from backend.app.core.config import settings
from backend.app.core.logging import logger


class SSRFSecurityError(Exception):
    """Raised when a URL violates SSRF security boundaries."""
    pass


class OversizeFileError(Exception):
    """Raised when an imported file exceeds size limits."""
    pass


BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network (only valid as source)
    ipaddress.ip_network("10.0.0.0/8"),          # RFC 1918 private
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local / Cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),       # RFC 1918 private
    ipaddress.ip_network("192.0.0.0/24"),        # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),        # TEST-NET-1 documentation
    ipaddress.ip_network("192.88.99.0/24"),      # 6to4 relay anycast
    ipaddress.ip_network("192.168.0.0/16"),      # RFC 1918 private
    ipaddress.ip_network("198.18.0.0/15"),       # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),     # TEST-NET-2 documentation
    ipaddress.ip_network("203.0.113.0/24"),      # TEST-NET-3 documentation
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 blocked ranges
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("::/128"),              # IPv6 Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),       # IPv4-mapped IPv6 (evaluated separately)
    ipaddress.ip_network("100::/64"),            # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),       # Documentation
    ipaddress.ip_network("fc00::/7"),            # Unique local address (ULA)
    ipaddress.ip_network("fe80::/10"),           # Link-local unicast
    ipaddress.ip_network("ff00::/8"),            # Multicast
]


def is_ip_allowed(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Checks whether an IP address is a publicly routable, safe destination."""
    # Check if IPv6 has mapped IPv4 address
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        return is_ip_allowed(ip_obj.ipv4_mapped)

    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved or ip_obj.is_unspecified:
        return False

    for network in BLOCKED_NETWORKS:
        if ip_obj in network:
            return False

    return True


def validate_url_security(url: str) -> Tuple[str, str, int, str]:
    """
    Parses and verifies URL scheme and hostname.
    Resolves DNS and asserts that ALL returned IP addresses are public and safe.
    Returns: (scheme, hostname, port, resolved_ip)
    """
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported protocol scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    if not parsed.hostname:
        raise SSRFSecurityError("URL must contain a valid hostname.")

    # Disallow user credentials in URL
    if parsed.username or parsed.password:
        raise SSRFSecurityError("URLs containing credentials (user:password@host) are forbidden.")

    hostname = parsed.hostname.strip().lower()
    if hostname in ("localhost", "ip6-localhost", "ip6-loopback"):
        raise SSRFSecurityError(f"Access to '{hostname}' is forbidden.")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    # Check if hostname is directly a numeric IP
    try:
        ip_direct = ipaddress.ip_address(hostname)
        if not is_ip_allowed(ip_direct):
            raise SSRFSecurityError(f"Access to private/restricted IP address '{hostname}' is blocked.")
        return parsed.scheme.lower(), hostname, port, str(ip_direct)
    except ValueError:
        pass  # Hostname is a domain name, proceed to DNS resolution

    # Resolve hostname to all addresses
    try:
        addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Failed to resolve hostname '{hostname}': {e}")

    if not addr_info:
        raise SSRFSecurityError(f"Hostname '{hostname}' resolved to 0 addresses.")

    resolved_ips = []
    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if not is_ip_allowed(ip_obj):
                raise SSRFSecurityError(f"Hostname '{hostname}' resolves to blocked/private IP '{ip_str}'.")
            resolved_ips.append(ip_str)
        except ValueError:
            raise SSRFSecurityError(f"Invalid resolved IP '{ip_str}'.")

    # Pick the first validated IP
    chosen_ip = resolved_ips[0]
    return parsed.scheme.lower(), hostname, port, chosen_ip


@dataclass
class SafeDownloadResult:
    destination_path: Path
    total_bytes: int
    content_type: str
    final_url: str


def download_safe_url(
    url: str,
    destination: Path,
    max_bytes: Optional[int] = None,
    timeout: Optional[int] = None,
    max_redirects: Optional[int] = None
) -> SafeDownloadResult:
    """
    Safely downloads a remote media file with anti-SSRF, anti-DNS-rebinding,
    redirect validation, and maximum size enforcement.
    """
    import http.client

    if max_bytes is None:
        max_bytes = settings.MAX_UPLOAD_GB * 1024 * 1024 * 1024
    if timeout is None:
        timeout = settings.SSRF_TIMEOUT_SECONDS
    if max_redirects is None:
        max_redirects = settings.SSRF_MAX_REDIRECTS

    current_url = url
    redirect_count = 0
    destination.parent.mkdir(parents=True, exist_ok=True)

    while True:
        scheme, hostname, port, target_ip = validate_url_security(current_url)
        parsed = urllib.parse.urlparse(current_url)
        path_query = (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")

        # Anti-DNS-Rebinding Connection:
        # Connect directly to the validated IP, passing the domain name as Host header.
        conn = None
        try:
            if scheme == "https":
                context = ssl.create_default_context()
                # To prevent DNS rebinding, connect to target_ip but verify TLS cert against hostname
                sock = socket.create_connection((target_ip, port), timeout=timeout)
                sslsock = context.wrap_socket(sock, server_hostname=hostname)
                conn = http.client.HTTPSConnection(hostname, port=port, timeout=timeout)
                conn.sock = sslsock
            else:
                sock = socket.create_connection((target_ip, port), timeout=timeout)
                conn = http.client.HTTPConnection(hostname, port=port, timeout=timeout)
                conn.sock = sock

            headers = {
                "Host": hostname if (port in (80, 443)) else f"{hostname}:{port}",
                "User-Agent": "LectureDubber/1.0 (+https://lecturedubber.local)",
                "Accept": "*/*",
                "Connection": "close"
            }

            conn.request("GET", path_query, headers=headers)
            resp = conn.getresponse()

            # Handle Redirects
            if resp.status in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SSRFSecurityError(f"Too many HTTP redirects (exceeded limit of {max_redirects}).")

                location = resp.getheader("Location")
                if not location:
                    raise SSRFSecurityError(f"Redirect response {resp.status} missing Location header.")

                # Resolve relative redirect URLs against current URL
                current_url = urllib.parse.urljoin(current_url, location)
                logger.info(f"SSRF downloader following redirect ({redirect_count}/{max_redirects}) to: {current_url}")
                conn.close()
                continue

            if resp.status not in (200, 206):
                raise SSRFSecurityError(f"Remote server returned HTTP {resp.status}: {resp.reason}")

            # Check Content-Length header if present
            cl_header = resp.getheader("Content-Length")
            if cl_header:
                try:
                    content_length = int(cl_header)
                    if content_length > max_bytes:
                        raise OversizeFileError(
                            f"Remote file size ({content_length / (1024*1024):.1f} MB) exceeds maximum permitted limit ({max_bytes / (1024*1024):.1f} MB)."
                        )
                except ValueError:
                    pass

            content_type = resp.getheader("Content-Type", "application/octet-stream")

            # Stream body to disk with cumulative size counting
            downloaded_bytes = 0
            chunk_size = 64 * 1024  # 64 KB
            temp_path = destination.with_suffix(destination.suffix + ".part")

            with open(temp_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    downloaded_bytes += len(chunk)
                    if downloaded_bytes > max_bytes:
                        temp_path.unlink(missing_ok=True)
                        raise OversizeFileError(
                            f"Downloaded content exceeded maximum size limit of {max_bytes / (1024*1024):.1f} MB."
                        )
                    f.write(chunk)

            # Move .part to final destination
            temp_path.replace(destination)

            return SafeDownloadResult(
                destination_path=destination,
                total_bytes=downloaded_bytes,
                content_type=content_type,
                final_url=current_url
            )

        except (socket.timeout, TimeoutError):
            raise SSRFSecurityError(f"Timed out connecting to or reading from {hostname}.")
        except OSError as e:
            raise SSRFSecurityError(f"Network error fetching {current_url}: {e}")
        finally:
            if conn:
                conn.close()
