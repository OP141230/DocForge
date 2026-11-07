"""URL safety checks used before any outbound research request.

Threat model
------------
Research fetches attacker-influenced URLs (search results and URLs typed by a
user). Without a guard, ``http://127.0.0.1:8000/api/auth/me`` or
``http://169.254.169.254/latest/meta-data/`` would turn DocForge into a proxy for
the machine it runs on, and ``http://[::1]/`` or a DNS name pointing at
``10.0.0.5`` would reach the local network.

Mitigations implemented here:

* only ``http``/``https``, only ports 80/443, no embedded credentials;
* the hostname is resolved and **every** resolved address must be public;
* loopback, private, link-local, CGNAT, multicast, reserved and unspecified
  ranges are rejected (including IPv6 and IPv4-mapped IPv6);
* single-label hostnames, ``localhost``, ``*.local`` and known cloud metadata
  names are rejected;
* :mod:`app.services.source_fetcher` disables automatic redirects and re-runs
  these checks on every hop.

Known limitation (documented in docs/phase-5-research.md): we validate the
addresses we resolve, then hand the hostname to httpx, so a hostile DNS server
could in theory return a public IP for the check and a private one microseconds
later (DNS rebinding). Full protection requires pinning the socket to the
validated IP, which needs a custom transport (or an outbound proxy). The window
is small, but it is real; do not expose this backend directly to untrusted
networks without that hardening.
"""
import asyncio
import ipaddress
import socket
from typing import List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
MAX_URL_LENGTH = 2048

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
}

BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa", ".lan")


class UnsafeUrlError(ValueError):
    """Raised when a URL must not be requested."""


def normalize_url(url: str) -> str:
    """Normalize a URL for storage and de-duplication.

    Lower-cases scheme/host, drops default ports and fragments, and removes a
    trailing slash from the root path so ``https://x.com`` and ``https://x.com/``
    collapse into one record.
    """
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    if port in (80, 443) and ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        port = None

    netloc = host
    if port is not None:
        netloc = f"{host}:{port}"

    path = parts.path or "/"
    if path == "/":
        path = ""

    return urlunsplit((scheme, netloc, path, parts.query, ""))


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True when an address must never be contacted."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True

    if isinstance(ip, ipaddress.IPv4Address):
        # Carrier-grade NAT (100.64.0.0/10) is reachable infrastructure.
        if ip in ipaddress.ip_network("100.64.0.0/10"):
            return True
        # Benchmarking range.
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            return True
        # "This network" and broadcast-ish space.
        if ip in ipaddress.ip_network("0.0.0.0/8"):
            return True
    return False


def validate_url_syntax(url: str) -> Tuple[str, str]:
    """Validate a URL structurally and return ``(normalized_url, hostname)``.

    No DNS resolution happens here, so this is cheap and synchronous - use it
    for input validation, then :func:`assert_safe_destination` before fetching.
    """
    if not isinstance(url, str) or not url.strip():
        raise UnsafeUrlError("URL is empty")

    candidate = url.strip()
    if len(candidate) > MAX_URL_LENGTH:
        raise UnsafeUrlError("URL is too long")

    parts = urlsplit(candidate)
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeUrlError("Only http and https URLs are allowed")

    if parts.username or parts.password:
        raise UnsafeUrlError("URLs containing credentials are not allowed")

    host = parts.hostname
    if not host:
        raise UnsafeUrlError("URL has no hostname")

    host = host.lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES or host.endswith(BLOCKED_HOST_SUFFIXES):
        raise UnsafeUrlError("Hostname resolves to a blocked destination")

    try:
        port = parts.port
    except ValueError as exc:  # malformed port
        raise UnsafeUrlError("URL has an invalid port") from exc
    if port not in ALLOWED_PORTS:
        raise UnsafeUrlError("Only ports 80 and 443 are allowed")

    # A bare IP literal is checked directly, without DNS.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and _is_blocked_ip(literal):
        raise UnsafeUrlError("URL points to a non-public address")

    if literal is None:
        # Single-label names ("intranet", "router") are infrastructure names.
        if "." not in host:
            raise UnsafeUrlError("Hostname is not a fully qualified public name")

    return normalize_url(candidate), host


async def resolve_host(host: str) -> List[str]:
    """Resolve a hostname to all of its addresses (IPv4 + IPv6)."""
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        pass

    loop = asyncio.get_running_loop()

    def _lookup() -> List[str]:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        return sorted({info[4][0] for info in infos})

    try:
        return await asyncio.to_thread(_lookup)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Hostname could not be resolved: {host}") from exc


async def assert_safe_destination(url: str) -> Tuple[str, str, List[str]]:
    """Validate syntax **and** resolution, returning ``(url, host, addresses)``.

    Every address the host resolves to must be public: a host that resolves to
    both a public and a private address is rejected outright.
    """
    normalized, host = validate_url_syntax(url)
    addresses = await resolve_host(host)
    if not addresses:
        raise UnsafeUrlError(f"Hostname could not be resolved: {host}")

    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise UnsafeUrlError("Hostname resolved to an invalid address") from exc
        if _is_blocked_ip(ip):
            raise UnsafeUrlError("URL resolves to a non-public address")

    return normalized, host, addresses


def redact_url(url: Optional[str]) -> Optional[str]:
    """Strip credentials/query secrets before logging a URL."""
    if not url:
        return url
    parts = urlsplit(url)
    if not parts.query:
        return url
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
